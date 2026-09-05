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
- [ ] **The primary number is a bootstrap over the out-of-fold predictions, and it is a claim
      about the *procedure*.** Not five folds. This is the number R4 is about — #26's **probe**
      measured a nested R² of **0.746** wt% against REPORT.md's published **0.892**.
      **0.746 is a probe number**: a reduced-trial cost check whose own run prints `These
      numbers are a cost check, not a result`. No full run has ever been made in this project,
      so it is quoted as a direction, never as this project's honest score
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
      from a real `python -m hydms.surrogate.train` run. **Decided (Q4):** un-ignore
      `reports/model/` the way #25 un-ignored `reports/feature_selection/`, so #37 quotes
      committed tables rather than somebody's local run. The tables themselves arrive with #34's
      real run — see the Q9 box below

### Settled 2026-09-05 by a grilling session

- [ ] **The bootstrap resamples canonical groups, never rows (Q2).** `hydms.data.canonical.group_keys`
      is *the seam* — #13 splits on it, #88 folds on it, #87 re-joins on it — and a row-level
      resample would be a fourth meaning of "the same material": leak L8's logic applied to
      intervals instead of splits. **Measured on the real matrix:** the training split is **893
      rows in 780 canonical groups**, group sizes 1–6, and **692 of the 780 are singletons**. So
      the correction is real but **small** — a 13 % reduction in independent units, not a halving.
      Taken on principle, not on magnitude, and the card says so rather than implying a big fix
- [ ] **The caveat goes in the table, not in prose (Q5).** The out-of-fold predictions come from
      **five different models** whose training sets overlap, so they are not exchangeable draws
      from one procedure and there is no unbiased estimator of the variance of K-fold CV (Bengio &
      Grandvalet 2004). The interval is therefore **too narrow** — in a chapter whose whole
      argument is that the old numbers were too optimistic. It is a column or header row in the
      emitted table, because prose is what a session drops, as this one did with "probe"
- [ ] **Carry the per-fold spread beside it as a second, cruder interval (Q5).**
      `Evaluation.per_fold` already exists so it costs nothing, and two intervals that disagree
      are more honest than one that looks authoritative
- [ ] **One resample at the split level; every breakdown computed from it (Q6).** **83 of the 780
      groups span more than one temperature** (up to 6 distinct values), so a resampled group
      carries all its temperature rows with it. Resampling *within* a temperature bin would split
      those groups and break the seam locally. Subgroup *n* therefore varies between replicates —
      record the min and max subgroup *n* across replicates, so a bin that is thin in most of them
      is visible rather than implied
- [ ] **Publish the group-versus-row comparison (Q7).** Both computed once, both reported, with
      the statement that the choice is principled rather than numerically forced. The #25
      precedent: publish the comparison that justifies a choice, so no later session re-litigates
      it from a paragraph
- [ ] **This card lands machinery, not published numbers (Q9).** No full run has ever been made in
      this project — every number in this layer comes from a probe. #34 pays for the real run and
      its tables are what get committed; this card lands the emit path plus a test that it
      reproduces whatever is committed, verified against a sentinel-budget probe. **Consequence,
      stated rather than discovered: #37 stays blocked on #34.** The out-of-fold route decouples
      the *code path* from #34, not the *publishable numbers* — an earlier handoff said "entirely"
      and that was too strong. Probe tables are **not** committed as a stopgap: a labelled probe
      number is exactly how 0.746 escaped its qualifier
- [ ] **The explainability record names what it ran on, and the sentinel reads that (Q10).** SHAP
      and PDP run on **the training rows of the deployed fit**. The record carries an explicit
      `computed_on` column, and the L11 sentinel asserts its value is not in
      `hydms.surrogate.validation.HELD_OUT_SPLITS` — the project's single definition of a
      held-out name, asserted against rather than restated, the same one-seam logic as
      `group_keys`. No dedicated explainability split: it costs rows the deployed fit needs and
      buys nothing over training-row SHAP
- [ ] **Out-of-fold predictions are a defaulted field on `Evaluation` (Q11).**
      `out_of_fold: pd.DataFrame`, defaulting empty, so every existing construction and both the
      L2 and L4 sentinels are untouched. `Evaluation`'s docstring already calls itself "the
      evidence a later reader checks it with", and this is exactly that evidence. Not a second
      return value from `nested_scores`, which would split one concept across two returns
- [ ] **Boxed, not chased (Q8): the canonical count is off by one against a stated invariant.**
      CLAUDE.md says 1,149 formula strings collapse to **1,115** canonical compositions; the
      modelling matrix measures **1,114** groups over 1,278 rows. The populations genuinely differ
      — the matrix carries temperature duplicates the formula-string count does not — so this need
      not be a defect. Nothing currently checks it, which is how a real off-by-one would hide

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
- 2026-09-05: Grilled before implementing. Eleven decisions settled and boxed above under *Settled
  by a grilling session*; three of them corrected something this session had itself got wrong.
  **(a)** The recommendation as first recorded said "~893 training rows resampled" — a row
  bootstrap, which would have been the only place in the project ignoring the `group_keys` seam.
  Corrected to canonical groups, and then *measured*: 780 groups over 893 rows with 692 singletons,
  so the objection is right on principle and worth only 13 % of the independent units. The
  magnitude is recorded because overselling it would be the mirror of the error it fixed.
  **(b)** This session propagated **0.746 without its "probe" qualifier** into the board handoff
  and into a box on this card, promoting a reduced-trial cost check to a result — the anti-pattern
  CLAUDE.md names in its own words. Fixed here, in the handoff, and in the `predict.py` and
  `conformal.py` docstrings, which stated 64.4 % just as flatly. **(c)** The claim that the
  out-of-fold route "decouples #29 from #34 entirely" was too strong: it decouples the code path,
  not the publishable numbers, which still need one real run that #34 pays for. **The verification
  finding behind all of it:** none of this layer's headline numbers — 0.746, 64.4 %, 0.6628,
  +0.030990 — is asserted by any test, and `git ls-files reports/` returns only
  `feature_selection/` while `git ls-files artifacts/` returns nothing. On a fresh clone every
  #26 and #27 number is unverifiable prose. That is what the Q4 and Q9 boxes exist to end.
  (by @assistant)
