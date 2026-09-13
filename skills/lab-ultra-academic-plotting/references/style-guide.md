# ML figure style and dimensions

The shared [material library](../../lab-ultra-scientific-figure-maker/references/material-library.md) owns styles and dated venue widths. Explicit manuscript dimensions and requested fonts override those presets. Measure final-size text after any scaling during inclusion in the paper.

Use one publication_style context for all panels. Do not combine global rcParams updates, Seaborn set_theme, cnsplots setup and multiple journal presets. Use the lab-ultra-scientific-visualization exporter to keep page dimensions explicit and SVG text editable.

Qualitative, sequential, diverging and cyclic palettes solve different tasks. No palette is universally distinguishable under all color-vision conditions; use redundant marks and review the actual rendering.

Emphasis follows the comparison question. Do not automatically gray all baselines or accent a method named "Ours". Error bands need real interval estimates and their definition; they are not a styling option.

For publication rules, read the sibling lab-ultra-scientific-visualization journal_requirements reference and verify the exact venue/year/stage when relevant. Presets named nature, ieee or cns are visual starting points.

Use PDF for LaTeX where suitable, SVG for editable vector graphics and raster output when required. Set DPI according to embedded raster content and the actual destination. A vector container can legitimately include an image layer with known provenance.

Place the exported figure at its planned width, describe the evidence and uncertainty in its caption, and recheck readability in the final manuscript.
