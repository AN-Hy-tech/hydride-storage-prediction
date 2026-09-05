---
id: 33
status: backlog
priority: High
blocked_by: [5, 28]
assignee: "@amirhossein"
tags: [p1, l3, AC-4]
---

# GATE AC-4: known alloys round-trip through predict()

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the screening path and the training path agree.

## Why this exists

Ten known training alloys fed through `predict()` must reproduce the trained model's
predictions on those same rows.

This catches the two silent failure modes that would otherwise poison every candidate list:
**a refit scaler, and a reordered feature matrix.** Neither raises an error on its own.

## Done when

- [ ] Ten training rows selected across different alloy classes
- [ ] Predictions via the screening path match the training-time predictions to floating tolerance
- [ ] Failure output shows per-feature values from both paths so the mismatch is diagnosable
- [ ] Registered as `AC-4` and run by CI

- [ ] **Compare like with like: `predict()` returns the CALIBRATED band (from #28).** The
      training-time heads are `QuantileModel.predict(features)` — raw. `predict()` widens the outer
      two by card #27's stored constant before back-transforming, so a round-trip that compares all
      three columns against a training-time `model.predict` will match on the median and fail on
      `q0.1` and `q0.9` by the transformed correction, every time, on a pipeline that is working.
      Either score the median head alone, or build the reference with
      `hydms.surrogate.conformal.calibrated_heads(model, features, conformal=conformal)`, which is
      exactly what `predict()` calls. `lcb` and `interval_width` are derived columns and are not
      part of the round trip
- [ ] **The interface, so the gate does not re-assemble it:**
      `hydms.surrogate.predict.predict(formulas, temperatures, version=, store=)` returns
      `[q0.1, q0.5, q0.9, lcb, interval_width]` in weight percent on the caller's index;
      `load_surrogate(...).feature_names` is the fitted column order the failure output must show
      both paths' values for. `store=` points it at a directory, which is how this gate scores a
      candidate version before the promotion pointer moves

- [x] **AC-4 passes against `artifacts/v1` (2026-09-06).** `python -m hydms.gates run --fast`
      reports `AC-4 PASSED 0 / 1e-12`: all 30 predictions agree between the screening path and the
      training path to 0.0000e+00 wt%, over 10 rows the model actually grew on across all 10 alloy
      classes, 14 fitted features, calibrated band on both sides. The version it scored is
      **v1 — the newest on disk, nothing promoted yet.**

      **The circle this card was written to worry about is already closed, in code, by this card's
      own decision.** `hydms/gates/_artifact.py` loads the bundle with `require_gates=False` — the
      door `hydms.artifacts.store` documents for "the card that has just written a version and
      wants it back" — and then builds the `Surrogate` through `surrogate_from`, the *same code*
      `load_surrogate` runs once it holds a bundle. So the only line of the delivery path a gate
      skips is the gate check whose input that gate is producing, and everything AC-4 exists to
      catch is downstream of it. `load_surrogate` grew no parameter and lost no guarantee, and
      `tests/gates/test_artifact.py` pins that it still refuses this very version. Recorded here
      because a session that meets the `GatesIncomplete` refusal without reading that module will
      re-open a settled question — as one did on 2026-09-06 before running the gate.

## Runnable check

```bash
python -m hydms.gates run AC-4
```

## Traces to

`docs/PRD-inverse-design.md` — AC-4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
