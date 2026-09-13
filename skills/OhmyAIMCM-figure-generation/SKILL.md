---
name: OhmyAIMCM-figure-generation
description: OhmyAIMCM CUMCM paper suite. Refine scientific plotting code through execution and visual feedback while preserving supplied data and statistical definitions. Use when a figure needs iterative code/render repair; reuse the shared material library and exporter.
metadata:
  local-role: iterative-code-and-visual-repair
---

This is the isolated `OhmyAIMCM` edition. Use only the sibling `OhmyAIMCM-*`
modules linked here; do not substitute stable or vendor skills.

# OhmyAIMCM-figure-generation

Use the [shared material library](../OhmyAIMCM-scientific-figure-maker/references/material-library.md) to select an existing recipe before writing new code. This locally rewritten adapter does not execute the unresolved-license upstream template or model prompts.

1. Expand the request into explicit data mappings, panel purpose, units, scales, supplied uncertainty and final-size constraints.
2. Resolve the relevant library example, or use OhmyAIMCM-scientific-figure-maker/scripts/render_recipe.py for an ordinary data figure.
3. Run code in the selected local environment. On an error, repair the code while preserving data, transforms and statistical meaning. Retry when there is a concrete correction, rather than repeating an unchanged call.
4. Inspect the actual image for clipping, overlap, missing glyphs, misleading encodings and label consistency. Record what changed and rerender when needed.
5. Use the shared exporter and final-size checks. Deliver the editable recipe/source with material and data provenance.

No automatic highlighting of "Ours", invented uncertainty, added regression fit or altered axis baseline is permitted as an aesthetic repair. Synthetic data are used only for explicitly labeled demos/tests.

For a starter launcher, scripts/figure_template.py accepts --type, --output and --name; the generated Python still requires an explicit --data recipe JSON. It contains no plausible-looking experiment values.

Read [figure-prompts.md](references/figure-prompts.md) for the local repair checklist.
