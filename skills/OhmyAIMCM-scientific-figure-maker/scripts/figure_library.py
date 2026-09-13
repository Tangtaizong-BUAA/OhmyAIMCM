"""Find pinned figure recipes and apply the bundled publication materials.

Catalog commands use only the standard library. Applying styles requires
Matplotlib and the sibling OhmyAIMCM-scientific-visualization skill, never vendor imports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
WORKSPACE = SKILL.parents[2]
ASSETS = SKILL / "assets"
UPSTREAM = ASSETS / "upstream"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def catalog():
    return read_json(ASSETS / "library-catalog.json")["libraries"]


def find_libraries(tag=None, ecosystem=None):
    return [
        item
        for item in catalog()
        if (tag is None or tag in item["tags"])
        and (ecosystem is None or ecosystem == item["ecosystem"])
    ]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_library(library_id, workspace=WORKSPACE):
    matches = [item for item in catalog() if item["id"] == library_id]
    if not matches:
        raise ValueError(f"unknown library: {library_id}")
    item = matches[0]
    repo = Path(workspace) / item["origin"]["local_path"]
    if not (repo / ".git").is_dir():
        raise ValueError(
            f"source checkout missing: {repo}; use the locked origin to restore it"
        )
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip() != item["origin"]["commit"]:
        raise ValueError(f"source commit drift: {library_id}")
    dirty = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if dirty.stdout:
        raise ValueError(f"source checkout has local changes: {library_id}")
    paths = [repo / part for part in item["entrypoints"]]
    for path in paths:
        if not path.exists():
            raise ValueError(f"recipe entrypoint missing: {path}")
    return {
        **item,
        "resolved_paths": [str(p) for p in paths],
        "runtime_status": "not_assumed_installed",
    }


def verify_bundle():
    manifest = read_json(UPSTREAM / "manifest.json")
    for item in manifest["files"]:
        path = SKILL / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise ValueError(f"bundled material missing or changed: {item['path']}")
    return {"valid": True, "files": len(manifest["files"])}


def profiles():
    verify_bundle()
    return read_json(ASSETS / "style-profiles.json")


def _positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise TypeError(f"{name} must be a positive finite number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return float(value)


def resolve_style(
    profile="science",
    *,
    width_mm=None,
    height_mm=None,
    venue=None,
    palette="okabe_ito_on_white",
    overrides=None,
    language=None,
):
    """Resolve one visual family, then explicit dimensions and caller overrides.

    Export crop, layout ownership, and canvas size use named arguments instead
    of upstream defaults. The returned rc dictionary can be used in rc_context.
    """
    import matplotlib as mpl

    sys.path.insert(0, str(SKILL.parent / "OhmyAIMCM-scientific-visualization" / "scripts"))
    from style_presets import get_style

    config = profiles()
    if not isinstance(profile, str) or profile not in config["profiles"]:
        raise ValueError(f"select one style from {list(config['profiles'])}")
    selected = config["profiles"][profile]
    rc = get_style("default", palette_name=palette)
    colors = rc.pop("_palette_colors")
    rc["axes.prop_cycle"] = mpl.cycler(color=colors)
    # These settings are resolved once for the whole FigureRequest.
    owned = {
        "figure.figsize",
        "figure.dpi",
        "savefig.bbox",
        "text.usetex",
        "text.latex.preamble",
        "axes.prop_cycle",
        "savefig.transparent",
        "figure.autolayout",
        "figure.constrained_layout.use",
    }
    suppressed = set()
    for rel in selected["files"]:
        layer = dict(
            mpl.rc_params_from_file(UPSTREAM / rel, use_default_template=False)
        )
        suppressed.update(owned.intersection(layer))
        rc.update({key: value for key, value in layer.items() if key not in owned})
    rc.update(selected.get("rc", {}))
    rc.update(
        {
            "text.usetex": False,
            "savefig.bbox": None,
            "savefig.transparent": False,
            "figure.autolayout": False,
            "figure.constrained_layout.use": True,
        }
    )
    size_source = "explicit_mm" if width_mm is not None else "general_150mm"
    if venue is not None:
        if venue not in config["venue_widths"]:
            raise ValueError(f"unknown dated venue preset: {venue}")
        if width_mm is None:
            width_mm = config["venue_widths"][venue]["width_in"] * 25.4
            size_source = venue
    width = _positive(150.0 if width_mm is None else width_mm, "width_mm")
    height = _positive(width * 0.66 if height_mm is None else height_mm, "height_mm")
    rc["figure.figsize"] = [width / 25.4, height / 25.4]
    overrides = dict(overrides or {})
    for key in ("figure.figsize", "savefig.bbox"):
        if key in overrides:
            raise ValueError(
                f"set {key} through figure dimensions/export options, not style overrides"
            )
    typography = None
    if (profile in {"nature", "cns"} or language is not None) and not any(
        key in overrides for key in ("font.family", "font.sans-serif", "font.serif")
    ):
        from figure_typography import resolve_figure_fonts
        font_rc, typography = resolve_figure_fonts(language or "en")
        rc.update(font_rc)
        if language and language.startswith("zh"):
            rc.update({"font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 8.5,
                       "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8})
    rc.update(overrides)
    # Mirrored ticks from an upstream style must not float on hidden spines.
    # Explicit caller tick choices still win, including unusual borderless axes.
    for tick, spine in (
        ("xtick.top", "axes.spines.top"),
        ("ytick.right", "axes.spines.right"),
    ):
        if tick not in overrides and not rc.get(spine, mpl.rcParamsDefault[spine]):
            if rc.get(tick, mpl.rcParamsDefault[tick]):
                suppressed.add(tick)
            rc[tick] = False
    if rc.get("figure.autolayout") and rc.get("figure.constrained_layout.use"):
        raise ValueError(
            "tight/autolayout and constrained layout cannot both own a figure"
        )
    # Validate once without changing global Matplotlib state.
    validated = mpl.RcParams(rc)
    manifest = read_json(UPSTREAM / "manifest.json")
    receipt = {
        "profile": profile,
        "profile_upstream": selected["upstream_id"],
        "palette": palette,
        "width_mm": width,
        "height_mm": height,
        "dimension_source": size_source,
        "ignored_upstream_defaults": sorted(suppressed),
        "explicit_overrides": overrides,
        "typography": typography or {"scope": "caller_or_serif_profile_owned; inspect actual fonts"},
        "material_manifest_sha256": sha256(UPSTREAM / "manifest.json"),
        "resolver_sha256": sha256(__file__),
        "sources": manifest["origins"],
        "notice": "Visual starting point; venue presets are dated and do not certify submission compliance.",
    }
    return dict(validated), receipt


@contextmanager
def publication_style(profile="science", **kwargs):
    import matplotlib as mpl

    rc, receipt = resolve_style(profile, **kwargs)
    with mpl.rc_context(rc):
        yield receipt


def colormap(name="batlow", *, kind=None):
    from matplotlib.colors import ListedColormap

    config = profiles()["colormaps"]
    if name not in config:
        raise ValueError(f"unknown bundled colormap: {name}")
    item = config[name]
    if kind is not None and item["kind"] != kind:
        raise ValueError(f"{name} is {item['kind']}, not {kind}")
    rows = [
        [float(x) for x in line.split()]
        for line in (UPSTREAM / item["file"]).read_text().splitlines()
        if line.strip()
    ]
    if len(rows) != 256 or any(
        len(row) != 3 or any(not 0 <= x <= 1 for x in row) for row in rows
    ):
        raise ValueError(f"invalid RGB lookup table: {name}")
    return ListedColormap(rows, name=f"cmcrameri_{name}").with_extremes(bad="#777777")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("find")
    find.add_argument("--tag")
    find.add_argument("--ecosystem")
    resolve = sub.add_parser("resolve")
    resolve.add_argument("library_id")
    verify = sub.add_parser("verify")
    verify.add_argument("--sources", action="store_true")
    sub.add_parser("styles")
    args = parser.parse_args(argv)
    try:
        if args.command == "find":
            result = find_libraries(args.tag, args.ecosystem)
        elif args.command == "resolve":
            result = resolve_library(args.library_id)
        elif args.command == "styles":
            result = profiles()
        else:
            result = verify_bundle()
            if args.sources:
                result["verified_sources"] = len(
                    [resolve_library(x["id"]) for x in catalog()]
                )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
