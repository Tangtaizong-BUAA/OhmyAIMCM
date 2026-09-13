# ML data recipe selection

Use the [shared material library](../../OhmyAIMCM-scientific-figure-maker/references/material-library.md) to obtain the actual recipe source and style. The following are selection hints, not automatic analysis steps.

| Evidence / comparison | Recipe |
|---|---|
| Training over ordered steps | line; retain gaps; use supplied intervals only |
| Benchmarks or ablations | dot/interval comparison; bar when a meaningful zero baseline helps |
| Effect estimates with intervals | forestplot / forest starter |
| Raw replicate distributions | box with raw observations; PtitPrince when KDE is justified |
| Confusion or attention matrix | heatmap with explicit units/normalization |
| Annotated or clustered matrices | Marsilea (Python), ComplexHeatmap (R) |
| Multi-panel narrative | shared Matplotlib layout, Marsilea or patchwork |
| Embeddings | supplied coordinates or an explicitly specified projection; record seed and parameters |

Keep held-out evaluation and training statistics separate. Do not fit regression, log-transform a metric merely because it is named loss, infer a confidence interval from an unlabeled error array, or normalize unrelated metrics into a radar chart without justification.

Preserve exact data and source hashes through the edit loop. Put any required estimation in an explicit analysis step. Shared figure_export writes requested formats and the provenance manifest; it does not replace scientific review.
