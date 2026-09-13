# Lightweight handoffs

Carry the task ID, purpose, input artifacts and versions, user-fixed constraints,
requested output and the checks that matter. Use a short record or existing case
notes; do not require a new file or a fixed paragraph template for every operation.

## Native collaboration, only where it helps

Use the host's actual spawn, message and wait tools as exposed in the current
session; a role heading or loading a child skill is not a worker execution. Do not
install a scheduler, route to paid models or assume a fixed team size. The main agent
keeps the overall argument and decisions coherent while a worker performs a bounded
task. Delegate only when another useful task can proceed independently, or when an
independent review is needed. Dependent work waits for its real inputs, not a guessed
result. Local polishing and small self-contained checks stay local.

Before dispatch, supply the relevant child entry, purpose and acceptance scope,
exact input paths/versions, authoritative evidence and material contrary evidence,
shared notation, output location and write boundaries. A section writer also needs
its role in the argument and adjacent context. Explain fixed scientific constraints,
not a predetermined model choice or wording. Workers read the relevant skill and
original evidence; a coordinator's summary is not a substitute for either.

Give each mutable output one writer at a time. Workers use isolated output paths or
return located proposals; the main agent or designated editor integrates shared
manuscript changes. A reviewer is read-only. Do not let workers overwrite each other's
sections, shared notation, evidence snapshots or final delivery files. Workers flag
missing inputs or scope conflicts instead of silently expanding the assignment.

Return actual artifacts/findings, inspected input versions, checks performed,
unchecked dimensions and consequential uncertainty. Keep a short trace in existing
case notes: task, actual worker identity, input/output versions, status and next owner.
Use meaningful states such as assigned, returned, needs-repair and reviewed; a tool
launch is not completion. Show the user material dispatches, findings and repairs,
without requiring a separate dashboard or logging every exchange.

The main agent inspects returned work against its sources and reads the integrated
argument, including transitions and compressed conclusions. Resolve conflicting
claims by checking evidence, assumptions and scope, not by majority vote or worker
confidence. Escalate only missing authority or choices beyond the user's scope.

For independent final review, use a reviewer who did not produce the candidate,
preferably with fresh context containing the request, candidate and necessary raw
evidence rather than the author's self-assessment. Independence does not establish
correctness or replace human contest review. Route each actionable defect to its
owner; after repair, send the changed version and affected evidence to review again.
Recheck downstream body text, figures/captions, abstract and final-size layout when
affected, not just the originally defective sentence. Unaffected findings can be
retained with their version bounds. Stop when the requested scope is checked or
report the specific unresolved limit; no ceremonial rounds or universal PASS.

## Domain handoffs

- Intake → modeling: exact requested quantities, data semantics, conditions and
  material ambiguities. Methods are not predetermined by topic labels.
- Modeling ↔ compute: mathematical expression, parameters and sources, proposed
  experiment, distinguishing checks, budget and provisional assumptions. Free-form
  math is allowed. An informative probe need not wait for a globally locked model.
- Compute → writing: actual outputs, units, run receipt, numerical diagnostics,
  uncertainty meaning and limitations. Theory/proofs and supplied external facts
  use their own sources instead of fabricated run IDs.
- Writing → figures (actual rendering only): stable figure ID, question or supported claim, exact source
  data, meaning, units and target size; use the existing FigureRequest/FigureIR.
  A figure may contradict a provisional claim. Revise the claim, not the evidence.
  Carry the reviewed target size; if final embedded size/layout changes readability,
  the affected visual review becomes stale and returns to the figure worker. Byte
  preservation by the typesetter alone cannot preserve a final-size visual verdict.
  A writing-only figure idea stays with the writer as a short prose brief; it does not
  invoke this rendering handoff or require a FigureIR.
- Writing → typesetting: completed text, equations, figures, captions, semantic
  tables and citations. The typesetter preserves content rather than repairing it.
- Review → coordinator: findings, inspected versions, what was not checked and
  required next actions. The producer cannot convert an unreviewed item to a PASS.

For consequential cross-artifact changes, use the shared
[evidence relationships](evidence-relationships.md), not a second run-manifest or
figure schema. Preserve a scoped claim, its assumptions, positive and adverse evidence,
and the current manuscript/figure uses. The map tracks versions; review judges support.

One authority per concern: compute owns numeric outputs; writing owns interpretation
and captions; the figure worker owns graphical encoding and styles; the typesetter
owns page composition. Table identifiers remain strings; only measurement columns
receive declared display precision. Missingness and significant digits retain meaning.

Writing remains the manuscript editor across specialist visits. A delegated section
receives its role, adjacent context, shared notation and current evidence; it should
not restart the paper with its own introduction or glossary. Return scoped changes,
then read the integrated manuscript for contradictions and broken transitions.
Reuse mechanical findings only when content, assets, options and checker version are
unchanged. Independent scientific review is not replaced by reusing a linter result.

For the E1 prototype, run records bind declared inputs, code, outputs and logs.
Scientific review remains separate. Copies of legacy visual workers retain known
limitations: final-size review is mandatory, and absent optional dependencies or
unadmitted layout policies must be reported rather than silently considered ready.
