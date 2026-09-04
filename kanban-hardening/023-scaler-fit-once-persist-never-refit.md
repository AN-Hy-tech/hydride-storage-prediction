---
id: 23
status: done
priority: High
blocked_by: [4, 13]
assignee: "@amirhossein"
tags: [p1, l3, AC-4]
---

# Scaler: fit once, persist, never refit

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The feature scaling transform and the fact that it belongs to the trained model.

## Why this exists

Memo 4.3 practical check 2 names refitting the scaler on candidates as a *silent
correctness bug*. `RobustScaler` is fit on training data only and then persisted with the
model.

Guard structurally: the loaded scaler should expose `transform` and not `fit`.

## Done when

- [x] `RobustScaler` fit on train only, persisted into the artifact directory —
      `hydms.surrogate.fit_scaler(features, split)` takes the **whole** matrix with #13's split
      assignment and selects the training rows itself, and it refuses a split that holds nothing
      out. What is persisted is `RobustScaler`'s *result* — the names, the medians, the IQRs — not
      the estimator; see the narrative for why, and for the measurement that says nothing is lost
- [x] The load path returns a transform-only wrapper; calling `fit` on it raises —
      `FittedScaler` has `transform` and no `fit`. `fit`, `fit_transform` and `partial_fit` raise
      `ScalerError` naming the defect; there is no estimator inside to reach past them
- [x] Scaler is versioned with the model, never re-derived from candidate data — it is the
      `scaler` payload of an artifact version (`SCALER_PAYLOAD`), and `scaler_from(bundle)` is the
      way back: it refuses a payload that is not a `FittedScaler`, and one whose columns are not
      among the version's own feature contract
- [x] Test asserts scaling a candidate batch twice yields identical output — and three stronger
      forms of the same property: another batch in between changes nothing, a candidate scales the
      same alone as in a crowd, and the statistics are unmoved by transforming

## Runnable check

```bash
python -m pytest tests/surrogate/test_scaler.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — AC-4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: Landed, opening S4. `hydms/surrogate/scaler.py` and 46 tests; suite 770 green, ruff
  and mypy clean, `run --fast` exits 0 with HG-1 still `SKIPPED` at 5/13 — no sentinel names
  `hydms.surrogate.scaler`, so nothing here was expected to move it. Five things worth keeping.

  **What is persisted is the fitted transform, not the estimator, and that was measured before it
  was decided.** `RobustScaler` does the fit — the definition of "robust" stays scikit-learn's —
  and `FittedScaler` keeps its result. Three things follow that do not follow from pickling the
  estimator: there is no `fit` anywhere inside to reach, so "never refit" is structural rather than
  a convention the next caller has to honour; the stored artifact carries no scikit-learn pickle,
  so an upgrade cannot change what a saved `v1` does, which is exactly the failure AC-1 exists to
  detect; and the numbers are legible in `describe()` and in review. The cost would have been
  arithmetic drift, and there is none: `(x - centre) / scale` in NumPy is **bit-identical** to
  `RobustScaler.transform` over all 1,278 x 21 values of the real training matrix — both are an
  elementwise float64 subtract then divide with no reduction to reassociate.
  `test_the_transform_is_bit_identical_to_robustscalers` re-measures it rather than trusting the
  sentence, and it is the test that goes red if this module ever stops reproducing the published
  fit. This is a deliberate reading of the first box rather than its literal wording.

  **The `ndarray` door is the one AC-4 cares about, and it was measured too.** On scikit-learn
  1.6.1 a `RobustScaler` fitted on a `DataFrame` *raises* on a reordered one — good — but accepts a
  bare `ndarray` with nothing but a `UserWarning`, and `fit_transform` returns an `ndarray`, so the
  column names are gone one line after the fit. That is where a permuted matrix becomes plausible,
  wrong numbers. `FittedScaler.transform` therefore takes a `DataFrame`, requires exactly the
  fitted column set, selects it **by name in fitting order**, and returns a `DataFrame` — so
  whatever order the caller had, the model downstream is handed the order it was fitted on.

  **`refuse_non_features` belongs at fit time, not at transform time.** Its docstring names the
  scaler as a caller, and the temptation was to call it on both paths. It is unnecessary on
  `transform`: requiring the column set to *equal* the fitted features is strictly stronger — a set
  equal to the features cannot contain the target. It is also expensive in the wrong place.
  `hydms.config.load()` parses `pipeline.yaml` on every call and is not cached, so a config read
  per `transform` would sit on the hot path of a candidate sweep; `transform` now reads no
  configuration at all. Its cost is **0.29 ms** for the full 1,278 x 21 matrix (scikit-learn's own
  is 0.60 ms) and **0.19 ms** for a single row — a per-call floor, like `featurize`'s 5 ms one, and
  the same instruction follows: scale in batches. Two numbers for #22 to fold into the end-to-end
  rate when #28 lands.

  **One published feature is constant over the training split.** `avg_is_alkaline`: zero IQR, so
  `RobustScaler` substitutes a scale of 1.0 and the scaled column is all zeros. A scale of exactly
  1.0 is indistinguishable from an IQR that genuinely equals 1.0 the moment the fit is over, so the
  names are captured at fit time in `FittedScaler.degenerate`, where they are still knowable.
  Removing it is not this card's — `selection.variance_threshold` is 0.001 and #24 owns the filter,
  where it is now an unticked box.

  **A scaler cannot be fitted without being told which rows are training rows.** The split is a
  parameter, never derived here — that is #13's protocol and its L8 guarantee is the reason a
  training row and a held-out row are different rows at all. `fit_scaler` refuses a split with no
  held-out rows, and the result records `fitted_rows` against `held_out_rows` (893 against 385 on
  the real matrix) so an artifact *states* the ratio rather than implying it. A caller can still
  defeat that by relabelling everything `train`; they cannot do it by accident, and the artifact
  says which happened.

  Two smaller notes. `scaler_from` checks the stored scaler's columns are a **subset** of the
  version's feature contract, not equal to it — #24 is expected to narrow them, and equality would
  go red on correct code the day selection lands. And the real matrix is 1,278 rows of 21 features:
  dropping `dev_Gordy_electonegativity` (266 rows refused) leaves every row but `Eu1Ni5`, whose
  jarvis cells are empty for six features. The test fixture finds the refused rows by asking
  `computability` once per **element** rather than once per row — a hole is a (feature, element)
  pair, so fifty-odd verdicts answer for all 1,279. That trade stays #24 and #25'. (by @assistant)
