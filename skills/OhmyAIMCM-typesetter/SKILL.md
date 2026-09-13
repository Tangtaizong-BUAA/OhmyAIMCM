---
name: OhmyAIMCM-typesetter
description: OhmyAIMCM CUMCM paper suite. Deterministically typeset a completed Chinese CUMCM mathematical-modeling paper from Markdown into editable LaTeX and an audited PDF without changing its academic content. Use when a user asks to format, typeset, compile, audit, or deliver an already-written CUMCM paper; preserve existing equations, figures, tables, citations, headings, numbers, claims, and conclusions. Do not use this Skill to solve the modeling problem, select methods, calculate results, redesign figure/table content, or rewrite arguments.
---

This is the isolated `OhmyAIMCM` edition. Use only the sibling `OhmyAIMCM-*`
modules linked here; do not substitute stable or vendor skills.

# OhmyAIMCM-typesetter

Treat academic content as immutable. Syntax normalization, escaping, semantic environments, automatic numbering, and cross-references are allowed only when their meaning and relationships stay unchanged.

## Workflow

1. Confirm the input is completed Markdown. If content is incomplete or the user asks for modeling or substantive rewriting, keep that work outside this Skill.
2. Preserve actual AI-use facts supplied by the user and observed in the workflow. AI-assisted drafting cannot become `not_used` through a template default. Resolve genuinely missing declaration/support information before contest delivery; never fabricate it. When `used`, require a concise purpose/stage summary and a valid file named exactly `AI工具使用详情.pdf`. Research previews are not contest-ready papers and must not acquire a false unused-AI declaration to bypass this gate.
3. Analyze before rendering:

   By the owner's explicit choice on 2026-09-06, default to the journal-derived
   `journal-dense-cn-v1` projection. This is an owner-selected legacy style, not
   newly verified cross-journal consensus. The runtime selects it when no explicit
   config, style tokens or semantic policy are supplied. Read
   [references/aesthetic-policy.md](references/aesthetic-policy.md) before changing
   that projection or using a fallback.

   The owner's later table-title preference is centered captions. The runtime
   applies and records this narrow override to its default projection; it does not
   rewrite the old research artifact or change the rest of the selected layout.

   ```bash
   python scripts/analyze.py PAPER.md \
     --rules references/compliance-2026.json \
     --semantic-policy assets/models/semantic-layout-policy-v1.json
   ```

   Resolve every error. Do not suppress anonymity, missing abstract, raw-TeX, table-of-contents, or missing-asset failures.
4. Render into a new output directory:

   ```bash
   python scripts/render.py PAPER.md \
     --output-dir OUTPUT \
     --rules references/compliance-2026.json \
     --semantic-policy assets/models/semantic-layout-policy-v1.json \
     --ai-usage used \
     --ai-summary "实际使用阶段与用途" \
     --ai-support-pdf /absolute/path/AI工具使用详情.pdf
   ```

   The summary/path above must refer to real usage and a real support file. Use
   `not_used` only when established facts support it, never as a convenient default.
5. Verify the delivery independently:

   ```bash
   python scripts/verify.py OUTPUT
   ```

   Previews cover every PDF page by default. Inspect every page, including table
   continuations, caption attachment, footnotes, and the final pages. The optional
   `--no-previews` explicitly records missing preview coverage; old PNGs do not
   count as a review of the current PDF.

   `layout-audit.json` and the build summary retain `status: pass/fail` for machine
   compatibility, with `status_scope: mechanical_checks_only`. Read `review_scope`
   for the checks actually run, PDF pages measured, preview coverage and PDF hash.
   Generating PNGs is not visual review: the script records visual and semantic
   review as `not_performed`. Record actual visual inspection separately against
   the PDF hash and reviewed page numbers. Mechanical PASS does not establish
   visual quality, mathematical validity, or delivery readiness.

6. Return `paper.tex`, `paper.pdf`, copied source assets, `build-report.json`, `content-lock.json`, `layout-audit.json`, and previews. Mention any unresolved warning; never call a failed audit complete.

## Hard boundaries

- Do not add ad-hoc `\vspace`, per-paragraph styles, arbitrary font shrinking, or content rewrites to fit pages.
- Table pagination is a content-preserving hard-layout safeguard, independent of
  the aesthetic profile. The runtime measures an unstreamed `longtable` body,
  first header/caption, footer, natural spacing and saved footnotes before output;
  when the total fits one text page it reserves that space. Taller tables and
  already-streamed chunks keep native `longtable` pagination. It never converts
  all tables into unbreakable boxes or uses row count as a height estimate. A row
  taller than a page still requires an explicit source-level table redesign
  outside this immutable-content Skill; do not shrink or silently rewrite it.
- Keep the supported `longtable` hook fail-closed and run the real Pandoc/XeLaTeX
  table regression after changing it. Caption numbering, labels, repeated heads,
  footnotes and long-cell fallbacks must survive; log guard decisions in the audit.
- Do not place participant, school, or competition-region identity in the abstract, body, or appendix.
- Preserve every source figure byte-for-byte. An SVG-to-PDF compile derivative is allowed only alongside the retained original and its hash.
- Check figure typography inside the compiled PDF as well as manuscript fonts.
  Embedded plot text cannot be fixed by changing the paper's CJK main font. Return
  bad glyphs, mismatched faces or literal `c_i` labels to OhmyAIMCM-scientific-figure-maker;
  replace figures only through an authorized, source-preserving figure revision.
- Keep all style changes inside the validated runtime projection. Reject a policy whose schema,
  model admission, semantic scope, accepted human veto, content bindings, or Style Token bounds
  fail. Production promotion requires a compiler-produced v2 policy whose canonical payload,
  Style Tokens, quality targets, compiler identity, selected admitted factors, source research
  artifact, and human veto hashes agree exactly. Every runtime Style Token must have one provenance
  owner: an admitted learned factor, or an explicit CUMCM `hard_constraint` that does not claim to
  be learned. The bundled v1 policy remains loadable only as `legacy_unverified_v1` and is never
  automatically promotable.
  If the selected policy is missing, invalid or unsuitable, stop that render and report
  the reason. Offer `balanced-cn` as a fallback, but do not silently substitute it;
  obtain approval unless the user already authorized that fallback.
- The admitted corpus model conditions runtime controls on structural semantics only. The other
  fifteen semantic axes were evaluated but did not survive within-paper template control and
  repeated grouped validation; do not invent local paragraph-level adjustments from them. The
  evidence-aware v2.1 research model repeats the multi-axis test over the all-in 752-paper pool,
  but currently admits zero runtime factors and zero semantic effects. Its weak-pool hypotheses
  are research evidence only and must not be applied by this Skill.
- Treat whole-page comparisons that alter reflow or pagination as density evidence only. They cannot supervise heading,
  paragraph, formula, or caption preferences; use fixed-flow localized comparisons for those axes.
- Compilation, A4/margin/page/file-size compliance, anonymity, content locking, overflow, and required sections are hard checks outside aesthetic scoring.
- Do not read the research corpus or train a reward model at runtime.

## Failure behavior

Fail closed when required tools are missing, the Markdown AST cannot be preserved, PDF compilation fails, the content-lock threshold fails, AI disclosure inputs are incomplete, or critical layout diagnostics remain. Give the user the exact failing artifact and next corrective action.

For the current versioned rules and source links, read [references/compliance-2026.json](references/compliance-2026.json). Runtime rendering assets live under `assets/latex/`; keep generated outputs outside the Skill folder.
