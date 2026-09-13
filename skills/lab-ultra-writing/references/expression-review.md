# Evidence-based expression review

Use for comprehensive content-expression audit or a completed paper's content review.
For a local edit, select only affected dimensions and state that scope. This is an
editorial/semantic inspection, not an automated top-journal score or a peer-review substitute.
Review stays read-only unless revision is authorized.

Identify who actually reviewed: author self-review, another model/agent, or a named
human only when that person really reviewed. Distinguish model semantic inspection
from script checks; neither may be described as human review or human acceptance.

Read the actual candidate and necessary evidence. Bind file-backed review to a content
hash, immutable version or immutable snapshot identifier; a mutable path only locates
the file and is not version evidence. Identify inspected source versions as well.
For a local excerpt, record its parent version and span; for inline text, identify the
exact message/excerpt reviewed. A source locator is not proof of support: inspect the relevant material.
If evidence is unavailable, report what can and cannot be checked from the manuscript.

Use two complementary views, not two redundant checklists. From the source evidence,
ask what claims and scope it supports; from the assembled manuscript, ask what a
reader would actually infer. Inspect seams between sections and between body,
captions, abstract and conclusion. A fact reviewed in isolation can be misstated,
mis-scoped or combined incorrectly in prose. Include omitted consequential negative
evidence, not only the evidence the writer chose to foreground.

When a source diagnostic reports several consequential outputs, compare their scope
with the manuscript's limitation and compressed summaries. Reporting one sensitive
metric must not hide another affected answer. Distinguish verification of a fixed
candidate from validation of the selection procedure: recalculating a chosen route
or fit does not itself establish optimality, uniqueness or search completeness.

Before accepting “only X changed,” inspect the effective comparison settings, not
just their names: output/snapshot scheduling, stopping rules or saved-state handling
can alter numerical execution too. If conditions differ, preserve the observation
but qualify the isolated-effect claim in the body, abstract and conclusion together.

For important final candidates, prefer a fresh review context when authorized and
available. Give it the actual paper, task and necessary sources, not the writer's
preferred verdict or self-praise. A separate agent is not automatically independent
in its errors; a second pass by the same author remains self-review. If independent
review is unavailable, record that limitation instead of inventing a reviewer.

| Dimension | Reader-level check | Useful evidence |
|---|---|---|
| Answer and meaning | Can the reader state what was learned for each requested question, beyond a list of methods? | Problem statement, section purposes, substantive answers |
| Inference and strength | Does the evidence justify this kind and scope of claim? Are adverse results and decisive alternatives handled? | Derivations, results, validation limits, relevant source passages |
| Hierarchy and progression | Are prerequisites available before use, dependencies real, and paragraph transitions warranted? | Actual section/paragraph order and cross-references |
| Mathematical explanation | Can a reader follow the important modeling choice and equation-to-conclusion step? | Definitions, assumptions, equations, implementation when in scope |
| Terms and notation | Do names, objects, indices, types, units and scales remain consistent? | First uses, symbol table, formulas, axes, code/data definitions |
| Evidence presentation | Do figures/tables/captions support the referenced inference without unnecessary duplication? | Actual panels/values, captions, data and uncertainty definitions |
| Compression and attribution | Do title, abstract and conclusion preserve the body's result and limits? Do citations support their attached claims? | Matched propositions and source evidence, not token counts |
| Precision and economy | Is language specific and readable, without empty praise, redundant explanation or forced rewriting? | Located sentences and a concrete reader misunderstanding |

Use `passed`, `failed`, `not-checked` or `not-applicable` by dimension with a reason
and reviewed scope. A pass means no defect found in that inspection, not proven
perfection. Do not aggregate into a journal ranking or let uninspected dimensions pass.
For example, caption semantics can be inspected in source while final-size legibility
remains not-checked. A mathematical proof may make statistical plots not-applicable.

For each material finding, give its location, the problematic claim/relationship,
the supporting evidence, its effect on interpretation and the smallest useful repair.
Prioritize scientific misrepresentation and broken reasoning over stylistic preferences.
An assertion such as “逻辑不够好” without a location or consequence is not an audit finding.
If the manuscript is already effective, say so rather than inventing defects.

For a paper dominated by implementation checks, ask what substantive comparison the
reader learns. Keep decisive numerical and physical limitations visible while moving
routine file/test accounting to its reproducibility role. Repeated disclaimers are
an editing opportunity only when their meaning and coverage survive the revision.

Separate proposed edits from performed analyses. A needed uncertainty estimate or
validation run goes back to the appropriate worker only if authorized; do not draft
its result. After revisions, recheck affected claims, notation and compressed summaries
on the new version. Keep the old review as history, not current acceptance.

For a case with recorded dependencies, consult
[evidence relationships](../../lab-ultra/references/evidence-relationships.md) to locate
affected results and review records. Recheck semantics even when numeric tokens are
unchanged: swapped objects, removed conditions and changed citation meanings matter.
If the declared dependency coverage is insufficient, broaden review rather than
assuming unaffected status. Source-level review does not replace final PDF inspection.

For a before/after comparison, use the same authoritative facts and requested scope,
retain all outputs, and allow ties or baseline wins. Prefer independent reviewers when
authorized and useful; give them the raw facts and anonymous texts without the builder's
desired outcome. A single model review is development evidence, not human validation.

`paper_preflight.py` intentionally leaves semantic dimensions unchecked. Its counts,
numeric-token preservation and reference parsing cannot close the findings above.
Attach real review evidence separately; never turn a self-reported review file into an
automatic semantic PASS. No new scoring engine or mandatory large claim database is needed.
