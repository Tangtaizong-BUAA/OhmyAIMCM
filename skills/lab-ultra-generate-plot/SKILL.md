---
name: lab-ultra-generate-plot
description: Experimental CUMCM lab suite. Generate a statistical plot through PaperBanana when its MCP or CLI runtime is explicitly available. Use only after verifying the backend, data privacy, and costs; prefer deterministic scientific plotting for data-bearing figures.
allowed-tools:
  - mcp__paperbanana__generate_plot
  - Read
  - "Bash(paperbanana *)"
metadata:
  upstream-user-invocable: "true"
---

This is the isolated `lab-ultra` edition. Use only the sibling `lab-ultra-*`
modules linked here; do not substitute stable or vendor skills.

# Generate Plot

Generate a publication-quality statistical plot from a data file using PaperBanana.

## Instructions

0. Verify actual MCP/CLI availability before invoking this optional backend. Reuse existing authorization for its provider and input data. Use the shared material library when unavailable. Require the generated plotting code and data mappings for a final quantitative figure; a bitmap alone cannot establish reproducibility.
1. Read the data file at `$ARGUMENTS[0]`.
2. Prepare the data for the MCP tool:
   - If the file is **CSV**: parse it and convert to a column-keyed dictionary (keys = column names, values = arrays of column values), then serialize with `json.dumps()` to produce a JSON string.
   - If the file is **JSON**: use the raw file content as-is (it is already a JSON string).
3. Use the supplied plot intent or the existing task context; ask only for unresolved data meaning.
4. Call the MCP tool `generate_plot` with:
   - `data_json`: the JSON string (not a parsed object)
   - `intent`: the plot description
   - `iterations`: bounded by the selected experiment and provider budget
5. Verify the source data, transformations and uncertainty, then deliver with the shared style/export contract. Do not treat backend scores as scientific validation.

## CLI Fallback

If the MCP tool is not available, fall back to the CLI:

```bash
paperbanana plot --data <file> --intent "<intent>"
```

## Example

```
/lab-ultra-generate-plot results.csv "Bar chart comparing model accuracy"
```
