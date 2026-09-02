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
