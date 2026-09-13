#!/usr/bin/env python3
"""Static SVG structure audit; overlap and final-size visual review are separate."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "{http://www.w3.org/2000/svg}"


def audit(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    root = ET.fromstring(raw)
    errors: list[str] = []
    warnings: list[str] = []
    if root.tag != SVG_NS + "svg":
        errors.append("root element is not SVG")
    if not root.get("viewBox"):
        errors.append("missing viewBox")
    if not root.get("width") or not root.get("height"):
        warnings.append("width or height is not explicit")
    if root.find(SVG_NS + "title") is None or root.find(SVG_NS + "desc") is None:
        errors.append("accessible title and desc are required")
    forbidden_tags = {SVG_NS + "script", SVG_NS + "foreignObject"}
    embedded_rasters = 0
    for element in root.iter():
        if element.tag in forbidden_tags:
            errors.append(f"forbidden element: {element.tag.removeprefix(SVG_NS)}")
        for name, value in element.attrib.items():
            lowered = name.lower()
            if lowered.startswith("on"):
                errors.append(f"event-handler attribute is forbidden: {name}")
            if lowered.endswith("href") and not value.startswith("#"):
                if element.tag == SVG_NS + "image" and re.match(
                    r"^data:image/(?:png|jpeg);base64,", value, flags=re.IGNORECASE
                ):
                    embedded_rasters += 1
                else:
                    errors.append(f"external or unsupported embedded href is forbidden: {value[:40]}")
    if embedded_rasters:
        warnings.append("embedded raster layers: verify source provenance and effective resolution")
    text_nodes = [element for element in root.iter() if element.tag == SVG_NS + "text"]
    if not text_nodes:
        warnings.append("no editable SVG text elements found")
    return {
        "path": str(path),
        "valid": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "counts": {
            "elements": sum(1 for _ in root.iter()),
            "text": len(text_nodes),
            "embedded_rasters": embedded_rasters,
            "paths": sum(1 for element in root.iter() if element.tag == SVG_NS + "path"),
        },
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: audit_svg.py figure.svg [figure2.svg ...]", file=sys.stderr)
        return 2
    failed = False
    for raw_path in sys.argv[1:]:
        try:
            report = audit(Path(raw_path))
        except (OSError, ET.ParseError, UnicodeDecodeError) as error:
            report = {"path": raw_path, "valid": False, "errors": [str(error)], "warnings": [], "counts": {}}
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        failed = failed or not report["valid"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
