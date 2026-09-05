---
id: 27
status: backlog
priority: High
blocked_by: [26]
assignee: "@amirhossein"
tags: [p1, l3, S2, AC-3]
---

# MAPIE conformal calibration

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How raw quantiles become intervals with a coverage guarantee.

## Why this exists

CatBoost's quantiles are not calibrated. Conformal prediction wraps any point or quantile
model with distribution-free, finite-sample coverage (Angelopoulos & Bates 2023).

**The calibration split must be carved from train, not taken from val or test** — reusing
validation would recycle data already used for early stopping and model selection.

## Done when

- [ ] MAPIE fitted on a calibration split held out from training data
- [ ] Calibration split defined in config and disjoint from the early-stopping split
- [ ] Calibrator persisted into the artifact directory alongside the model
- [ ] Documented which nominal coverage level is targeted

- [ ] **The raw quantile heads under-cover, and by how much is measured (from #26).** CatBoost's
      `MultiQuantile` P10/P90 band covered **64.4 %** of held-out rows against a nominal 80 %, in
      a nested five-fold probe over the real matrix — fold by fold 0.57, 0.63, 0.70, 0.69, 0.63,
      under-covered in every one. So this card is not a formality on top of an already-honest
      interval; it is what makes the interval mean its own number, and gate AC-3 has a real gap
      to close rather than a rounding. The heads did **not** cross on any real row, so the
      monotonicity CQR would want is there to start with. `hydms.surrogate.model.quantile_metrics`
      already reports `interval_coverage`, `interval_width` and `crossings`, so the before-and-
      after is one column comparison rather than new measurement code
- [ ] **The early-stopping split this must be disjoint from is not a config value but a cut
      (from #26).** `hydms.surrogate.model.stopping_slice` carves one fold of `model.stopping_folds`
      out of the rows a fit owns, per fit, with `grouped_folds`. A calibration split "disjoint
      from the early-stopping split" therefore has to be disjoint from *whichever* rows that cut
      chose, which is recorded per fit in `FitLog` / `model-fits.csv` — read it rather than
      assuming a fixed slice

## Runnable check

```bash
python -m hydms.surrogate.calibrate --target capacity
```

## Traces to

`docs/PRD-inverse-design.md` — S2, AC-3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-08-30: **API check before implementation — MAPIE 1.x is not 0.x.** `MapieRegressor(...)`
  with `.predict(X, alpha=...)` is gone. Current usage is `fit(X_train, y_train)` then
  `conformalize(X_conf, y_conf)` then `predict_interval(X_test)`, with `confidence_level=0.95`
  rather than `alpha`. Coverage is `regression_coverage_score(y_test, y_pis)[0]`; interval width
  is `y_pis[:, 1, 0] - y_pis[:, 0, 0]`. The `pyproject.toml` floor was corrected from `>=0.8` to
  `>=1.0`, since 0.8 would have admitted the incompatible interface.

  **Open question this card must settle first:** MAPIE's `ConformalizedQuantileRegressor` expects
  a scikit-learn-style quantile estimator, and a single CatBoost `MultiQuantile` model emitting
  all quantiles at once may not be that shape. Decide between CQR on the MultiQuantile model, one
  CatBoost model per quantile, or `SplitConformalRegressor` around the median — before building
  on either. Details in `docs/LIBRARY-APIS.md`. (by @assistant)
