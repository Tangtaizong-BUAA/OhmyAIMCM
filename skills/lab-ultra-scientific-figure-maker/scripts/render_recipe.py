"""Render supplied JSON data using shared publication materials and export.

Six small starter recipes cover ordinary figures. Specialized layouts use the
pinned recipe catalog instead of accumulating competing plotting frameworks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from figure_library import SKILL, colormap, publication_style, read_json, sha256

KINDS = ("line", "scatter", "bar", "heatmap", "forest", "box")


def _numbers(values, name, *, missing=False):
    import numpy as np

    if not isinstance(values, list) or not values:
        raise ValueError(
            f"{name} must contain supplied data; no example values are generated"
        )
    for value in values:
        if value is None and missing:
            continue
        if (
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not np.isfinite(value)
        ):
            raise ValueError(f"{name} contains a missing or non-finite value")
    return np.array(
        [np.nan if value is None else value for value in values], dtype=float
    )


def _same_length(*arrays):
    if len({len(array) for array in arrays}) != 1:
        raise ValueError("data arrays and labels must have matching lengths")


def draw_panel(ax, panel):
    """Draw without changing global styles, calculating tests, or fitting models."""
    import numpy as np
    from matplotlib.colors import Normalize, TwoSlopeNorm

    kind = panel.get("kind")
    if kind not in KINDS:
        raise ValueError(f"unknown recipe {kind!r}; supported: {KINDS}")
    for key in ("xlabel", "ylabel"):
        if not isinstance(panel.get(key), str) or not panel[key].strip():
            raise ValueError(
                f"panel requires {key} with variable name and units where applicable"
            )
    markers = ("o", "s", "^", "D", "v", "P")
    if kind in {"line", "scatter"}:
        series = panel.get("series", [])
        if not series:
            raise ValueError("line/scatter requires supplied series")
        for i, item in enumerate(series):
            x = _numbers(item["x"], "x")
            y = _numbers(item["y"], "y", missing=kind == "line")
            _same_length(x, y)
            if kind == "line" and np.any(np.diff(x) < 0):
                raise ValueError(
                    "line x must be ordered; do not silently reorder observations"
                )
            if kind == "line":
                (artist,) = ax.plot(
                    x,
                    y,
                    label=item["label"],
                    marker=markers[i % len(markers)],
                    linestyle=("-", "--", ":", "-.")[i % 4],
                )
                if "lower" in item or "upper" in item:
                    if not item.get("interval_label"):
                        raise ValueError(
                            "an interval requires its supplied statistical definition"
                        )
                    lower = _numbers(item["lower"], "lower", missing=True)
                    upper = _numbers(item["upper"], "upper", missing=True)
                    _same_length(x, lower, upper)
                    observed = np.isfinite(y)
                    if np.any(~np.isfinite(lower[observed])) or np.any(
                        ~np.isfinite(upper[observed])
                    ):
                        raise ValueError(
                            "observed values require finite interval bounds"
                        )
                    if np.any(lower[observed] > y[observed]) or np.any(
                        upper[observed] < y[observed]
                    ):
                        raise ValueError("interval bounds must contain the estimate")
                    ax.fill_between(
                        x,
                        lower,
                        upper,
                        where=observed,
                        color=artist.get_color(),
                        alpha=0.18,
                        linewidth=0,
                        label=item["interval_label"],
                    )
            else:
                ax.scatter(x, y, label=item["label"], marker=markers[i % len(markers)])
        ax.legend()
    elif kind == "bar":
        values = _numbers(panel.get("values"), "values")
        labels = panel["labels"]
        _same_length(labels, values)
        ax.bar(range(len(values)), values)
        ax.set_xticks(range(len(values)), labels)
        low, high = ax.get_ylim()
        ax.set_ylim(min(0, low), max(0, high))
    elif kind == "heatmap":
        rows = panel.get("values", [])
        if not rows:
            raise ValueError("heatmap requires supplied matrix values")
        arrays = [_numbers(row, "matrix row", missing=True) for row in rows]
        _same_length(*arrays)
        values = np.array(arrays)
        if not np.any(np.isfinite(values)):
            raise ValueError("heatmap has no observed values")
        _same_length(panel["xlabels"], values[0])
        _same_length(panel["ylabels"], values)
        color_kind = panel.get("color_kind", "sequential")
        cmap = colormap(
            panel.get(
                "cmap",
                {"sequential": "batlow", "diverging": "vik", "cyclic": "romaO"}.get(
                    color_kind
                ),
            ),
            kind=color_kind,
        )
        if color_kind == "diverging":
            if "center" not in panel:
                raise ValueError(
                    "diverging color requires an explicit scientific center"
                )
            norm = TwoSlopeNorm(
                vcenter=panel["center"], vmin=panel.get("vmin"), vmax=panel.get("vmax")
            )
        elif color_kind == "cyclic":
            if "vmin" not in panel or "vmax" not in panel:
                raise ValueError("cyclic color requires an explicit full-cycle domain")
            norm = Normalize(panel["vmin"], panel["vmax"])
        else:
            norm = Normalize(panel.get("vmin"), panel.get("vmax"))
        # pcolormesh retains editable vector cells; no resampling or smoothing.
        image = ax.pcolormesh(
            np.ma.masked_invalid(values),
            cmap=cmap,
            norm=norm,
            shading="flat",
            edgecolors="none",
        )
        ax.invert_yaxis()
        ax.set_xticks(np.arange(values.shape[1]) + 0.5, panel["xlabels"])
        ax.set_yticks(np.arange(values.shape[0]) + 0.5, panel["ylabels"])
        if not panel.get("color_label"):
            raise ValueError("heatmap requires color_label with units where applicable")
        color_label = panel["color_label"]
        if np.isnan(values).any():
            color_label += "\nMissing = gray"
        colorbar = ax.figure.colorbar(image, ax=ax, label=color_label)
        if colorbar.solids is not None:
            colorbar.solids.set_rasterized(False)
            # Avoid vector-viewer hairline seams between adjacent color swatches.
            colorbar.solids.set_edgecolor("face")
    elif kind == "forest":
        estimate = _numbers(panel.get("values"), "estimates")
        lower = _numbers(panel.get("lower"), "lower")
        upper = _numbers(panel.get("upper"), "upper")
        _same_length(estimate, lower, upper, panel["labels"])
        if not panel.get("interval_label"):
            raise ValueError("forest intervals require a statistical definition")
        if np.any(lower > estimate) or np.any(upper < estimate):
            raise ValueError("interval bounds must contain the estimate")
        ax.errorbar(
            estimate,
            np.arange(len(estimate)),
            xerr=[estimate - lower, upper - estimate],
            fmt="o",
            capsize=3,
            label=panel["interval_label"],
        )
        ax.set_yticks(range(len(estimate)), panel["labels"])
        if "reference" in panel:
            ax.axvline(panel["reference"], color="0.4", linestyle="--", linewidth=0.7)
        ax.invert_yaxis()
        ax.legend()
    else:
        groups = panel.get("groups", [])
        if not groups:
            raise ValueError("box requires supplied raw groups")
        arrays = [_numbers(group["values"], "group") for group in groups]
        ax.boxplot(
            arrays,
            tick_labels=[group["label"] for group in groups],
            showfliers=False,
            whis=1.5,
        )
        for i, values in enumerate(arrays, start=1):
            # Fixed horizontal offsets affect only overlap, never data values.
            ax.scatter(
                i + np.linspace(-0.09, 0.09, len(values)), values, s=10, zorder=3
            )
    ax.set(xlabel=panel["xlabel"], ylabel=panel["ylabel"])
    if panel.get("title"):
        ax.set_title(panel["title"], loc="left")


def render(
    spec_path, output, *, formats=("svg", "pdf", "png"), dpi=300, overwrite=False
):
    import matplotlib.pyplot as plt

    sys.path.insert(0, str(SKILL.parent / "lab-ultra-scientific-visualization" / "scripts"))
    from figure_export import export_figure

    spec_path = Path(spec_path).resolve()
    spec = read_json(spec_path)
    for key in ("title", "description", "data_source"):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ValueError(f"recipe requires {key}")
    panels = spec.get("panels", [])
    if not isinstance(panels, list) or not 1 <= len(panels) <= 12:
        raise ValueError("provide between one and twelve panels")
    ncols = spec.get("ncols", min(2, len(panels)))
    if (
        isinstance(ncols, bool)
        or not isinstance(ncols, int)
        or not 1 <= ncols <= len(panels)
    ):
        raise ValueError("ncols must be an integer between one and the panel count")
    output = Path(output).resolve()
    recipe_path = Path(str(output) + ".recipe.json")
    replay_path = Path(str(output) + ".reproduce.py")
    if not overwrite and any(
        p.exists()
        for p in [
            recipe_path,
            replay_path,
            *[Path(str(output) + "." + fmt) for fmt in formats],
        ]
    ):
        raise ValueError("output already exists; choose a new base or use --force")
    with publication_style(
        spec.get("style", "science"),
        width_mm=spec.get("width_mm"),
        height_mm=spec.get("height_mm"),
        venue=spec.get("venue"),
        palette=spec.get("palette", "okabe_ito_on_white"),
        overrides=spec.get("style_overrides"),
        language=spec.get("language"),
    ) as receipt:
        fig, axes = plt.subplots(
            (len(panels) + ncols - 1) // ncols, ncols, squeeze=False
        )
        try:
            for ax, panel in zip(axes.flat, panels):
                draw_panel(ax, panel)
            for ax in list(axes.flat)[len(panels) :]:
                ax.remove()
            report = export_figure(
                fig,
                output,
                formats=formats,
                dpi=dpi,
                mkdir=True,
                overwrite=overwrite,
                write_manifest=True,
                accessibility={"title": spec["title"], "desc": spec["description"]},
                provenance={
                    "data_source": spec["data_source"],
                    "input_recipe": str(spec_path),
                    "input_sha256": sha256(spec_path),
                    "renderer_sha256": sha256(__file__),
                    "style": receipt,
                    "statistics": "none fitted; box summary uses supplied raw values",
                },
            )
        finally:
            plt.close(fig)
    recipe_path.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    replay_path.write_text(
        "# Reproduce with the recorded local figure-library environment.\n"
        "from pathlib import Path\nimport sys\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\n"
        "from render_recipe import main\n"
        f"raise SystemExit(main([str(Path(__file__).with_name({recipe_path.name!r})), "
        f"'--output', str(Path(__file__).with_name({output.name!r})), "
        f"'--formats', {','.join(formats)!r}, '--dpi', {str(dpi)!r}, *sys.argv[1:]]))\n",
        encoding="utf-8",
    )
    report["editable_recipe"] = str(recipe_path)
    report["reproduce_script"] = str(replay_path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--formats", default="svg,pdf,png")
    parser.add_argument("--dpi", type=float, default=300)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = render(
            args.spec,
            args.output,
            formats=args.formats.split(","),
            dpi=args.dpi,
            overwrite=args.force,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
