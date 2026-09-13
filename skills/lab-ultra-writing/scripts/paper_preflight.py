#!/usr/bin/env python3
"""Bounded CUMCM Markdown checks and explicit stable-figure-reference preparation.

Requires Pandoc. No model calls, downloads or changes in check mode. This is not a
mathematical, medical, originality, prose-quality or final-PDF validator.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def object_digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def pandoc(*args: str, payload: str | None = None) -> str:
    result = subprocess.run(["pandoc", *args], input=payload, capture_output=True,
                            text=True, timeout=45, check=False)
    if result.returncode:
        raise ValueError(f"Pandoc failed: {result.stderr.strip()}")
    return result.stdout


def load_ast(source: Path, *, source_text: str | None = None) -> dict:
    text = source.read_text(encoding="utf-8") if source_text is None else source_text
    return json.loads(pandoc("--from=markdown", "--to=json", payload=text))


def assert_current(binding: dict):
    """Detect drift in this invocation's inputs; not a saved-report authenticator."""
    if digest(Path(binding["source"])) != binding["source_sha256"]:
        raise ValueError("Source changed during preflight; rerun on settled inputs")
    if digest(Path(__file__)) != binding["checker_sha256"]:
        raise ValueError("Checker changed during preflight; rerun")
    for asset in binding["assets"]:
        if asset["state"] == "bound":
            # Resolve the original target again to catch a retargeted symlink too.
            path = local_image(Path(binding["source"]), asset["target"])
            if str(path) != asset["path"] or digest(path) != asset["sha256"]:
                raise ValueError("Figure asset changed during preflight: " + asset["target"])
        elif asset["state"] == "missing":
            path = local_image(Path(binding["source"]), asset["target"])
            if path.is_file():
                raise ValueError("Figure asset appeared during preflight: " + asset["target"])


def walk(value, location="document"):
    if isinstance(value, dict):
        if "t" in value:
            yield value, location
        for key, child in value.items():
            yield from walk(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{location}[{index}]")


def wording(value, exclude=()):
    if isinstance(value, list):
        return "".join(wording(child, exclude) for child in value)
    if not isinstance(value, dict):
        return ""
    kind, content = value.get("t"), value.get("c")
    if kind in exclude:
        return " "
    if kind == "Str":
        return content
    if kind in {"Space", "SoftBreak", "LineBreak"}:
        return " "
    if kind in {"Math", "Code"}:
        return content[1]
    if kind in {"RawInline", "RawBlock", "CodeBlock"}:
        return " "
    if kind in {"Link", "Image"}:
        return wording(content[1], exclude)
    if kind == "Header":
        return wording(content[2], exclude)
    return wording(content, exclude)


def figure_nodes(value, location="document", inside=False):
    if isinstance(value, dict):
        kind = value.get("t")
        if kind == "Figure":
            content = value["c"]
            images = [node for node, _ in walk(content[2]) if node.get("t") == "Image"]
            yield content[0], images, wording(content[1][1]), location
            inside = True
        elif kind == "Image" and not inside:
            yield value["c"][0], [value], wording(value["c"][1]), location
        for key, child in value.items():
            yield from figure_nodes(child, f"{location}.{key}", inside)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from figure_nodes(child, f"{location}[{index}]", inside)


def figure_map(ast: dict):
    entries = []
    for number, (attr, images, caption, location) in enumerate(figure_nodes(ast), 1):
        attrs = dict(attr[2])
        # Pandoc 3 promotes the identifier to Figure but leaves image attributes
        # such as panels on its single Image child. Do not guess across images.
        if len(images) == 1:
            image_attrs = dict(images[0]["c"][0][2])
            if "panels" in image_attrs:
                if "panels" in attrs and attrs["panels"] != image_attrs["panels"]:
                    raise ValueError(f"conflicting panel declarations for {attr[0]}")
                attrs.setdefault("panels", image_attrs["panels"])
        entries.append({"id": attr[0], "number": number, "caption": caption,
                        "panels": [p.strip() for p in attrs.get("panels", "").split(",") if p.strip()],
                        "images": [image["c"][2][0] for image in images], "location": location})
    return entries


def numeric_payload(value):
    """Ordered visible numeric tokens, excluding only generated figure labels."""
    if isinstance(value, list):
        return [token for child in value for token in numeric_payload(child)]
    if not isinstance(value, dict):
        return []
    if value.get("t") == "Link" and value["c"][2][0].startswith("#fig-"):
        return []
    if value.get("t") in {"Str", "Math", "Code"}:
        return re.findall(r"[+\-−]?\d+(?:[.,]\d+)*(?:[eE][+\-]?\d+)?", wording(value))
    return [token for child in value.values() for token in numeric_payload(child)]


def local_image(source: Path, target: str):
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def table_rows(table):
    content = table["c"]
    if not isinstance(content, list) or len(content) != 6:
        raise ValueError("unsupported Pandoc Table schema")
    heads = content[3][1]
    rows = [row for body in content[4] for row in body[2] + body[3]] + content[5][1]
    if not heads:
        return [], []
    return [wording(cell[4]).strip() for cell in heads[-1][1]], rows


def inspect(source: Path, *, phase="draft", ai_usage="unknown", ast=None):
    if phase not in {"draft", "release"} or ai_usage not in {"unknown", "used", "not_used"}:
        raise ValueError("invalid phase or AI usage state")
    source = source.absolute()
    source_bytes = source.read_bytes()
    binding = {"scope": "markdown_mechanical_inputs",
               "source": str(source),
               "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
               "checker_sha256": digest(Path(__file__)),
               "python_version": sys.version,
               "pandoc_version": pandoc("--version").strip(),
               "options": {"phase": phase, "ai_usage": ai_usage,
                           "reader": "markdown"}, "assets": []}
    parsed = load_ast(source, source_text=source_bytes.decode("utf-8"))
    if ast is not None and ast != parsed:
        raise ValueError("Supplied AST does not match the current source bytes")
    ast = parsed
    binding["ast_sha256"] = object_digest(ast)
    entries = figure_map(ast)
    issues = []
    strict = "error" if phase == "release" else "warning"

    def issue(code, detail, location, severity="error"):
        issues.append({"severity": severity, "code": code, "location": location, "detail": detail})

    by_id = {}
    for entry in entries:
        identifier, loc = entry["id"], entry["location"]
        if not identifier.startswith("fig-"):
            issue("FIGURE_ID_REQUIRED", "Captioned figures need stable fig-... IDs", loc, strict)
        if identifier and identifier in by_id:
            issue("DUPLICATE_FIGURE_ID", identifier, loc)
        if identifier:
            by_id[identifier] = entry
        if not entry["images"]:
            issue("FIGURE_WITHOUT_IMAGE", "No Image node; check unsupported figure construction", loc)
        for target in entry["images"]:
            asset = local_image(source, target)
            if asset is None:
                binding["assets"].append({"target": target, "state": "nonlocal"})
                issue("NONLOCAL_FIGURE", "Bind a local export before preparing a paper: " + target, loc, strict)
            elif not asset.is_file():
                binding["assets"].append({"target": target, "path": str(asset), "state": "missing"})
                issue("MISSING_FIGURE_ASSET", str(asset), loc)
            else:
                binding["assets"].append({"target": target, "path": str(asset),
                                          "state": "bound", "sha256": digest(asset)})

    for node, loc in walk(ast):
        kind = node.get("t")
        if kind == "Link" and node["c"][2][0].startswith("#fig-"):
            target = node["c"][2][0][1:]
            label = wording(node["c"][1]).strip()
            match = re.fullmatch(r"图(?:\s*(\d+))?(?:\s*([A-Za-z]))?", label)
            if target not in by_id:
                issue("UNRESOLVED_FIGURE_REFERENCE", target, loc)
            if not match:
                issue("INVALID_FIGURE_LINK_LABEL", "Use [图] or [图 b], without a number: " + label, loc)
            elif target in by_id:
                if match.group(1) and int(match.group(1)) != by_id[target]["number"]:
                    issue("STALE_FIGURE_NUMBER", f"{target} is figure {by_id[target]['number']}, not {match.group(1)}", loc)
                if match.group(2) and match.group(2) not in by_id[target]["panels"]:
                    issue("UNDECLARED_SUBPANEL", f"{target} does not declare panel {match.group(2)}", loc)

        if kind in {"Para", "Plain", "Header"}:
            prose = wording(node, exclude={"Math", "Code", "Link", "Image"})
            for pattern, code in [
                (r"(?<![A-Za-z0-9])图\s*(?:[0-9]+[A-Za-z]?|[A-Z])", "UNBOUND_FIGURE_REFERENCE"),
                (r"\b[A-Za-z]+_(?:\{[^}]+\}|[A-Za-z0-9]+)", "RAW_SUBSCRIPT"),
                (r"\b(?:cm|mm|kg|m|s)\s*\^\s*\{?-?\d", "RAW_UNIT_EXPONENT"),
            ]:
                if re.search(pattern, prose):
                    issue(code, prose[:200], loc, strict)
            if re.search(r"run_record\.py|artifacts/|runs/|candidate_not_confirmed", wording(node)):
                issue("PROCESS_LANGUAGE_REVIEW", "Check whether internal records belong in methods/appendix: " + wording(node)[:160], loc, "warning")

        if kind == "Table":
            headers, rows = table_rows(node)
            unit_indices = [index for index, header in enumerate(headers)
                            if header.lower() in {"单位", "量纲", "unit", "units"}]
            for row_index, row in enumerate(rows):
                for index in unit_indices:
                    if index >= len(row[1]):
                        continue
                    unit = wording(row[1][index][4]).strip()
                    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", unit) and unit != "1":
                        issue("VALUE_IN_UNIT_COLUMN", f"Unit cell contains value {unit}; separate unit and parameter value", f"{loc}.row[{row_index}]", strict)

    text = " ".join(wording(node) for node, _ in walk(ast) if node.get("t") in {"Para", "Plain"})
    compact = re.sub(r"\s+", "", text)
    no_ai = bool(re.search(r"(?:本论文|本文|本研究)(?:未|没有)使用(?:任何)?(?:人工智能|AI)(?:工具)?", compact, re.I))
    says_used = bool(re.search(r"(?:本论文|本文|本研究)使用了?(?:人工智能|AI)(?:工具)?", compact, re.I))
    if no_ai and ai_usage != "not_used":
        issue("AI_DECLARATION_CONFLICT" if ai_usage == "used" else "AI_USAGE_UNVERIFIED",
              "A no-AI declaration is incompatible with supplied used/unknown context", "document")
    if says_used and ai_usage == "not_used":
        issue("AI_DECLARATION_CONFLICT", "Paper reports assistance but supplied state is not_used", "document")
    if ai_usage == "unknown":
        issue("AI_USAGE_UNRESOLVED", "Do not invent a not_used default; retain known usage context", "document", strict)
    assert_current(binding)
    return {"schema_version": "paper-preflight/0.2", "phase": phase,
            "source": str(source), "source_sha256": binding["source_sha256"],
            "input_binding": binding, "input_binding_sha256": object_digest(binding),
            "direct_assets_bound": all(asset["state"] == "bound" for asset in binding["assets"]),
            "ai_usage_context": ai_usage, "figures": entries, "findings": issues,
            "mechanical_errors": sum(item["severity"] == "error" for item in issues),
            "review": {key: "not_checked" for key in
                       ("mathematical_correctness", "complete_notation_semantics", "argument_quality",
                        "figure_semantics", "final_pdf_layout", "contest_release")}}


def prepare(source: Path, output: Path, *, phase="release", ai_usage="unknown"):
    if output.exists() or output.is_symlink() or output.resolve() == source.resolve():
        raise ValueError("Output must be a new file, never the source")
    ast = load_ast(source)
    report = inspect(source, phase=phase, ai_usage=ai_usage, ast=ast)
    if report["mechanical_errors"]:
        return report
    prepared = copy.deepcopy(ast)
    mapping = {entry["id"]: entry for entry in report["figures"]}
    replacements = 0
    for node, _ in list(walk(prepared)):
        if node.get("t") == "Link" and node["c"][2][0].startswith("#fig-"):
            target = node["c"][2][0][1:]
            panel = re.fullmatch(r"图(?:\s*(\d+))?(?:\s*([A-Za-z]))?", wording(node["c"][1]).strip()).group(2) or ""
            node["c"][1] = [{"t": "Str", "c": f"图 {mapping[target]['number']}{panel}"}]
            replacements += 1
        elif node.get("t") == "Image":
            original = node["c"][2][0]
            path = local_image(source, original)
            if path is not None:
                parsed = urlsplit(original)
                relative = Path(os.path.relpath(path, output.parent.resolve())).as_posix()
                node["c"][2][0] = urlunsplit(("", "", relative, parsed.query, parsed.fragment))
        elif node.get("t") == "Math":
            # Pandoc's Markdown Math writer trims payload boundaries, including
            # LF after a final TeX % comment. Emit the original payload verbatim
            # as Markdown math instead; never normalize it for the comparison.
            # Reparse below still requires exactly the original Math kind/text,
            # and catches any delimiter/context that cannot round-trip safely.
            math_kind, payload = node["c"]
            delimiter = {"InlineMath": "$", "DisplayMath": "$$"}.get(math_kind["t"])
            if delimiter is None:
                raise ValueError("Unsupported mathematical kind; no file written")
            node["t"] = "RawInline"
            node["c"] = ["markdown", delimiter + payload + delimiter]
    # The smart Markdown writer straightens Chinese curly quotes. Re-reading
    # those adjacent to CJK can reverse opening quotes in LaTeX. Keep Unicode.
    # Standalone is required to emit YAML metadata, including the abstract;
    # the fragment writer silently omits it and loses its numeric payload.
    rendered = pandoc("--from=json", "--to=markdown-smart", "--wrap=none",
                      "--standalone",
                      payload=json.dumps(prepared, ensure_ascii=False))
    roundtrip = json.loads(pandoc("--from=markdown", "--to=json", payload=rendered))
    math_before = [node["c"] for node, _ in walk(ast) if node.get("t") == "Math"]
    math_after = [node["c"] for node, _ in walk(roundtrip) if node.get("t") == "Math"]
    if math_before != math_after:
        raise ValueError("Preparation changed mathematical payload; no file written")
    if numeric_payload(ast) != numeric_payload(roundtrip):
        raise ValueError("Preparation changed visible numeric payload; no file written")
    assert_current(report["input_binding"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(rendered)
    report.update({"output": str(output.resolve()), "output_sha256": digest(output),
                   "resolved_reference_count": replacements, "math_payload_preserved": True,
                   "visible_numeric_payload_preserved": True,
                   "note": "Prepared numbering is bound to this source/order; review and content-lock this derivative, not a separately modified copy"})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "prepare"])
    parser.add_argument("source", type=Path)
    parser.add_argument("--phase", choices=["draft", "release"])
    parser.add_argument("--ai-usage", choices=["used", "not_used", "unknown"], default="unknown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    args.phase = args.phase or ("release" if args.command == "prepare" else "draft")
    try:
        if args.command == "prepare":
            if not args.output:
                parser.error("prepare requires --output")
            result = prepare(args.source, args.output, phase=args.phase, ai_usage=args.ai_usage)
        else:
            if args.output:
                parser.error("check is read-only and does not accept --output")
            result = inspect(args.source, phase=args.phase, ai_usage=args.ai_usage)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["mechanical_errors"] else 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"error": str(error), "review": "not_checked"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
