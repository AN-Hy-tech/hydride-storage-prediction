---
id: 26
status: done
priority: High
blocked_by: [23, 25, 88]
assignee: "@amirhossein"
tags: [p1, l3, S2, R4]
---

# CatBoost MultiQuantile with honest early stopping

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** The capacity model and its quantile heads.

## Why this exists

Two changes from the archived model.

First, **the leak**: `Catboostmodel.py:605` calls `fit(combined_pool, eval_set=test_pool,
early_stopping_rounds=5000)` — early stopping on the **test** set. Here early stopping uses
validation, and test is touched once, at the end.

Second, **quantiles**: `MultiQuantile` with alpha 0.1 / 0.5 / 0.9 so the model emits an
interval, not a point. This is what makes LCB ranking possible.

## Done when

- [x] `loss_function='MultiQuantile:alpha=0.1,0.5,0.9'`
- [x] **`use_best_model=True`** — CatBoost validates at fit time that `eval_set` is non-empty, which
      makes the guard mechanical rather than a convention
- [x] Early stopping on the validation split; the test split is not passed to `fit`
- [x] A test asserting the test split is never referenced during training
- [x] The quantile **column order** is asserted in a test — position is the only thing identifying
      P10 / P50 / P90
- [x] Folds come from ticket 88's protocol; no fold is both tuned on and scored on
- [x] **The budget is a product, and it is 4,500 fits.** #88's protocol is `model.cv_folds` (5)
      outer x `model.inner_cv_folds` (3) inner x `model.optuna_trials` (300) per contender. Record
      the measured wall time; if it is prohibitive, lower `inner_cv_folds` or `optuna_trials` in
      `pipeline.yaml` -- never collapse the nesting, which is leak L4 returning
- [x] Optuna search space ported from the archived script, selection on validation score only
- [x] Training is CPU-only (`MultiQuantile` has no GPU support) and the runtime is recorded for the
      slow lane's budget
- [x] The **L1 sentinel** and the **L5 sentinel** (ticket 71) are wired to this module — `live`
      checks in `hydms/qa/sentinels.py` calling `hydms.qa.assert_early_stopping_is_honest` with the
      real `eval_set` and scored-row identities, once for the final fit and once per fold. Gate HG-1
      goes red once `hydms/surrogate/model.py` exists without them
- [x] **L12 has no sentinel and this card owes one.** `Catboostmodel.py:516-518` set
      `weights = np.where(np.expm1(y) > 3, 2.0, 1.0)` — sample weights conditioned on the target,
      with a hand-tuned threshold. Whatever weighting scheme this card chooses, add the
      **L12 sentinel** to `hydms/qa/sentinels.py`: weights must be a function of the training rows'
      own features and of nothing else. Until it exists, HG-1 cannot report green

- [x] **Screening removes between 2 % and 20 % of a fold's training rows, depending on the fold
      (from #24).** Measured on the real five-fold cut: CleanLab flags 15, 45, 54, 71 and **144**
      rows out of roughly 710. `outer-1` therefore fits on 571 rows where `outer-2` fits on 704 —
      a 23 % difference in training size between two folds of one protocol, before the model sees
      anything. Two things follow for this card. The fold-to-fold spread in any score is partly
      this and not the model, so `Evaluation.per_fold` must be read beside
      `reports/selection/selection-per-fold.csv` rather than alone. And the **weighting decision
      this card owns** (#14 declined to make it, since the only archival weighting is L12's
      target-conditioned one) now has a second candidate reason to exist: an unweighted fit
      treats a 571-row fold and a 704-row fold as equal evidence

- [x] **The feature set to fit on is `hydms.descriptors.contract.SELECTED`, and the cost of the
      alternative is why (from #25).** #25 declared the consensus 14 — the features all five outer
      folds chose — and `CONTRACT` stays the published 22, so a matrix built for this card is
      `featurize(..., contract=SELECTED)` and the manifest records that contract, not the 22.
      **What this card must not do is re-run selection inside its own folds:** Boruta at the
      configured budget is 676 s a pass, and #88's protocol is 5 x 3 x 300 fits per contender, so
      per-fold selection inside the tuning loop is not a slower option, it is an impossible one.
      The consequence is a sentence this card owes rather than a defect: the folds that produced
      #25's stability table each selected **16-20** features, so a score reported here belongs to a
      *fixed* 14-feature pipeline and not to the procedure that chose them. Say which, in the
      metrics record itself, and #29 carries the same box

## Runnable check

```bash
python -m hydms.surrogate.train --target capacity && python -m pytest tests/surrogate/test_no_test_leak.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S2, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-08-30: **API check before implementation.** `loss_function="MultiQuantile:alpha=0.1,0.5,0.9"`
  returns one column per alpha, **in the order given in the string** — position is the only thing
  identifying P10/P50/P90, so that order deserves an explicit assertion in a test rather than a
  comment. `use_best_model=True` is validated at fit time to require a non-empty `eval_set`, which
  is the mechanical guard this card wants against the audit's early-stopping-on-test leak: the
  honest `eval_set` is the validation split. Note `MultiQuantile` is one of the few regression
  losses with **no GPU support**, so this trains CPU-only — relevant to the slow lane's runtime
  budget. Details in `docs/LIBRARY-APIS.md`. (by @assistant)

- 2026-09-02: Amended for Phase H. Blocked on 88 as well: fixing the early-stopping-on-test leak (L1) without
  fixing fold reuse (L4) and row-level folds (L7) would still report a tuning optimum as a held-out
  score. The `use_best_model=True` requirement is what turns the guard from a convention into a
  fit-time error (by @assistant)

- 2026-09-04: The budget box above was added by #88, whose protocol decides the multiplier. (by @assistant)

- 2026-09-05: **Landed.** `hydms/surrogate/model.py` is the capacity model,
  `hydms/surrogate/train.py` runs it through #88's protocol, and HG-1 is **12/13** — L1, L5 and
  L12 all green, L11 the only one left and it is #29's. Six findings, four of them measurements
  that contradicted an assumption this card or the archival script was carrying.

  **(a) The guard is the signature, not a convention.** `fit_quantile_model(frame, train=,
  eval_on=, scored_on=, where=)` cannot be called without naming the rows the resulting model
  will be *claimed about*, and the first statement of the body hands those identities to
  `assert_early_stopping_is_honest`. There is no path through the module that fits without it,
  which is what lets the L1 and L5 sentinels point at the real function rather than a copy.
  `scored_on` is never read, and `tests/surrogate/test_no_test_leak.py` asserts that by
  **value** as well as by identity: the scored rows are filled with `NaN` and the fit is
  expected to succeed. That test found one real read on the way past — the target was being
  transformed over the whole frame — and it is now scoped to the two row sets a fit owns.
  Two things are refused beyond the inventory: fitting on the scored rows (cruder than L1, and
  a `ModelError` so that a raised `LeakDetected` always means L1), and growing on the eval set
  (early stopping that watches rows the trees are already growing on never fires, and reads
  afterwards as a model that happened not to overfit).

  **(b) `early_stopping_rounds: 5000` was paying four times over for an identical model.**
  Measured on a real inner fold: at `od_wait` 5000 the fit costs **26.9 s**, at 500 it costs
  **6.9 s**, at 200 **5.4 s** — and all three return the *same model*, best iteration 1042 in
  every case and R² 0.7050 to four decimals. `od_wait` multiplies the iterations grown after
  the optimum, which `use_best_model` then discards. `pipeline.yaml` now says 500, with the
  measurement beside it. This is the one change to a configured value that costs nothing: the
  archival number was not a modelling choice, it was an unmeasured one.

  **(c) The budget: 4,500 fits is 42 hours, and 25 trials is 3.5.** A full end-to-end probe ran
  the real protocol over the real matrix — 5 outer folds, 2 trials, 35 fits in **19.4 min**, so
  **33 s a fit** on this machine. The configured product at 300 trials is 4,500 tuning fits,
  which is 42 h; `optuna_trials` is now **25**, projecting ~3.5 h. The nesting was not touched,
  which is the one thing this card was told not to do. **Where the hours actually are** is worth
  recording for whoever revisits: the ported space pairs `learning_rate` down to 1e-4 with
  `iterations` up to 30,000, and at that corner a fit costs **397 s** against 7 s at the fast
  one, reaches its best iteration at 29,999 — still improving when the budget ran out — and
  scores *worse*, R² 0.691 against 0.705. Sixty times the cost for a worse model. The space is
  ported anyway, because the card's instruction is to lower the trial count; narrowing it is a
  modelling decision and it is boxed onto #34, which is the card that has to pay the bill.

  **(d) One of the archival search's nine dimensions did nothing.** `bagging_temperature` is a
  Bayesian-bootstrap parameter and CatBoost's CPU default is not Bayesian. Measured: under the
  default, temperature 0.0 and 1.0 give a bit-identical fit — same trees, same best iteration,
  the same loss to six decimals — while under `bootstrap_type="Bayesian"` they give 0.1444 and
  0.1526. So `FIXED` pins the bootstrap, which is the one departure from the archival
  parameters and the one that makes a sampled dimension mean something. Two other beliefs about
  that space were checked and were **wrong**: `depth=25` under `Lossguide` is accepted, not
  refused (`max_leaves` makes it mostly inert), so the bound is ported verbatim; and
  `od_type='IncToDec'` alongside `early_stopping_rounds` is accepted too — the two are a
  redundancy, not a conflict, and the module sets only the one `pipeline.yaml` declares.
  `MedianPruner(n_startup_trials=5, n_warmup_steps=10, ...)` at `:541` reported one step per
  fold over ten folds — steps 0 to 9, every one below the ten-step warmup — so **the archival
  pruner never pruned**; the warmup here is 1, over 3 inner folds.

  **(e) The weighting decision is unweighted, and the whole of it is the blindness.** L12 is not
  the number 3; it is that the weighting is a function of `y`. `sample_weights(frame, settings)`
  slices to the declared features in its first statement and never reads the frame again — the
  same guard `select_features` uses for L6 — and `assert_weights_ignore_target` measures the
  consequence rather than trusting the statement. The fold-size argument the card offered as a
  second reason to weight does not land: a 571-row fold and a 704-row fold being treated as
  equal evidence is an argument about how folds are *aggregated*, not about rows inside one fit,
  and it is answered by carrying `rows_fitted` as a metric so the spread sits in the same table
  as the scores. **The detector needed two perturbations, and a test is what found that out.**
  Written with one — shuffle plus a 1.5x affine — it passed `np.where(y > 9, 2, 1)` over a batch
  topping out at 5 wt%, because that weighting is constant before *and* after. The second pass
  replaces the column with a ramp over a millionfold range. What remains uncoverable is stated
  on the detector rather than hidden: on the rows it is given, a threshold beyond even the ramp
  *is* a constant function, and no behavioural check can say otherwise.

  **(f) The interval is real and it is not calibrated — which is #27's whole reason to exist.**
  The probe's raw quantile heads cover **64.4 %** of held-out rows against a nominal 80 % for
  [P10, P90], fold by fold 0.57 / 0.63 / 0.70 / 0.69 / 0.63. Under-covered, consistently, in
  every fold. **Zero crossings** on real data, though — the heads came back ordered on every
  row, where a small synthetic fit crossed on 23 % of them, so `crossings` is reported as a
  number rather than assumed away. The probe's honest cross-validated R² is **0.746** (weight
  percent, median head, nested and group-aware, screening off), against REPORT.md's published
  test R² 0.892 and the committed CSVs' 0.376. It is a probe and the run says so in its own
  output; the configured run is #34's to publish.

  Two smaller decisions, both stated where they live. **No scaler.** CatBoost splits on
  thresholds and `FittedScaler` is affine, so the fit is invariant to it; the scaler belongs to
  the distance work downstream (#48) and to the artifact bundle, and refitting it per fold
  inside a tuning loop would add a leak surface for no effect. A model from here consumes raw
  features and says so in `feature_names`. **The eval set inside the folds** is one fold of
  `model.stopping_folds` (a new configured value, 5) cut from the rows a fit already owns by
  `grouped_folds` — the project's only fold generator, so no composition spans the two sides.
  The final fit needs no such cut: `val` is already a group-disjoint tenth, which is what
  `pipeline.yaml`'s `early_stopping_rounds` comment has said all along. (by @assistant)

- 2026-09-05: **Two small edits outside this card's files, both because #26 is the first card to
  put the project in a state their authors had not seen.** HG-1's `SKIPPED` message said "the
  modules they guard do not exist yet" about every unguarded leak; with L11 the only one left and
  it a *deferral*, that sentence was simply untrue — a deferred leak has no sentinel at all,
  because the decision it would assert has not been made. The message now follows whichever states
  are present. And `docs/LIBRARY-APIS.md` gained the four CatBoost facts this card had to measure
  rather than read: `bagging_temperature` is inert outside the Bayesian bootstrap, `depth` beyond
  16 is accepted under `Lossguide`, `od_type` beside `early_stopping_rounds` is a redundancy rather
  than a conflict, and `early_stopping_rounds` is a wall-time multiplier on an identical model.
  That document exists so the next card does not have to run the experiment again. (by @assistant)

- 2026-09-05: **The column-order assertion is in the fast lane, and that took measuring too.** It
  was written `@pytest.mark.slow` out of caution because it fits a real model. Measured: **0.97 s**
  — sixty iterations of a four-deep tree on 200 synthetic rows. The marker is defined as "takes more
  than a few seconds", so it was wrong, and it mattered: the CI fast lane runs `-m "not slow"`, and
  a deselected test does not assert the thing the card asked to be asserted. The empirical form is
  what makes it worth running at all — it checks that the share of truths at or below each head
  lands near that head's alpha, so a transposed mapping fails by 0.8 rather than by a rounding.
  (by @assistant)

