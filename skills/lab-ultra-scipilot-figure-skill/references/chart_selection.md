# Chart selection from the scientific question

Read the supplied data profile before selecting an encoding. Treat numeric identifiers as labels, not measurements; distinguish paired observations from independent samples.

| Question | Useful starting point | Check before rendering |
|---|---|---|
| Change over time or ordered dose | Line / point-range | Keep missing gaps; don't connect unordered categories |
| Compare groups or effects | Dot/interval, bar, or raw distribution | Use a zero baseline for lengths; show sample structure |
| Small sample distribution | Raw points, optionally a box summary | Avoid smooth density claims unsupported by the sample |
| Large or multimodal distribution | ECDF, histogram, box/violin/raincloud | Record bin edges or KDE bandwidth; show n |
| Association between continuous variables | Scatter / binned density | Regression and r/p annotations require an explicit analysis |
| Matrix with side annotations | Marsilea / ComplexHeatmap | Share comparable normalization and record clustering |
| Set overlap | UpSetPlot | Define intersection and denominator semantics |
| Circular topology | pyCirclize | Use a circular layout only when topology warrants it |
| Multi-panel evidence | Shared layout / patchwork / SVG composition | Same variable should keep its units, color and scale policy |

A pie chart, dual axis, small-n bar or projected 3D surface is not automatically a scientific falsehood. Prefer clearer alternatives when they improve comparison; reject the misleading encoding rather than applying a blanket chart-name ban.

Read [shared integrity gates](../../lab-ultra-scientific-figure-maker/references/selection-and-integrity.md) for admissibility and [plot_recipes.md](plot_recipes.md) for code entrypoints.
