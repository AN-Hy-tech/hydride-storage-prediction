---
id: 27
status: done
priority: High
blocked_by: [26]
assignee: "@amirhossein"
tags: [p1, l3, S2, AC-3]
---

# MAPIE conformal calibration

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How raw quantiles become intervals with a coverage guarantee.

## Why this exists

CatBoost's quantiles are not calibrated. Conformal prediction wraps any point or quantile
model with distribution-free, finite-sample coverage (Angelopoulos & Bates 2023).

**The calibration split must be carved from train, not taken from val or test** — reusing
validation would recycle data already used for early stopping and model selection.

## Done when

- [x] MAPIE fitted on a calibration split held out from training data
- [x] Calibration split defined in config and disjoint from the early-stopping split
- [x] Calibrator persisted into the artifact directory alongside the model
- [x] Documented which nominal coverage level is targeted

- [x] **The raw quantile heads under-cover, and by how much is measured (from #26).** CatBoost's
      `MultiQuantile` P10/P90 band covered **64.4 %** of held-out rows against a nominal 80 %, in
      a nested five-fold probe over the real matrix — fold by fold 0.57, 0.63, 0.70, 0.69, 0.63,
      under-covered in every one. So this card is not a formality on top of an already-honest
      interval; it is what makes the interval mean its own number, and gate AC-3 has a real gap
      to close rather than a rounding. The heads did **not** cross on any real row, so the
      monotonicity CQR would want is there to start with. `hydms.surrogate.model.quantile_metrics`
      already reports `interval_coverage`, `interval_width` and `crossings`, so the before-and-
      after is one column comparison rather than new measurement code
- [x] **The band is 80 %, and `conformal.confidence_level` moves 0.90 -> 0.80.** `pipeline.yaml`
      currently asserts two incompatible things: `model.quantiles: [0.1, 0.5, 0.9]` is an 80 %
      band, while `conformal.confidence_level: 0.90` tells MAPIE to expect heads at 0.05/0.95.
      CQR's prefit contract is exact — lower `(1-cl)/2`, upper `(1+cl)/2`, median 0.5 — so this is
      a precondition, not a preference. Moving the *confidence level* rather than the heads costs
      nothing measured and keeps #26's 64.4 % as a live baseline; moving the heads would invalidate
      it. The value is inert today — nothing reads it — so **this card is where it changes**
- [x] **Conformalise once, on the final fit, and let AC-3 read the test split.** Not inside every
      outer fold. The PRD's AC-3 says "coverage on the held-out test set", and a per-fold
      calibration would spend training rows the folds cannot spare (#26's folds fit on ~571) and
      would move #26's baseline under a new partition. A per-fold coverage *spread* is more
      informative and it is #29's or #30's question, not this card's
- [x] **The artifact stores the correction as a number, not a pickled MAPIE object.** #23 already
      made this decision once, the other way round: `FittedScaler` stores the medians and the IQRs
      rather than the `RobustScaler`, so "a scikit-learn upgrade cannot change what a saved `v1`
      does". A conformalised CQR object is strictly worse to pickle — MAPIE wrapping three adapter
      objects wrapping one booster, four surfaces that must all still unpickle when Chapter 3 is
      examined. **MAPIE is a fit-time dependency and must not be imported at predict time**
- [x] **Use MAPIE as the reference implementation and check it with a parity test — the AC-2
      pattern.** What is left of MAPIE's job after the box above is producing one float, and CQR's
      conformalisation is ten lines. It is used anyway because the `⌈(n+1)(1-α)⌉/n` finite-sample
      correction is exactly the off-by-one a reimplementation gets subtly wrong, and **a wrong
      conformal constant is invisible**: it under- or over-covers by a few points, which is
      precisely and only what AC-3 measures — so a hand-roll would use AC-3 to check the thing
      AC-3 exists to certify. So: fit with MAPIE, extract the constant, and assert that applying
      the stored constant reproduces MAPIE's own `predict_interval` on the calibration set to
      1e-12. **MAPIE is not installed in `Project`**; adding it touches `environment.lock.yml` and
      `requirements-lock.txt`, which `pyproject.toml` anticipates ("installed by the card that
      first needs them") and which is the price of the guarantee having an owner
- [x] **The calibration rows are a group-disjoint carve from `train`, behind a new
      `model.calibration_folds`.** Not `val` — the card forbids it above, since val chose the
      stopping iteration. Not a fourth entry in `SPLIT_NAMES` — that reaches back into #13, a
      landed card, and moves every split-size number in the docs and in `HELD_OUT_SPLITS`. The cut
      is `grouped_folds`, because a calibration set that is not group-disjoint on the canonical key
      is leak L8 at a new stage, and a test asserts no other module in this project imports a
      `KFold`. At `calibration_folds: 5` that is ~179 rows. **State the cost**: the deployed model
      then grows on ~714 rows where the cross-validation that estimated its performance fitted on
      893 — a real asymmetry, to be reported rather than hidden
- [x] **One constant, not two — `symmetric_correction=True` — and it is chosen before any number
      is seen.** MAPIE defaults to two, one per head at `alpha/2`, which is tighter when the
      miscoverage is one-sided. The trap is that **you cannot choose between them on evidence**:
      coverage on the calibration set is nominal by construction for both, so the comparison is
      empty, and choosing on the test set is leak L2 in a new place — selecting a calibration rule
      using the data that certifies it. Decided a priori: symmetric is the form Romano et al.
      report coverage for, it estimates one quantile rather than two from the same ~179 rows, and
      it puts one number in the manifest. Report the one-sided miscoverage in the model card as a
      **diagnostic**, and do not act on it
- [x] **The interval width is informative, measured, and that is why CQR rather than split
      conformal.** On outer-0's 185 held-out rows the raw P10-P90 width has **CV 0.572** — p25
      0.459, median 0.611, p75 0.847, max 2.315, a 12.2x max/min spread — and
      **Spearman(width, |median error|) = +0.474**: the band is wider where the model is wrong.
      CQR adds a constant to both heads, so the calibrated width inherits that spread exactly;
      `SplitConformalRegressor` with the `"absolute"` score would replace the whole distribution
      with one number and LCB ranking would reduce to mean ranking minus a constant, losing R1's
      mitigation. Two caveats belong in the ADR rather than in folklore: +0.474 is moderate, not
      strong, and the model measured was tuned by a 2-trial probe

- [x] **The early-stopping split this must be disjoint from is not a config value but a cut
      (from #26).** `hydms.surrogate.model.stopping_slice` carves one fold of `model.stopping_folds`
      out of the rows a fit owns, per fit, with `grouped_folds`. A calibration split "disjoint
      from the early-stopping split" therefore has to be disjoint from *whichever* rows that cut
      chose, which is recorded per fit in `FitLog` / `model-fits.csv` — read it rather than
      assuming a fixed slice

## Runnable check

```bash
python -m hydms.surrogate.calibrate --target capacity
```

## Traces to

`docs/PRD-inverse-design.md` — S2, AC-3

## Narrative

- 2026-09-06: **This card's headline numbers were measured on CatBoost's defaults, not on the
  deployed configuration, and are corrected in [../docs/PHASE-H-RUNBOOK.md](../../docs/PHASE-H-RUNBOOK.md)
  S4.** The calibration run that produced 0.6628 / +0.030990 / 0.7317 → 0.9155 ran at 14:35 on
  2026-09-05; `model-chosen.csv` was not written until 23:44, so `_params` took its documented
  "no deployed configuration on disk" branch and fitted with library defaults. The command *said*
  so, on stdout, which is where the note went to die — the same failure `model-run.csv` exists to
  prevent for the training command, and the conformal tables have no equivalent. Re-run against the
  deployed configuration the numbers are **0.6744 → 0.8081, correction +0.037355, width
  0.6741 → 0.8951**, zero crossings either way; the row accounting (893/20/172/701) is unchanged,
  because the carve does not depend on the hyperparameters. The prose above is left as written —
  it is the record of what this card measured — and this note is the correction. **A box for
  whoever next touches this module: `conformal.csv` should carry its own provenance column the way
  `model-run.csv` does**, so that "which configuration produced this constant" is answerable from
  the file rather than from a terminal nobody kept. (by @assistant)

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

- 2026-09-05: **Design settled before implementation, by grilling.** The open question this card's
  previous note left — CQR on the MultiQuantile model, one CatBoost per quantile, or
  `SplitConformalRegressor` around the median — is answered: **CQR, via MAPIE `prefit=True` with
  three thin adapters over #26's single model.** The reasoning, and the five decisions that turned
  out to sit *above* it, are the boxes added above. Three things were checked in MAPIE's source
  rather than its documentation, which 404s: `prefit=False` accepts only four named sklearn
  estimators and CatBoost is not among them; `prefit=True` wants a list of three fitted regressors
  **in the order [lower, upper, median]** — `single_estimator_ = self.estimators_[2]`, median
  *last* — which is precisely the positional trap #26 built `column_names` to kill, reintroduced at
  the MAPIE boundary and needing its own assertion; and each `predict` must return one column,
  which a `(n, 3)` MultiQuantile model does not, hence the adapters. The alternatives were rejected
  on measurement, not taste: one model per quantile triples a budget already at 3.5 h **and**
  forfeits the zero-crossing property #26 measured, since nothing holds independent heads in order
  and CQR's widening cannot repair a crossing; split conformal was killed by the width measurement
  in the last box above. Q3 is the decision that most changed the shape of the answer — once the
  artifact stores a number rather than an object, the adapters live for one function call and never
  have to survive a pickle, so most of the cost of the recommended option evaporates. (by @assistant)

- 2026-09-05: **Landed.** `hydms/surrogate/conformal.py` and `hydms/surrogate/calibrate.py`, with
  `model.calibration_folds` and `conformal.confidence_level: 0.80` in `pipeline.yaml`. Every
  decision above survived contact; four things are worth recording because they were not visible
  from the design.

  **The contradiction was worse than "inert".** The box above says the confidence level is a value
  nothing reads, so moving it costs nothing. True — but the reason it could sit wrong for a whole
  phase is that **MAPIE does not check its own prefit contract**: `_check_prefit_params` counts to
  three and never asks which quantile an estimator predicts. A 0.90 level beside heads at
  `[0.1, 0.5, 0.9]` would have produced a calibrated interval, silently, and the only thing that
  would ever have noticed is AC-3 — the gate this card exists to let pass. So the check went into
  `hydms.config._validate` rather than into the calibrator: the file refuses at load time, before a
  run has cost anything. That flipped a landed test,
  `test_an_alpha_passed_as_a_confidence_level_is_caught`, from asserting that 0.10 is *accepted*
  with a warning to asserting that 0.20 is *refused* — a range check alone cannot catch an alpha
  passed as a level, but a level checked against the heads can.

  **The measured gap reproduced.** Raw coverage on the 172 calibration rows is **0.6628** against
  nominal 0.80, on a different partition and with CatBoost's default hyperparameters, where #26
  measured 0.644 across its five nested folds. Two independent measurements of the same defect.
  The correction is **+0.030990** in model space; calibrated coverage on those rows is 0.8081 and
  the mean width goes 0.7317 -> 0.9155, a 25 % widening. **Zero crossings**, before and after.
  Nothing here is scored on `test` — the command says so in its own output, because a command that
  printed test coverage would invite the calibration to be adjusted until AC-3 passed, which is
  leak L2 wearing new clothes.

  **The row cost is 172, not the ~179 the box estimated**, and the deployed model grows on **701**
  rather than ~714. The difference is screening: CleanLab drops 20 of the 893 training rows before
  the carve, so the fifth is a fifth of 873. `conformal-rows.csv` carries the whole accounting in
  one row, because the asymmetry — the deployed fit sees 701 where the cross-validation that
  estimated its performance fitted on folds cut from 893 — is only visible if the two numbers sit
  side by side.

  **A negative correction is legal and the tests exercise it.** On a synthetic frame whose raw heads
  *over*-covered (0.875), the constant came out at −0.0161 and the band correctly narrowed to 0.821.
  Refusing a negative constant would have replaced a measured calibration with a floor nobody
  fitted, so `FittedConformal` refuses only a non-finite one.

  **What is not done here, deliberately.** The "persisted into the artifact directory" box is ticked
  on the same terms card #23 ticked its own: `CONFORMAL_PAYLOAD` and `conformal_from` are the
  persistence contract, and #34 writes the directory — a box naming both now sits on that card.
  `final_fit` was **not** changed: it grows on all of `train`, which is right for a run that is not
  calibrating, and `hydms.surrogate.calibrate` assembles the carved version itself rather than
  putting a calibration flag through a landed function.

  MAPIE **1.5.0** is installed in `Project` and pinned in `requirements-lock.txt` (209 packages now,
  and the misfiled-name check still reports `none`); pip resolved it without moving a single
  existing pin, since it needs only `numpy>=1.23` and `scikit-learn>=1.4`. It stays in the optional
  `uq` extra because it is genuinely fit-time — but CI now installs `.[dev,uq]`, since the parity
  and prefit-ordering tests are the only checks of a number whose wrongness is invisible, and
  letting them `importorskip` away on every push would leave the guarantee unchecked. (by @assistant)
