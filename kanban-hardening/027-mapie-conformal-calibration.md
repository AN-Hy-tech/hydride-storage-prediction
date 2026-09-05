---
id: 27
status: backlog
priority: High
blocked_by: [26]
assignee: "@amirhossein"
tags: [p1, l3, S2, AC-3]
---

# MAPIE conformal calibration

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How raw quantiles become intervals with a coverage guarantee.

## Why this exists

CatBoost's quantiles are not calibrated. Conformal prediction wraps any point or quantile
model with distribution-free, finite-sample coverage (Angelopoulos & Bates 2023).

**The calibration split must be carved from train, not taken from val or test** — reusing
validation would recycle data already used for early stopping and model selection.

## Done when

- [ ] MAPIE fitted on a calibration split held out from training data
- [ ] Calibration split defined in config and disjoint from the early-stopping split
- [ ] Calibrator persisted into the artifact directory alongside the model
- [ ] Documented which nominal coverage level is targeted

- [ ] **The raw quantile heads under-cover, and by how much is measured (from #26).** CatBoost's
      `MultiQuantile` P10/P90 band covered **64.4 %** of held-out rows against a nominal 80 %, in
      a nested five-fold probe over the real matrix — fold by fold 0.57, 0.63, 0.70, 0.69, 0.63,
      under-covered in every one. So this card is not a formality on top of an already-honest
      interval; it is what makes the interval mean its own number, and gate AC-3 has a real gap
      to close rather than a rounding. The heads did **not** cross on any real row, so the
      monotonicity CQR would want is there to start with. `hydms.surrogate.model.quantile_metrics`
      already reports `interval_coverage`, `interval_width` and `crossings`, so the before-and-
      after is one column comparison rather than new measurement code
- [ ] **The band is 80 %, and `conformal.confidence_level` moves 0.90 -> 0.80.** `pipeline.yaml`
      currently asserts two incompatible things: `model.quantiles: [0.1, 0.5, 0.9]` is an 80 %
      band, while `conformal.confidence_level: 0.90` tells MAPIE to expect heads at 0.05/0.95.
      CQR's prefit contract is exact — lower `(1-cl)/2`, upper `(1+cl)/2`, median 0.5 — so this is
      a precondition, not a preference. Moving the *confidence level* rather than the heads costs
      nothing measured and keeps #26's 64.4 % as a live baseline; moving the heads would invalidate
      it. The value is inert today — nothing reads it — so **this card is where it changes**
- [ ] **Conformalise once, on the final fit, and let AC-3 read the test split.** Not inside every
      outer fold. The PRD's AC-3 says "coverage on the held-out test set", and a per-fold
      calibration would spend training rows the folds cannot spare (#26's folds fit on ~571) and
      would move #26's baseline under a new partition. A per-fold coverage *spread* is more
      informative and it is #29's or #30's question, not this card's
- [ ] **The artifact stores the correction as a number, not a pickled MAPIE object.** #23 already
      made this decision once, the other way round: `FittedScaler` stores the medians and the IQRs
      rather than the `RobustScaler`, so "a scikit-learn upgrade cannot change what a saved `v1`
      does". A conformalised CQR object is strictly worse to pickle — MAPIE wrapping three adapter
      objects wrapping one booster, four surfaces that must all still unpickle when Chapter 3 is
      examined. **MAPIE is a fit-time dependency and must not be imported at predict time**
- [ ] **Use MAPIE as the reference implementation and check it with a parity test — the AC-2
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
- [ ] **The calibration rows are a group-disjoint carve from `train`, behind a new
      `model.calibration_folds`.** Not `val` — the card forbids it above, since val chose the
      stopping iteration. Not a fourth entry in `SPLIT_NAMES` — that reaches back into #13, a
      landed card, and moves every split-size number in the docs and in `HELD_OUT_SPLITS`. The cut
      is `grouped_folds`, because a calibration set that is not group-disjoint on the canonical key
      is leak L8 at a new stage, and a test asserts no other module in this project imports a
      `KFold`. At `calibration_folds: 5` that is ~179 rows. **State the cost**: the deployed model
      then grows on ~714 rows where the cross-validation that estimated its performance fitted on
      893 — a real asymmetry, to be reported rather than hidden
- [ ] **One constant, not two — `symmetric_correction=True` — and it is chosen before any number
      is seen.** MAPIE defaults to two, one per head at `alpha/2`, which is tighter when the
      miscoverage is one-sided. The trap is that **you cannot choose between them on evidence**:
      coverage on the calibration set is nominal by construction for both, so the comparison is
      empty, and choosing on the test set is leak L2 in a new place — selecting a calibration rule
      using the data that certifies it. Decided a priori: symmetric is the form Romano et al.
      report coverage for, it estimates one quantile rather than two from the same ~179 rows, and
      it puts one number in the manifest. Report the one-sided miscoverage in the model card as a
      **diagnostic**, and do not act on it
- [ ] **The interval width is informative, measured, and that is why CQR rather than split
      conformal.** On outer-0's 185 held-out rows the raw P10-P90 width has **CV 0.572** — p25
      0.459, median 0.611, p75 0.847, max 2.315, a 12.2x max/min spread — and
      **Spearman(width, |median error|) = +0.474**: the band is wider where the model is wrong.
      CQR adds a constant to both heads, so the calibrated width inherits that spread exactly;
      `SplitConformalRegressor` with the `"absolute"` score would replace the whole distribution
      with one number and LCB ranking would reduce to mean ranking minus a constant, losing R1's
      mitigation. Two caveats belong in the ADR rather than in folklore: +0.474 is moderate, not
      strong, and the model measured was tuned by a 2-trial probe

- [ ] **The early-stopping split this must be disjoint from is not a config value but a cut
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
