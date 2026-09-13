# Shared recipe entrypoints

Use [material-library.md](../../lab-ultra-scientific-figure-maker/references/material-library.md) for the executable starter schema, library lookup and style context. All routes use actual supplied data and a single export owner.

| Figure | Source |
|---|---|
| Line / scatter / bar / simple matrix | lab-ultra-scientific-figure-maker/scripts/render_recipe.py |
| Raw distribution / raincloud | box starter; PtitPrince tutorial for raincloud |
| Complex annotated heatmap | Marsilea examples or ComplexHeatmap vignette |
| Effect estimate intervals | forest starter or forestplot examples |
| Set intersections | UpSetPlot examples |
| Circular or chord diagram | pyCirclize notebooks |
| Text or statistical annotation | adjustText / ggrepel / statannotations |
| Multi-panel composition | Matplotlib constrained layout, Marsilea, patchwork or svg_utils |
| Interactive web chart | Vega-Lite examples or an available Plotly runtime |

Use figure_library.py resolve <id> to verify the checkout and obtain exact example paths. Read the selected example, preserve scientific mappings, and adapt its marks and layout. Do not copy its random/simulated data into a real result or inherit its global styling, automatic tests, crop, fonts or export settings.

Use lab-ultra-figure-generation when code/render/visual repair is needed. Repairs preserve the source data and chosen statistical definitions.
