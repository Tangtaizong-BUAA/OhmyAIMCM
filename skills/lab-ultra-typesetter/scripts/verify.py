#!/usr/bin/env python3
"""Verify content lock, compliance, layout metrics, and a compiled PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _runtime import TypesetterError, print_json, verify_output, write_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("output_dir", type=Path, help="directory produced by render.py")
    result.add_argument("--no-previews", action="store_true", help="skip full-PDF PNG previews; the audit records missing preview coverage")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        report = verify_output(args.output_dir, render_previews=not args.no_previews)
        write_json(args.output_dir.resolve() / "layout-audit.json", report)
        print_json(report)
        return 0 if report["status"] == "pass" else 3
    except (TypesetterError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
