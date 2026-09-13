# Figure request and intermediate representation

Create these JSON objects before rendering non-trivial figures.

## FigureRequest

Required fields:

```json
{
  "schema_version": "1.0.0",
  "figure_id": "stable-id",
  "claim": "One precise statement the figure must support",
  "audience": "CUMCM judges",
  "medium": "A4 paper",
  "final_width_mm": 150,
  "language": "zh-CN",
  "data_sources": [{"path": "data.csv", "sha256": "..."}],
  "variables": [{"name": "error", "unit": "%", "role": "outcome"}],
  "uncertainty": {"kind": "bootstrap_ci", "level": 0.95},
  "editable_format": "svg",
  "claim_locked": true
}
```

Use `null` for unavailable facts. Do not invent a unit, uncertainty definition, sample size, or source hash.

## DataProfile

Record row count, column types, missingness, finite ranges, grouping cardinality, repeated-measure structure, outliers, transforms, and whether observations are paired. Chart selection must follow this profile.
For physical scenes without observations, describe geometry sources, named bodies,
units, coordinates, assumptions and unknown dimensions instead. Do not fabricate
rows, samples or uncertainty to satisfy a statistical profile; a source/model brief
can be the hashed input. See [physical-scenes.md](physical-scenes.md).

## FigureIR

```json
{
  "schema_version": "1.0.0",
  "figure_id": "stable-id",
  "claim": "same locked claim",
  "route": "quantitative_code",
  "recipe": "line_with_interval",
  "panels": [{"panel_id": "a", "purpose": "primary evidence"}],
  "encodings": [{"field": "time", "channel": "x", "scale": "linear"}],
  "annotations": [{"target": "event-1", "text": "policy change"}],
  "style_tokens": {"palette": "okabe-ito", "base_font_pt": 8.5},
  "exports": ["svg", "pdf", "png"],
  "invariants": ["data", "units", "claim", "transform", "uncertainty"],
  "provenance": {"renderer": "matplotlib", "seed": 20260812}
}
```

Every data-bearing layer must map to a named field or a documented derived field. Every free-form annotation must identify its evidence target.

When using the material library, add the selected library IDs/locked commits and the publication_style receipt to provenance. Keep one style family and composition owner across panels. Additional supported editable source formats are r, matlab, javascript and json (for declarative chart specs); include the requested source format in exports as well as any rendered deliverables.

## Conditional image-assistance record

Only for the [image-assisted route](image-assisted-figures.md), use
`hybrid_with_deterministic_overlay` and add `provenance.image_assistance`. This is
not an extra form for ordinary plots or native scenes. Plan the invariants first;
populate actual hashes and review observations after the corresponding files exist.

| Field | Meaning |
|---|---|
| `tool` | Actually invoked host tool or authorized API route |
| `requested_model` | Requested ID; for this owner's refinement route initially `gpt-image-2.5-sunburst` |
| `observed_model` | Actual ID supported by invocation/response evidence, or `null`; never infer it from the prompt |
| `assets` | Named `{ "path": "relative/to/case", "sha256": "actual 64-hex digest" }` entries |
| `review` | Observations bound to the exact artifacts and final width, as below |

Required asset roles are `source` (native draft source), `draft` (viewed render),
`prompt` (full edit brief), `generated` (selected image-model output), `overlay`
(editable annotation/composition source) and `final` (reviewed composed export).
Add dependencies, style references, or a redacted `model_receipt` under additional
asset names when used. Paths are relative to the supplied case root and must resolve
inside it. Required roles may refer to the same file when genuinely appropriate.
Every data-bearing `encodings` entry must declare `source_layer: "deterministic"`;
qualitative surface shading is not a fabricated field encoding.

`review` contains `status: "pass"`, a nonempty `reviewer` identity/role (self-review
is labeled as such), `final_width_mm` matching the request, and `asset_sha256`
mapping **every** asset name to the hash actually reviewed. Its `observations`
contains nonempty notes for `scientific_invariants`, `overlay_alignment`,
`final_size` and `raster_limits`. Record specific inspected relationships, remaining
limits and the actual size, not a claim that a schema checked physics. Do not record
a pass until this review occurred. Re-review affected checks after changes and bind
them to the new artifact set; updating a hash alone is not a review.

`scripts/audit_image_assistance.py request.json ir.json --root /absolute/case`
checks this conditional record, file hashes and review freshness, alongside the
base FigureRequest/FigureIR contract. Optional `--require-model EXACT_ID` additionally
requires a matching recorded `observed_model` and an intact `model_receipt` asset.
This is metadata consistency, not independent backend attestation: inspect the
receipt itself before claiming a confirmed model. Without that evidence, retain an
unknown model even when the artifact checks pass.
