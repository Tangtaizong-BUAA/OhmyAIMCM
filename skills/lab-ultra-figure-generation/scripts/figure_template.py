"""Write a local recipe launcher; no invented data or copied upstream templates."""

from __future__ import annotations

import argparse
from pathlib import Path

KINDS = ("bar", "line", "scatter", "heatmap", "forest", "box")
ALIASES = {"training-curve": "line", "ablation": "bar", "attention": "heatmap"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=(*KINDS, *ALIASES))
    parser.add_argument("--output", "-o", type=Path, default=Path("figure_script.py"))
    parser.add_argument("--name", default="figure")
    parser.add_argument("--list-types", action="store_true")
    args = parser.parse_args(argv)
    if args.list_types:
        print("\n".join(KINDS))
        return 0
    if args.type is None:
        parser.error("--type is required")
    kind = ALIASES.get(args.type, args.type)
    scripts = (
        Path(__file__).resolve().parents[2] / "lab-ultra-scientific-figure-maker" / "scripts"
    )
    code = (
        "# Local Figure Library launcher. Supply a documented recipe JSON; no example results.\n"
        "import argparse\nimport json\nfrom pathlib import Path\nimport sys\n"
        f"sys.path.insert(0, {str(scripts)!r})\n"
        "from render_recipe import render\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--data', type=Path, required=True)\n"
        f"parser.add_argument('--output', default={args.name!r})\n"
        "parser.add_argument('--force', action='store_true')\n"
        "args = parser.parse_args()\n"
        "spec = json.loads(args.data.read_text(encoding='utf-8'))\n"
        f"if not spec.get('panels') or any(p.get('kind') != {kind!r} for p in spec['panels']):\n"
        f"    parser.error('supply panels of kind {kind}; see material-library.md')\n"
        "print(json.dumps(render(args.data, args.output, overwrite=args.force), indent=2))\n"
    )
    try:
        with args.output.open("x", encoding="utf-8") as target:
            target.write(code)
    except OSError as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Created {args.output}; run it with --data supplied.recipe.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
