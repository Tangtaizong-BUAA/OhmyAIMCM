---
name: OhmyAIMCM-compute
description: OhmyAIMCM CUMCM paper suite. Implement, execute and check CUMCM computations, including exploratory probes before a model is finalized. Use for data processing, numerical solving, simulations, validation and reproduction within the user's authorized scope and budget.
---

This is the isolated `OhmyAIMCM` edition. Use only the sibling `OhmyAIMCM-*`
modules linked here; do not substitute stable or vendor skills.

# OhmyAIMCM-compute

Implement the mathematical task, not a method-name template. Match project size
and language to the task and available tools. A small calculation need not become
a multi-command framework. Existing user code and raw inputs are not disposable.

Confirm inputs, units, parameters, computational goal and what would falsify the
result. For open exploration, label provisional assumptions and run the cheapest
informative probe. For a fixed-model request, preserve the supplied mathematics.
Inspect versions/APIs before introducing dependencies; do not install large packages
or change the model merely to bypass an unavailable solver.
Implementation examples supply API usage, not authority to replace the formulation.
If evidence challenges an exploratory model, return that evidence to modeling; a
fixed-model task instead reports the limitation without silently substituting a method.

Keep computation distinct from display. Save full-precision outputs and semantic
metadata before producing tables/plots. Identifier strings are not measurements.
Prevent leakage when relevant and record meaningful convergence, feasibility,
numerical error, seeds or uncertainty diagnostics rather than only exit status.

For a local executable result, read [run-evidence.md](references/run-evidence.md)
and use [run_record.py](scripts/run_record.py) or an equivalent verified runner.
This prototype records declared files and process execution; it does not certify
numerical or scientific correctness. Hand actual results, diagnostics and limits to
[OhmyAIMCM-writing](../OhmyAIMCM-writing/SKILL.md) and the figure worker.

Failures and incomplete probes are valid working artifacts, not final evidence.
Never return placeholder arrays or hand-entered metrics as computed results.
Pure theory does not require inventing a computational run.
