---
name: OhmyAIMCM-evaluate-diagram
description: OhmyAIMCM CUMCM paper suite. Evaluate a generated diagram against a human reference through PaperBanana when its MCP or CLI runtime is explicitly available. Use scores as review evidence only, never as scientific correctness or an automatic acceptance gate.
allowed-tools:
  - mcp__paperbanana__evaluate_diagram
  - Read
  - "Bash(paperbanana *)"
metadata:
  upstream-user-invocable: "true"
---

This is the isolated `OhmyAIMCM` edition. Use only the sibling `OhmyAIMCM-*`
modules linked here; do not substitute stable or vendor skills.

# OhmyAIMCM-evaluate-diagram

Evaluate a generated diagram against a human reference using PaperBanana's VLM-as-Judge scoring.

## Instructions

0. Verify actual MCP/CLI availability for this explicitly selected backend. If unavailable, use local structure/visual review. Reuse already supplied context and existing provider authorization.
1. `$ARGUMENTS[0]` is the path to the generated image.
2. `$ARGUMENTS[1]` is the path to the human reference image.
3. Resolve these from the supplied request or paper; ask only for missing scientific context:
   - **Source context**: the methodology text (or a file path to read it from). If the user provides a file path, read that file to get the text.
   - **Figure caption**: a description of what the diagram communicates.
4. Call the MCP tool `evaluate_diagram` with:
   - `generated_path`: the generated image path
   - `reference_path`: the reference image path
   - `context`: the methodology text content
   - `caption`: the figure caption
5. Present the evaluation scores as review evidence. Scores cover Faithfulness, Conciseness, Readability, and Aesthetics; they cannot replace source correspondence checks or decide scientific correctness.

## CLI Fallback

If the MCP tool is not available, fall back to the CLI:

```bash
paperbanana evaluate --generated <generated-img> --reference <reference-img> --context <context-file> --caption "<caption>"
```

## Example

```
/OhmyAIMCM-evaluate-diagram output.png reference.png
```
