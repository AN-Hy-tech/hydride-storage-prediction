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
- [ ] Callers never see the model object, the scaler or the calibrator

## Runnable check

```bash
python -m pytest tests/surrogate/test_predict.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
