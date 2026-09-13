---
name: OhmyAIMCM-generate-diagram
description: OhmyAIMCM CUMCM paper suite. Generate a publication methodology diagram through PaperBanana when its MCP or CLI runtime is explicitly available. Use only after verifying the optional PaperBanana backend and costs; otherwise use the deterministic OhmyAIMCM-figure-spec or OhmyAIMCM-draw-io route.
allowed-tools:
  - mcp__paperbanana__generate_diagram
  - Read
  - "Bash(paperbanana *)"
metadata:
  upstream-user-invocable: "true"
---

This is the isolated `OhmyAIMCM` edition. Use only the sibling `OhmyAIMCM-*`
modules linked here; do not substitute stable or vendor skills.

# OhmyAIMCM-generate-diagram

Generate a publication-quality methodology diagram from a text file using PaperBanana.

## Instructions

0. Select this route only for an explicitly chosen PaperBanana experiment. Verify that the named MCP tool is actually callable or that the CLI is installed; reuse existing authorization for the provider and inputs. If unavailable, use OhmyAIMCM-figure-spec/OhmyAIMCM-draw-io. A generated bitmap may be a concept draft, but scientific nodes, edges and labels require verified editable source for final delivery.
1. Read the file at `$ARGUMENTS[0]` to get the methodology text content.
2. Use the supplied caption or infer one from the provided methodology; ask only if the intended scientific relationship is unresolved.
3. Call the MCP tool `generate_diagram` with:
   - `source_context`: the text content read from the file
   - `caption`: the figure caption
   - `iterations`: bounded by the chosen experiment and provider budget, not a mandatory three attempts
4. Review the generated relationships against the source and deliver under the shared OhmyAIMCM-scientific-figure-maker contract, distinguishing drafts from editable final figures.

## CLI Fallback

If the MCP tool is not available, fall back to the CLI:

```bash
paperbanana generate --input <file> --caption "<caption>"
```

## Example

```
/OhmyAIMCM-generate-diagram method.txt "Overview of our encoder-decoder architecture"
```
