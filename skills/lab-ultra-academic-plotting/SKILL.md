---
name: lab-ultra-academic-plotting
description: Experimental CUMCM lab suite. Extract ML paper context into figure requirements, including method components, data flows, benchmark comparisons, ablations and training curves. Route the resulting specification through the shared scientific figure library for editable rendering.
license: MIT
metadata:
  upstream-author: Orchestra Research
  local-role: paper-context-extraction-and-shared-library-routing
---

This is the isolated `lab-ultra` edition. Use only the sibling `lab-ultra-*`
modules linked here; do not substitute stable or vendor skills.

# Academic Plotting for ML Papers

Translate a paper section or result table into a precise figure specification. Use the shared [Scientific Figure Maker](../lab-ultra-scientific-figure-maker/SKILL.md) for rendering and final validation.

## Extract the evidence

For methods, identify named components, groups, inputs/outputs and directed relationships. Distinguish data flow, control flow and feedback from layout decoration. Preserve every label's wording and note relationships that the paper does not establish.

For results, record metric units, evaluation split, model/configuration names, seeds or replicate counts, aggregation, interval definition, missing runs and comparison intent. Do not treat a label such as "Ours" as a command to visually favor it.

Select encodings by the comparison: ordered training steps suggest lines; close benchmark differences often suit dots or intervals; raw distributions need sample displays; matrices need justified normalization. Categories do not automatically imply grouped bars.

Use manuscript context to resolve ordinary omissions. Ask only for information that cannot be inferred and would change the scientific meaning.

## Routes

- Method architecture: [editable diagram guidance](references/diagram-generation.md), then lab-ultra-figure-spec or lab-ultra-draw-io.
- Experimental results: [data recipe selection](references/data-visualization.md), then a bundled starter or resolved upstream recipe.
- Sizing and fonts: [style guidance](references/style-guide.md), then one shared publication_style context.

An optional generated illustration may serve as a non-quantitative underlay. Keep boxes, arrows, scientific labels, equations and evidence-bearing geometry in editable source. No default provider or fixed number of paid generation attempts is required.

Deliver the source, data mapping and selected material provenance with the requested exports. Scientific correctness and final-size readability take precedence over aesthetic scoring.
