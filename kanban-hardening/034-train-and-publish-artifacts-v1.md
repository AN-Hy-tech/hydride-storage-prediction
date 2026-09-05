---
id: 34
status: backlog
priority: High
blocked_by: [29, 31, 32, 33]
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

- [ ] **This card no longer pays for the fit — #29 does, and this card promotes *that* run
      (decided 2026-09-05, #29 Q12).** Two independent 3.5 h runs would mean the numbers in
      Chapter 1 describe a different model from the one that ships, so there is **one run**: #29
      pays for it and writes the tables, this card gates and promotes the artifact from it. Hence
      the new `blocked_by: 29`. **Two boxes below moved to #29 with the bill** — the config
      re-read race and the search-space narrowing — because this card owned them only on the
      stated ground that it "pays the 3.5-hour bill". They are struck through below rather than
      deleted, so the reasoning stays legible

- [ ] **OPEN DECISION — this card's premise is broken: the run persisted no model
      (found 2026-09-05, after the fit).** The box above says this card "promotes *that* run".
      `train.py` **saves nothing** — `final_fit` is handed to SHAP and PDP and dropped; the only
      `store` hits in that file are argparse's `store_true`. So there is no model on disk to
      promote, and #31 and #33 need one too.

      **Left open on purpose, for a session that is not the one that just ran the fit.** Options:
      **(A)** refit outer-0's configuration from `model-chosen.csv` — 32.979 s per `model-fits.csv`,
      no second search needed; **(B)** add persistence to `train.py` and re-run, 1 h 41 m, so the
      promoted model is literally the one that made the numbers; **(C)** a hybrid that refits but
      gates promotion on proven equality.

      **What it turns on.** The out-of-fold numbers are safe either way — they came from the five
      outer-fold models, not the deployed fit. **`model-shap.csv` and `model-pdp.csv` are the
      stake**: those were computed on the deployed fit, so a refit that lands elsewhere leaves the
      committed explainability tables describing a model nobody ships — the same class of mismatch
      as leak L11. And the fit is seeded (`random_seed`, the stopping slice, the Optuna sampler)
      but **`model.FIXED` pins no `thread_count`**, while #7's slow lane runs on `windows-latest`.
      See the 2026-09-06 handoff in [README.md](README.md) for the full framing.

- [ ] Full pipeline run from `data/raw/` produces `artifacts/v1/`
- [ ] Manifest complete: git SHA, seeds, package versions, feature contract, gate results
- [ ] All Phase 1 gates pass and are recorded in the manifest

- [ ] ~~**The full run is about 3.5 hours and the reason is one corner of the search space (from
      #26).**~~ **MOVED TO #29 (2026-09-05)** — the narrowing decision follows the bill, and #29
      now pays it. Narrowing must happen *before* the run Chapter 1 quotes, otherwise this card
      improves a model the thesis has already reported. Left here for its measurements:
      Measured: 33 s a fit on this machine, and the configured budget is
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
- [ ] ~~**A run re-reads `pipeline.yaml` from disk while it is running, so an edit lands
      mid-flight (measured 2026-09-05).**~~ **MOVED TO #29 (2026-09-05)**, by this box's own
      rule — "this card pays the 3.5-hour bill, so it owns the fix" — now that #29 pays it. It
      must land *before* #29's run. Left here in full, because the measurements are this card's: `hydms.config.load` is uncached and re-parses the file on
      every call, and `hydms.surrogate.model._columns` calls it through `load_config()` whenever
      `target_column` is `None` — which is the whole scoring path. Counted under `sentinel_settings()`:
      **210 reads in one nested run** of ~35 fits, so about six a fit, at **7.6 ms each**; the
      configured 381-fit run is therefore roughly **2,300 windows** in which a working-tree edit
      changes what the run believes. It has already fired once: a `--trials 8` probe died on trial 3
      with `unknown key(s) ['calibration_folds']` because #27 wrote the new YAML into the shared
      worktree after the process had imported the old `Model` dataclass. **This card pays the
      3.5-hour bill, so it owns the fix**: thread the target column into `ModelSettings` so
      `_columns` never falls back to disk, and record the config the run actually used in the
      manifest beside the git SHA and the seeds — `artifacts/store.py` records `load_config().seed`
      today and nothing else about the file. A guard in the project's grain is a test asserting that
      `fit_quantile_model` reaches `hydms.config.load` zero times
- [ ] **Nothing records which commit a fit ran from, and this card owns the manifest that
      should (from #29, 2026-09-05).** `train.py`'s `_run()` writes trials, folds, seed and
      feature set into `model-run.csv` — but not the SHA. The only SHA anywhere is the one
      `evaluate --emit` stamps, which is `HEAD` **when the document was generated**, not when the
      fit ran. #29 found this while fixing the clean-tree stamp and deliberately did not patch it
      mid-run: adding a column would have changed the shape of a table the running fit was already
      going to write in the old shape, and `read_run` would have been reading one shape from a run
      that wrote another.

      **It has already bitten once, harmlessly, and the record exists so nobody re-derives it:**
      the 2026-09-05 run fitted from `a101205` and its document stamps `5f696d9`, because the
      stamp defect was fixed while the fit was running. `git diff a101205 5f696d9` over
      `hydms/surrogate/{train,model,validation,selection,scaler}.py`, `hydms/data/`,
      `hydms/descriptors/` and `hydms/config/` is **empty** — no fitting code moved. This card's
      manifest must record the run's own SHA rather than promotion-time `HEAD`, or the next
      occurrence will not be harmless.
- [ ] `current` points at `v1`

## Runnable check

```bash
python -m hydms.pipeline run --promote && python -m hydms.gates run --all
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-09-05: A `--trials 8` probe run died on trial 3 with `ConfigError: pipeline.yaml:model: unknown key(s) ['calibration_folds']`, and nothing was wrong with the code at any commit: the process had imported the pre-#27 `Model` dataclass and then re-read a post-#27 `pipeline.yaml` off the shared worktree. The interesting part is not the race but what it exposed — a run is not hermetic against its own configuration file. Measured while diagnosing it: one `load()` is 7.6 ms and a sentinel-budget nested run makes 210 of them, 21.6% of that run's wall time. At the configured budget that is ~2,300 re-reads spread over 3.5 hours. Recorded as a box above rather than fixed in place, because the fix changes what a published run records about itself and that is this card's subject. (by @assistant)
- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
