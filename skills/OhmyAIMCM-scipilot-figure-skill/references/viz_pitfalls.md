# Scientific visualization pitfalls

Use these checks in context; they are not a blacklist of chart names.

1. Preserve raw observations and declared exclusions. A template must not generate experimental scores, erase outliers or fill missing samples silently.
2. Bar/area magnitude needs a meaningful baseline. Points and lines may use nonzero limits when the comparison is honestly represented.
3. Do not connect unordered categories or bridge missing runs as observations.
4. Show small samples directly when feasible. KDE/violin smoothness is an estimation choice requiring sample and bandwidth context.
5. Error bands are not decoration: name SD, SE, CI or another supplied interval and the unit of replication.
6. Regression, significance tests, smoothing, clustering and normalization must be declared analysis choices.
7. Dual axes, projections and 3D views require an interpretable mapping; prefer aligned panels where correlation could be manufactured.
8. Use palette semantics that match the data, with redundant categorical marks and visible missingness.
9. Keep one style and one layout owner. Do not run global setup functions or tight_layout after a shared constrained layout.
10. Inspect the delivered file at its intended size. Check scientific labels, CJK glyphs, scale bars, panel alignment and raster resolution.

For active style and export code, use the [shared material library](../../OhmyAIMCM-scientific-figure-maker/references/material-library.md). The old local setup/export/check scripts are compatibility utilities, not competing defaults.
