#!/usr/bin/env python3
"""Read-only artifact/freshness checks, NOT scientific or backend attestation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from validate_figure_contract import load_object, validate

ROLES = {"source", "draft", "prompt", "generated", "overlay", "final"}
CHECKS = {"scientific_invariants", "overlay_alignment", "final_size", "raster_limits"}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def asset_digest(root, entry):
    if not isinstance(entry, dict) or not nonempty(entry.get("path")):
        raise ValueError("asset requires a relative path")
    relative = Path(entry["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("asset path must stay inside the case root")
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("asset must resolve to a file inside the case root")
    declared = entry.get("sha256")
    if (not isinstance(declared, str) or len(declared) != 64
            or any(char not in "0123456789abcdef" for char in declared)):
        raise ValueError("asset requires an actual lowercase SHA-256 digest")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != declared:
        raise ValueError("asset bytes changed or declared hash is incorrect")
    return actual


def audit(request, ir, root, require_model=None):
    report = {
        "artifact_check": "fail", "errors": [], "warnings": [],
        "scientific_and_aesthetic_quality": "not_assessed",
        "provider_authenticity": "not_attested",
    }
    errors = report["errors"]
    errors.extend(validate(request, ir))
    if errors:
        return report
    provenance = ir.get("provenance")
    record = provenance.get("image_assistance") if isinstance(provenance, dict) else None
    if not isinstance(record, dict):
        errors.append("provenance.image_assistance is required for this audit")
        return report
    if ir["route"] != "hybrid_with_deterministic_overlay":
        errors.append("image assistance requires hybrid_with_deterministic_overlay")
    for field in ("tool", "requested_model"):
        if not nonempty(record.get(field)):
            errors.append(f"image_assistance.{field} must be recorded")
    observed = record.get("observed_model")
    if "observed_model" not in record or (observed is not None and not nonempty(observed)):
        errors.append("observed_model must be an evidenced ID or explicit null")
    for index, encoding in enumerate(ir["encodings"]):
        if not isinstance(encoding, dict) or encoding.get("source_layer") != "deterministic":
            errors.append(f"encodings[{index}] must declare a deterministic source_layer")

    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("case root must be a directory")
    assets = record.get("assets")
    actual = {}
    if not isinstance(assets, dict) or not ROLES.issubset(assets):
        errors.append("assets must include source, draft, prompt, generated, overlay and final")
    if isinstance(assets, dict):
        for role, entry in assets.items():
            try:
                actual[role] = asset_digest(root, entry)
            except (OSError, ValueError, RuntimeError) as error:
                errors.append(f"assets.{role}: {error}")

    review = record.get("review")
    if not isinstance(review, dict):
        errors.append("version-bound visual review is missing")
    else:
        if review.get("status") != "pass" or not nonempty(review.get("reviewer")):
            errors.append("review requires pass status and a truthful reviewer identity/role")
        width = review.get("final_width_mm")
        if isinstance(width, bool) or width != request["final_width_mm"]:
            errors.append("review final_width_mm does not match the current request")
        if review.get("asset_sha256") != actual or not actual:
            errors.append("review hashes do not match the current artifact set; re-review changes")
        notes = review.get("observations")
        if not isinstance(notes, dict) or any(not nonempty(notes.get(key)) for key in CHECKS):
            errors.append("review requires observations for invariants, alignment, size and raster limits")

    receipt = "model_receipt" in actual
    report["requested_model"] = record.get("requested_model")
    report["observed_model"] = observed
    report["model_evidence"] = "recorded_receipt_requires_inspection" if receipt else "unavailable"
    if not observed or not receipt:
        report["warnings"].append("Exact model use is unverified; artifact checks cannot confirm Image 2.5.")
    elif observed != record.get("requested_model"):
        report["warnings"].append("Requested and observed IDs differ; inspect alias/snapshot or substitution evidence.")
    if require_model and (observed != require_model or not receipt):
        errors.append("required exact model needs matching observed_model and an intact model_receipt asset")
    if not errors:
        report["artifact_check"] = "pass"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("ir", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--require-model", help="Check recorded exact ID + receipt presence, not backend authenticity")
    args = parser.parse_args()
    try:
        report = audit(load_object(args.request), load_object(args.ir), args.root, args.require_model)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        report = {"artifact_check": "fail", "errors": [f"invalid input: {error}"]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["artifact_check"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
