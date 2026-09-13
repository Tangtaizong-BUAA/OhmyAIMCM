---
name: OhmyAIMCM-review
description: OhmyAIMCM CUMCM paper suite. Audit CUMCM mathematical arguments, execution evidence, paper consistency and delivery readiness. Use for read-only review or pre-release checks; distinguish file/format checks from numerical, scientific, visual and team review.
---

This is the isolated `OhmyAIMCM` edition. Use only the sibling `OhmyAIMCM-*`
modules linked here; do not substitute stable or vendor skills.

# OhmyAIMCM-review

Inspect the designated current artifacts. Audit is read-only unless the user
separately requests repair. Report findings, affected evidence and next actions;
do not edit a candidate and pretend the same inspection still covers it.

Choose review depth from the claim and risk, not a universal score or checklist quota.
Check each required answer is substantive; formulas, sources, units, code, results,
figures and conclusions agree; and limitations survive compression into the abstract.
Identify absent links as well as visible errors. Do not demand statistical tests
for a proof or treat a successful solver exit as an optimality certificate.

Judge method suitability from assumptions, objective, constraints and evidence, not
agreement with a preferred algorithm list. An unlisted or simple method is not a
defect; a listed or complex one is not automatically adequate. Require additional
comparisons only when they can affect a consequential claim, not to satisfy a quota.

For paper review, select [paper conventions](../OhmyAIMCM-writing/references/paper-conventions.md)
when notation/references are in scope. For comprehensive content-expression or pre-release review, use
[expression review](../OhmyAIMCM-writing/references/expression-review.md): inspect meaning,
inference, hierarchy, mathematical explanation, notation, evidence presentation,
compression/attribution and precision in the requested scope. Give located findings
and evidence; do not treat a checklist or a flattering score as the review itself.
Check symbol meaning/scope/units, first definitions, formula-to-code correspondence,
figure ID/number/subpanel/caption bindings and the inference after each key result.
For a complete supported Markdown candidate, run `../OhmyAIMCM-writing/scripts/paper_preflight.py check`
or inspect a report bound to identical content, assets, options and checker version;
inspect findings and unchecked dimensions. Do not create a format conversion merely
to lint a local edit or another input format. State inapplicable/unavailable checks;
automated lint is not a scientific review.

For a local review, return the located finding and consequence at that scope; do not
produce a whole-paper audit matrix or require irrelevant runtime records. The writer's
ordinary self-edit does not automatically invoke this module. In an authorized repair
loop, return defects to their owner and review the changed version; do not silently
take over modeling, writing or typesetting.

When acting as a delegated reviewer, follow the
[native handoff contract](../OhmyAIMCM/references/handoffs.md). Identify the exact candidate
and evidence inspected, return located defects with consequence and required check,
and leave integration to the main agent/editor. Review repaired versions and affected
downstream uses before closing findings. A finding on an older candidate does not
approve a replacement. State whether this was independent review or author self-review;
loading this skill or running its checks does not create an independent reviewer.

For computations, verify the actual run binding with
[run_record.py](../OhmyAIMCM-compute/scripts/run_record.py). Then inspect mathematical
and numerical evidence separately. Receipt validity means only declared files and
process records agree; a valid receipt can accompany a wrong model.

For figures require data/encoding review and actual final-size visual inspection.
SVG structure checks cannot establish legibility. Existing visual workers retain
known limitations; if a required backend or gate is unavailable, report that scope.
For rendered papers use the typesetter's content and layout checks on the exact files.

For a polished full-paper delivery, inspect every final page and the actual table and
figure joins. A short comparison table split after a lone data row, an unidentified
continuation or unreadable main-figure labels is a repair finding even when content
is preserved and the compile log is clean. Return it to the responsible owner and
inspect the replacement. An explicitly provisional preview may retain located open
defects; do not relabel it as finished. Preview generation and a mechanical `pass`
are not evidence that anyone performed this visual review.

For comprehensive audits and release acceptance, state outcomes by dimension: execution binding, mathematical/numerical,
claims/citations, content expression, visual/layout and contest compliance. Use passed, failed,
not-checked or not-applicable with reasons. Never merge unknowns into a universal PASS.
Unperformed analyses stay missing even if an editorial revision reads persuasively.

Before actual contest release, recheck current official rules, anonymity, support
files and truthful AI-use declaration/details. The team must lead and verify core
AI-assisted analysis; do not invent a human reviewer, acceptance or an unused-AI state.
Known assistance conflicts with an unused-AI declaration. Missing usage records
remain missing; never fill them with a convenient `not_used` default.
No external submission without explicit authorization.

Return prioritized defects and the exact inspected versions. Content changes
invalidate affected reviews. This audit cannot guarantee an award or perfect figures.
