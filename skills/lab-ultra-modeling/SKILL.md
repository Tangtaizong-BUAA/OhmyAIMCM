---
name: lab-ultra-modeling
description: Experimental CUMCM lab suite. Formulate and revise mathematical models for CUMCM tasks from actual problem conditions and evidence. Use for derivation, assumptions, route selection, interpretation of pilot results and validation design without a prescribed method catalogue.
---

This is the isolated `lab-ultra` edition. Use only the sibling `lab-ultra-*`
modules linked here; do not substitute stable or vendor skills.

# CUMCM Modeling

Choose a representation that answers the requested quantity, then explain why its
assumptions and available information can support that answer. Distinguish the
mathematical model from the algorithm or software used to solve it.

Candidate count, representation and exploration order are open. Derive a choice
from the requested answer, available information, dependence structure, constraints
and decision costs, not from a task-label-to-algorithm table. A simple analytic
solution needs no decorative advanced model; a difficult problem may justify
multiple hypotheses, mixed approaches or a new formulation.

Keep a broad, prescreened collection available without preloading its contents into
the modeling context. For a concrete knowledge or implementation gap, query
[lab-ultra-references](../lab-ultra-references/SKILL.md) or another authoritative source. Treat its
recommendations as conditional examples, not a default, whitelist or required
comparison set. A familiar listed method is still legitimate when it fits; choosing
an unlisted method is not itself innovation. Preserve explicit user-fixed methods.
Explain the consequential rationale, not a transcript of every alternative considered.

Make load-bearing variables, units, parameters and their sources, constraints and
boundary conditions explicit. Find the most informative way to challenge the model:
an analytic special case, feasibility check, identifiable parameter test, independent
prediction test or other problem-appropriate evidence. Read
[validation-questions.md](references/validation-questions.md) only for the relevant
claim type. These questions are not a compulsory experimental checklist.

Use [lab-ultra-compute](../lab-ultra-compute/SKILL.md) for authorized pilot computations
before global model convergence. Interpret failures and revise the hypothesis;
record material changes so old results cannot migrate into the revised argument.
Do not silently change a model the user explicitly asked to preserve.

Return the formulation, its rationale, uncertainties and the next informative
check at the granularity the task needs. Unknown results remain unknown. In active
contests, proposals and AI-assisted analyses remain subject to team leadership and
human verification; a model's confidence is not approval or validation.
