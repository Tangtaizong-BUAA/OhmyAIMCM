# Upstream adoption and conflict resolution

The owner has authorized adoption of the researched materials. Read the current machine-readable catalog at assets/library-catalog.json and its usage guide in [material-library.md](material-library.md).

## Current adoption

- Bundled materials: selected SciencePlots styles, cnsplots typography, tueplots dated dimensions, and cmcrameri RGB tables. These are ordinary local assets; using them requires no additional approval or vendor imports.
- Recipe references: the catalog resolves original examples by ecosystem and chart purpose. Read the returned files, adapt their code to supplied data, and retain the applicable attribution.
- Optional backends: install or invoke only the backend actually needed by the selected route and covered by the user's task. Reuse prior authorization. A checkout is not an installed runtime; do not bulk-install all catalog projects.

Source revisions remain in provenance/upstreams.lock.yaml. Bundled copies have source and content hashes in assets/upstream/manifest.json. Clones in vendor/figure-upstreams remain unchanged as update/reference baselines. Active local copies may intentionally differ; record those changes rather than rewriting upstream history.

## One owner for each decision

| Decision | Owner | Conflict resolution |
|---|---|---|
| Data, transforms, estimates, intervals and claims | FigureRequest / supplied analysis | Template example data and automatic tests/fits cannot override supplied evidence |
| Requested font, physical size, palette and deliverables | Explicit user/manuscript specification | Override style defaults; verify actual rendered dimensions |
| Venue requirements | Current exact venue instructions, or a labeled dated snapshot | A style named nature/ieee/cns is not a compliance profile |
| Visual family | One publication_style context | Select science, nature, ieee or cns; do not stack competing global setup functions |
| Palette meaning | Variable semantics | Qualitative categories differ from sequential, diverging and cyclic values |
| Layout | One selected composition engine | Do not combine constrained layout with tight_layout or run global Seaborn setup afterward |
| Export | OhmyAIMCM-scientific-visualization figure_export.py | Explicit crop/DPI/fonts; preserve physical page size by default |
| Acceptance | Scientific checks plus final-size inspection | SVG checks or model aesthetic scores are review evidence only |

SciencePlots' implicit LaTeX, tight crop, default canvas and category colors are overridden by the request-level resolver. cnsplots supplies typography without adopting its global setup, pixel canvas, gnuplot colormap or automatic statistical annotations. Upstream examples of emphasis on "Ours", inferred confidence bands, arbitrary axis truncation and default regression fitting are not adopted.

## Source terms

Preserve bundled MIT/BSD notices. GPL tools can be used as tools; review their source terms when copying or distributing code, rather than imposing a blanket runtime ban. Rougier book code is BSD-2-Clause while its prose/illustrations have separate CC BY-NC-SA terms. Unresolved-license MatPlotAgent and the original OhmyAIMCM-figure-generation sources remain historical references; active iterative instructions and the starter generator are locally rewritten.

PaperBanana wrappers have already been adapted as local Skills. Their MCP/CLI availability must be checked when selected; do not label them unadapted or presume a backend is present. No wrapper may return bitmap-only scientific structure as an editable final figure.

The separate [image-assisted illustration route](image-assisted-figures.md) can
deliver a reviewed raster mechanism with its native draft, generation provenance
and editable annotation/composition source. State that editability boundary; do not
call the raster a vector or mesh, or silently substitute a PaperBanana backend for
an explicitly requested OpenAI model.
