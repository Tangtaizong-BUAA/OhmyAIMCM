# Physical scenes: make the modeled world visible

Use for apparatus, physical environments, material structures and spatial mechanisms,
not 3D-styled statistical charts or extruded workflow boxes. During substantive paper
work, actively consider a scene when depth, occlusion, contact, orientation, layers,
motion or sensor placement is necessary to understand the model. Do not wait for the
user to request an extra illustration. A clearer section view can be sufficient;
3D is not a quota, and a physical topic alone does not justify a decorative scene.

## Start from the physical explanation

Identify the actual objects, interfaces, reference frame, relative placement and the
relationship the reader must inspect. Distinguish real apparatus from the idealized
model: a chamber, specimen and detector may need recognizable bodies, not anonymous
boxes. Link these objects to the variables/equations used nearby. Describe what this
view adds beyond a plot or sentence; do not turn the analysis steps into scene objects.

Use supplied drawings, dimensions, observations or model definitions as authority.
Unknown dimensions remain unknown. A conceptual reconstruction may use illustrative
proportions, explicitly labeled not to scale, but must preserve known topology,
orientation, contact and ordering. Separate measured geometry, assumed idealizations
and purely presentational choices. Never claim a schematic is to scale without
checking its geometry and projection against actual dimensions.

Choose a view that exposes the load-bearing relationship: oblique overview for
apparatus placement, cutaway for interiors, exploded view for assembly/layers, local
section for an interface, or matched views for motion. Use only the views needed.
Explain separation or thickness exaggeration; a perspective view is not a measuring
instrument. A simplified scene is not experimental observation or a validated field.

## Choose a genuine scene tool when needed

- Blender scripting is a useful route for recognizable solid objects, controlled
  cameras, cutaways and restrained surface shading. Verify the installed executable
  and version. Retain the Python scene generator and `.blend`, not only the render.
- Existing CAD geometry can be imported or rendered with an available CAD tool when
  exact surfaces matter. Check units and transforms; do not redraw supplied geometry
  by eye or require a commercial tool solely for prestige.
- PyVista/VTK suits supplied scientific meshes and computed fields. Field colors,
  streamlines and vectors must come from actual data, with their scale and units.
- Matplotlib 3D or native projected SVG/TikZ can suffice for simple analytic solids.
  They are not a reason to reduce a complex apparatus to a cube or add 3D chart axes.
  Choose by explanatory fidelity and available tools, not software name alone.

For a Blender figure, use an isolated background session and task-owned output paths;
do not reset an open user scene. A typical installed-runtime command is:

```sh
blender --background --factory-startup --python-exit-code 1 --python scene.py -- --output-dir /new/case/scene
```

Inspect local `--help`/API for that version and set a bounded render budget. A missing
renderer does not justify replacing the scene with a colorful workflow. Select an
adequate available route or identify the missing capability; no bulk installation.

## Let image models refine an evidence-grounded draft when useful

A verified Blender render or SVG section can be the structural draft for a richer
scientific illustration: recognizable bodies, material interfaces, cutaways and
multiscale mechanisms need not remain crude primitives. When that would explain the
model better, use [image-assisted-figures.md](image-assisted-figures.md). The image
model may refine the main illustration, not only a decorative background.

Keep exact surfaces or computed fields native wherever their geometry or magnitude
is evidence. Conditioning on a draft does not lock geometry: check contacts, counts,
layer order and hidden/visible surfaces again. Re-register annotation anchors after
refinement; the original camera projection need not match newly drawn contours.
Retain the native draft and generated layer separately. A `.blend` of the draft
does not make the refined raster a recoverable 3D scene.

## Scientific composition and typography

Begin with a white/paper background, neutral materials and modest lighting that
reveals shape. Use color for material, component or scientifically meaningful paths;
do not manufacture heat maps, force magnitudes, turbulence or optical intensity.
Avoid cinematic depth of field, bloom and reflections that hide the modeled relation.
Orthographic or restrained perspective often helps; verify occlusion rather than
assuming transparency makes hidden structure clear.

Keep labels, dimension annotations and relation arrows in an editable overlay when
possible. Project their anchor points from the same camera/geometry; arbitrary screen
positions can silently detach a label from its object. Use the shared diagram font
guidance, not beveled 3D text or the manuscript's heading font. Perspective angles
need not look equal in projection; don't alter correct geometry to make them look so.

Crop useful content before fitting to the paper width. A 160 mm image with a tiny
object inside a huge blank canvas is not a readable 160 mm figure. Keep a scene-only
render for composition plus the annotated version; never call a raster scene fully
vector-editable just because it is embedded in SVG or PDF.

For spatial networks, a centerline view is legitimate geometry evidence. Treat it as
an overview when that is its role; it does not by itself explain tunnel interiors,
interfaces or field evolution. Test the view against the adjacent 2D map: does depth
reveal an otherwise hidden relationship? Use a local inset or section when the full
network makes the decisive branch unreadable. Do not invent terrain to make it look
like a landscape. A known rectangular section can be shown with simple analytic
solids; software complexity is not an acceptance criterion.

Use the final paper crop to judge label separation and occupied area. A default 3D
axis cage, empty axis range or distant legend can consume most of the available
space. Keep coordinate axes when readers need coordinates; otherwise an orientation
triad or direct dimensions may communicate the frame more clearly. Where paths
coincide, make their shared segment and later split readable without changing either
path. Retain declared exaggeration and camera-projected annotation anchors.

## Reuse the existing figure contract

No second scene workflow or method database is required. For a non-data scene,
DataProfile describes geometry sources, units, named objects, assumptions and unknowns,
not fabricated sample counts. FigureRequest `data_sources` may bind the supplied
geometry/model brief; it need not be a CSV. Use `uncertainty: null` when inapplicable.
FigureIR can use `hybrid_with_deterministic_overlay`, `editable_format: python`, and
exports including `python`, `blend`, `svg` and requested raster/PDF outputs. Record
camera/projection, illustrative scale choices, renderer/version and source bindings
in its existing provenance. Pure vector geometry uses `editable_vector` instead.

Review both the physics and the page: object identity, coordinate handedness, units,
contacts, arrow direction, hidden surfaces, scaling claims, label attachment and final
size. Check the scene against its explanatory paragraph and caption, not just against
the generation prompt. Reinspect after camera, crop or geometry changes. Report the
scope of review; no schema check certifies physical correctness.

Tool references (consult the installed version):
[Blender command-line rendering](https://docs.blender.org/manual/zh-hans/5.0/advanced/command_line/render.html),
[Blender camera capabilities](https://www.blender.org/features/rendering/).
