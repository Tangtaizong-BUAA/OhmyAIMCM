---
name: lab-ultra-figure-spec
description: Experimental CUMCM lab suite. Render editable workflow and dependency diagrams from FigureSpec JSON. Use when nodes and edges express the actual scientific relationships; route optical, geometric or other mechanisms beyond this grammar to native TikZ or SVG.
---

This is the isolated `lab-ultra` edition. Use only the sibling `lab-ultra-*`
modules linked here; do not substitute stable or vendor skills.

# FigureSpec

Use the local `scripts/figure_renderer.py`; no ARIS checkout, remote reviewer or
external model is required. This is a bounded node/edge tool, not a universal
scientific illustration engine or a publication-quality certificate.

Before drawing a paper diagram, read the shared
[scientific diagram guide](../lab-ultra-scientific-figure-maker/references/diagram-design.md).
Choose scientific entities and edge meanings before box styles. Do not draw an
arrow merely because two sections are consecutive in the paper.

## Defaults and freedom

- `style.theme: "paper"` is the default: white rectangular nodes, neutral outlines,
  normal-weight labels and no automatic per-node color cycle.
  The font stack includes Chinese sans-serif candidates; it does not bundle fonts
  or guarantee the chosen face. Verify actual glyph coverage and exported font weight.
- Explicit node shapes, fills and strokes remain available for meaningful encoding.
  A rounded terminator or colored experimental group is not universally forbidden.
- `style.theme: "presentation"` opts into legacy automatic colors and rounding.
  Do not use it for this owner's paper figures unless the request calls for it.
- Group backgrounds are optional. Prefer alignment, spacing or light boundary lines
  when they communicate the same relationship. Avoid decorative nested cards.
- Set `canvas.width_mm` from the FigureRequest. Pixel canvas size alone does not
  define paper size. Supply `title` and `description` for SVG metadata.

## Execute

From this Skill directory, using an existing Python interpreter:

```bash
python3 -B scripts/figure_renderer.py schema
python3 -B scripts/figure_renderer.py validate /absolute/path/spec.json
python3 -B scripts/figure_renderer.py render /absolute/path/spec.json --output /new/path/figure.svg
rsvg-convert -f pdf /new/path/figure.svg -o /new/path/figure.pdf
```

Use new output paths; the renderer refuses replacement unless `--force` is explicit.
Check converter availability before use. Keep JSON as source of truth and modify it
before rerendering, rather than silently diverging SVG and JSON.

## Inspect and deliver

Schema errors and node canvas escape stop rendering. Text-fit estimates and small-font
warnings are screening heuristics, not a font-shaping or line-collision engine.
Inspect the actual figure in the paper for label fit, arrow paths, group boundaries,
final-size readability and scientific meaning. Review warnings; do not satisfy them
by arbitrary font shrinking or deleting meaningful edges.

Deliver JSON, editable SVG and requested exports with the FigureRequest/IR, source
bindings, checks performed and limitations. The shared figure owner performs contract
and SVG checks. A model's score is not an acceptance certificate.
