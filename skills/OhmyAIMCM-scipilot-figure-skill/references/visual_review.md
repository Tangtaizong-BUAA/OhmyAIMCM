# Final-size visual review

Render the figure using the selected shared style and layout. The retained visual_qa.audit_layout(fig) helper can report missing glyphs, out-of-bounds text and possible overlaps; it does not certify the evidence or publication acceptance.

Inspect a rendered preview and the actual exported file. Check:

1. CJK text, minus signs, scientific symbols and subscripts are present.
2. Axes, tick labels, legends and annotations are not clipped or overlapping.
3. Panel labels align and keep the chosen typography.
4. Colorbars and other neighboring axes have enough space.
5. Categories remain distinguishable through marks/line styles as well as color.
6. All observations, interval bounds and declared missing values remain visible.
7. Comparable panels retain the same variable mapping, units and scale policy.
8. Font sizes and image resolution remain suitable in the final manuscript.

Repair the editable source, then rerender the affected result. Use installed glyph-complete fonts through publication_style overrides; resolve overlaps with the current layout engine or catalog label-placement tools. Do not switch to a tight crop merely to conceal a layout issue when physical dimensions are fixed.

Several related fixes can be reviewed together. Continue when there is a concrete improvement; report limitations that require a different specification. No fixed number of model calls is required.

Use [the shared material library](../../OhmyAIMCM-scientific-figure-maker/references/material-library.md) and OhmyAIMCM-scientific-visualization's figure_export for final output. Run post-export metadata checks and inspect the delivered file, since a preview alone can miss export-specific differences.
