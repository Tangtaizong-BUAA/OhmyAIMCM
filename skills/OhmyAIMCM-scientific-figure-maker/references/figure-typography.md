# Figure typography: actual faces, not prestigious preset names

The 2025B/2023A audit found two distinct implementation problems: the `nature`
upstream put DejaVu Sans first, while a custom Chinese renderer forced every text
artist to `STHeiti Light.ttc`. That file's default face was **Heiti TC Light**, not
the recorded Heiti SC; its Latin letters/numerals were also used indiscriminately.
Neither DejaVu nor a Chinese sans face is inherently unusable. The failure is an
unexamined font fallback and inconsistent language/math/size roles.

## A coherent, adjustable starting point

- Use a regular Arial/Helvetica-like face for Latin labels, numerals and upright
  units; add a compatible regular simplified-Chinese face for CJK glyphs. Do not
  force the whole figure into a CJK font file or inherit the paper's Songti headings.
- For a 150–170 mm Chinese-paper figure, start near 8–9 pt for labels and 7.5–8 pt
  for ticks/secondary keys. These are owner-oriented starting sizes, not a journal
  rule or an automatic readability pass. Specify size at the **embedded width**:
  effective pt = source pt × embedded width / source width. Reflow before shrinking.
- Keep ordinary labels regular weight; reserve emphasis for panel identifiers or
  scientific notation that actually requires it. Do not make every title bold or
  let an oversized formula dominate the physical diagram.
- Typeset indices and variables as mathematics: `$c_i$`, not literal `c_i` or Unicode
  lookalike subscripts. Match vector/scalar distinctions to the manuscript. Units
  stay upright; keep minus, multiplication, degree signs and parentheses consistent.
  In Matplotlib, a single CJK + `$math$` Text may send its ordinary Chinese through
  MathText's single-font path and lose glyphs. For such mixed labels use the helper's
  `mixed_textbox` with `AnnotationBbox`/an offset box, or a verified TeX renderer.
  It packs separate prose/math runs with a shared baseline and preserves the text.
- Keep full explanatory sentences in the caption when already repeated there.
  If restructuring labels is needed, preserve all scientific qualifiers; a font-only
  comparison must not quietly rewrite the explanation or change plotted values.

## Matplotlib route

Use the loaded suite's helper, for example:

```python
from figure_library import publication_style
from figure_typography import inspect_figure_typography

with publication_style("nature", language="zh-CN", width_mm=160, height_mm=85) as receipt:
    # Create axes, draw supplied data, and place math/text without font-file forcing.
    # Apply explicit per-figure overrides only when scientifically/visually needed.
    typography_review = inspect_figure_typography(fig, final_width_mm=160)
    # Export through the shared exporter; keep receipt and typography_review.
```

`resolve_figure_fonts` (in the same typography helper) is available for native custom
composition. It returns scoped rc settings and actual face/file/index/hash records.
The material resolver uses it for nature/cns unless the caller explicitly owns the
font family. The `language` argument also supports a Chinese-first task brief without
silently translating all labels to English. Other languages need an explicit font
choice. Existing serif requests remain valid; one family's presence is not a veto.

Preserve Matplotlib's resolved `FontPath` face index. Converting it to an ordinary
string, or passing an unindexed `.ttc` filename to every artist, can select face zero.
The resolver verifies the face actually loaded; an older backend that cannot load
the requested face must use a supported local font, not report false success.
No system fonts are modified, extracted, downloaded or redistributed by this helper.

```python
from matplotlib.offsetbox import AnnotationBbox
from figure_typography import mixed_textbox

box = mixed_textbox(r"镜心 $c_i$：位置", fontsize=8.5)
ax.add_artist(AnnotationBbox(box, xy=anchor, xybox=label_position,
    xycoords="axes fraction", boxcoords="axes fraction", frameon=False,
    box_alignment=(0, 0.5), pad=0, arrowprops={"arrowstyle": "-"}))
```

For SVG/TikZ/draw.io/image-model overlays, apply the same language and role decisions
in that renderer. Retain editable text, resolve real glyph coverage and inspect the
actual PDF conversion. A CSS fallback list or an SVG screenshot alone is insufficient.

## Export acceptance

Inspect the actual figure and the final paper PDF. For a Poppler-equipped environment,
`pdffonts figure.pdf` and `pdffonts paper.pdf` reveal embedded face names and types;
compare them with the intended faces. Check that body labels are not unexpectedly
TC/Black/Light, synthetic bold, Type 3 or missing glyphs. Legitimate explicitly chosen
faces remain allowed. PDF font embedding does not prove visual quality, and SVG text
without embedded fonts may look different on another machine.

The helper's inspection screens faces, literal subscript-like labels and effective
size; it does not certify math glyphs, pairwise kerning, readability or attractiveness.
Judge a representative plot and mechanism at final width, then reuse the verified
family/size roles across that paper. Recheck after composition, resize or conversion.
Do not repair data figures with a generative image model merely to replace fonts.

Basis checked 2026-09-09: [Nature figure specifications](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/)
recommend sans-serif Arial/Helvetica, editable embedded text and a distinct panel-label
hierarchy. Their exact English-journal point sizes are **not** adopted as CUMCM rules.
[Matplotlib font documentation](https://matplotlib.org/stable/users/explain/text/fonts.html)
distinguishes default fonts, glyph coverage and PDF embedding.
