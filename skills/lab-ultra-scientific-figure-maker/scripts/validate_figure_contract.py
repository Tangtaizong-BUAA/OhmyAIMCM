#!/usr/bin/env python3
"""Validate a FigureRequest and FigureIR without third-party dependencies."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

REQUEST_REQUIRED = {
    "schema_version",
    "figure_id",
    "claim",
    "audience",
    "medium",
    "final_width_mm",
    "language",
    "data_sources",
    "variables",
    "uncertainty",
    "editable_format",
    "claim_locked",
}
IR_REQUIRED = {
    "schema_version",
    "figure_id",
    "claim",
    "route",
    "recipe",
    "panels",
    "encodings",
    "annotations",
    "style_tokens",
    "exports",
    "invariants",
    "provenance",
}
ALLOWED_ROUTES = {"quantitative_code", "editable_vector", "bitmap_asset", "hybrid_with_deterministic_overlay"}


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def validate(request: dict[str, Any], ir: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing_request = sorted(REQUEST_REQUIRED - set(request))
    missing_ir = sorted(IR_REQUIRED - set(ir))
    if missing_request:
        errors.append(f"FigureRequest missing fields: {missing_request}")
    if missing_ir:
        errors.append(f"FigureIR missing fields: {missing_ir}")
    if errors:
        return errors
    if request["schema_version"] != "1.0.0" or ir["schema_version"] != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if request["figure_id"] != ir["figure_id"]:
        errors.append("figure_id changed between request and IR")
    if not request["claim_locked"] or request["claim"] != ir["claim"]:
        errors.append("locked claim changed between request and IR")
    width = request["final_width_mm"]
    if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(width) or width <= 0:
        errors.append("final_width_mm must be a positive finite number")
    if request["editable_format"] not in {"svg", "pdf", "drawio", "python", "tex", "r", "matlab", "javascript", "json"}:
        errors.append("editable_format is unsupported")
    if ir["route"] not in ALLOWED_ROUTES:
        errors.append("FigureIR route is unsupported")
    if not isinstance(request["data_sources"], list) or not request["data_sources"]:
        errors.append("at least one data source is required")
    else:
        for index, source in enumerate(request["data_sources"]):
            if not isinstance(source, dict) or not isinstance(source.get("sha256"), str) or len(source["sha256"]) != 64:
                errors.append(f"data_sources[{index}] requires a 64-character sha256")
    if not isinstance(ir["invariants"], list) or not {"data", "units", "claim", "transform"}.issubset(ir["invariants"]):
        errors.append("FigureIR invariants must lock data, units, claim, and transform")
    data_channels = {encoding.get("channel") for encoding in ir["encodings"] if isinstance(encoding, dict)}
    if ir["route"] == "bitmap_asset" and data_channels:
        errors.append("bitmap_asset route cannot contain data-bearing encodings")
    if not isinstance(ir["exports"], list) or request["editable_format"] not in ir["exports"]:
        errors.append("exports must include the requested editable format")
    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: validate_figure_contract.py request.json ir.json", file=sys.stderr)
        return 2
    try:
        errors = validate(load_object(Path(sys.argv[1])), load_object(Path(sys.argv[2])))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"invalid: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"invalid: {error}", file=sys.stderr)
        return 1
    print("valid: FigureRequest and FigureIR contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
