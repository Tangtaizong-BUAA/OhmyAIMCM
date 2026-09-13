#!/usr/bin/env python3
"""Analyze a completed Markdown paper before deterministic rendering."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _runtime import TypesetterError, analyze_source, load_config, print_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("input", type=Path, help="completed Markdown paper")
    result.add_argument("--config", type=Path, help="JSON override merged over the safe defaults")
    result.add_argument("--rules", type=Path, help="official compliance JSON or a rules object")
    result.add_argument("--style-tokens", type=Path, help="controlled style-token JSON or profile")
    result.add_argument(
        "--semantic-policy",
        type=Path,
        help="validated corpus-model policy containing a bounded runtime projection",
    )
    result.add_argument("--output", type=Path, help="also write the JSON analysis report here")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        config = load_config(
            args.config,
            rules_path=args.rules,
            style_tokens_path=args.style_tokens,
            semantic_policy_path=args.semantic_policy,
        )
        _, report = analyze_source(args.input, config)
        print_json(report)
        if args.output:
            from _runtime import write_json

            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_json(args.output, report)
        return 0 if report["ready_to_render"] else 2
    except TypesetterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
