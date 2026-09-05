---
id: 28
status: backlog
priority: High
blocked_by: [27]
assignee: "@amirhossein"
tags: [p1, l3, S2]
---

# predict() — the surrogate's public interface

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** Model choice, scaling, quantile heads and conformal calibration — all of it.

## Job story

When I want a capacity estimate for a candidate alloy, I want one call that returns a calibrated interval, so I can rank on what the model actually knows rather than on a point estimate.

## Why this exists

The deep interface the search layer sees:

```python
predict(formulas, temperatures) -> DataFrame[p10, p50, p90, lcb, interval_width]
```

Callers must not know that a CatBoost model, a RobustScaler and a MAPIE calibrator are
involved. **Information-hiding check:** swapping CatBoost for another regressor should
require no change outside this layer.

`lcb` is a first-class output, not something callers derive, so that no caller can
accidentally rank on the mean.

## Done when

- [ ] Single public function taking formulas and temperatures, returning the interval frame
- [ ] Loads the pinned artifact version; refuses to run against an unpromoted version
- [ ] Applies the feature contract and the persisted scaler internally

- [ ] **The model consumes raw, unscaled features (from #26).** CatBoost splits on thresholds and
      `FittedScaler` is affine, so the tree ensemble is invariant to it; #26 therefore fits on raw
      features and records that in `QuantileModel.feature_names`. Applying the persisted scaler on
      the way into `predict` would feed the model a matrix it was never fitted on. The scaler is
      still in the bundle and still has a job — the applicability domain (#48) is distance-based
      and needs it — so the box above is right about *persisting* it and wrong about where it is
      applied
- [ ] **Two prediction spaces, and the public one is weight percent (from #26).**
      `QuantileModel.predict` returns wt%, `predict_model_space` returns the `log1p` the booster
      emits. The back-transform is exact rather than approximate: `expm1` is strictly increasing
      and a quantile is equivariant under a monotone map. Nothing is clipped — a negative lower
      band is the signal cards #48 and #77 act on
- [ ] Callers never see the model object, the scaler or the calibrator

## Runnable check

```bash
python -m pytest tests/surrogate/test_predict.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
