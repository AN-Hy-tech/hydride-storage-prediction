---
id: 28
status: done
priority: High
blocked_by: [27]
assignee: "@amirhossein"
tags: [p1, l3, S2]
---

# predict() — the surrogate's public interface

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 1 d

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

- [x] Single public function taking formulas and temperatures, returning the interval frame
- [x] Loads the pinned artifact version; refuses to run against an unpromoted version
- [x] Applies the feature contract internally — and **not** the persisted scaler, per the
      correcting box below. The contract is rebuilt from the model's own `feature_names` in
      fitting order, so a version whose model was fitted outside its manifest's contract is
      refused rather than featurised against the wrong declaration

- [x] **The model consumes raw, unscaled features (from #26).** CatBoost splits on thresholds and
      `FittedScaler` is affine, so the tree ensemble is invariant to it; #26 therefore fits on raw
      features and records that in `QuantileModel.feature_names`. Applying the persisted scaler on
      the way into `predict` would feed the model a matrix it was never fitted on. The scaler is
      still in the bundle and still has a job — the applicability domain (#48) is distance-based
      and needs it — so the box above is right about *persisting* it and wrong about where it is
      applied
- [x] **Two prediction spaces, and the public one is weight percent (from #26).**
      `QuantileModel.predict` returns wt%, `predict_model_space` returns the `log1p` the booster
      emits. The back-transform is exact rather than approximate: `expm1` is strictly increasing
      and a quantile is equivariant under a monotone map. Nothing is clipped — a negative lower
      band is the signal cards #48 and #77 act on
- [x] Callers never see the model object, the scaler or the calibrator

## Runnable check

```bash
python -m pytest tests/surrogate/test_predict.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-05: Closed. `hydms/surrogate/predict.py`: `predict(formulas, temperatures)` featurises
  against the contract rebuilt from the stored model's own `feature_names`, widens the heads with
  card #27's stored constant, and returns them in weight percent with `lcb` and `interval_width`
  appended. `load_surrogate()` is the load path and `Surrogate` is what it returns — a frozen
  object whose public surface is facts (version, quantiles, feature names, confidence level) and
  whose model, correction and contract are private fields. 24 tests, 3.5 s, no `slow` marker.
  (by @assistant)

- 2026-09-05: **The card's `[p10, p50, p90, ...]` was not taken, and the reason is not cosmetic.**
  The heads keep `hydms.surrogate.model.column_names`' spelling — `q0.1`, `q0.5`, `q0.9`. Two
  reasons. `model.quantiles` is configuration, so `p10` is a literal restatement of one possible
  value of it; and `column_names` is this project's single place where a CatBoost column position
  becomes a name, so a second naming rule one layer up is the positional trap coming back. The
  practical consequence is the one that decided it: `quantile_metrics(truth, frame, quantiles)`
  scores this frame unchanged, which is what card #29 needs and what a rename would have cost.
  (by @assistant)

- 2026-09-05: **`lcb` is looked up by `conformal.lower`, never by column 0.** It does duplicate one
  head column and that is deliberate — the card's point is that no caller should have to derive the
  ranking key — but the *derivation* is by name, so a band whose quantiles are not ascending still
  gets the bound its own calibration targeted. `test_the_bound_is_read_by_name_rather_than_by_position`
  builds a correction whose `lower` is the last column and asserts the frame follows it. (by @assistant)

- 2026-09-05: **`interval_width` is not the stored constant doubled.** The correction is a constant
  in `log1p` space and `expm1` is convex, so the same widening is a wider band at a high prediction
  than at a low one. Measured on three candidates at 250/400/600 K: three distinct widths. That is
  why AC-7 asks a published candidate to carry a width rather than reading it off the manifest.
  (by @assistant)

- 2026-09-05: **The "scaler is never applied" claim is measured, not stated.** A second artifact
  version is written whose stored scaler is a `FittedScaler` subclass raising on `transform`; the
  test first arms the trap (loads it back and asserts it still raises after a joblib round trip)
  and then demands `pd.testing.assert_frame_equal` against the ordinary version. A one-line
  "scale on the way in" would take it red. The card's third box was right about persisting the
  scaler and wrong about where it is applied, and it is ticked with that correction written into it.
  (by @assistant)

- 2026-09-05: **The gate check is never relaxed, and that is strictly stronger than the pointer.**
  `load_surrogate` does not forward `artifacts.load`'s `require_gates=False` and takes no
  equivalent, so a version with a `SKIPPED` criterion cannot answer a prediction. Since
  `artifacts.promote` already refuses a version whose gates are incomplete, *promoted* implies
  *gates established*; the converse is what this adds. Naming a version explicitly stays legal,
  because card #33's gate and a rollback inspection both have to score a candidate version before
  the pointer moves — but a named version faces exactly the same check. (by @assistant)

- 2026-09-05: **A load path was owed and did not exist.** `scaler_from` and `conformal_from` had no
  sibling for the model, so this card added `MODEL_PAYLOAD` and `model_from` to
  `hydms/surrogate/model.py` — beside the type, where the other two live beside theirs. It refuses a
  bare `CatBoostRegressor` (which unpickles happily, has its own `predict`, and returns an unnamed
  array — the positional trap one layer down) and a model recording no fitted columns. The
  contract cross-check deliberately stays in `predict.py`, where an undeclared name stops being an
  observation and becomes an unbuildable column. (by @assistant)

- 2026-09-05: **A cache, and why it is defensible here.** `_LOADED` memoises by `(store, version)`.
  An artifact version is written once and never edited, so a key can only ever name one set of
  bytes; the promotion pointer is *not* cached, so a rollback takes effect on the next prediction
  rather than the next process, which `test_the_promotion_pointer_is_re_read_rather_than_cached`
  asserts. `clear_cache()` exists for tests that write into a directory the process has already
  read. Card #76's "no global mutable state" box is about the delivery module; a box has been left
  there so it wraps this rather than adding a second cache. (by @assistant)

- 2026-09-05: **What this layer deliberately does not do.** It does not clip — a negative `lcb`
  survives, because it is the signal cards #48 and #77 act on — and it does not refuse an
  out-of-domain candidate, because the temperature window, the AD ceiling and the novelty distance
  are L4 screens and the refusal that carries them is L6. A surrogate that silently declined rows
  would make the screen verdict unobservable, which is the thing card #44 exists to prevent.
  (by @assistant)

- 2026-09-05: HG-1 unchanged at 12/13 — this card owed no sentinel and touched none. Suite 960 fast
  tests green (936 before this card), ruff and mypy clean, `check_board.py` and `check_freeze.py`
  OK, `python -m hydms.gates run --fast` exits 0 with AC-2 at 2.7285e-12. (by @assistant)
