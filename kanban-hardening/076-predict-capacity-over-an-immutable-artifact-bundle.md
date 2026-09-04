---
id: 76
status: backlog
priority: High
blocked_by: [28, 48, 49, 75]
assignee: "@amirhossein"
tags: [ph, l6, S2]
---

# predict_capacity() over an immutable artifact bundle

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** Everything between a formula string and a trustworthy answer: parsing, canonicalisation, featurisation, column order, scaling, quantile assembly, conformal widening, the domain check and the novelty distance.

## Why this exists

This is the phase's one genuinely deep module. Its interface is a single call:

```python
predict_capacity(formula: str, temperature_k: float) -> PredictionResult
```

Everything the audit found dangerous lives behind that signature — the scaler that must not refit, the
column order that must not drift, the interval that must not be dropped. If any of it leaks upward into
the API or the app, it will be duplicated between them, and the two copies will disagree.

The artifacts load **once**, as an immutable version-stamped bundle. A prediction path that can silently
pick up a different model between two calls cannot honour AC-4, and cannot be reasoned about at all.

## Done when

- [ ] `hydms/delivery/predict.py` exposes `predict_capacity()` and nothing else of substance
- [ ] An `ArtifactBundle` — model, scaler, feature contract, conformal calibration, AD reference set —
      loads once, is immutable, and carries the artifact version
- [ ] The scaler is **used**, never fitted, on this path
- [ ] Feature column order is asserted against the contract, not assumed
- [ ] The domain verdict (#48) and the ElMD distance (#49) are computed on every call
- [ ] Predictions are returned in wt%, back-transformed, with the interval transformed consistently
- [ ] No absolute path, no network call, no global mutable state
- [ ] Ten known training alloys reproduce the trained model's predictions on those rows (AC-4)
- [ ] **The trained-temperature bound is `hydms.screens.temperature_window()` (#44) — used, not
      re-written.** This layer owns no comparison against `domain.temperature_min_k/max_k`: it runs
      the screens and reads the verdict, so the refusal path and the screening path cannot disagree
      about what is in range. Read the domain verdict off `Verdicts`, and note that a screen may
      answer `INDETERMINATE`, which is a refusal and not a pass.

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_predict.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6; `docs/PRD-inverse-design.md` — S2, AC-4

## Narrative

- 2026-09-02: Created for Phase H. Shaped with the `codebase-design` and
  `software-design-philosophy` vocabulary: this is the deep module, and the API and app above it are
  deliberately thin transports (by @assistant)

- 2026-09-04: #44 landed the screen contract, so the domain verdict this card must carry has a
  shape: `apply_screens(candidates, screens)` returns one row per candidate with a code and a
  sentence per screen, and nothing is filtered until `Verdicts.select` is called. (by @assistant)
