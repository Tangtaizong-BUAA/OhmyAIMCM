#!/usr/bin/env python3
"""Shared deterministic runtime for the CUMCM typesetter skill.

Only the Python standard library and command-line tools already required by the
skill (Pandoc, XeLaTeX/latexmk, Poppler) are used here.
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LATEX_ASSET_DIR = SKILL_DIR / "assets" / "latex"
DEFAULT_CONFIG_PATH = LATEX_ASSET_DIR / "default-config.json"
MARKDOWN_FORMAT = (
    "markdown+yaml_metadata_block+fenced_divs+bracketed_spans+pipe_tables"
    "+table_captions+tex_math_dollars+implicit_figures+footnotes+citations"
)
GENERATED_FILES = {
    "paper.tex",
    "paper.pdf",
    "paper.aux",
    "paper.fdb_latexmk",
    "paper.fls",
    "paper.log",
    "paper.out",
    "paper.synctex.gz",
    "input.ast.json",
    "render-input.ast.json",
    "rendered.ast.json",
    "assets-manifest.json",
    "content-lock.json",
    "effective-config.json",
    "render-config.tex",
    "build-report.json",
    "layout-audit.json",
    "OhmyAIMCM-paper.cls",
    "OhmyAIMCM-style.sty",
    "semantic.lua",
    "ai-declaration.json",
    "AI工具使用详情.pdf",
}
RUNTIME_POLICY_COMPILER_NAME = "layout_lab.runtime_policy_compiler"
RUNTIME_POLICY_COMPILER_VERSION = "1.0.0"


class TypesetterError(RuntimeError):
    """A controlled user-facing runtime error."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    location: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.location:
            result["location"] = self.location
        return result


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise TypesetterError(f"Required executable not found: {name}")
    return path


def run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd else None,
            env=env,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise TypesetterError(f"Could not execute {command[0]}: {exc}") from exc
    if check and completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        stdout = completed.stdout.decode("utf-8", errors="replace").strip()
        detail = stderr or stdout or f"exit code {completed.returncode}"
        raise TypesetterError(f"Command failed ({' '.join(command)}):\n{detail[-6000:]}")
    return completed


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TypesetterError(f"Could not load {label} from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TypesetterError(f"{label} root must be a JSON object: {path}")
    return value


def _normalize_external_rules(value: dict[str, Any]) -> dict[str, Any]:
    hard = value.get("hard_constraints", value)
    if not isinstance(hard, dict):
        raise TypesetterError("rules hard_constraints must be an object")
    result: dict[str, Any] = {}
    aliases = {
        "anonymous": "anonymous",
        "abstract_max_pages": "abstract_max_pages",
        "body_max_pages": "body_max_pages",
        "table_of_contents_allowed": "allow_toc",
        "paper_max_bytes": "pdf_max_bytes",
    }
    for external, internal in aliases.items():
        if external in hard:
            result[internal] = hard[external]
    if "paper_size" in hard:
        result["paper_size"] = str(hard["paper_size"]).lower()
    if "electronic_first_page" in hard:
        result["abstract_first_page"] = hard["electronic_first_page"] == "abstract"
        result["abstract_required"] = hard["electronic_first_page"] == "abstract"
    margins = hard.get("minimum_margin_mm")
    if isinstance(margins, dict) and margins:
        numeric = [float(item) for item in margins.values() if isinstance(item, (int, float)) and not isinstance(item, bool)]
        if numeric:
            result["minimum_margin_mm"] = max(numeric)
    elif isinstance(margins, (int, float)) and not isinstance(margins, bool):
        result["minimum_margin_mm"] = float(margins)
    return result


def _normalize_style_tokens(value: dict[str, Any]) -> dict[str, Any]:
    tokens = value.get("style_tokens", value)
    if not isinstance(tokens, dict):
        raise TypesetterError("style_tokens must be an object")
    # The canonical research/runtime contract is the nested Style Tokens v1
    # schema.  Retain the legacy flat adapter only for older local fixtures.
    if any(key in tokens for key in ("page", "body", "paragraphs")):
        page = tokens.get("page", {})
        body = tokens.get("body", {})
        title = tokens.get("title", {})
        abstract = tokens.get("abstract", {})
        headings = tokens.get("headings", {})
        captions = tokens.get("captions", {})
        math_tokens = tokens.get("math", {})
        paragraphs = tokens.get("paragraphs", {})
        flow = tokens.get("flow", {})
        if not all(
            isinstance(section, dict)
            for section in (
                page,
                body,
                title,
                abstract,
                headings,
                captions,
                math_tokens,
                paragraphs,
                flow,
            )
        ):
            raise TypesetterError("canonical style token sections must be objects")
        normalized = {
            "margin_top_mm": page.get("margin_top_mm"),
            "margin_bottom_mm": page.get("margin_bottom_mm"),
            "margin_left_mm": page.get("margin_left_mm"),
            "margin_right_mm": page.get("margin_right_mm"),
            "body_font_pt": body.get("font_size_pt"),
            "line_height_ratio": body.get("leading_ratio"),
            "cjk_font": body.get("cjk_font"),
            "latin_font": body.get("latin_font"),
            "math_font": body.get("math_font"),
            "h1_size_ratio": headings.get("h1_size_ratio"),
            "h2_size_ratio": headings.get("h2_size_ratio"),
            "h3_size_ratio": headings.get("h3_size_ratio"),
            "h1_before_em": headings.get("h1_before_em"),
            "h1_after_em": headings.get("h1_after_em"),
            "h2_before_em": headings.get("h2_before_em"),
            "h2_after_em": headings.get("h2_after_em"),
            "display_above_em": math_tokens.get("display_above_em"),
            "display_below_em": math_tokens.get("display_below_em"),
            "array_stretch": math_tokens.get("array_stretch"),
            "paragraph_indent_em": paragraphs.get("indent_em"),
            "paragraph_skip_em": paragraphs.get("paragraph_skip_em"),
            "first_after_heading_indent": paragraphs.get("first_after_heading_indent"),
            "widow_penalty": flow.get("widow_penalty"),
            "club_penalty": flow.get("club_penalty"),
            "heading_keep_lines": flow.get("heading_keep_lines"),
            "abstract_page_break": True,
        }
        optional = {
            "title_font_role": title.get("font_role"),
            "title_alignment": title.get("alignment"),
            "title_size_ratio": title.get("size_ratio"),
            "abstract_heading_font_role": abstract.get("heading_font_role"),
            "abstract_heading_alignment": abstract.get("heading_alignment"),
            "h1_font_role": headings.get("h1_font_role"),
            "h1_alignment": headings.get("h1_alignment"),
            "h2_font_role": headings.get("h2_font_role"),
            "h2_alignment": headings.get("h2_alignment"),
            "section_numbering_style": headings.get("numbering_style"),
            "caption_font_ratio": captions.get("font_size_ratio"),
            "figure_caption_alignment": captions.get("figure_alignment"),
            "table_caption_alignment": captions.get("table_alignment"),
        }
        normalized.update({key: value for key, value in optional.items() if value is not None})
        return normalized
    aliases = {
        "body_font_size_pt": "body_font_pt",
        "line_spacing_ratio": "line_height_ratio",
        "paragraph_indent": "paragraph_indent_em",
        "paragraph_spacing_em": "paragraph_skip_em",
    }
    normalized = dict(tokens)
    for external, internal in aliases.items():
        if external in normalized and internal not in normalized:
            normalized[internal] = normalized.pop(external)
    return normalized


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise TypesetterError(f"{label} must be a SHA-256 value")
    return value


def _style_token_leaf_paths(style_tokens: dict[str, Any]) -> set[str]:
    leaves: set[str] = set()

    def visit(value: Any, prefix: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                visit(item, path)
            return
        leaves.add(prefix)

    visit(style_tokens, "")
    return leaves - {"schema_version", "profile_id"}


def _runtime_token_path_matches(pattern: str, path: str) -> bool:
    if pattern == path:
        return True
    return pattern.endswith(".*") and bool(pattern[:-2]) and path.startswith(
        f"{pattern[:-2]}."
    )


def _validate_runtime_rule_provenance(
    rule_provenance: list[Any],
    *,
    selected_factor_ids: list[str],
    style_tokens: dict[str, Any],
) -> None:
    selected = set(selected_factor_ids)
    referenced_factors: set[str] = set()
    rule_ids: set[str] = set()
    coverage: dict[str, list[str]] = {
        path: [] for path in sorted(_style_token_leaf_paths(style_tokens))
    }
    for rule in rule_provenance:
        if not isinstance(rule, dict):
            raise TypesetterError("semantic policy rule_provenance entries must be objects")
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id or rule_id in rule_ids:
            raise TypesetterError(
                "semantic policy rule_provenance requires unique rule_id values"
            )
        rule_ids.add(rule_id)
        token_paths = rule.get("token_paths")
        if (
            not isinstance(token_paths, list)
            or not token_paths
            or any(not isinstance(path, str) or not path for path in token_paths)
            or len(token_paths) != len(set(token_paths))
        ):
            raise TypesetterError(
                f"semantic policy runtime rule {rule_id!r} has invalid token_paths"
            )
        provenance_class = rule.get("provenance_class")
        if provenance_class == "learned_factor":
            factor_id = rule.get("factor_id")
            if not isinstance(factor_id, str) or factor_id not in selected:
                raise TypesetterError(
                    f"semantic policy runtime rule {rule_id!r} references an unselected factor"
                )
            if "constraint_id" in rule:
                raise TypesetterError(
                    f"learned runtime rule {rule_id!r} cannot claim a hard constraint"
                )
            referenced_factors.add(factor_id)
        elif provenance_class == "hard_constraint":
            constraint_id = rule.get("constraint_id")
            if not isinstance(constraint_id, str) or not constraint_id:
                raise TypesetterError(
                    f"hard-constraint runtime rule {rule_id!r} requires constraint_id"
                )
            if "factor_id" in rule:
                raise TypesetterError(
                    f"hard-constraint runtime rule {rule_id!r} cannot masquerade as learned"
                )
        else:
            raise TypesetterError(
                f"semantic policy runtime rule {rule_id!r} has invalid provenance_class"
            )
        for pattern in token_paths:
            matches = [
                path
                for path in coverage
                if _runtime_token_path_matches(pattern, path)
            ]
            if not matches:
                raise TypesetterError(
                    f"semantic policy runtime rule {rule_id!r} references no Style Token"
                )
            for path in matches:
                coverage[path].append(rule_id)

    missing = [path for path, owners in coverage.items() if not owners]
    overlapping = [path for path, owners in coverage.items() if len(owners) > 1]
    if missing:
        raise TypesetterError(
            "semantic policy Style Tokens lack provenance ownership: "
            + ", ".join(missing)
        )
    if overlapping:
        raise TypesetterError(
            "semantic policy Style Tokens have overlapping provenance ownership: "
            + ", ".join(overlapping)
        )
    unused = selected - referenced_factors
    if unused:
        raise TypesetterError(
            "semantic policy selected factors are unused by runtime rules: "
            + ", ".join(sorted(unused))
        )


def _normalize_semantic_policy_v2(
    value: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify a content-addressed compiled policy before applying any token."""

    if value.get("policy_type") != "journal_semantic_layout_projection_v2":
        raise TypesetterError("unsupported semantic policy type")
    if value.get("status") != "compiled_validated_consensus":
        raise TypesetterError("semantic policy is not a compiled validated consensus")
    if value.get("runtime_export_eligible") is not True:
        raise TypesetterError("semantic policy is not eligible for runtime export")
    if value.get("fallback_profile") != "balanced-cn":
        raise TypesetterError("semantic policy must retain balanced-cn as its fallback")

    source = value.get("source_artifact")
    admission = value.get("source_admission")
    projection = value.get("runtime_projection")
    integrity = value.get("integrity")
    human_veto = value.get("human_veto")
    if not all(
        isinstance(section, dict)
        for section in (source, admission, projection, integrity, human_veto)
    ):
        raise TypesetterError(
            "compiled semantic policy is missing a required integrity section"
        )
    assert isinstance(source, dict)
    assert isinstance(admission, dict)
    assert isinstance(projection, dict)
    assert isinstance(integrity, dict)
    assert isinstance(human_veto, dict)

    if (
        admission.get("runtime_export_eligible") is not True
        or admission.get("consensus_transferable") is not True
    ):
        raise TypesetterError("source consensus is not transferable")
    source_status = admission.get("status")
    if not isinstance(source_status, str) or not source_status.startswith("validated_"):
        raise TypesetterError("source consensus does not have validated status")
    if integrity.get("algorithm") != "sha256-canonical-json-v1":
        raise TypesetterError("unsupported semantic policy integrity algorithm")
    compiler = value.get("compiler")
    if compiler != {
        "name": RUNTIME_POLICY_COMPILER_NAME,
        "version": RUNTIME_POLICY_COMPILER_VERSION,
    }:
        raise TypesetterError("unsupported semantic policy compiler identity")
    if (
        integrity.get("compiler_name") != RUNTIME_POLICY_COMPILER_NAME
        or integrity.get("compiler_version") != RUNTIME_POLICY_COMPILER_VERSION
    ):
        raise TypesetterError("semantic policy compiler integrity mismatch")

    style = projection.get("style_tokens")
    quality_targets = projection.get("quality_targets")
    profile_id = projection.get("profile_id")
    if not isinstance(style, dict) or not isinstance(quality_targets, dict):
        raise TypesetterError(
            "compiled semantic policy must retain Style Tokens and quality_targets"
        )
    if not quality_targets:
        raise TypesetterError("compiled semantic policy quality_targets must not be empty")
    if not isinstance(profile_id, str) or style.get("profile_id") != profile_id:
        raise TypesetterError("semantic policy style_tokens profile_id mismatch")
    selected_factor_ids = value.get("selected_factor_ids")
    if (
        not isinstance(selected_factor_ids, list)
        or not selected_factor_ids
        or any(
            not isinstance(factor_id, str) or not factor_id
            for factor_id in selected_factor_ids
        )
        or len(selected_factor_ids) != len(set(selected_factor_ids))
    ):
        raise TypesetterError("compiled semantic policy selected_factor_ids are invalid")
    rule_provenance = value.get("rule_provenance")
    if not isinstance(rule_provenance, list) or not rule_provenance:
        raise TypesetterError("compiled semantic policy rule_provenance is missing")
    _validate_runtime_rule_provenance(
        rule_provenance,
        selected_factor_ids=selected_factor_ids,
        style_tokens=style,
    )

    source_hash = _require_sha256(source.get("sha256"), "source artifact hash")
    _require_sha256(source.get("canonical_sha256"), "canonical source artifact hash")
    source_model_id = _require_sha256(
        value.get("source_model_id"), "source research model identity"
    )
    expected_style_hash = sha256_bytes(canonical_json_bytes(style))
    expected_quality_hash = sha256_bytes(canonical_json_bytes(quality_targets))
    payload = {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key not in {"human_veto", "integrity"}
    }
    expected_payload_hash = sha256_bytes(canonical_json_bytes(payload))
    expected_veto_hash = sha256_bytes(canonical_json_bytes(human_veto))

    bound_payload_hash = _require_sha256(
        integrity.get("accepted_policy_payload_sha256"), "policy payload hash"
    )
    bound_style_hash = _require_sha256(
        integrity.get("accepted_style_tokens_sha256"), "Style Token hash"
    )
    bound_quality_hash = _require_sha256(
        integrity.get("accepted_quality_targets_sha256"), "quality target hash"
    )
    bound_source_hash = _require_sha256(
        integrity.get("accepted_source_artifact_sha256"), "bound source artifact hash"
    )
    bound_veto_hash = _require_sha256(
        integrity.get("human_veto_sha256"), "human veto hash"
    )
    if bound_payload_hash != expected_payload_hash:
        raise TypesetterError("semantic policy payload integrity mismatch")
    if bound_style_hash != expected_style_hash:
        raise TypesetterError("semantic policy Style Token integrity mismatch")
    if bound_quality_hash != expected_quality_hash:
        raise TypesetterError("semantic policy quality target integrity mismatch")
    if bound_source_hash != source_hash:
        raise TypesetterError("semantic policy source artifact integrity mismatch")
    if bound_veto_hash != expected_veto_hash:
        raise TypesetterError("semantic policy human veto integrity mismatch")

    policy_id = value.get("policy_id")
    if not isinstance(policy_id, str) or not policy_id:
        raise TypesetterError("semantic policy requires a policy_id")
    if human_veto.get("status") != "accepted":
        raise TypesetterError("semantic policy human aesthetic veto is not accepted")
    if human_veto.get("training_eligible") is not False:
        raise TypesetterError("human veto evidence must remain ineligible for training")
    if human_veto.get("accepted_policy_id") != policy_id:
        raise TypesetterError("human veto policy_id does not match the semantic policy")
    if human_veto.get("accepted_runtime_profile_id") != profile_id:
        raise TypesetterError("human veto profile_id does not match the projection")
    exact_bindings = {
        "accepted_policy_payload_sha256": expected_payload_hash,
        "accepted_style_tokens_sha256": expected_style_hash,
        "accepted_quality_targets_sha256": expected_quality_hash,
        "accepted_source_artifact_sha256": source_hash,
    }
    for field, expected in exact_bindings.items():
        if human_veto.get(field) != expected:
            raise TypesetterError(
                f"human veto {field} does not bind the exact semantic policy"
            )

    metadata = {
        "policy_id": policy_id,
        "policy_type": value["policy_type"],
        "source_model_id": source_model_id,
        "source_artifact_sha256": source_hash,
        "status": value["status"],
        "semantic_scope": value.get("semantic_scope"),
        "runtime_profile_id": profile_id,
        "fallback_profile": value["fallback_profile"],
        "human_veto_status": human_veto["status"],
        "human_veto_pair_id": human_veto.get("pair_id"),
        "policy_payload_sha256": expected_payload_hash,
        "style_tokens_sha256": expected_style_hash,
        "quality_targets_sha256": expected_quality_hash,
        "quality_targets": copy.deepcopy(quality_targets),
        "rule_provenance": copy.deepcopy(rule_provenance),
        "selected_factor_ids": list(selected_factor_ids),
        "compiler": copy.deepcopy(compiler),
        "integrity_status": "verified_content_addressed_v2",
        "automatic_promotion_eligible": True,
    }
    return _normalize_style_tokens(style), metadata


def _normalize_semantic_policy_v1(
    value: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if value.get("schema_version") != "1.0.0":
        raise TypesetterError("semantic policy schema_version must be 1.0.0")
    if value.get("policy_type") != "journal_semantic_layout_projection_v1":
        raise TypesetterError("unsupported semantic policy type")
    if value.get("status") != "validated_core_robust":
        raise TypesetterError(
            "semantic policy has not passed repeated-split validation"
        )
    if value.get("runtime_export_eligible") is not True:
        raise TypesetterError("semantic policy is not eligible for runtime export")
    if value.get("fallback_profile") != "balanced-cn":
        raise TypesetterError("semantic policy must retain balanced-cn as its fallback")
    validation = value.get("validation")
    if not isinstance(validation, dict):
        raise TypesetterError("semantic policy validation must be an object")
    if validation.get("semantic_scope") != "structure_role_only":
        raise TypesetterError(
            "runtime accepts only the validated structure-role semantic core"
        )
    if (
        int(validation.get("document_grouped_split_count", 0)) < 5
        or int(validation.get("passing_splits", 0)) < 5
    ):
        raise TypesetterError("semantic policy requires five passing grouped splits")
    source_model_id = value.get("source_model_id")
    if (
        not isinstance(source_model_id, str)
        or re.fullmatch(r"[0-9a-f]{64}", source_model_id) is None
    ):
        raise TypesetterError("semantic policy source_model_id must be a SHA-256 id")
    projection = value.get("runtime_projection")
    if not isinstance(projection, dict):
        raise TypesetterError("semantic policy runtime_projection must be an object")
    profile_id = projection.get("profile_id")
    style = projection.get("style_tokens")
    if not isinstance(profile_id, str) or not profile_id:
        raise TypesetterError("semantic policy projection requires a profile_id")
    if not isinstance(style, dict) or style.get("profile_id") != profile_id:
        raise TypesetterError("semantic policy style_tokens profile_id mismatch")
    policy_id = value.get("policy_id")
    if not isinstance(policy_id, str) or not policy_id:
        raise TypesetterError("semantic policy requires a policy_id")
    human_veto = value.get("human_veto")
    if not isinstance(human_veto, dict):
        raise TypesetterError(
            "semantic policy requires an accepted human aesthetic veto"
        )
    if human_veto.get("status") != "accepted":
        raise TypesetterError("semantic policy human aesthetic veto is not accepted")
    if human_veto.get("training_eligible") is not False:
        raise TypesetterError(
            "human veto evidence must remain ineligible for model training"
        )
    if human_veto.get("accepted_policy_id") != policy_id:
        raise TypesetterError("human veto policy_id does not match the semantic policy")
    if human_veto.get("accepted_runtime_profile_id") != profile_id:
        raise TypesetterError(
            "human veto profile_id does not match the runtime projection"
        )
    decision = human_veto.get("decision")
    winning_side = human_veto.get("winning_side")
    if decision not in {"left_better", "right_better"}:
        raise TypesetterError("human veto must record a decisive blinded comparison")
    expected_side = "left" if decision == "left_better" else "right"
    if winning_side != expected_side:
        raise TypesetterError("human veto decision and winning_side are inconsistent")
    required_text_fields = (
        "pair_id",
        "document_id",
        "created_at",
        "strength",
        "winning_role",
        "rejected_role",
    )
    if any(
        not isinstance(human_veto.get(field), str) or not human_veto[field]
        for field in required_text_fields
    ):
        raise TypesetterError("human veto is missing required review identity fields")
    hash_fields = (
        "left_reviewed_assets_sha256",
        "left_pdf_sha256",
        "right_reviewed_assets_sha256",
        "right_pdf_sha256",
        "preference_record_sha256",
        "final_veto_queue_sha256",
        "blind_mapping_sha256",
    )
    if any(
        not isinstance(human_veto.get(field), str)
        or re.fullmatch(r"[0-9a-f]{64}", human_veto[field]) is None
        for field in hash_fields
    ):
        raise TypesetterError("human veto evidence hashes must be SHA-256 values")
    metadata = {
        "policy_id": policy_id,
        "policy_type": value["policy_type"],
        "source_model_id": source_model_id,
        "status": value["status"],
        "semantic_scope": validation["semantic_scope"],
        "runtime_profile_id": profile_id,
        "fallback_profile": value["fallback_profile"],
        "human_veto_status": human_veto["status"],
        "human_veto_pair_id": human_veto["pair_id"],
        "human_veto_decision": decision,
        "human_veto_preference_sha256": human_veto["preference_record_sha256"],
        "integrity_status": "legacy_unverified_v1",
        "automatic_promotion_eligible": False,
    }
    return _normalize_style_tokens(style), metadata


def _normalize_semantic_policy(
    value: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    schema_version = value.get("schema_version")
    if schema_version == "2.0.0":
        return _normalize_semantic_policy_v2(value)
    return _normalize_semantic_policy_v1(value)


def load_config(
    path: Path | None,
    *,
    rules_path: Path | None = None,
    style_tokens_path: Path | None = None,
    semantic_policy_path: Path | None = None,
) -> dict[str, Any]:
    # Owner selection (2026-09-06), not promotion to validated v2 consensus.
    # Explicit configs/styles retain their existing override semantics.
    if path is None and style_tokens_path is None and semantic_policy_path is None:
        semantic_policy_path = SKILL_DIR / "assets/models/semantic-layout-policy-v1.json"
    if style_tokens_path and semantic_policy_path:
        raise TypesetterError(
            "choose either --style-tokens or --semantic-policy, not both"
        )
    try:
        default = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
        override = json.loads(path.read_text(encoding="utf-8")) if path else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise TypesetterError(f"Could not load configuration: {exc}") from exc
    if not isinstance(default, dict) or not isinstance(override, dict):
        raise TypesetterError("Configuration root must be a JSON object")
    merged = deep_merge(default, override)
    if rules_path:
        merged["rules"] = deep_merge(
            merged["rules"], _normalize_external_rules(_read_json_object(rules_path, "rules"))
        )
    if style_tokens_path:
        merged["style_tokens"] = deep_merge(
            merged["style_tokens"],
            _normalize_style_tokens(_read_json_object(style_tokens_path, "style tokens")),
        )
    if semantic_policy_path:
        projected, metadata = _normalize_semantic_policy(
            _read_json_object(semantic_policy_path, "semantic policy")
        )
        merged["style_tokens"] = deep_merge(merged["style_tokens"], projected)
        merged["model_policy"] = metadata
        # Keep the accepted legacy research artifact immutable. This later owner
        # preference modifies only its local default projection, not its evidence
        # or the unrelated explicitly selected hybrid/v2/custom profiles.
        owner_policy = SKILL_DIR / "assets/models/semantic-layout-policy-v1.json"
        if path is None and semantic_policy_path.resolve() == owner_policy.resolve():
            original = merged["style_tokens"]["table_caption_alignment"]
            merged["style_tokens"]["table_caption_alignment"] = "centered"
            merged["owner_style_overrides"] = [{
                "token": "table_caption_alignment", "base_value": original,
                "effective_value": "centered", "authority": "owner_request_20260909",
                "evidence_class": "explicit_preference_not_learned",
                "base_veto_scope": "unchanged_legacy_projection_only",
            }]
    findings = validate_config(merged)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        lines = "\n".join(f"- {item.code}: {item.message}" for item in errors)
        raise TypesetterError(f"Invalid configuration:\n{lines}")
    return merged


def _number(
    value: Any,
    path: str,
    minimum: float,
    maximum: float,
    findings: list[Finding],
) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        findings.append(Finding("error", "CONFIG_TYPE", "must be a number", path))
        return None
    number = float(value)
    if not minimum <= number <= maximum:
        findings.append(
            Finding(
                "error",
                "CONFIG_RANGE",
                f"must be between {minimum:g} and {maximum:g}",
                path,
            )
        )
    return number


def _choice(
    value: Any,
    path: str,
    choices: set[str],
    findings: list[Finding],
) -> str | None:
    if not isinstance(value, str) or value not in choices:
        findings.append(
            Finding(
                "error",
                "CONFIG_CHOICE",
                f"must be one of {', '.join(sorted(choices))}",
                path,
            )
        )
        return None
    return value


def validate_config(config: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if config.get("version") != 1:
        findings.append(
            Finding("error", "CONFIG_VERSION", "only configuration version 1 is supported", "version")
        )
    rules = config.get("rules")
    style = config.get("style_tokens")
    lock = config.get("content_lock")
    if not isinstance(rules, dict):
        findings.append(Finding("error", "CONFIG_TYPE", "must be an object", "rules"))
        rules = {}
    if not isinstance(style, dict):
        findings.append(Finding("error", "CONFIG_TYPE", "must be an object", "style_tokens"))
        style = {}
    if not isinstance(lock, dict):
        findings.append(Finding("error", "CONFIG_TYPE", "must be an object", "content_lock"))
        lock = {}

    if rules.get("paper_size") != "a4":
        findings.append(
            Finding("error", "PAPER_SIZE", "CUMCM runtime only accepts A4", "rules.paper_size")
        )
    minimum_margin = _number(
        rules.get("minimum_margin_mm"), "rules.minimum_margin_mm", 25.0, 45.0, findings
    )
    for side in ("top", "bottom", "left", "right"):
        margin = _number(
            style.get(f"margin_{side}_mm"),
            f"style_tokens.margin_{side}_mm",
            25.0,
            45.0,
            findings,
        )
        if margin is not None and minimum_margin is not None and margin < minimum_margin:
            findings.append(
                Finding(
                    "error",
                    "MARGIN_MINIMUM",
                    f"must be at least rules.minimum_margin_mm ({minimum_margin:g})",
                    f"style_tokens.margin_{side}_mm",
                )
            )
    _number(style.get("body_font_pt"), "style_tokens.body_font_pt", 9.5, 12.0, findings)
    _number(
        style.get("line_height_ratio"),
        "style_tokens.line_height_ratio",
        1.25,
        1.65,
        findings,
    )
    paragraph_indent = _number(
        style.get("paragraph_indent_em"),
        "style_tokens.paragraph_indent_em",
        0.0,
        2.5,
        findings,
    )
    paragraph_skip = _number(
        style.get("paragraph_skip_em"),
        "style_tokens.paragraph_skip_em",
        0.0,
        0.8,
        findings,
    )
    if (
        paragraph_indent is not None
        and paragraph_skip is not None
        and paragraph_indent < 1.0
        and paragraph_skip < 0.25
    ):
        findings.append(
            Finding(
                "error",
                "PARAGRAPH_SEPARATION",
                "indent below 1em requires at least 0.25em paragraph spacing",
                "style_tokens",
            )
        )
    _number(
        style.get("title_size_ratio"),
        "style_tokens.title_size_ratio",
        1.4,
        2.2,
        findings,
    )
    _number(
        style.get("caption_font_ratio"),
        "style_tokens.caption_font_ratio",
        0.75,
        1.0,
        findings,
    )
    for path in (
        "title_font_role",
        "abstract_heading_font_role",
        "h1_font_role",
        "h2_font_role",
    ):
        _choice(
            style.get(path),
            f"style_tokens.{path}",
            {"serif", "sans"},
            findings,
        )
    for path in (
        "title_alignment",
        "abstract_heading_alignment",
        "h1_alignment",
        "h2_alignment",
        "figure_caption_alignment",
        "table_caption_alignment",
    ):
        _choice(
            style.get(path),
            f"style_tokens.{path}",
            {"centered", "left_aligned"},
            findings,
        )
    _choice(
        style.get("section_numbering_style"),
        "style_tokens.section_numbering_style",
        {"none", "arabic", "chinese_h1_arabic_h2"},
        findings,
    )
    for path, minimum, maximum in (
        ("h1_size_ratio", 1.20, 1.65),
        ("h2_size_ratio", 1.08, 1.40),
        ("h3_size_ratio", 1.0, 1.25),
        ("h1_before_em", 0.8, 2.2),
        ("h1_after_em", 0.3, 1.1),
        ("h2_before_em", 0.6, 1.8),
        ("h2_after_em", 0.2, 0.9),
        ("display_above_em", 0.3, 1.4),
        ("display_below_em", 0.3, 1.4),
        ("array_stretch", 1.0, 1.5),
    ):
        _number(style.get(path), f"style_tokens.{path}", minimum, maximum, findings)
    for path, minimum, maximum in (
        ("widow_penalty", 500, 10000),
        ("club_penalty", 500, 10000),
        ("heading_keep_lines", 2, 5),
    ):
        value = style.get(path)
        if isinstance(value, bool) or not isinstance(value, int):
            findings.append(Finding("error", "CONFIG_TYPE", "must be an integer", f"style_tokens.{path}"))
        elif not minimum <= value <= maximum:
            findings.append(
                Finding(
                    "error",
                    "CONFIG_RANGE",
                    f"must be between {minimum} and {maximum}",
                    f"style_tokens.{path}",
                )
            )
    for path in ("cjk_font", "latin_font", "math_font"):
        value = style.get(path)
        if not isinstance(value, str) or not value.strip() or any(char in value for char in "{}\\\n\r"):
            findings.append(
                Finding("error", "CONFIG_TYPE", "must be a safe non-empty font name", f"style_tokens.{path}")
            )
    _number(
        lock.get("minimum_pdf_text_similarity"),
        "content_lock.minimum_pdf_text_similarity",
        0.75,
        1.0,
        findings,
    )
    for path, value in (
        ("rules.anonymous", rules.get("anonymous")),
        ("rules.abstract_required", rules.get("abstract_required")),
        ("rules.abstract_first_page", rules.get("abstract_first_page")),
        ("rules.allow_toc", rules.get("allow_toc")),
        ("content_lock.allow_raw_tex", lock.get("allow_raw_tex")),
        ("style_tokens.abstract_page_break", style.get("abstract_page_break")),
        ("style_tokens.first_after_heading_indent", style.get("first_after_heading_indent")),
    ):
        if not isinstance(value, bool):
            findings.append(Finding("error", "CONFIG_TYPE", "must be a boolean", path))
    for path, value, low, high in (
        ("rules.abstract_max_pages", rules.get("abstract_max_pages"), 1, 2),
        ("rules.body_max_pages", rules.get("body_max_pages"), 1, 100),
        ("rules.pdf_max_bytes", rules.get("pdf_max_bytes"), 1024, 1024**3),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            findings.append(
                Finding("error", "CONFIG_RANGE", f"must be an integer from {low} to {high}", path)
            )
    if rules.get("abstract_first_page") and not style.get("abstract_page_break"):
        findings.append(
            Finding(
                "error",
                "ABSTRACT_PAGE_BREAK",
                "must be true while abstract_first_page is enforced",
                "style_tokens.abstract_page_break",
            )
        )
    return findings


def pandoc_ast(source: Path) -> dict[str, Any]:
    require_tool("pandoc")
    completed = run(
        [
            "pandoc",
            str(source),
            f"--from={MARKDOWN_FORMAT}",
            "--to=json",
            f"--resource-path={source.parent}",
        ],
        cwd=source.parent,
    )
    try:
        ast = json.loads(completed.stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise TypesetterError(f"Pandoc returned invalid JSON: {exc}") from exc
    if not isinstance(ast, dict) or "blocks" not in ast or "meta" not in ast:
        raise TypesetterError("Pandoc JSON is missing required meta/blocks fields")
    return ast


def walk(value: Any) -> Iterator[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def stringify_pandoc(value: Any) -> str:
    pieces: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            node_type = item.get("t")
            content = item.get("c")
            if node_type in {
                "AlignLeft",
                "AlignRight",
                "AlignCenter",
                "AlignDefault",
                "ColWidth",
                "ColWidthDefault",
                "MathType",
                "DisplayMath",
                "InlineMath",
                "CitationMode",
            }:
                return
            if node_type == "Str" and isinstance(content, str):
                pieces.append(content)
                return
            if node_type in {"Space", "SoftBreak", "LineBreak"}:
                pieces.append(" ")
                return
            if node_type == "Math":
                pieces.append(" ")  # PDF text extraction of formulae is not stable
                return
            if node_type in {"Code", "CodeBlock"} and isinstance(content, list) and content:
                tail = content[-1]
                if isinstance(tail, str):
                    pieces.extend((tail, "\n" if node_type == "CodeBlock" else ""))
                    return
            if node_type == "MetaString" and isinstance(content, str):
                pieces.append(content)
                return
            if node_type == "MetaBool":
                pieces.append("true" if content else "false")
                return
            if node_type in {"RawInline", "RawBlock"}:
                return
            if node_type == "Header" and isinstance(content, list) and len(content) >= 3:
                visit(content[2])
                pieces.append("\n")
                return
            if node_type in {"Div", "Span"} and isinstance(content, list) and len(content) >= 2:
                visit(content[1])
                if node_type == "Div":
                    pieces.append("\n")
                return
            if node_type in {"Link", "Image"} and isinstance(content, list) and len(content) >= 2:
                visit(content[1])
                return
            if node_type == "Cite" and isinstance(content, list) and len(content) >= 2:
                visit(content[1])
                return
            if node_type == "OrderedList" and isinstance(content, list) and len(content) >= 2:
                visit(content[1])
                pieces.append("\n")
                return
            if node_type in {"Para", "Plain", "BlockQuote", "BulletList", "DefinitionList"}:
                visit(content)
                pieces.append("\n")
                return
            if node_type in {"TableHead", "TableFoot", "Row"} and isinstance(content, list):
                visit(content[-1])
                pieces.append("\n")
                return
            if node_type == "TableBody" and isinstance(content, list) and len(content) >= 4:
                visit(content[2])
                visit(content[3])
                pieces.append("\n")
                return
            if node_type == "Cell" and isinstance(content, list) and content:
                visit(content[-1])
                pieces.append(" ")
                return
            if node_type == "Table" and isinstance(content, list) and len(content) >= 6:
                visit(content[1])  # caption
                visit(content[3])  # head
                visit(content[4])  # bodies
                visit(content[5])  # foot
                pieces.append("\n")
                return
            if node_type == "Figure" and isinstance(content, list) and len(content) >= 3:
                visit(content[1])
                visit(content[2])
                pieces.append("\n")
                return
            if node_type == "MetaList" and isinstance(content, list):
                for index, child in enumerate(content):
                    if index:
                        pieces.append("；")
                    visit(child)
                return
            if node_type in {"MetaInlines", "MetaBlocks", "MetaMap"}:
                visit(content)
                return
            if content is not None:
                visit(content)
                return
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, str):
            pieces.append(item)

    visit(value)
    text = "".join(pieces)
    text = re.sub(r"[ \t\r]+", " ", text)
    text = re.sub(r" *\n+ *", "\n", text)
    return text.strip()


def metadata_text(ast: dict[str, Any], key: str) -> str:
    return stringify_pandoc(ast.get("meta", {}).get(key, {}))


def _node_attr(node: dict[str, Any]) -> tuple[str, list[str], list[list[str]]] | None:
    content = node.get("c")
    if isinstance(content, list) and content and isinstance(content[0], list) and len(content[0]) == 3:
        attr = content[0]
        if isinstance(attr[0], str) and isinstance(attr[1], list) and isinstance(attr[2], list):
            return attr[0], attr[1], attr[2]
    return None


def extract_images(ast: dict[str, Any]) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    for item in walk(ast.get("blocks", [])):
        if not isinstance(item, dict) or item.get("t") != "Image":
            continue
        content = item.get("c")
        if not isinstance(content, list) or len(content) < 3:
            continue
        target = content[2]
        if isinstance(target, list) and target and isinstance(target[0], str):
            images.append({"path": target[0], "alt": stringify_pandoc(content[1])})
    return images


def _truthy_meta(value: Any) -> bool:
    if isinstance(value, dict) and value.get("t") == "MetaBool":
        return bool(value.get("c"))
    text = stringify_pandoc(value).strip().lower()
    return text in {"true", "yes", "1"}


def inspect_ast(ast: dict[str, Any], source: Path, config: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    meta = ast.get("meta", {})
    rules = config["rules"]
    lock = config["content_lock"]
    title = metadata_text(ast, "title")
    abstract = metadata_text(ast, "abstract")
    if not title:
        findings.append(
            Finding("error", "TITLE_REQUIRED", "YAML metadata must contain a non-empty title", "meta.title")
        )
    if rules["abstract_required"] and not abstract:
        findings.append(
            Finding(
                "error",
                "ABSTRACT_REQUIRED",
                "YAML metadata must contain a non-empty abstract so it can be the first page",
                "meta.abstract",
            )
        )
    if rules["anonymous"]:
        identity_keys = {
            "author",
            "authors",
            "affiliation",
            "affiliations",
            "institution",
            "school",
            "university",
            "team",
            "team_id",
            "team-number",
            "student_id",
            "email",
        }
        for key in sorted(identity_keys):
            if key in meta and stringify_pandoc(meta[key]).strip():
                findings.append(
                    Finding(
                        "error",
                        "ANONYMITY_METADATA",
                        f"identifying metadata is forbidden in anonymous mode: {key}",
                        f"meta.{key}",
                    )
                )
    toc_requested = _truthy_meta(meta.get("toc")) or _truthy_meta(meta.get("table-of-contents"))
    body_text = stringify_pandoc(ast.get("blocks", []))
    raw_toc = False
    raw_nodes = 0
    for item in walk(ast.get("blocks", [])):
        if isinstance(item, dict) and item.get("t") in {"RawBlock", "RawInline"}:
            raw_nodes += 1
            raw = item.get("c")
            if isinstance(raw, list) and len(raw) == 2 and "tableofcontents" in str(raw[1]):
                raw_toc = True
    if not rules["allow_toc"] and (toc_requested or raw_toc):
        findings.append(
            Finding("error", "TOC_FORBIDDEN", "table of contents is disabled by the active rules")
        )
    if not rules["allow_toc"] and re.search(r"(^|\s)目录($|\s)", body_text):
        findings.append(
            Finding(
                "warning",
                "TOC_HEADING_SUSPECT",
                "body text contains '目录'; confirm this is not a table of contents",
            )
        )
    if raw_nodes and not lock["allow_raw_tex"]:
        findings.append(
            Finding(
                "error",
                "RAW_TEX_FORBIDDEN",
                f"found {raw_nodes} raw Pandoc node(s); disable raw TeX to keep the content lock auditable",
            )
        )

    seen_assets: set[str] = set()
    for image in extract_images(ast):
        target = image["path"]
        if target in seen_assets:
            continue
        seen_assets.add(target)
        parsed = urllib.parse.urlparse(target)
        if parsed.scheme in {"http", "https"}:
            findings.append(
                Finding(
                    "error",
                    "REMOTE_IMAGE",
                    "remote images are not fetched; save the exact source asset locally",
                    target,
                )
            )
            continue
        if parsed.scheme == "data":
            findings.append(
                Finding("error", "DATA_IMAGE", "embedded data URI images are unsupported", target[:80])
            )
            continue
        candidate = Path(urllib.parse.unquote(target))
        if not candidate.is_absolute():
            candidate = source.parent / candidate
        if not candidate.is_file():
            findings.append(Finding("error", "IMAGE_MISSING", "image file does not exist", target))
    if not extract_images(ast):
        findings.append(Finding("info", "NO_IMAGES", "the document contains no Pandoc Image nodes"))
    return findings


def analyze_source(source: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source = source.resolve()
    if not source.is_file():
        raise TypesetterError(f"Input Markdown does not exist: {source}")
    if source.suffix.lower() not in {".md", ".markdown"}:
        raise TypesetterError("Input must be a Markdown file (.md or .markdown)")
    ast = pandoc_ast(source)
    findings = inspect_ast(ast, source, config)
    report = {
        "schema_version": 1,
        "source": str(source),
        "source_sha256": sha256_file(source),
        "source_ast_sha256": sha256_bytes(canonical_json_bytes(ast)),
        "title": metadata_text(ast, "title"),
        "abstract_characters": len(metadata_text(ast, "abstract")),
        "keywords": metadata_text(ast, "keywords"),
        "figures": extract_images(ast),
        "finding_counts": {
            severity: sum(item.severity == severity for item in findings)
            for severity in ("error", "warning", "info")
        },
        "findings": [item.as_dict() for item in findings],
        "ready_to_render": not any(item.severity == "error" for item in findings),
    }
    return ast, report


def prepare_output_dir(output_dir: Path, force: bool) -> Path:
    output_dir = output_dir.resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise TypesetterError(f"Output path is not a directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    occupied = [
        path
        for path in output_dir.iterdir()
        if path.name in GENERATED_FILES or path.name in {"previews", "assets"}
    ]
    if occupied and not force:
        names = ", ".join(sorted(path.name for path in occupied)[:8])
        raise TypesetterError(f"Output contains generated files ({names}); pass --force to replace them")
    if force:
        for path in occupied:
            if path.is_dir() and path.name in {"previews", "assets"}:
                for child in path.iterdir():
                    allowed_asset = path.name == "assets" and child.is_file()
                    allowed_preview = (
                        path.name == "previews"
                        and child.is_file()
                        and child.suffix.lower() == ".png"
                    )
                    if allowed_asset or allowed_preview:
                        child.unlink()
                    else:
                        raise TypesetterError(f"refusing to remove unknown generated-directory entry: {child}")
                try:
                    path.rmdir()
                except OSError:
                    pass
            elif path.is_file():
                path.unlink()
    return output_dir


def copy_runtime_assets(output_dir: Path) -> None:
    for name in ("OhmyAIMCM-paper.cls", "OhmyAIMCM-style.sty", "semantic.lua"):
        shutil.copy2(LATEX_ASSET_DIR / name, output_dir / name)


def materialize_images(
    source_ast: dict[str, Any], source: Path, output_dir: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Copy every source figure byte-for-byte and rewrite only render paths.

    SVG is also deterministically converted to a PDF derivative because XeLaTeX
    cannot consume it without shell escape.  The original SVG remains in the
    standalone delivery and both hashes are recorded.
    """

    ast = copy.deepcopy(source_ast)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    entries: list[dict[str, Any]] = []
    target_by_source: dict[str, str] = {}
    supported = {".pdf", ".png", ".jpg", ".jpeg", ".eps"}
    image_index = 0
    for item in walk(ast.get("blocks", [])):
        if not isinstance(item, dict) or item.get("t") != "Image":
            continue
        content = item.get("c")
        if not isinstance(content, list) or len(content) < 3:
            continue
        target = content[2]
        if not isinstance(target, list) or not target or not isinstance(target[0], str):
            continue
        original_reference = target[0]
        if original_reference in target_by_source:
            target[0] = target_by_source[original_reference]
            continue
        parsed = urllib.parse.urlparse(original_reference)
        original_path = Path(urllib.parse.unquote(parsed.path))
        if not original_path.is_absolute():
            original_path = source.parent / original_path
        original_path = original_path.resolve()
        if not original_path.is_file():
            raise TypesetterError(f"image disappeared after analysis: {original_reference}")
        image_index += 1
        original_hash = sha256_file(original_path)
        suffix = original_path.suffix.lower()
        if suffix not in supported | {".svg"}:
            raise TypesetterError(
                f"image format {suffix or '(none)'} is not supported; use PDF, PNG, JPEG, EPS, or SVG: {original_reference}"
            )
        copied_name = f"asset-{image_index:03d}-{original_hash[:12]}{suffix}"
        copied_path = assets_dir / copied_name
        shutil.copy2(original_path, copied_path)
        render_path = copied_path
        derived: dict[str, Any] | None = None
        if suffix == ".svg":
            require_tool("rsvg-convert")
            render_path = assets_dir / f"asset-{image_index:03d}-{original_hash[:12]}.pdf"
            run(["rsvg-convert", "-f", "pdf", "-o", str(render_path), str(copied_path)])
            derived = {
                "path": str(render_path.relative_to(output_dir)),
                "sha256": sha256_file(render_path),
                "bytes": render_path.stat().st_size,
                "conversion": "rsvg-convert -f pdf",
            }
        rendered_reference = render_path.relative_to(output_dir).as_posix()
        target[0] = rendered_reference
        target_by_source[original_reference] = rendered_reference
        entries.append(
            {
                "source_reference": original_reference,
                "source_path_at_build": str(original_path),
                "source_sha256": original_hash,
                "copied_original": {
                    "path": str(copied_path.relative_to(output_dir)),
                    "sha256": sha256_file(copied_path),
                    "bytes": copied_path.stat().st_size,
                },
                "render_reference": rendered_reference,
                "derived": derived,
            }
        )
    manifest = {
        "schema_version": 1,
        "policy": "Every source figure is copied byte-for-byte; only an SVG render derivative may be added",
        "assets": entries,
    }
    return ast, manifest


def render_config_tex(config: dict[str, Any]) -> str:
    style = config["style_tokens"]
    body = float(style["body_font_pt"])
    leading = body * float(style["line_height_ratio"])
    caption_justification = {
        "centered": "centering",
        "left_aligned": "raggedright",
    }
    abstract_switch = (
        "\\OhmyAIMCMabstractpagebreaktrue" if style["abstract_page_break"] else "\\OhmyAIMCMabstractpagebreakfalse"
    )
    return (
        "% Generated only from validated controlled style tokens.\n"
        "\\OhmyAIMCMApplyStyle"
        f"{{{float(style['margin_top_mm']):.3f}}}"
        f"{{{float(style['margin_bottom_mm']):.3f}}}"
        f"{{{float(style['margin_left_mm']):.3f}}}"
        f"{{{float(style['margin_right_mm']):.3f}}}"
        f"{{{body:.3f}}}"
        f"{{{leading:.3f}}}"
        f"{{{float(style['paragraph_indent_em']):.3f}}}"
        f"{{{float(style['paragraph_skip_em']):.3f}}}\n"
        "\\OhmyAIMCMApplyFonts"
        f"{{{style['cjk_font']}}}"
        f"{{{style['latin_font']}}}"
        f"{{{style['math_font']}}}\n"
        "\\OhmyAIMCMApplyHeadingStyle"
        f"{{{float(style['h1_size_ratio']):.4f}}}"
        f"{{{float(style['h2_size_ratio']):.4f}}}"
        f"{{{float(style['h3_size_ratio']):.4f}}}"
        f"{{{float(style['h1_before_em']):.4f}}}"
        f"{{{float(style['h1_after_em']):.4f}}}"
        f"{{{float(style['h2_before_em']):.4f}}}"
        f"{{{float(style['h2_after_em']):.4f}}}\n"
        "\\OhmyAIMCMApplyRoleStyle"
        f"{{{style['title_font_role']}}}"
        f"{{{style['title_alignment']}}}"
        f"{{{float(style['title_size_ratio']):.4f}}}"
        f"{{{style['abstract_heading_font_role']}}}"
        f"{{{style['abstract_heading_alignment']}}}"
        f"{{{style['h1_font_role']}}}"
        f"{{{style['h1_alignment']}}}"
        f"{{{style['h2_font_role']}}}"
        f"{{{style['h2_alignment']}}}\n"
        f"\\OhmyAIMCMApplyNumbering{{{style['section_numbering_style']}}}\n"
        "\\OhmyAIMCMApplyCaptionStyle"
        f"{{{float(style['caption_font_ratio']):.4f}}}"
        f"{{{caption_justification[style['figure_caption_alignment']]}}}"
        f"{{{caption_justification[style['table_caption_alignment']]}}}\n"
        "\\OhmyAIMCMApplyMathStyle"
        f"{{{float(style['display_above_em']):.4f}}}"
        f"{{{float(style['display_below_em']):.4f}}}"
        f"{{{float(style['array_stretch']):.4f}}}\n"
        "\\OhmyAIMCMApplyFlowStyle"
        f"{{{int(style['widow_penalty'])}}}"
        f"{{{int(style['club_penalty'])}}}"
        f"{{{int(style['heading_keep_lines'])}}}"
        f"{{{'true' if style['first_after_heading_indent'] else 'false'}}}\n"
        f"{abstract_switch}\n"
    )


def render_ast_with_declaration(
    source_ast_path: Path,
    output_ast_path: Path,
    lua_filter: Path,
    cwd: Path,
    *,
    ai_usage: str,
    ai_summary: str,
) -> None:
    command = [
        "pandoc",
        str(source_ast_path),
        "--from=json",
        "--to=json",
        f"--lua-filter={lua_filter}",
        f"--metadata=ai-usage-state:{ai_usage}",
        f"--metadata=ai-usage-summary:{ai_summary}",
        f"--output={output_ast_path}",
    ]
    run(command, cwd=cwd)


def prepare_ai_declaration(
    *,
    state: str,
    summary: str | None,
    support_pdf: Path | None,
    output_dir: Path,
) -> dict[str, Any]:
    if state not in {"used", "not_used"}:
        raise TypesetterError("AI usage must be explicitly 'used' or 'not_used'")
    normalized_summary = re.sub(r"\s+", " ", summary or "").strip()
    declaration: dict[str, Any] = {
        "schema_version": 1,
        "state": state,
        "explicit_user_choice": True,
        "summary": normalized_summary,
        "support_pdf": None,
    }
    if state == "used":
        if len(normalized_summary) < 10:
            raise TypesetterError("--ai-summary must explain the AI purpose/stage when --ai-usage=used")
        if support_pdf is None:
            raise TypesetterError("--ai-support-pdf is required when --ai-usage=used")
        support_pdf = support_pdf.resolve()
        if support_pdf.name != "AI工具使用详情.pdf":
            raise TypesetterError("AI support PDF must be named exactly AI工具使用详情.pdf")
        if not support_pdf.is_file() or support_pdf.read_bytes()[:5] != b"%PDF-":
            raise TypesetterError(f"AI support PDF is missing or invalid: {support_pdf}")
        target = output_dir / "AI工具使用详情.pdf"
        if support_pdf != target.resolve():
            shutil.copy2(support_pdf, target)
        declaration["support_pdf"] = {
            "filename": target.name,
            "sha256": sha256_file(target),
            "bytes": target.stat().st_size,
        }
    elif normalized_summary or support_pdf is not None:
        raise TypesetterError("AI summary/support PDF must be omitted when --ai-usage=not_used")
    write_json(output_dir / "ai-declaration.json", declaration)
    return declaration


def render_tex(
    rendered_ast_path: Path,
    tex_path: Path,
    header_path: Path,
    cwd: Path,
    *,
    number_sections: bool = False,
) -> None:
    command = [
            "pandoc",
            str(rendered_ast_path),
            "--from=json",
            "--to=latex",
            "--standalone",
            "--variable=documentclass:OhmyAIMCM-paper",
            "--top-level-division=section",
            "--no-highlight",
            f"--include-in-header={header_path}",
            f"--resource-path={cwd}",
            f"--output={tex_path}",
        ]
    if number_sections:
        command.append("--number-sections")
    run(command, cwd=cwd)


def add_content_lock_markers(tex_path: Path, source_hash: str, rendered_hash: str) -> None:
    text = tex_path.read_text(encoding="utf-8")
    marker = (
        "% Generated by OhmyAIMCM-typesetter; editable TeX.\n"
        f"% CUMCM-SOURCE-AST-SHA256: {source_hash}\n"
        f"% CUMCM-RENDERED-AST-SHA256: {rendered_hash}\n"
    )
    tex_path.write_text(marker + text, encoding="utf-8")


def compile_tex(tex_path: Path, output_dir: Path, source_dir: Path) -> dict[str, Any]:
    require_tool("latexmk")
    require_tool("xelatex")
    env = os.environ.copy()
    existing_texinputs = env.get("TEXINPUTS", "")
    tex_roots = [str(output_dir), str(LATEX_ASSET_DIR)]
    if existing_texinputs:
        tex_roots.append(existing_texinputs)
    tex_roots.append("")  # trailing separator preserves the TeX default path
    env["TEXINPUTS"] = os.pathsep.join(tex_roots)
    env["SOURCE_DATE_EPOCH"] = "946684800"
    env["FORCE_SOURCE_DATE"] = "1"
    command = [
        "latexmk",
        "-xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-synctex=1",
        f"-outdir={output_dir}",
        str(tex_path),
    ]
    started = time.monotonic()
    completed = run(command, cwd=output_dir, env=env, check=False)
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        log_path = output_dir / "paper.log"
        log_tail = ""
        if log_path.exists():
            log_tail = log_path.read_text(encoding="utf-8", errors="replace")[-10000:]
        stderr = completed.stderr.decode("utf-8", errors="replace")[-5000:]
        raise TypesetterError(f"XeLaTeX build failed.\n{stderr}\n{log_tail}")
    pdf_path = output_dir / "paper.pdf"
    if not pdf_path.is_file():
        raise TypesetterError("latexmk reported success but paper.pdf was not created")
    return {
        "command": command,
        "cwd": str(output_dir),
        "source_root": str(source_dir),
        "duration_seconds": round(elapsed, 3),
        "returncode": completed.returncode,
        "pdf_sha256": sha256_file(pdf_path),
        "pdf_bytes": pdf_path.stat().st_size,
    }


def tool_version(name: str) -> str | None:
    path = shutil.which(name)
    if not path:
        return None
    version_flag = "-v" if name in {"pdftotext", "pdfinfo", "pdftoppm"} else "--version"
    completed = run([name, version_flag], check=False)
    output = (completed.stdout + completed.stderr).decode("utf-8", errors="replace").strip()
    return output.splitlines()[0] if output else str(path)


def normalize_for_compare(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]+", text)).lower()


def expected_text(ast: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("title", "abstract", "keywords"):
        text = metadata_text(ast, key)
        if text:
            parts.append(text)
    parts.append(stringify_pandoc(ast.get("blocks", [])))
    return "\n".join(parts)


def _page_texts(pdf_path: Path) -> list[str]:
    require_tool("pdftotext")
    with tempfile.TemporaryDirectory(prefix="OhmyAIMCM-text-") as tmp:
        text_path = Path(tmp) / "paper.txt"
        run(["pdftotext", "-layout", str(pdf_path), str(text_path)])
        text = text_path.read_text(encoding="utf-8", errors="replace")
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def _bbox_pages(pdf_path: Path) -> list[dict[str, Any]]:
    require_tool("pdftotext")
    with tempfile.TemporaryDirectory(prefix="OhmyAIMCM-bbox-") as tmp:
        bbox_path = Path(tmp) / "bbox.html"
        run(["pdftotext", "-bbox-layout", str(pdf_path), str(bbox_path)])
        root = ET.fromstring(bbox_path.read_text(encoding="utf-8", errors="replace"))
    pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(root.iter(), start=0):
        if page.tag.rsplit("}", 1)[-1] != "page":
            continue
        page_number += 1
        width = float(page.attrib.get("width", "0"))
        height = float(page.attrib.get("height", "0"))
        words: list[tuple[float, float, float, float]] = []
        for node in page.iter():
            if node.tag.rsplit("}", 1)[-1] != "word":
                continue
            try:
                words.append(
                    tuple(float(node.attrib[key]) for key in ("xMin", "yMin", "xMax", "yMax"))
                )
            except (KeyError, ValueError):
                continue
        mm = 25.4 / 72.0
        # Page numbers live in the footer.  Measure the body box after excluding
        # a 20 mm header/footer band; the configured geometry remains canonical.
        body_words = [word for word in words if word[1] >= 20 / mm and word[3] <= height - 20 / mm]
        measured = body_words or words
        if measured:
            min_x = min(word[0] for word in measured)
            min_y = min(word[1] for word in measured)
            max_x = max(word[2] for word in measured)
            max_y = max(word[3] for word in measured)
            margins = {
                "left_mm": round(min_x * mm, 2),
                "top_mm": round(min_y * mm, 2),
                "right_mm": round((width - max_x) * mm, 2),
                "bottom_mm": round((height - max_y) * mm, 2),
            }
        else:
            margins = None
        pages.append(
            {
                "page": len(pages) + 1,
                "width_pt": round(width, 2),
                "height_pt": round(height, 2),
                "word_count": len(words),
                "body_text_margins": margins,
            }
        )
    return pages


def _render_previews(pdf_path: Path, preview_dir: Path, pages: int | None = None) -> list[str]:
    """Render every page by default; report only files from this PDF/render.

    A caller can still request a bounded prefix with ``pages``. Stage first so
    that a failed Poppler invocation cannot replace good previews with a partial
    set, and discard only the known generated page names after success.
    """
    require_tool("pdftoppm")
    if pages is not None and pages < 1:
        raise TypesetterError("preview page count must be positive")
    preview_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".render-", dir=preview_dir) as raw_tmp:
        staging = Path(raw_tmp)
        command = ["pdftoppm", "-png", "-r", "120", "-f", "1"]
        if pages is not None:
            command.extend(["-l", str(pages)])
        run([*command, str(pdf_path), str(staging / "page")])
        rendered = sorted(
            staging.glob("page-*.png"),
            key=lambda path: int(path.stem.rsplit("-", 1)[1]),
        )
        if not rendered:
            raise TypesetterError("Poppler produced no page previews")
        for old in preview_dir.iterdir():
            if old.is_file() and re.fullmatch(r"page-\d+\.png", old.name):
                old.unlink()
        previews = []
        for source in rendered:
            page_number = int(source.stem.rsplit("-", 1)[1])
            target = preview_dir / f"page-{page_number}.png"
            source.replace(target)
            previews.append(str(target))
    return previews


def _preview_page_numbers(previews: list[str]) -> list[int]:
    return sorted({
        int(match.group(1))
        for path in previews
        if (match := re.fullmatch(r"page-(\d+)\.png", Path(path).name))
    })


def _parse_lock_markers(tex_path: Path) -> dict[str, str]:
    text = tex_path.read_text(encoding="utf-8", errors="replace")[:3000]
    result: dict[str, str] = {}
    for key in ("SOURCE", "RENDERED"):
        match = re.search(rf"CUMCM-{key}-AST-SHA256:\s*([0-9a-f]{{64}})", text)
        if match:
            result[key.lower()] = match.group(1)
    return result


def verify_output(output_dir: Path, *, render_previews: bool = True) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    findings: list[Finding] = []
    required = [
        "paper.tex",
        "paper.pdf",
        "input.ast.json",
        "rendered.ast.json",
        "render-input.ast.json",
        "assets-manifest.json",
        "content-lock.json",
        "effective-config.json",
        "ai-declaration.json",
    ]
    for name in required:
        if not (output_dir / name).is_file():
            findings.append(Finding("error", "OUTPUT_MISSING", f"missing required output: {name}"))
    if any(item.severity == "error" for item in findings):
        return _audit_report(
            output_dir, findings, {}, [], [], {}, previews_requested=render_previews
        )

    config = json.loads((output_dir / "effective-config.json").read_text(encoding="utf-8"))
    declaration = json.loads((output_dir / "ai-declaration.json").read_text(encoding="utf-8"))
    lock = json.loads((output_dir / "content-lock.json").read_text(encoding="utf-8"))
    source_ast = json.loads((output_dir / "input.ast.json").read_text(encoding="utf-8"))
    render_input_ast = json.loads((output_dir / "render-input.ast.json").read_text(encoding="utf-8"))
    rendered_ast = json.loads((output_dir / "rendered.ast.json").read_text(encoding="utf-8"))
    actual_source_hash = sha256_bytes(canonical_json_bytes(source_ast))
    actual_rendered_hash = sha256_bytes(canonical_json_bytes(rendered_ast))
    markers = _parse_lock_markers(output_dir / "paper.tex")
    for label, actual in (("source", actual_source_hash), ("rendered", actual_rendered_hash)):
        recorded = lock.get(f"{label}_ast_sha256")
        marker = markers.get(label)
        if actual != recorded or actual != marker:
            findings.append(
                Finding(
                    "error",
                    "CONTENT_LOCK_BROKEN",
                    f"{label} AST hash differs from lock or TeX marker",
                )
            )
    if sha256_bytes(canonical_json_bytes(render_input_ast)) != lock.get("render_input_ast_sha256"):
        findings.append(
            Finding("error", "CONTENT_LOCK_BROKEN", "render-input AST differs from its lock")
        )
    assets_manifest_path = output_dir / "assets-manifest.json"
    if sha256_file(assets_manifest_path) != lock.get("assets_manifest_sha256"):
        findings.append(Finding("error", "ASSET_MANIFEST_HASH", "asset manifest differs from its lock"))
    assets_manifest = json.loads(assets_manifest_path.read_text(encoding="utf-8"))
    for asset in assets_manifest.get("assets", []):
        for key in ("copied_original", "derived"):
            record = asset.get(key)
            if not isinstance(record, dict):
                continue
            asset_path = output_dir / str(record.get("path", ""))
            if not asset_path.is_file() or sha256_file(asset_path) != record.get("sha256"):
                findings.append(
                    Finding("error", "ASSET_HASH", "delivered figure asset differs from the recorded source", str(asset_path))
                )
    if lock.get("tex_sha256_at_build") and sha256_file(output_dir / "paper.tex") != lock["tex_sha256_at_build"]:
        findings.append(
            Finding(
                "warning",
                "TEX_EDITED",
                "paper.tex was edited after generation; rebuild the PDF before final delivery",
            )
        )

    pdf_path = output_dir / "paper.pdf"
    pages = _page_texts(pdf_path)
    bbox_pages = _bbox_pages(pdf_path)
    pdf_text = "\n".join(pages)
    expected = normalize_for_compare(expected_text(source_ast))
    actual = normalize_for_compare(pdf_text)
    similarity = difflib.SequenceMatcher(None, expected, actual, autojunk=False).ratio() if expected else 1.0
    # Coverage is less sensitive to inserted section/page numbers than global similarity.
    chunks = [normalize_for_compare(chunk) for chunk in re.split(r"[。！？.!?\n]+", expected_text(source_ast))]
    chunks = [chunk for chunk in chunks if len(chunk) >= 4]
    covered = sum(chunk in actual for chunk in chunks)
    coverage = covered / len(chunks) if chunks else 1.0
    required_coverage = float(config["content_lock"]["minimum_pdf_text_similarity"])
    if coverage < required_coverage:
        findings.append(
            Finding(
                "error",
                "PDF_TEXT_COVERAGE",
                f"only {coverage:.1%} of source text chunks were recovered from the PDF; required {required_coverage:.1%}",
            )
        )

    rules = config["rules"]
    declaration_heading = "人工智能工具使用声明"
    declaration_index = pdf_text.find(declaration_heading)
    references_candidates = [pdf_text.find(item) for item in ("参考文献", "References")]
    references_indices = [item for item in references_candidates if item >= 0]
    if declaration_index < 0:
        findings.append(Finding("error", "AI_DECLARATION_MISSING", "PDF lacks the explicit AI-use declaration"))
    elif references_indices and declaration_index > min(references_indices):
        findings.append(
            Finding("error", "AI_DECLARATION_POSITION", "AI-use declaration must appear before references")
        )
    state = declaration.get("state")
    if state not in {"used", "not_used"} or declaration.get("explicit_user_choice") is not True:
        findings.append(
            Finding("error", "AI_DECLARATION_INVALID", "AI-use state is not a valid explicit choice")
        )
    if state == "used":
        support = declaration.get("support_pdf")
        support_path = output_dir / "AI工具使用详情.pdf"
        if not isinstance(support, dict) or not support_path.is_file():
            findings.append(
                Finding("error", "AI_SUPPORT_MISSING", "used state requires AI工具使用详情.pdf")
            )
        elif sha256_file(support_path) != support.get("sha256"):
            findings.append(
                Finding("error", "AI_SUPPORT_HASH", "AI support PDF differs from the declared source")
            )
    pdf_bytes = pdf_path.stat().st_size
    if pdf_bytes > int(rules["pdf_max_bytes"]):
        findings.append(
            Finding(
                "error",
                "PDF_TOO_LARGE",
                f"PDF is {pdf_bytes} bytes; limit is {rules['pdf_max_bytes']} bytes",
            )
        )
    a4_width, a4_height = 595.28, 841.89
    for page in bbox_pages:
        if abs(page["width_pt"] - a4_width) > 2 or abs(page["height_pt"] - a4_height) > 2:
            findings.append(
                Finding("error", "NOT_A4", "rendered page size is not A4", f"page {page['page']}")
            )

    abstract_end_page = 0
    abstract_text = normalize_for_compare(metadata_text(source_ast, "abstract"))
    if abstract_text:
        tail = abstract_text[-min(30, len(abstract_text)) :]
        for index, page_text in enumerate(pages, start=1):
            if tail and tail in normalize_for_compare(page_text):
                abstract_end_page = index
                break
        if rules["abstract_first_page"] and (not pages or "摘要" not in pages[0]):
            findings.append(
                Finding("error", "ABSTRACT_NOT_FIRST", "page 1 does not contain the abstract marker")
            )
        if not abstract_end_page:
            findings.append(
                Finding("warning", "ABSTRACT_END_UNDETECTED", "could not locate the end of the abstract in PDF text")
            )
        elif abstract_end_page > int(rules["abstract_max_pages"]):
            findings.append(
                Finding(
                    "error",
                    "ABSTRACT_TOO_LONG",
                    f"abstract ends on page {abstract_end_page}; maximum is {rules['abstract_max_pages']}",
                )
            )
    body_pages = max(0, len(pages) - max(abstract_end_page, 1 if abstract_text else 0))
    if body_pages > int(rules["body_max_pages"]):
        findings.append(
            Finding(
                "error",
                "BODY_TOO_LONG",
                f"body is approximately {body_pages} pages; maximum is {rules['body_max_pages']}",
            )
        )
    if not rules["allow_toc"] and any(re.search(r"(^|\s)目录($|\s)", page) for page in pages):
        findings.append(Finding("error", "TOC_FOUND", "PDF text contains a table-of-contents marker"))

    log_findings: dict[str, Any] = {}
    log_path = output_dir / "paper.log"
    if log_path.is_file():
        log = log_path.read_text(encoding="utf-8", errors="replace")
        overfull = re.findall(r"Overfull \\hbox[^\n]*", log)
        overfull_vboxes = re.findall(r"Overfull \\vbox[^\n]*", log)
        undefined = re.findall(r"(?:Reference|Citation) `[^']+'[^\n]*undefined", log)
        table_guards = re.findall(r"CUMCM-TABLE-GUARD[^\n]*", log)
        log_findings = {
            "overfull_hboxes": overfull[:50],
            "overfull_vboxes": overfull_vboxes[:50],
            "undefined_references": undefined[:50],
            "table_pagination_guards": table_guards,
        }
        if overfull:
            findings.append(
                Finding("warning", "OVERFULL_HBOX", f"LaTeX reported {len(overfull)} overfull line(s)")
            )
        if undefined:
            findings.append(
                Finding(
                    "error",
                    "UNDEFINED_REFERENCE",
                    f"LaTeX reported {len(undefined)} undefined reference(s) or citation(s)",
                )
            )
        if overfull_vboxes:
            findings.append(
                Finding(
                    "error", "OVERFULL_VBOX",
                    f"LaTeX reported {len(overfull_vboxes)} vertically overfull box(es)",
                )
            )
    else:
        findings.append(
            Finding("warning", "LATEX_LOG_MISSING", "LaTeX overflow/reference diagnostics were not checked")
        )

    previews: list[str] = []
    if render_previews:
        previews = _render_previews(pdf_path, output_dir / "previews", pages=max(1, len(pages)))
        if _preview_page_numbers(previews) != list(range(1, len(pages) + 1)):
            findings.append(
                Finding("error", "PREVIEW_COVERAGE", "generated previews do not cover every PDF page")
            )
    metrics = {
        "pdf_sha256": sha256_file(pdf_path),
        "pdf_bytes": pdf_bytes,
        "page_count": len(pages),
        "abstract_end_page": abstract_end_page or None,
        "estimated_body_pages": body_pages,
        "global_text_similarity": round(similarity, 6),
        "source_chunk_coverage": round(coverage, 6),
        "required_source_chunk_coverage": required_coverage,
    }
    return _audit_report(
        output_dir, findings, metrics, bbox_pages, previews, log_findings,
        previews_requested=render_previews,
    )


def _audit_report(
    output_dir: Path,
    findings: list[Finding],
    metrics: dict[str, Any],
    pages: list[dict[str, Any]],
    previews: list[str],
    latex_log: dict[str, Any],
    *,
    previews_requested: bool = False,
) -> dict[str, Any]:
    status = "pass" if not any(item.severity == "error" for item in findings) else "fail"
    page_count = int(metrics.get("page_count", 0))
    page_numbers = list(range(1, page_count + 1))
    preview_numbers = _preview_page_numbers(previews)
    missing_previews = sorted(set(page_numbers) - set(preview_numbers))
    checks = ["required_output_files"]
    if metrics:
        checks.extend([
            "ast_hashes_and_tex_lock_markers",
            "figure_asset_manifest_and_hashes",
            "extracted_pdf_text_chunk_coverage",
            "ai_declaration_presence_order_and_support_hash",
            "pdf_A4_page_size_and_file_size",
            "abstract_and_estimated_body_page_limits",
            "table_of_contents_marker_absence",
        ])
    if latex_log:
        checks.append("latex_log_overflow_and_undefined_references")
    preview_status = (
        "unavailable" if not page_count else
        "not_generated" if not previews_requested else
        "complete" if preview_numbers == page_numbers else "incomplete"
    )
    return {
        "schema_version": 1,
        "output_dir": str(output_dir),
        # Keep pass/fail and exit codes compatible; make their limited meaning
        # explicit beside them and in the build report, including skipped QA.
        "status": status,
        "status_scope": "mechanical_checks_only",
        "review_status": "pending_visual_and_semantic_review",
        "review_scope": {
            "mechanical": {
                "status": status,
                "checks": checks,
                "pdf_pages_checked": page_numbers,
                "text_bbox_pages_measured": [page["page"] for page in pages],
                "limitations": [
                    "Text recovery and hashes do not establish mathematical or semantic correctness.",
                    "Text bounding boxes do not inspect figure pixels, table rules, or visual page composition.",
                    "Table guard logs record reservation decisions, not a post-render proof of table integrity.",
                    "Warning findings remain unresolved even when the mechanical status is pass.",
                ],
            },
            "previews": {
                "status": preview_status,
                "requested": previews_requested,
                "pdf_sha256": metrics.get("pdf_sha256") if previews else None,
                "pdf_page_count": page_count,
                "rendered_pages": preview_numbers,
                "missing_pages": missing_previews,
                "coverage_ratio": round(len(set(preview_numbers) & set(page_numbers)) / page_count, 6)
                if page_count else None,
                "rendering_is_visual_review": False,
            },
            "visual": {"status": "not_performed", "reviewed_pages": []},
            "semantic": {"status": "not_performed"},
        },
        "finding_counts": {
            severity: sum(item.severity == severity for item in findings)
            for severity in ("error", "warning", "info")
        },
        "findings": [item.as_dict() for item in findings],
        "metrics": metrics,
        "pages": pages,
        "previews": previews,
        "latex_log": latex_log,
    }


def print_json(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
