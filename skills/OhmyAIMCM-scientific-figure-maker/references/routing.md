# Rendering routes

Select a route by evidence type and the requested editable format. This file owns routing; the material catalog supplies implementation examples.

| Request | Primary owner | Materials / support |
|---|---|---|
| Statistical or experimental data | OhmyAIMCM-scientific-figure-maker, with OhmyAIMCM-scientific-visualization for export/audit | Bundled publication styles; catalog specialized recipes |
| Data profiling and chart selection | OhmyAIMCM-scipilot-figure-skill | Existing profile_data.py; shared integrity/selection rules |
| ML method or result extraction | OhmyAIMCM-academic-plotting | Convert paper context into FigureRequest; return to the selected renderer |
| Workflow / dependency graph | OhmyAIMCM-figure-spec; OhmyAIMCM-draw-io when native .drawio is required | Apply diagram-design.md; meaningful dependencies, not paper section order |
| Physical / geometric / mathematical mechanism | Native TikZ or SVG; Inkscape for optional composition | Verify the local tool; preserve editable source, equations and geometry; no mandatory node/edge grammar |
| 3D physical scene / apparatus / layered solid | Available Blender/CAD scene scripting; PyVista for supplied meshes/fields | Read physical-scenes.md; preserve physical relationships, native geometry, camera and editable labels; simple analytic scenes may use Matplotlib 3D |
| Complex illustrative mechanism / physical scene needing visual refinement | Verified Blender/SVG draft → available imagegen edit → deterministic annotation/composition | Read image-assisted-figures.md; preserve topology and scientific meaning, then re-review the actual generated image against the draft and model |
| Search visual references | OhmyAIMCM-agent-figure-gallery | Stable reference IDs; catalog design_examples |
| Iterative code and visual feedback | OhmyAIMCM-figure-generation | Shared recipes/style/export; preserve input data on repair |
| R / MATLAB source requested | Catalog entries for that ecosystem | patchwork/ComplexHeatmap/gramm; verify the installed runtime before running |
| TeX source requested | Native PGFPlots recipe or compatible converter | Keep .tex and input data; verify the local TeX runtime |
| Conceptual bitmap asset | Available imagegen | Keep the source/prompt and review; exact scientific labels and relationships belong in editable overlays |
| PaperBanana experiment explicitly selected | OhmyAIMCM-generate-plot / OhmyAIMCM-generate-diagram / OhmyAIMCM-evaluate-diagram | Check actual MCP or CLI availability; wrappers alone are not a runtime |

For multi-panel figures, all panels share one FigureIR, category mapping, normalization where comparable, and final-size specification. Use Matplotlib constrained layout for ordinary panels, Marsilea for Python annotated matrix compositions, patchwork for ggplot composition, or svg_utils for already-rendered mixed SVG panels. Do not run a second layout engine over the first without rechecking coordinates.

Vega-Lite and Flint are optional implementation references. Preserve FigureIR as the outer contract instead of replacing it with an upstream IR. Data Formulator, AutoFigure-Edit and DeTikZify require their own runtime and model configuration; catalog availability does not enable them automatically.

API/CLI execution is real use of scientific software. Do not require a GUI or
commercial product merely for prestige. Do not silently fall back to colored-card
templates when a mechanism route is unavailable; use an adequate native route or
report the specific missing capability. A vector editor must never move data marks,
resize error bars or alter scientific relationships for appearance.

Image assistance is not compulsory for every complex figure: dense workflows, exact
geometric constructions and data fields often remain clearer in native vector/code.
The host's imagegen capability is optional and is not installed by this 20-module
suite. Preserve an explicitly requested model; tool availability alone does not
prove that model was used. Do not silently change providers or incur API billing.
