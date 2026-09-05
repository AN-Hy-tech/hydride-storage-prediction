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

### Settled by card #27, against MAPIE 1.5.0's source

The RISK this section used to carry — whether CQR accepts a `MultiQuantile` model, needs one
CatBoost per quantile, or should be replaced by `SplitConformalRegressor` around the median — is
resolved. **CQR, via `prefit=True`, with three one-column adapters over the single model.** The
four facts that decide it were read out of `mapie/regression/quantile_regression.py`, because the
hosted documentation for these internals 404s:

- **`prefit=False` accepts four estimators and CatBoost is not one of them.** The class docstring
  names `QuantileRegressor`, `GradientBoostingRegressor`, `HistGradientBoostingRegressor` and
  `LGBMRegressor`; `_fit_estimators` looks the estimator up in `quantile_estimator_params` by class
  name and raises otherwise. No duck typing gets in.
- **`prefit=True` takes `[lower, upper, median]` — the median LAST.**
  `_initialize_and_check_prefit_estimators` does `self.single_estimator_ = self.estimators_[2]`, and
  `conformalize` reads positions 0 and 1 as the band. `_check_prefit_params` only counts to three;
  it never checks which quantile an estimator predicts. Hand it the wrong order and you get a
  plausible, wrong interval and no error. This is the positional trap `column_names` exists to kill,
  reappearing at the library boundary, so `hydms.surrogate.conformal` asserts it two ways.
- **Each estimator must `predict` one column**, which a `(n, 3)` MultiQuantile booster does not —
  hence the adapters. Each carries `fitted_ = True` and deliberately **not** `n_features_in_`:
  `check_sklearn_user_model_is_fitted` probes any estimator that has the latter by calling
  `predict(np.zeros((1, n)))`, and an adapter that refuses an unnamed array on purpose fails it.
- **The heads must match the level exactly**: lower `(1 - confidence_level) / 2`, upper
  `(1 + confidence_level) / 2`, median `0.5`. `pipeline.yaml` shipped violating this — heads at
  `[0.1, 0.5, 0.9]` beside `confidence_level: 0.90` — and nothing raised because nothing read
  either key. `hydms.config._validate` now refuses the pair.

The alternatives were rejected on measurement: one CatBoost per quantile triples a search budget
already at 3.5 h **and** forfeits the zero-crossing property card #26 measured, since nothing holds
independent heads in order and CQR's widening cannot repair a crossing; `SplitConformalRegressor`
with the `"absolute"` score would replace a width distribution with CV 0.572 by a single number,
collapsing lower-confidence-bound ranking to mean ranking minus a constant.

Two more calls worth writing down, both used by `fit_conformal`:

```python
# symmetric_correction=True: ONE constant for both heads, not MAPIE's default of one per head.
point, intervals = calibrator.predict_interval(X_calib, symmetric_correction=True)
low, high = intervals[:, 0, 0], intervals[:, 1, 0]
```

`predict_interval` returns `(n, 2, 1)`; the third axis exists only for consistency with the other
regressors. And `_check_lower_upper_bounds` **logs** ill-sorted predictions at INFO — it does not
raise — so a crossed head passes through silently and has to be counted elsewhere
(`quantile_metrics(...)["crossings"]`).

**What HydMS stores is the constant, not the calibrator.** MAPIE is a fit-time dependency: the
constant is read back off `predict_interval`'s own output, checked to be a single number, and
asserted to reproduce that output to 1e-12 before it is returned. Nothing on the prediction path
imports MAPIE.

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
  the honest `eval_set` is the **validation** split, never the test split. Verified against
  catboost 1.2.8: `CatBoostError: To employ param {'use_best_model': True} provide non-empty
  'eval_set'.`

### Measured against catboost 1.2.8 while card #26 ported the archival parameters

Everything above was read from documentation. These four were **run**, because the archival
script's parameter block turned out to contain three things nobody had checked.

- **`bagging_temperature` does nothing unless `bootstrap_type="Bayesian"`.** CatBoost's CPU
  default is not Bayesian, and it accepts the parameter anyway rather than warning. Measured on
  an identical fit: temperature 0.0 and 1.0 give the same tree count, the same best iteration
  and the same loss to six decimals under the default; under `Bayesian` they give 0.1444 and
  0.1526. `Catboostmodel.py:549` sampled it without pinning the bootstrap, so one of the
  search's nine dimensions was noise. Pin the bootstrap, or drop the dimension.
- **`depth` beyond 16 is accepted under `grow_policy="Lossguide"`.** `depth=25` fits without
  complaint; `max_leaves` is what bounds the tree, so a 64-leaf tree cannot be 25 deep and the
  parameter is mostly inert there. Only `max_leaves` itself is refused outside Lossguide:
  `max_leaves option works only with lossguide tree growing`.
- **`od_type='IncToDec'` + `od_pval` alongside `early_stopping_rounds` is accepted**, not a
  conflict. On a fit where both could act they stopped at the same iteration. It is a
  redundancy to remove rather than an error to resolve — set the one you mean.
- **`early_stopping_rounds` is a wall-time multiplier, not a model choice.** `od_wait` only
  governs how many non-improving iterations are grown *after* the optimum, which
  `use_best_model` then discards. Measured on a real inner fold: 26.9 s at 5000, 6.9 s at 500,
  5.4 s at 200 — with best iteration 1042 and R² 0.7050 in **all three**. Same model, four
  times the cost.

---

## Corrections made to committed work

| File | Was | Now | Why |
|---|---|---|---|
| `pyproject.toml` | `mapie>=0.8` | `mapie>=1.0` | 0.8 predates the `fit`/`conformalize`/`predict_interval` API documented above. The old floor would have silently allowed a version whose interface does not match any code written against these notes. Card #27 installed **1.5.0** into `Project` and pinned it in `requirements-lock.txt`; pip resolved it without moving any existing pin. |

`pymoo>=0.6`, `streamlit>=1.30` and `ElMD>=0.5` are unchanged — nothing found contradicts them,
though only pymoo was checked against upstream docs in this pass.

## Not covered yet

- **ElMD** (card #49) — not queried; the novelty metric's API is still unverified.
- **OPTIMADE** (cards #65, and #49's prior-art cross-check) — not queried.
- **Streamlit** (cards #58, #66) — not queried; low risk, stable surface.
