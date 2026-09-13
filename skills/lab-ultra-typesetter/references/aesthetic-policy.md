# Aesthetic profile policy

## Owner profile

On 2026-09-06 the owner explicitly selected the previously accepted journal-derived
`journal-dense-cn-v1` as this suite's default. Use
`assets/models/semantic-layout-policy-v1.json` without requiring repeated confirmation.
The runtime selects it when no explicit config/style/policy is provided, and records
its identity and evidence status in the effective configuration. It remains reproducible and loadable,
but the evidence-aware v2 audit marks it `legacy_unverified_v1` and
`automatic_promotion_eligible=false`; it must not be represented as the current cross-journal
consensus. On 2026-09-04, the owner selected that projection over the historical
`system-atlas-dense` profile in a blinded whole-system veto. That preference record remains bound to
v1 and does not transfer to a later model.

Do not replace this owner-selected style merely because v2 consensus is not eligible for export.
Preference selection and scientific admission are separate. Retain all provenance, token-bound,
readability and hard-layout checks; a missing/invalid policy or failed check stops the render.
Report the cause and offer `balanced-cn`; use it only with explicit user selection or previously
authorized fallback. `hybrid-cn` also remains an explicit alternative. Never change profiles silently.

On 2026-09-09 the owner rejected left-aligned table titles in the 2025B and 2023A
deliveries. For the bundled default journal projection, center table captions over
the table/page center, including short captions and wrapped titles. The runtime
records this in `owner_style_overrides` as an explicit preference, not a learned
factor or a new blind-review result. Keep the original v1 artifact and its veto
unchanged. Explicit custom configs/styles and external policies retain their own
alignment choices. Check the compiled caption, not just `\centering` on the table
body; Pandoc longtable captions have their own justification.

## Evidence boundary

The legacy v1 policy combined three bounded inputs:

- 752 selected journal papers as the positive aesthetic standard, with one vote per paper;
- repeated paper-grouped validation of structure-role and page-composition models;
- the owner's final-veto acceptance of the restrained high-density projection inside those observed
  journal envelopes.

The two FRB whole-page review rounds are diagnostic only. The owner reported that information density
dominated most choices and that other changes were not reliably visible. Preserve those append-only click
logs, but do not train a reward model from them or infer fine-grained heading, paragraph, formula, caption,
or reviewer-position preferences. The final whole-system vote may admit or reject an already validated
projection, but it is not a new top-journal standard and remains explicitly ineligible for model training.

The legacy runtime core uses structural semantics only. Five independent grouped splits consistently
support role-conditioned size, leading, local-gap, and line-fill models plus page-composition models. After
within-paper template control, none of the other fifteen semantic axes supports an independent production
adjustment. This negative result is binding: runtime must not style individual claims or paragraphs from
those axes.

The projection uses journal quartiles only for transferable controls. Body leading is clipped to the CUMCM
readability floor; two-em first-line indentation, centered title/figure-caption discipline, section
numbering, A4 margins, and absolute body size remain governed by Chinese contest conventions. Annual rules
and hard readability checks always override the corpus projection.

## Future calibration

For the owner's award-led corpus calibration, read
[award-layout-calibration.md](award-layout-calibration.md). The offline shared-geometry
mixture gives the 64 award papers 0.60 total mass and the existing 752 journal identities
0.40, equal within each source. This is an explicit task preference, not a learned optimum
or runtime policy promotion. Conditional figure/text reading relations can guide manuscript
organization now; measured envelopes cannot silently replace font sizes or the selected policy.

The v2.1 research artifact contains all 752 papers as discovery members, but only 21 publisher-final
anchors. It finds no production-admissible common factor and no verified cross-journal semantic effect.
Do not ask for aesthetic preference on its weak hypotheses. First repair provenance and diversity,
rerun the evidence gate, compare surviving deviations with `balanced-cn`, and only then build a blind
whole-paper review matrix.

- Calibrate information density directly with a readability-bounded density ladder.
- For a local axis, keep page geometry, text flow, line breaks, and pagination fixed. Show matched enlarged
  crops or same-position blink overlays so the intended difference is the only useful cue.
- Ask for an aesthetic choice only after the reviewer confirms that the intended axis is perceptible.
- Store perceptibility, preference, and hard-compliance outcomes separately.
- Do not let runtime rendering read the research corpus or fit a reward model.
