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

### Measured against catboost 1.2.8 while card #29 explained the deployed fit

- **`MultiQuantile` supports SHAP natively, and it is fast.**
  `booster.get_feature_importance(Pool(X), type="ShapValues")` returns an
  **`(n_rows, n_heads, n_features + 1)`** array — one exact TreeSHAP explanation per quantile
  head, with the **base value last** on the trailing axis. Measured: 0.02 s on a 200-tree fit
  over 708 rows x 14 features. Card #29 had budgeted this as the expensive step of the card;
  it is not, and the `shap` package (which is installed) is not needed for it.
- **`type="LossFunctionChange"` refuses on a `Pool` with no label**:
  `catboost/private/libs/target/data_providers.cpp:552: Regression loss/metrics require target
  data`. `PredictionValuesChange` works on an unlabelled pool and returns one number per
  feature — collapsed across heads, so it cannot answer a per-head question.
- **There is no partial-dependence helper for a multi-output regressor.**
  `sklearn.inspection.partial_dependence` is written for one output and its estimator checks
  reject this model; the curve is short enough to own directly (hold every other column, set
  one to a grid value, average the predictions), which also lets the grid sit on the feature's
  **own observed quantiles** rather than on a Cartesian box that walks out of the applicability
  domain.

---

## ElMD — Element Mover's Distance (card #49 / AC-7)

### Settled by card #49, against ElMD 0.5.15's source

**Installed 0.5.15 into `Project`, and it moved nothing.** Its requirements — `numba`, `numpy`,
`scipy`, `setuptools`, `flit` — were all already satisfied there (numba 0.60.0, numpy 1.26.4,
scipy 1.15.2), so pip installed exactly one package. `requirements-lock.txt` gained one line.

- **The pin `ElMD>=0.5` is correct and resolves to 0.5.15. `ElMD==0.5.0` is unsatisfiable.**
  That sdist's metadata declares itself version `0.4.25`, so pip discards it: *"has inconsistent
  version: expected '0.5.0', but metadata has '0.4.25'"*. The floor is fine; a hard pin on that
  release is not.
- **The licence is GPL-3.0.** `LICENSE.txt` in the sdist is the GPL v3 text and `setup.py` says
  `license='GPL3'`, but the trove classifier says *LGPLv3*. The licence file governs, and GPL-3.0
  is compatible with this project's own `GPL-3.0-or-later`.
- **The API is three names**: `ElMD(formula, metric="mod_petti")`, the instance method
  `.elmd(other)`, and a module-level `elmd(a, b, metric=...)`. Both distance calls accept a
  string or an `ElMD` object. There is no batch or matrix entry point — `ElM2D` is a separate
  package and is not needed, see the closed form below.
- **On `mod_petti` the metric is a closed form, and that is the whole batching story.**
  `elmd()` dispatches to `simple_emd(a.feature_vector, b.feature_vector)`, which is literally
  `np.sum(np.abs(np.cumsum(dist1 - dist2)))` over the 103-slot vector of atomic fractions
  (`feature_vector is ratio_vector` for integer-valued tables such as this one). So a whole
  batch is one `cdist(cumsum(C), cumsum(T), "cityblock")`. Verified equal to ElMD's own answer
  to **3.6e-15** over the curated corpus. Every *other* metric routes through the network
  simplex over a full cost matrix and does **not** reduce this way.
- **Measured cost.** `cdist` on cumulative vectors runs at ~37 M pairs/s, flat from 1e3 to 1e5
  candidates; a warm `ElMD.elmd()` loop is **46x** slower, and `ElMD(formula)` construction is
  **48.6 us**, which is the cost that actually dominates and is why formulas are parsed once
  per distinct string rather than once per comparison. The broadcast form
  `abs(C[:,None,:] - T[None,:,:]).sum(2)` agrees to 2.8e-13 and is **23x slower** than `cdist`
  while allocating `n x m x 103` floats.
  **Warm the JIT before timing anything**: a cold `ElMD.elmd()` measures ~3.5 ms/pair, which is
  numba compiling `simple_emd`, not the metric. That is a 2,500x error in the ratio.
- **It does not raise on an unparseable formula, and it fails two ways, not one.** `_dictify`
  silently drops any symbol absent from the lookup, which has a loud half and a quiet half.
  *Total loss:* `ElMD("")`, `ElMD("NotAnElement")` and `ElMD("Xx2")` return an object whose
  `ratio_vector` sums to **zero**, and a zero vector has a finite, meaningless distance to
  everything — a normalisation check catches this one.
  *Partial loss, which no normalisation check can catch:* `ElMD("LaNi5Xx2")` drops `Xx` and
  keeps the rest, so it **is** `LaNi5` — `composition == {La: 1.0, Ni: 5.0}`, `ratio_vector`
  sums to exactly 1.0, and `elmd()` to a real `LaNi5` returns **0.0**. Likewise `TiFeQ` is
  `TiFe`, and `<NA>` — what `str(pd.NA)` produces — is **nitrogen**. A typo or a missing value
  therefore arrives as a confident zero distance from a known alloy unless the caller checks.
  The only reliable guard is a **second, independent parse**: `hydms.screens.novelty` reads
  every string with `hydms.data.load.parse_formula` as well and requires both parsers to name
  the same elements, treating any disagreement as `INDETERMINATE`, which is a rejection. The
  two agree on all 1,149 distinct curated formulas, so the cross-check costs nothing real.
  One string they agree on and *should* be known about: `"NaN"` is sodium-plus-nitrogen to
  both, so a missing value written as that text is a valid formula no guard can catch.
- **`ratio_vector` is 103 long and `petti_vector` is 121.** The distance uses the former. They
  are not interchangeable.

### The defect that cost card #49 a bug fix

**`ratio_vector` is not reproducible across processes for a formula of three or more elements.**
`_fuse` builds its composition dict from `{... for atom in set(mol1) | set(mol2)}`, so element
*insertion order* follows the per-process randomised hashes of the element symbols;
`_normalise_composition` then divides by `sum(composition.values())` summed in that order, and
the total differs by an ulp between runs. Measured on the training split: **76 of 780
compositions moved by 2.2e-16 between two processes, and every one had three elements or more.**
Within a single process ElMD is perfectly stable, which is why this hides from casual testing.

The consequence was not the 1e-16 — it was that `python -m hydms.screens.novelty --emit` did not
produce byte-identical output twice, so the committed reference could not be asserted to be what
the code generates. `hydms.screens.novelty` therefore sums the parsed counts itself, in **sorted
symbol order**, and a test pins the result against `ratio_vector` to 1e-12 so the deterministic
path stays ElMD's metric rather than becoming a private one. ElMD's own `_gen_ratio_vector`
already sorts when it *places* the fractions; only the total was order-dependent.

---

## Corrections made to committed work

| File | Was | Now | Why |
|---|---|---|---|
| `pyproject.toml` | `mapie>=0.8` | `mapie>=1.0` | 0.8 predates the `fit`/`conformalize`/`predict_interval` API documented above. The old floor would have silently allowed a version whose interface does not match any code written against these notes. Card #27 installed **1.5.0** into `Project` and pinned it in `requirements-lock.txt`; pip resolved it without moving any existing pin. |

`pymoo>=0.6` and `streamlit>=1.30` are unchanged — nothing found contradicts them, though only
pymoo was checked against upstream docs in this pass. `ElMD>=0.5` is unchanged and is now
**verified** against 0.5.15; card #49 confirmed the floor is right and that a hard `==0.5.0`
would not resolve.

## Not covered yet

- **OPTIMADE** (cards #65, and #49's prior-art cross-check) — not queried.
- **Streamlit** (cards #58, #66) — not queried; low risk, stable surface.
