# Image-assisted scientific illustrations

Use selectively for complex mechanisms, physical scenes, apparatus, layered bodies
or multiscale cutaways where recognizable form and careful rendering clarify the
model. The generated illustration may be a main paper panel. Do not confine this
capability to decoration, or run every diagram through it.

Prefer native code/vector for plots, exact constructions, graph connectivity,
dimensioned drawings and computed fields. A mixed figure can combine a qualitative
illustration with an unchanged quantitative panel. Never repaint evidence to make
it attractive. A synthetic scene is an explanatory reconstruction, not a photograph,
simulation result or observation.

## One chain, two kinds of control

`model/source → verified Blender/SVG draft → image edit → editable annotations → review`

The source owns scientific meaning; the draft establishes structure and composition;
the image model refines visual form; the final review checks that meaning survived.
Draft conditioning is guidance, not a geometric guarantee.

1. **Design the explanation.** Name the relationship the reader should understand
   and bind it to the model, nearby paragraph and notation. Identify bodies, counts,
   connections, contact surfaces, layer order, orientation and unknown dimensions.
   Choose an overview, section, exploded view or local inset for that relationship.
   Do not require Blender when a clean SVG section explains it better.
2. **Construct and inspect the draft.** Keep the native source and a rendered PNG
   at the intended aspect ratio. Verify topology and known geometry before editing.
   Separate stylistic choices from facts. Simplified proportions or exaggerated
   separation must be explicit. Leave room for labels; retain a draft without text
   where possible. Exact fields and measurement marks stay outside the edit layer.
3. **Refine through an actual image edit.** Read the host's imagegen instructions,
   inspect the draft image, then attach it as the structural reference. Identify any
   additional reference as style-only; it cannot supply new scientific objects or
   facts. Ask for one coherent scientific illustration, not a dashboard, slide or
   cinematic scene. Start with one candidate and targeted repairs; no automatic
   large best-of batch or paid fallback. Keep all consequential versions.
4. **Compose precise annotations.** Add symbols, arrows, dimensions, panel labels
   and legend keys through SVG/TikZ or another deterministic editable layer. Use the
   paper's notation and verified regular CJK fonts. Re-register anchors against the
   actual output: an old Blender camera projection may no longer land on the right
   generated surface. If exact geometry matters, retain the native rendering there
   instead of silently moving a dimension arrow to accommodate distorted geometry.
5. **Compare, repair and inspect in the paper.** Check the final image against both
   the original model/source and the draft. Reject extra/missing components, false
   connections, impossible contacts, reversed directions and invented fields. Then
   inspect the final crop beside its caption at the actual paper width: visual
   hierarchy, label legibility, muted but distinguishable materials, useful depth,
   occupied area and raster detail. Improve composition before adding more color.
   A repair or new crop invalidates affected checks. If refinement cannot preserve
   the science within budget, deliver the verified native figure and state the limit.

## Art direction that leaves room for judgment

Translate "top-journal/CUMCM style" into a readable explanatory plate: intentional
viewpoint, recognizable scientific objects, clear interfaces, restrained depth and
lighting, white/paper background, meaningful color and disciplined annotation.
Semi-realistic illustration, a clean section or a detailed isometric scene may each
be appropriate. Photorealism is not the objective. Preserve Pro's physical-scene and
diagram guidance; avoid giant rounded colored cards, decorative shadows, heavy Song
display labels, fake heat maps and gratuitous molecular/particle texture.

Adapt this compact edit brief rather than pasting a universal style incantation:

```text
Purpose: [the specific mechanism and the reader's question].
Reference 1 is the verified structural draft; [other references] are style-only.
Preserve: [named bodies/counts, topology, layer/contact order, directions, viewpoint].
May improve: [recognizable form, surface rendering, edge clarity, restrained lighting].
Must not add/change: [scientific exclusions, unknown structures, data/field patterns].
Composition: [overview/section/inset, final aspect ratio, reserved annotation space].
Appearance: a precise scientific illustration for a Chinese modeling paper;
white background, restrained material colors, depth that explains structure.
Do not generate text, equations, axes, scale bars, legend keys or quantitative marks;
these will be added in editable source. No presentation cards or decorative effects.
```

Use targeted feedback after seeing the output, restating scientific invariants in
each edit. Do not silently relax them to obtain a prettier candidate. Supplied text
that survives an edit still needs inspection; remove/replace stray generated text.

## OpenAI GPT Image 2.5: request is not execution evidence

The owner's requested model family is GPT Image 2.5. As verified on 2026-09-09,
OpenAI documents `gpt-image-2.5-sunburst` for precise editing and
`gpt-image-2.5-flare` for faster generation. Sunburst is the initial preference for
draft-conditioned refinement, not a permanent assumption about all future tools.
Consult current official model docs when selecting an API ID or snapshot.

Use the host's built-in image tool when available and appropriate. Inspect its real
schema: if it exposes references but no model selector or model receipt, record the
requested model and `observed_model: null`. Never relabel that result as a verified
2.5 run. If the task requires a confirmed exact model, report that capability gap
before generating with an unverified backend. An explicitly authorized API route
may select the documented ID; keep invocation/response evidence, with credentials
removed. Do not silently change provider, reuse unrelated credentials or add billing.
The suite packages instructions, not a hosted model or its authentication.

Sources: [Sunburst model](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst),
[Flare model](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare),
[image generation/editing guide](https://developers.openai.com/api/docs/guides/image-generation).

## Delivery and review binding

Reuse FigureIR's `hybrid_with_deterministic_overlay` route. Only for this route,
record `provenance.image_assistance` as described in [figure-ir.md](figure-ir.md).
Deliver the native draft (and its dependencies), viewed draft render, full edit
brief, reference assets, generated raster, editable overlay/composition and final
exports. Preserve actual tool/model evidence when available, not secret headers or
credential-bearing URLs. Keep provenance outside the paper's scientific prose.

The draft source and overlay are editable; the generated raster is not a recovered
mesh or fully editable vector. Retain its pixels and hashes, not a promise of an
identical stochastic rerun. SVG/PDF embedding does not create vector detail.
Compute effective resolution at the embedded size (pixels / inches); review the
actual detail and current target requirements. Upscaling alone is not new detail.

After visual review, run the optional route-specific artifact check:

```sh
python3 scripts/audit_image_assistance.py request.json ir.json --root /absolute/case
```

It checks file identity, review freshness, declared layer separation and recorded
model evidence, not physics, aesthetic quality, provider authenticity or whether a
reviewer truly looked. A passing result is not visual acceptance. Preserve truthful
AI-use information for the manuscript and contest disclosure. A journal's visual
style is not permission to submit generated imagery; check current rules for the
actual competition or venue when preparing a submission.
