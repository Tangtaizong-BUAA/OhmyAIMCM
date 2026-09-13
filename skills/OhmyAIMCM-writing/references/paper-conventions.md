# Paper conventions and preflight

Read during substantial CUMCM drafting/revision or pre-delivery audit. Control
communication, not modeling methods. Reuse case notes instead of requiring a new
schema or large symbol database for every task.

## Notation with meaning

Record important symbols: mathematical form, meaning/scope, type/index/domain, unit,
and parameter value/source where relevant. A compact paper table can omit local
auxiliary quantities if they are defined beside first use.

- One meaning per symbol within its scope; distinguish quantities, observations
  and estimates. Avoid accidental reuse for vectors, phases, penalties or categories.
- Define index sets and their values, e.g. `j in {1,2}` with angles defined separately.
  Define transformed coordinates and the argument of each function.
- Scalar quantities are conventionally italic; units, named operators and descriptive
  subscripts upright. Pick a consistent vector/matrix convention. Use real math
  (`$Y_{ij}$`), not literal `Y_ij`; use `\operatorname` and `\mathrm` where appropriate.
- A parameter value is not a unit. Dimensionless `1` is valid; penalty `8` belongs
  in a value/source column with its cost scale defined separately.
- State conversions between quantities and numerical units. Do not silently switch
  cm/micrometres or proportions/percentage points. Preserve string identifiers and
  source precision; display measurement precision appropriate to uncertainty.
- Explain what a consequential equation computes, why it follows, which parameters
  are fixed/estimated and its limits. A glossary cannot replace these connections.

Treat notation as a semantic interface, not decoration. Where relevant, distinguish
the object measured, one observation, a latent/decision quantity, an estimator and
its realized estimate. In repeated or hierarchical data, define both the group and
within-group index; observation count is not automatically independent sample size.
For vectors, matrices and maps, give the dimensions/domain/codomain needed to check
the operations. Do not infer missing definitions from the letter's usual meaning.

For consequential equations, inspect free and bound indices, summation limits,
dimensions and admissible values. State whether a formula operates on physical
quantities or numerical values in specified units. A scalar logarithm/exponential
argument needs dimensionless meaning, e.g. $\log(T/T_0)$, or an explicit convention
that it denotes a numerical value in a specified unit. A weighted sum may retain
units: its terms must be compatible, with weights carrying units where needed.
Do not require every objective to be normalized.
Check that nearby prose, a symbol table, figure axes and implementation refer to the
same object; consistent typography alone cannot establish this.

Expose arguments that change a consequential quantity: a direction-dependent speed
needs a stated direction argument or a clearly fixed directed-edge scope. Define the
time-step index, active-source total and neighborhood relation at first use when the
update depends on them. Distinguish an event aggregated over individual objects from
an event requiring all objects to satisfy a condition simultaneously; similar labels
do not make their bounds interchangeable.

Within substantive revision, an unambiguous notation alias can be normalized if its
definitions and dependent uses are updated throughout the affected scope and the
mapping is recorded. Preserve user-protected formulas in fidelity-only editing.
An ambiguous collision, missing scale or inconsistent model definition is a finding
to resolve, not permission to guess an intended equation. Do not create a symbol for
a quantity that is clearer in ordinary language or list every temporary index in a table.

Introduce a consequential formula at the point where the reader understands what
problem it solves; unpack the terms that make this model different, then use the
formula to draw the next inference. This need not be a fixed before/after paragraph
pair. Keep indispensable reasoning in the main text; routine derivations may move to
an appendix when the task permits. CUMCM exposition must remain independently intelligible.

Give equations that are reused, compared or needed to audit the method stable labels
and references supported by the authoring format. Numbering every local calculation
is unnecessary, but a long derivation should not force the reader to hunt for an
unnamed formula. Use explicit figure/table references where the prose draws a key
inference; phrases such as “the 3D scene” become ambiguous after insertion or reflow.

General convention basis: [NIST](https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-10-more-printing-and-using-symbols-and-numbers),
checked 2026-09-05. This does not prescribe a universal choice of letters.

## Stable figure references

Use ordinary Pandoc Markdown IDs and links while authoring:

```markdown
两组拟合见[图](#fig-fit)，残差见[图 b](#fig-fit)。

![联合拟合与残差：点表示观测，线表示模型。](figures/fit.svg){#fig-fit panels="a,b"}
```

Captioned figures need stable `fig-...` IDs. Optional `panels` lists actual subpanels.
Do not hand-number captions or link labels. Captions explain the figure's meaning,
conditions/units and uncertainty semantics, not just the chart type.

From this Skill directory, with an installed Pandoc:

```bash
python3 -B scripts/paper_preflight.py check /path/paper.md --ai-usage used
python3 -B scripts/paper_preflight.py prepare /path/paper.md --output /new/path/resolved.md --phase release --ai-usage used
```

`check` is read-only. `prepare` writes a new file, resolves these links into current
figure order and rebases local image paths. It never overwrites source files or
selects a model. It rejects round trips that alter Math payloads or tracked visible
numeric tokens, and preserves Unicode punctuation in the Markdown writer. These
checks are not a complete semantic-equivalence proof. The report records source/output
hashes and the figure map. Re-run after figure insertion/reordering. Review the derivative before passing
that exact file to the typesetter for content lock. Then inspect the final PDF: its
numbering/order must still match. Use the actual typesetter's supported mechanism
for equation/table references; this helper does not implement every reference form.

Reports from `paper-preflight/0.2` bind the parsed source bytes, direct local image
paths/bytes, checking options, checker code, Python and Pandoc versions, and parsed AST
in `input_binding`; `input_binding_sha256` identifies that input combination. Asset,
option or checker changes invalidate old findings even when the Markdown is unchanged.
Missing/nonlocal images make `direct_assets_bound` false; none are downloaded. Source
or bound-asset drift detected during checking/preparation aborts the operation.

When reusing a mechanical report, check its bindings against the current inputs;
older reports without these bindings cannot establish freshness. Equality is only
a necessary freshness condition, not an acceptance result: inspect the findings and
unchecked dimensions too. The binding covers direct Pandoc Image targets, not SVG
external resources, raw-TeX inclusions, bibliography dependencies, fonts or final-PDF
rendering. Review those separately when relevant. `prepare` binds checks to the input
manuscript and separately hashes its new derivative; it does not claim that the output
already received an independent review. These unsigned records are not authentication.

## Scope of mechanical checks

The helper parses Pandoc structure, not Markdown with regex alone. It detects missing
or duplicate figure IDs, unresolved targets/subpanels, fragile numeric references,
some raw notation/unit markup, values in recognized unit columns, missing local
figure assets and selected AI-declaration conflicts. It returns findings and unchecked
dimensions, not a general PASS or complete symbol-coverage certificate. Raw TeX,
unusual front matter and custom table/figure constructions still need manual review;
unknown syntax is not a reason to assert complete coverage.

In `release`, unbound numeric figure references and recognized notation defects are
errors; in `draft`, warnings. Audit known usage with `--ai-usage`. Unknown facts cannot
support a claim of no AI use. This argument is supplied context, not independent proof
of all usage. Practice drafts can record known assistance without fabricating final
contest documentation, prompts, tool versions or human acceptance.

Manually check symbol collisions/definitions, dimensions, equation/code correspondence,
reference and subpanel meaning, citation support, replication, abstract/body consistency
and truthful declarations. Typesetting must not change the science to repair them.
