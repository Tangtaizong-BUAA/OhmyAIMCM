# Scientific diagrams, not presentation cards

Read for paper workflows, mechanisms, architectures and redesigns. This is the
owner's paper preference, not a rule that all journals prohibit color or rounding.

## Select the explanatory content

Ask what the reader cannot understand from a short sentence or the equations alone.
Use a diagram for dependencies, geometry, mechanisms, hierarchy or changes of state.
A sequence of performed tasks is not automatically a useful scientific figure.

For an explanation-rich paper, distinguish a result plot from an object/construction diagram.
Consider the scientific objects, geometry, measurement formation, constraints or state changes
that the reader must understand; draw them when that adds information. Do not force every
relationship into a workflow, and do not force every paper to have a mechanism diagram.
Read the [writing playbook](../../lab-ultra-writing/references/writing-playbook.md) when planning
the figure with its mathematical explanation. Reconstruct from this task's model, not from an
exemplar's artwork. A layer fill may identify material; it is not a decorative card background.

- Mechanism: show entities, interfaces, directions, relevant quantities and assumptions.
  Geometry must agree with the model; label a schematic as not to scale if appropriate.
- Workflow: show what each step consumes, transforms or produces. Distinguish data
  flow, parameter sharing and validation feedback. Different populations need separate
  branches, not an invented sequential arrow.
- Decision: give conditions and outcomes, including uncertainty/refusal when part
  of the method. Do not draw a decisive outcome unsupported by evidence.

Leave hashes, receipt paths and internal audit states outside the paper figure unless
the paper studies that machinery. Keep scientific validation, expressed as the
scientific question it tests rather than an internal process label.

## Choose a capable medium

FigureSpec fits nodes and edges. Native TikZ suits mathematical labels and controlled
geometry. Native SVG supports editable paths, labels and composition. Inkscape or an
already licensed editor may refine composition when useful. Prefer actual scripts,
API or CLI over requiring GUI clicks; do not install all optional tools.
For recognizable 3D physical objects, apparatus and spatial scenes, use
[physical-scenes.md](physical-scenes.md); a node/edge renderer is not that route.
For an illustrative mechanism whose bodies or interfaces benefit from image-model
refinement, use [image-assisted-figures.md](image-assisted-figures.md). Keep ordinary
workflows and exact mathematical constructions native unless there is an actual
explanatory gain; a complex subject alone does not require a generated bitmap.

For TikZ, verify a TeX engine and `tikz.sty`, compile with shell escape disabled unless
separately needed and authorized, and keep `.tex` plus PDF. An SVG conversion may
outline glyphs; do not call that text-editable. For SVG, retain text and record fonts;
inspect converted PDFs for glyphs. Software availability is not quality evidence.

## Paper visual family

Start with white backgrounds, neutral text, restrained strokes, consistent spacing
and meaningful alignment. For this owner, do not default to colored rounded cards,
large tinted containers, gradients, shadows or one color per step.

Color may encode population, experimental condition, ray identity or an evidenced
status. Add non-color cues where needed. A material layer or an exclusion band is
not a decorative card. Keep text predominantly neutral and readable.
Restrained shading that reveals a physical body's shape is also legitimate; the
card-style warning is not a ban on scientific depth cues or material rendering.

Do not replace the old family with a mandatory black-and-white box template. A
borderless annotated mechanism may be better. Explicit user choices and scientific
conventions take precedence over the starting style.

These defaults apply to custom plotting code too. Importing a publication-style
helper does not make a diagram compliant: inspect explicit `FancyBboxPatch`/TikZ
rounding, fill arrays, per-step color cycles and inherited fonts. Do not choose the
`science` serif profile simply because the output is called a scientific figure.
For a paper workflow, use neutral lines and white/unfilled ordinary states, with
short object/operation labels; keep long equations and repeated result tables in the
text unless their relationship is the diagram's purpose. Color must earn its role.

## Diagram typography is independent of manuscript headings

Use [figure-typography.md](figure-typography.md) for the executable font resolver,
mixed-script hierarchy and collection-face checks. A family name or style name is
not a receipt for the actual exported face.

Use a verified regular-weight sans-serif for Chinese diagram labels by default,
with compatible Latin/math glyphs. Do not inherit Songti, small-title Song, decorative
display faces or synthetic bold from the paper heading style. Explicit user font
requirements still take precedence. Keep symbol meaning and math style consistent;
do not turn every label into a bold heading.

Verify the actual face used, not just the requested family. Font collections and
fallbacks can resolve a normal `Songti SC` request to a Black face. Where available,
inspect a rendered PDF's embedded font names and the final-size appearance; for an
SVG, inspect the rendered glyphs with the intended converter. A `sans-serif` keyword
or `fontweight='normal'` alone does not establish Chinese glyph coverage or weight.
Use a locally installed regular face (for example PingFang/Heiti or a suitable Noto/
Source Han Sans face after checking availability), then retain the font identity in
provenance. If a chosen face exports incorrectly, change or correctly resolve that
face; do not silently accept black/heavy, missing or substituted glyphs.

Avoid shrinking dense labels to force a fit. Simplify duplication, widen or reflow
the layout and review at the final embedded size. Keep meaningful group structure,
not large tinted nested panels. This is the owner's starting family, not a claim
that all color, rounded terminators or serif text is universally unscientific.

## Review in context

1. Verify arrows/geometry against the source/model: independent branches, conditions,
   missing feedback and shared parameters.
2. Read every label at final width; reflow or simplify before shrinking.
3. Inspect exports for label/line overlap, clipping and glyph loss, then check the
   figure beside its caption and referring paragraph in the paper.
4. Lock scientific content for controlled style comparisons. A mechanism redesign
   changing content is not a palette-only A/B experiment.

Deliver native source, exports and version-bound review. Automatic schema/geometry
checks remain separate from semantic and aesthetic review.

Basis, checked 2026-09-05: [Nature figure guidance](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/)
supports legibility, editable artwork and avoiding unnecessary decoration. Exact
English-journal fonts and dimensions are not a Chinese CUMCM specification.

## Located explanatory references

For an unclear geometric construction, reference-frame/force diagram, measurement
formation, or definition-disambiguation task, consult the writing module's
[conditional exposition library](../../lab-ultra-writing/references/exposition-library.md).
Retrieve by the relationship to explain, not the contest letter or an algorithm name.
Transfer the explanatory role and notation mapping; rebuild geometry from this task.
The source papers are not a visual template pack and their formulas are not certified.
