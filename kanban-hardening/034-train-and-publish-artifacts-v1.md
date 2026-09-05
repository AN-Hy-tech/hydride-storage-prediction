---
id: 34
status: backlog
priority: High
blocked_by: [31, 32, 33]
assignee: "@amirhossein"
tags: [p1, l3, S1]
---

# Train and publish artifacts v1

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The first promoted artifact version.

## Why this exists

The moment Architecture A becomes possible. Everything downstream pins this version.

Promotion requires the gates to pass — this ticket is blocked on 31, 32 and 33 for exactly
that reason.

## Done when

- [ ] Full pipeline run from `data/raw/` produces `artifacts/v1/`
- [ ] Manifest complete: git SHA, seeds, package versions, feature contract, gate results
- [ ] All Phase 1 gates pass and are recorded in the manifest

- [ ] **The full run is about 3.5 hours and the reason is one corner of the search space (from
      #26).** Measured: 33 s a fit on this machine, and the configured budget is
      `cv_folds` x `inner_cv_folds` x `optuna_trials` = 5 x 3 x 25 = 375 tuning fits plus six
      more. `optuna_trials` came down from the archival 300 — which would be 42 h — and the
      nesting was not touched. **Where the hours are**: the ported space pairs `learning_rate`
      down to 1e-4 with `iterations` up to 30,000, and at that corner one fit costs 397 s against
      7 s at the fast one, has not converged at iteration 29,999, and scores *worse* (R² 0.691
      against 0.705). #26 ported the space rather than narrowing it, because its instruction was
      to lower the trial count. **Narrowing it is a modelling decision and it belongs to this
      card**, which is the one that has to pay the bill: a lower bound on `learning_rate`, or an
      upper bound on `iterations`, would buy back most of the wall time for a model that is not
      worse. If it is narrowed, `tests/surrogate/test_model.py::test_the_search_space_is_the_archival_one`
      is what has to be updated, deliberately and with the reason in it
- [ ] **The deployed configuration is chosen on an inner-fold number (from #26).**
      `hydms.surrogate.train._deployed` takes the configuration whose own search achieved the best
      inner-fold pinball loss. The outer scores — the ones a run reports — take no part in it,
      which is what keeps picking a configuration from being leak L2 in a new place. Keep that
      property if this card chooses differently
- [ ] **The version carries a conformal correction, and it is a number (from #27).** The payload
      key is `hydms.surrogate.conformal.CONFORMAL_PAYLOAD` and the value is a `FittedConformal`,
      read back with `conformal_from(bundle)` exactly as the scaler is with `scaler_from`. Two
      things this card owns and #27 could not: the calibration slice must be carved **before** the
      deployed fit — `calibration_slice(frame, kept.kept)` over the screened training rows, then
      `fit_quantile_model(train=fitting, eval_on=val, scored_on=test)`, which is what
      `hydms.surrogate.calibrate` does and what `final_fit` does *not* — and the row asymmetry must
      be published beside the score: at `calibration_folds: 5` the deployed model grows on ~701
      rows where the cross-validation that estimated its performance fitted on folds cut from ~893.
      **Never store a pickled MAPIE object**; `conformal_from` refuses one and says why
- [ ] `current` points at `v1`

## Runnable check

```bash
python -m hydms.pipeline run --promote && python -m hydms.gates run --all
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
