# Executed-result records

Run from a case directory outside all Skill/source-snapshot directories. Explicitly
declare code, data/config inputs and expected result files, using case-relative paths.
All paths must be distinct, local regular files; expected outputs must not already exist.
Use a new output path for each run. Never run unknown attachment scripts automatically.

Example command shape (replace filenames with actual case files):

```bash
python scripts/run_record.py record --case CASE --run-id pilot-01 \
  --code solve.py --input input.csv --output results/pilot-01.json \
  --data-kind synthetic --timeout 30 -- python -B solve.py
python scripts/run_record.py verify --case CASE --run-id pilot-01
```

`synthetic` is mandatory for invented test fixtures. `user-provided` and
`official` describe inspected source provenance, not a way to upgrade evidence.
No-input calculations require `--no-input-reason`; constants must still be justified
in the code or accompanying model evidence. Empty output lists are not executed
result evidence; proofs and audits use their own evidence types instead.

The record contains command, timing, Python/platform, return status and hashes of
declared inputs/code, actual outputs and captured logs. Declare configuration,
local helper modules and other scientifically relevant dependencies as inputs/code.
It is not an automatic detector of undeclared dependencies or a locked environment.

Verification rejects changed inputs/code/results/logs, missing/empty results,
failed or timed-out processes and malformed/self-declared legacy PASS manifests.
Output schemas, equations, solver diagnostics and claimed conclusions need
separate problem-specific tests and review. The runner neither executes through
a shell nor serves as a security sandbox; it can run only already-authorized code.
