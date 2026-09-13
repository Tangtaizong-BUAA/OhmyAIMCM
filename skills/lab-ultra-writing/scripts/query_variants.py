#!/usr/bin/env python3
"""Offline, bounded lookup for source-linked writing-technique variants."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


VARIANTS_NAME = "technique-variants.json"
CARDS_NAME = "exposition-cards.json"
REQUIRED_SOURCE = ("source_id", "source_sha256", "analysis_path", "field")


def _paths() -> tuple[Path, Path]:
    references = Path(__file__).resolve().parent.parent / "references"
    return references / VARIANTS_NAME, references / CARDS_NAME


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _payload(message: str, **values: Any) -> dict[str, Any]:
    result = {"message": message}
    result.update(values)
    return result


def _emit(result: dict[str, Any], status: int = 0) -> int:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return status


def _health(variants_path: Path, cards_path: Path) -> tuple[bool, list[str], dict[str, Any] | None]:
    errors: list[str] = []
    try:
        data = _load(variants_path)
    except Exception as exc:  # pragma: no cover - message is user-facing
        return False, [f"cannot load variants: {exc}"], None
    try:
        cards_data = _load(cards_path)
    except Exception as exc:  # pragma: no cover - message is user-facing
        return False, [f"cannot load cards: {exc}"], data if isinstance(data, dict) else None

    if not isinstance(data, dict) or not isinstance(data.get("variants"), list) or not isinstance(data.get("scope"), str) or not data["scope"].strip():
        errors.append("schema requires non-empty scope and variants list")
        return False, errors, data if isinstance(data, dict) else None
    cards = cards_data.get("cards") if isinstance(cards_data, dict) else None
    card_ids = {c.get("id") for c in cards or [] if isinstance(c, dict)}
    seen: set[str] = set()
    for index, variant in enumerate(data["variants"]):
        prefix = f"variants[{index}]"
        if not isinstance(variant, dict):
            errors.append(f"{prefix} is not an object")
            continue
        variant_id = variant.get("id")
        if not isinstance(variant_id, str) or not variant_id.strip():
            errors.append(f"{prefix}.id is empty")
        elif variant_id in seen:
            errors.append(f"duplicate variant id: {variant_id}")
        else:
            seen.add(variant_id)
        card_id = variant.get("card_id")
        if card_id not in card_ids:
            errors.append(f"{prefix}.card_id has no parent card: {card_id}")
        if not isinstance(variant.get("rule"), str) or not variant["rule"].strip():
            errors.append(f"{prefix}.rule is empty")
        if not isinstance(variant.get("review_status"), str) or not variant["review_status"].strip():
            errors.append(f"{prefix}.review_status is empty")
        source = variant.get("source")
        if not isinstance(source, dict):
            errors.append(f"{prefix}.source is missing")
            continue
        missing = [key for key in REQUIRED_SOURCE if key not in source or source[key] in (None, "")]
        if missing:
            errors.append(f"{prefix}.source missing: {','.join(missing)}")
        if source.get('field') == 'moves' and any(key not in source for key in ('move_index','start','end')):
            errors.append(f"{prefix}.source move requires index and source line range")
        if source.get('field') != 'moves' and not source.get('locator') and not ('start' in source and 'end' in source):
            errors.append(f"{prefix}.source nonmove requires an analysis-field locator")
        digest = source.get("source_sha256")
        if digest and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)):
            errors.append(f"{prefix}.source.source_sha256 is not a 64-hex hash")
        for key in ("move_index", "start", "end"):
            if key in source and (not isinstance(source[key], int) or isinstance(source[key], bool) or source[key] < 0):
                errors.append(f"{prefix}.source.{key} is not a non-negative integer")
        if isinstance(source.get("start"), int) and isinstance(source.get("end"), int) and source["end"] < source["start"]:
            errors.append(f"{prefix}.source end precedes start")
    provenance=data.get('provenance',{})
    for v in data['variants']:
        for member in v.get('member_ids',[]):
            if member not in provenance:errors.append(f"missing source member: {member}")
    summary = {"variant_count": len(data["variants"]), "parent_card_count": len(card_ids), "unique_id_count": len(seen),
               "scope":"Local structure and source links only; not a new semantic or scientific review."}
    return not errors, errors, summary


def main(argv: list[str] | None = None) -> int:
    variants_path, cards_path = _paths()
    parser = argparse.ArgumentParser(description="Query source-linked writing-technique variants (literal substring match).")
    subparsers = parser.add_subparsers(dest="command", required=True)
    query = subparsers.add_parser("query", help="search rule and card_id by literal keyword")
    query.add_argument("keyword")
    query.add_argument("--card", dest="card_id")
    query.add_argument("--limit", type=int, default=3)
    show = subparsers.add_parser("show", help="show exactly one variant")
    show.add_argument("variant_id")
    source = subparsers.add_parser("source", help="show one exact candidate's provenance")
    source.add_argument("candidate_id")
    subparsers.add_parser("health", help="validate the local variant and parent-card files")
    args = parser.parse_args(argv)

    if args.command == "health":
        ok, errors, summary = _health(variants_path, cards_path)
        if ok:
            return _emit(_payload("health ok", valid=True, **(summary or {})))
        return _emit(_payload("health failed", valid=False, errors=errors), 1)

    try:
        data = _load(variants_path)
    except Exception as exc:
        return _emit(_payload(f"cannot load {VARIANTS_NAME}: {exc}"), 1)
    variants = data.get("variants", []) if isinstance(data, dict) else []
    def compact(v):
        return {**{k:value for k,value in v.items() if k!='member_ids'},
                'source_member_count':len(v.get('member_ids',[])),
                'source_note':'source gives one locator; all member provenance is stored in technique-variants.json.'}
    if args.command=='source':
        record=data.get('provenance',{}).get(args.candidate_id)
        return _emit(_payload('Exact candidate provenance; no inferred source.',candidate_id=args.candidate_id,source=record),0 if record else 1)
    if args.command == "query":
        if not args.keyword.strip() or not 1 <= args.limit <= 10:
            return _emit(_payload("--limit 必须在1到10之间。", mode="query", keyword=args.keyword, card_id=args.card_id, limit=args.limit, results=[]), 2)
        needle = args.keyword.casefold()
        matches = [v for v in variants if needle in str(v.get("rule", "")).casefold() or needle in str(v.get("card_id", "")).casefold()]
        if args.card_id is not None:
            matches = [v for v in matches if v.get("card_id") == args.card_id]
        result = [compact(v) for v in matches[: args.limit]]
        message = "字面匹配；未找到结果，不强行选用。" if not result else "字面匹配；结果仅供按需回查，不强行选用。"
        return _emit(_payload(message, mode="query", keyword=args.keyword, card_id=args.card_id, limit=args.limit, match_count=len(matches), results=result))

    found = [v for v in variants if v.get("id") == args.variant_id]
    if not found:
        return _emit(_payload("未找到精确 variant_id；不强行选用。", mode="show", variant_id=args.variant_id, results=[]), 1)
    return _emit(_payload("精确 variant_id 回查。", mode="show", variant_id=args.variant_id, results=[compact(found[0])]))


if __name__ == "__main__":
    sys.exit(main())
