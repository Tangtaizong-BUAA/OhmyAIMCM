# Material library

Use this library before recreating a scientific chart or copying a random template. Resolve paths relative to this Skill's scripts directory; catalog commands need only Python's standard library.

## Find and inspect a recipe

```bash
python3 scripts/figure_library.py find --tag heatmap --ecosystem python
python3 scripts/figure_library.py resolve marsilea
python3 scripts/figure_library.py styles
python3 scripts/figure_library.py verify --sources
```

find lists candidates; resolve verifies the pinned checkout and returns real files to read. It does not import or execute upstream Python. If a source checkout is missing, the bundled styles still work; restore only the needed source from its locked origin or use an available deterministic recipe.

| Need | Catalog tag / preferred material |
|---|---|
| Common line, bar, scatter, matrix, interval or raw-distribution figure | render_recipe.py; shared style and export |
| Annotated heatmap / dendrogram / complex matrix panels | heatmap: Marsilea (Python), ComplexHeatmap (R) |
| Set intersections | set_intersection: UpSetPlot |
| Circular topology / chord diagram | circular / chord: pyCirclize |
| Raincloud distributions | raincloud: PtitPrince |
| Forest / effect estimates | forest: forestplot |
| Supplied statistical annotations | significance: statannotations |
| Label overlap | label_collision: adjustText (Python), ggrepel (R) |
| Composition | multi_panel: Marsilea, patchwork; svg_composition: svg_utils |
| Design examples and typography | design_examples: scientific-visualization-book code |
| Web / Agent IR | declarative_chart: Vega-Lite; agent_ir: Flint |
| MATLAB plotting or export | statistical_plot: gramm; figure_export: export_fig |
| TeX export | native_tex: PGFPlots; tikz_export: converters after compatibility checks |

## Scoped styles

Put this Skill's scripts and the sibling lab-ultra-scientific-visualization scripts on sys.path in the figure's source. Use one style context for the whole figure:

```python
from figure_library import publication_style, colormap
from figure_export import export_figure
import matplotlib.pyplot as plt

with publication_style("nature", language="zh-CN", width_mm=150, height_mm=90) as materials:
    fig, ax = plt.subplots()
    # Draw the supplied data with the selected recipe.
    export_figure(fig, "outputs/result", formats=["svg", "pdf"], mkdir=True,
                  provenance={"materials": materials}, write_manifest=True,
                  accessibility={"title": title, "desc": description})
```

Profiles: science and ieee retain their explicit serif starting points. Nature and
cns now resolve an available regular Arial/Helvetica-style Latin face, not the
upstream's DejaVu-first family list. `language="zh-CN"` adds a verified simplified
Chinese face after Latin, with a Chinese-paper size starting point. Explicit font
overrides still win and are caller-owned. Read [figure-typography.md](figure-typography.md)
for face-index, glyph and final-PDF checks. No font downloads, extraction or implicit
TeX activation. A missing verified face must be resolved, not hidden by a fallback.
These plot profiles are not diagram templates. For flows or scenes, follow
[diagram-design.md](diagram-design.md) and verify the actual regular Chinese font
face; an explicit Songti override can undo the intended sans-serif choice. Neither
the style's name nor successful PDF export establishes acceptable diagram typography.

Explicit width_mm and height_mm win over upstream sizes. Optional venue names include icml2024-single, icml2024-full, neurips2024-full and iclr2024-full; their year is intentional. Height defaults to 0.66 × width if omitted and should be set for dense panels. Exact publication rules still come from the target manuscript.

Use colormap("batlow", kind="sequential"), colormap("vik", kind="diverging"), or colormap("romaO", kind="cyclic"). A diverging palette needs a meaningful center; cyclic data need a full-period domain. Missing cells are gray. Keep data normalization separate from the palette.

## Runnable starter

The current workspace has a verified core runtime at figure-lab/.venv/bin/python. From the repository root, recreate it if needed with uv venv figure-lab/.venv --python 3.13, then uv pip install --python figure-lab/.venv/bin/python -r figure-lab/requirements-figure-library.txt. Use an existing compatible environment when appropriate; do not install optional catalog backends in bulk.

```bash
python3 scripts/render_recipe.py supplied.recipe.json --output outputs/figure1
```

Here python3 means the selected environment's interpreter, not an assumption that the
system Python includes Matplotlib. Use this loaded edition's `scripts/render_recipe.py`,
not a historical root `.agents/skills/` copy.

The JSON requires title, description, data_source and a nonempty panels list. It accepts style, language, width_mm, height_mm, venue, ncols, palette and style_overrides. Every panel requires kind, xlabel and ylabel. No sample results, uncertainty or fits are generated.

| kind | Data fields |
|---|---|
| line / scatter | series: list of label, x, y; line may use lower, upper and interval_label |
| bar | labels, values; values are plotted directly with a zero baseline |
| heatmap | values matrix, xlabels, ylabels, color_label; optional color_kind/cmap, center, vmin/vmax |
| forest | labels, values, lower, upper, interval_label; optional reference |
| box | groups: list of label, values containing raw observations |

Line null values retain gaps; heatmap null cells are marked missing. Other starters reject missing numeric inputs so they cannot silently omit them. A box shows the supplied observations and a standard 1.5 IQR summary. More complex analysis belongs in source code chosen from the catalog, not hidden template calculations.

The starter emits SVG/PDF/PNG, an export manifest, an editable recipe JSON and a reproduction script referencing the local helper. Preserve the helper revision and environment for replay. Run the contract/metadata checks appropriate to the figure and inspect at final size; the starter does not certify scientific claims.
