# Editable method diagrams

Extract the graph before arranging it: each node has an ID, exact paper label, role and group; each edge has source, target, direction and a stated meaning. Keep uncertainty about a relationship explicit.

Use lab-ultra-figure-spec for structured SVG, or lab-ultra-draw-io when native editing is needed. Use a left-to-right pipeline for ordered stages, bands for layers, a tree for hierarchy, and a separate return edge for feedback when these relationships match the source.

Use one palette and type hierarchy from the FigureIR. Distinguish edge meanings through labels or line styles as well as color. Arrow thickness only encodes quantitative weight if that weight is supplied.

Check node/edge correspondence against the paper before reviewing alignment, crossings and text at final size. Export the native source and a vector rendition. Complex layout is a reason to group or use a stronger editable renderer, not to rasterize the scientific graph.

AutoFigure-Edit and DeTikZify are cataloged experiments for explicit selection. Their inferred output requires editable reconstruction/verification and does not establish the paper's scientific relationships.

Read [shared routes](../../lab-ultra-scientific-figure-maker/references/routing.md) and [material library](../../lab-ultra-scientific-figure-maker/references/material-library.md) for the current entrypoints.
