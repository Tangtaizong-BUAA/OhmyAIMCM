---
name: OhmyAIMCM-scipilot-figure-skill
description: OhmyAIMCM CUMCM paper suite. Profile scientific datasets and recommend chart types from the research question, sample structure, missingness and uncertainty. Use for choosing how to show supplied data, statistical visualization advice and final-size visual review; use the shared figure library for styles and rendering.
license: MIT
metadata:
  local-role: data-profiling-chart-selection-and-visual-review
---

This is the isolated `OhmyAIMCM` edition. Use only the sibling `OhmyAIMCM-*`
modules linked here; do not substitute stable or vendor skills.

# OhmyAIMCM-scipilot-figure-skill

Understand the data and comparison before selecting a chart. The shared [Scientific Figure Maker](../OhmyAIMCM-scientific-figure-maker/SKILL.md) owns rendering routes, material selection and delivery.

## Data profiling

Infer the comparison question from the user's request and paper context. If data meaning is unresolved, ask only for the missing scientific information. Exploratory plots do not require a pre-existing conclusion.

Use the retained profiler when its dependencies are available:

```bash
python scripts/profile_data.py data.csv --group condition
```

Read [data_profiling.md](references/data_profiling.md) when interpreting the report. Verify column semantics, numeric IDs, paired/repeated observations, per-group sample counts, missingness and outliers. A profiling suggestion does not authorize filtering or inferential testing.

## Chart choice

Read [chart_selection.md](references/chart_selection.md). Choose a recommended encoding and explain the relevant tradeoff briefly. User-specified encodings may be kept if they preserve the evidence; add raw points or an explicit scale explanation where useful.

For implementation, use [plot_recipes.md](references/plot_recipes.md). These routes reuse the common styles, mature specialized libraries and OhmyAIMCM-scientific-visualization exporter.

## Shared figure settings

Use one publication_style context from OhmyAIMCM-scientific-figure-maker/scripts/figure_library.py. Explicit final width, font selection and palette semantics win over preset defaults. For Chinese text, inspect installed CJK glyph coverage and pass the chosen font as a style override. A minus-sign setting does not fix missing CJK glyphs.

Read [journal_specs.md](references/journal_specs.md) only when a particular publication target matters. Otherwise proceed with a stated general figure size.

The original setup_style.py, export_figure.py and check_figure.py remain for compatibility with old scripts, but are not the default pipeline. Do not mix their global settings or independent export rules into the shared route.

## Review

Read [viz_pitfalls.md](references/viz_pitfalls.md) and [publication_checklist.md](references/publication_checklist.md). The retained visual_qa.py helpers can inspect an already configured figure. Use visual_review.md for visual review; treat its styling suggestions as optional under the shared settings.

Check meaning, visible missingness, uncertainty descriptions, labels, clipping, panel alignment and final-size glyphs. A grayscale preview is one diagnostic, not a color-vision certification. Export using the shared exporter, then inspect the actual delivered file.
