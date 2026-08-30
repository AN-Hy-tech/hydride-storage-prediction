# Library APIs the plan depends on

Practical API reference for the libraries this project has *committed to* but not yet run.
Distinct from [`research/inverse-design-methods.md`](../research/inverse-design-methods.md) §6,
which argues *which* library to choose; this records *how each one is actually called*.

Fetched from current upstream documentation via Context7 on **2026-08-30**. Anything below marked
**RISK** is an inference about how the pieces fit together, not something the docs assert — treat
those as questions for the implementing card to settle, not as findings.

> **Why this exists.** `pyproject.toml`'s optional-dependency version floors were written from
> memory when the package was scaffolded, and none of these libraries is installed, so nothing
> checked them. One floor was wrong in a way that would have silently admitted an incompatible
> API. See *Corrections made* at the end.

---

## MAPIE — conformal prediction intervals (cards #27, #31 / AC-3)

**The 1.x API is not the 0.x API.** The old `MapieRegressor(estimator, method=…, cv=…)` with
`.predict(X, alpha=…)` is gone. Current usage splits fitting from calibration explicitly:

```python
from mapie.regression import (
    SplitConformalRegressor,
    CrossConformalRegressor,
    JackknifeAfterBootstrapRegressor,
    ConformalizedQuantileRegressor,
)

# Split conformal — fit and conformalize on disjoint data
mapie = ConformalizedQuantileRegressor(estimator, confidence_level=0.95)
mapie.fit(X_train, y_train)
mapie.conformalize(X_conformalize, y_conformalize)
y_pred, y_pis = mapie.predict_interval(X_test)

# Cross-conformal variants do both in one call
mapie = CrossConformalRegressor(estimator, method="plus", cv=10, confidence_level=0.95)
mapie.fit_conformalize(X, y)
y_pred, y_pis = mapie.predict_interval(X_test)
```

Points that decide whether AC-3 is measured correctly:

- **`confidence_level`, not `alpha`.** 0.95 means a 95% interval directly.
- **Two-step calibration.** `fit()` then `conformalize()` on a *held-out* conformalization set.
  Conformalizing on training data invalidates the coverage guarantee — which is the entire point
  of the gate.
- **`predict_interval` returns `(y_pred, y_pis)`.** The interval array is 3-D; width is
  `y_pis[:, 1, 0] - y_pis[:, 0, 0]`.
- **Coverage:** `regression_coverage_score(y_test, y_pis)` returns an array — index `[0]`.

```python
from mapie.metrics.regression import regression_coverage_score
coverage = regression_coverage_score(y_test, y_pis)[0]     # compare against 0.95
width = (y_pis[:, 1, 0] - y_pis[:, 0, 0]).mean()
```

**RISK for card #27.** The plan is CatBoost `MultiQuantile` (#26) *then* MAPIE calibration (#27).
MAPIE's `ConformalizedQuantileRegressor` expects a scikit-learn-style quantile estimator, and a
single CatBoost `MultiQuantile` model emitting all quantiles at once is not obviously that shape.
Card #27 should establish, before building on it, whether CQR accepts the MultiQuantile model
directly, needs one CatBoost model per quantile, or whether `SplitConformalRegressor` around the
median prediction is the honest fit. This is unresolved here.

---

## pymoo — NSGA-II on the composition simplex (cards #59, #60, #62)

```python
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

class MyProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, n_ieq_constr=2,
                         xl=np.array([-2, -2]), xu=np.array([2, 2]))

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = [f1, f2]     # objectives, minimised
        out["G"] = [g1, g2]     # inequality constraints, feasible when <= 0

res = minimize(problem, NSGA2(pop_size=100), ("n_gen", 100), seed=1, verbose=False)
```

- **Everything is minimised.** Maximising the capacity lower confidence bound means returning
  `-lcb`. Getting this backwards produces a confident, plausible, exactly wrong Pareto front.
- **Constraints are `g <= 0` feasible** (card #60). A VEC window `lo <= v <= hi` becomes two
  constraints, `lo - v` and `v - hi`.
- **`seed=`** is on `minimize`, which is what multi-seed stability (card #63) varies.
- Non-dominated set: `from pymoo.util.nds.non_dominated_sorting import find_non_dominated`.
- Hypervolume is a standard reported indicator (`hv`); SMS-EMOA computes it exactly up to 5
  objectives and switches to approximation above that. With 3 objectives we are in the exact
  regime (card #62).

**RISK for card #59.** The snippet above uses `ElementwiseProblem`, which calls `_evaluate` once
per candidate. PRD risk **R6** requires batched featurisation and forbids per-candidate loops —
NSGA-II makes far more surrogate calls than enumeration does. pymoo's vectorised `Problem` base
class evaluates a whole population per call and is the shape this project needs. Card #59 should
subclass `Problem`, not `ElementwiseProblem`, and card #22's throughput budget is what decides
whether that is sufficient.

---

## CatBoost — MultiQuantile (card #26)

```python
model = CatBoostRegressor(
    loss_function="MultiQuantile:alpha=0.1,0.5,0.9",
    early_stopping_rounds=100,
    use_best_model=True,
)
model.fit(X_train, y_train, eval_set=(X_val, y_val))
preds = model.predict(X_test)      # shape (n, 3), columns in alpha order
```

- **Output dimension equals the number of alphas**, and columns follow the order given in the
  string. P10/P50/P90 come back as columns 0/1/2 for the alpha string above — position is the
  only thing identifying them, so the order is a contract worth asserting in a test.
- **`MultiQuantile` has no GPU support.** It is one of the few regression losses excluded
  (unlike `Quantile`, which has it). Training is CPU-only; relevant to the slow lane's runtime.
- **`early_stopping_rounds` sets `od_type='Iter'` and `od_wait`.**
- **`use_best_model=True` requires a non-empty `eval_set`** and raises at fit time otherwise.
  This is the mechanical guard against the audit's *early-stopping-on-test* leak (PRD §2.2.3):
  the honest `eval_set` is the **validation** split, never the test split.

---

## Corrections made to committed work

| File | Was | Now | Why |
|---|---|---|---|
| `pyproject.toml` | `mapie>=0.8` | `mapie>=1.0` | 0.8 predates the `fit`/`conformalize`/`predict_interval` API documented above. The old floor would have silently allowed a version whose interface does not match any code written against these notes. |

`pymoo>=0.6`, `streamlit>=1.30` and `ElMD>=0.5` are unchanged — nothing found contradicts them,
though only pymoo was checked against upstream docs in this pass.

## Not covered yet

- **ElMD** (card #49) — not queried; the novelty metric's API is still unverified.
- **OPTIMADE** (cards #65, and #49's prior-art cross-check) — not queried.
- **Streamlit** (cards #58, #66) — not queried; low risk, stable surface.
