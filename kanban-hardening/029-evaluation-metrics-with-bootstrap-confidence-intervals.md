---
id: 29
status: doing
priority: Normal
blocked_by: [28]
assignee: "@amirhossein"
tags: [p1, l3, S6, R4]
---

# Evaluation metrics with bootstrap confidence intervals

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How model quality is measured and reported.

## Why this exists

The domain memo 3.3 item 5 warns that at n=239 a test R2 of 0.916 carries a wide interval,
and that a bare point estimate should not be reported.

This module produces every number that goes into the Chapter 1 revision, so it must report
intervals alongside point estimates by default — not as an option.

## Done when

- [ ] R2, RMSE, MAE reported on both log and wt% scales
- [ ] Bootstrap confidence intervals (2000 resamples) accompany every point metric
- [ ] Metrics computed per split and per temperature subgroup

- [ ] **The per-fold table already carries its own row counts, and that is not decoration (from
      #26).** `hydms.surrogate.model` returns `rows_fitted` and `rows_scored` as metrics, so
      `Evaluation.per_fold` and `reports/model/model-per-fold.csv` put the fold sizes in the same
      table as the fold scores. Screening removes between 15 and 144 of a fold's ~710 training
      rows (#24), so part of any fold-to-fold spread is training size and not the model. A
      bootstrap CI over the folds that does not say so is a CI over two different things
- [ ] Output is a structured table written to `reports/`, ready for the thesis
- [ ] SHAP and PDP are computed on train or a dedicated split, **never on test**. Leak L11:
      `benchmark_model_selection.py:1375,1383,1394` computed both on `X_test`, which makes REPORT §6.1
      a test-set artefact
- [ ] **L11 has no sentinel and this card owes one.** Once this card decides what the explainability
      record looks like, add the **L11 sentinel** to `hydms/qa/sentinels.py`: the record names no
      held-out split. Until it exists, HG-1 cannot report green

- [ ] **Every reported number must name the feature set it belongs to (from #25).** There are now
      two, and they are not interchangeable: `SELECTED`, the consensus 14 a shipped model is fitted
      on, and the per-fold sets of **16-20** features that #25's five-fold run actually produced.
      A bootstrap interval over folds that each selected their own columns is an interval about a
      *procedure*; one over a fixed 14-column pipeline is about a model. Both are legitimate and
      they are different claims, so the record carries which — and the Chapter 1 revision (#37)
      quotes it from there rather than from a paragraph

- [ ] **The bootstrap has no unit to resample until the predictions are kept.** Measured
      2026-09-05, before any code was written. `hydms/surrogate/model.py:_score_fold` computes
      `model.predict(scored)`, hands it straight to `quantile_metrics`, and **discards the
      frame**; nothing in `validation.py` retains a row-level prediction, and
      `Evaluation.per_fold` is one aggregate row per (model, fold). So the only thing
      resamplable today is **five fold scores** — and the box above says that spread is
      confounded with training size. 2000 resamples of five confounded numbers is not the
      interval the domain memo asks for. **The first change this card makes is to keep the
      out-of-fold predictions** `_score_fold` already computes, and hang an out-of-fold table
      off `Evaluation` for `evaluate` to read
- [ ] **The primary number is a row bootstrap over the out-of-fold predictions, and it is a
      claim about the *procedure*.** ~893 training rows resampled, not five folds. This is the
      number R4 is about — #26's honest nested **0.746** wt% against REPORT.md's published
      **0.892** — and resampling rows is what makes the interval mean anything
- [ ] **`--artifact current` is the *second* reading, and it cannot run yet.** `artifacts/`
      holds only `gate-results.json`: no version directory, no `current.json`, so
      `load_surrogate()` raises `PredictionError: nothing is promoted`. The artifact is #34,
      behind #31/#32/#33. Routing this card's primary number through the artifact would
      serialise the tail of S4 and make #37 wait on all of it; the out-of-fold route needs no
      artifact at all. Once #34 lands, a fixed model scored on held-out rows is a claim about
      **a model** rather than a procedure — a different and equally legitimate number, and the
      record says which, exactly as #25 forced for the feature set
- [ ] **Do not spend the session measuring the bootstrap.** 2000 resamples over a few hundred
      rows is milliseconds. The cost in this card is SHAP over a MultiQuantile CatBoost, and
      that is a question for the explainability step, not the metrics step
- [ ] **#26's tables are not on disk and cost ~3.5 h to regenerate.** `reports/model/` holds
      only #27's three conformal CSVs, because `/reports/*` is gitignored except
      `feature_selection/`. The `model-per-fold.csv` the fold-size box above builds on comes
      from a real `python -m hydms.surrogate.train` run. **Open call for this card:** un-ignore
      `reports/model/` the way #25 un-ignored `reports/feature_selection/`, so #37 quotes
      committed tables rather than somebody's local run

## Runnable check

```bash
python -m hydms.surrogate.evaluate --artifact current
```

The command as written is the **artifact** reading, and it cannot run until #34 promotes a
version. The card's primary number comes from the out-of-fold predictions of a nested run and
needs no artifact; both readings land behind this module, and the boxes above say which is which.

## Traces to

`docs/PRD-inverse-design.md` — S6, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-05: Opened. Nothing implemented; the session measured the card's own premises first and
  found two of them false. **(a)** The card asks for a 2000-resample bootstrap, but the pipeline
  keeps no row-level predictions to resample — `_score_fold` collapses `model.predict(scored)` into
  a metrics dict and drops the frame — so the only available bootstrap was over five fold scores
  whose spread the card itself warns is confounded with training size. **(b)** The card's runnable
  check names `--artifact current`, and no artifact exists: `artifacts/` holds only
  `gate-results.json`, and the version is #34's, three gates downstream. Taking the check literally
  would have made the primary number wait on #31/#32/#33/#34 and put #37 behind all of it. The
  decision is therefore to keep the out-of-fold predictions and make the row bootstrap over those
  the card's primary reading — a claim about the procedure, needing no artifact — and to keep the
  artifact-scored reading as the second one once #34 lands, labelled as a claim about a model. Both
  findings are boxed above. (by @assistant)
