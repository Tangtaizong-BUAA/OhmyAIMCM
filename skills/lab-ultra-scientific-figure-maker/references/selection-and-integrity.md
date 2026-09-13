# Selection and integrity gates

## Profile before choosing

- Continuous over ordered x: line or point-range; do not connect unordered categories.
- Two continuous variables: scatter; use density bins/contours when overplotting hides structure.
- Distribution: show raw observations when sample size permits; prefer box/violin/ECDF over mean-only bars.
- Ranking: dot or horizontal bar; preserve source order only when it has meaning.
- Matrix or field: perceptually ordered sequential/diverging palettes with a justified center.
- Time forecast: distinguish history from forecast and state interval semantics.
- Process or architecture: editable graph with explicit node/edge semantics.

## Hard failures

Do not send these to aesthetic ranking:

- fabricated, silently imputed, or selectively omitted values;
- an unsupported mean, interval, p-value, model fit, or causal claim;
- truncated axes that materially distort magnitude without explicit justification;
- logarithmic or normalized scales without visible labels;
- rainbow maps for ordered scientific magnitude;
- dual y-axes that invite false correspondence;
- hidden missing values, failed runs, exclusions, or changing denominators;
- area/volume marks encoding linear values without correct scaling;
- illegible labels, clipped marks, missing glyphs, or inconsistent units;
- using image-generated data marks, measured/computed fields, axes, scales, numbers,
  equations or legends as quantitative evidence; keep those in deterministic layers;
- invented or changed bodies, contacts, layer order or causal paths in a generated
  mechanism, or passing off a synthetic illustration as an observation.

Image-assisted qualitative mechanisms are admissible after comparison with their
model/source and review of final annotations; see [image-assisted-figures.md](image-assisted-figures.md).
An appealing image and a provenance check do not certify scientific correctness.

## Aesthetic degrees of freedom

Only after hard gates pass, optimize palette character, typography, whitespace, grid strength, mark weight, label density, legend placement, annotation style, panel composition, and narrative order. These can be learned as context-dependent preferences; they are not universal scientific truths.

## Comparison discipline

For A/B calibration, lock data, seed, dimensions, final viewing scale, labels, units, transforms, and claim. Change one declared parameter or one explicit tradeoff bundle. Randomize left/right placement and reserve repeated scenarios for reliability measurement.
