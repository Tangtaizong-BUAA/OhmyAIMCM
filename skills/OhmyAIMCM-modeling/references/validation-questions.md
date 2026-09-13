# Choose tests from the claim

These are failure questions, not a model lookup table or required test quota.

- Mechanistic/geometry claim: do units, limits, constraints and initial/boundary
  conditions agree? Does discretization change the answer materially? A simulator
  can run successfully while violating the proposed physics.
- Optimization claim: is the decision feasible in the original units and domain?
  What justifies local, best-found or global optimality? Compare a simpler feasible
  decision or a bound when informative; do not prescribe a solver family.
- Prediction/inference claim: what is the independent observational unit and the
  evaluation target? Can preprocessing, repeated subjects, time or spatial neighbors
  leak information? A training fit is not independent prediction evidence.
- Ranking/decision claim: whose preferences do weights represent? Are units and
  directions compatible, and can plausible assumptions reverse the decision?
- Robustness claim: what was varied, held fixed and measured? Restrict the claim
  to the inspected uncertainty/range; do not equate a single seed with stability.
- Mathematical derivation: are assumptions sufficient, domains stated and each
  implication justified? An exact proof need not invent a data set or significance test.

Compare added complexity against the gap it closes. If the scientific objective
does not require an empirical superiority claim, do not manufacture an ablation
exercise or benchmark score just to complete a template.
