---
id: 23
status: done
priority: High
blocked_by: [4, 13]
assignee: "@amirhossein"
tags: [p1, l3, AC-4]
---

# Scaler: fit once, persist, never refit

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 0.5 d

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

- [x] **The persisted scaler has lost its named consumer, and the payload leaves the next
      version's contract** (added 2026-09-07 by #48; decided 2026-09-12). Two module docstrings
      justified keeping `FittedScaler` in the bundle by naming exactly one downstream reader —
      the applicability domain, card #48 — and **#48 landed as a capacity ceiling that reads no
      scaled matrix**, because per-class transfer R2 turned out not to correlate with chemical
      distance in any space measured, including the model's own feature space.

      **The decision: the next version's payload set drops `SCALER_PAYLOAD`. `v1` and `v2` keep
      it, because a version is sealed when it is written.** The removal is boxed on #34, which
      writes the next one.

      What decided it was not the missing reader but `deploy.py`'s own stated invariant.
      `DeployedFit.payloads` documents the rule the payload set is built on — the three keys are
      "each declared by the module that reads it back, **so this mapping cannot name a key
      nothing loads**". That is the property that keeps the set self-justifying rather than
      accumulating, and `SCALER_PAYLOAD` is now the counter-example to it. Restoring the
      invariant admits exactly two moves: find a reader, or drop the key. No reader exists, and
      none is forecast — #48 *measured* that distance in the model's feature space does not order
      transfer failure, so that consumer is not coming back; #49's ElMD reads compositions, not
      the feature matrix. So the key goes, and the invariant is a rule again rather than a
      description of two cases out of three.

      The counter-argument, and why it does not carry: a persisted scaler is insurance against a
      future refit-on-candidates, which memo 4.3 names a *silent correctness bug*. But that risk
      only exists for a consumer that scales, and the measurement above says there is none. An
      unread payload buys no insurance and costs a live claim — "fit on train only" — that no
      test on a real artifact can falsify, because the one test that touches a deployed scaler
      (`test_the_stored_scaler_is_never_applied`) asserts it is *not* used and runs against a
      fixture store. `/artifacts/` is gitignored, so nothing in CI reads the deployed payload at
      all.

      `fit_scaler`, `FittedScaler` and `scaler_from` all stay: `TRAIN` is imported by
      `hydms.screens.domain`, `selection.py` fits one in the moment for VIF, and the refusal
      behaviour is what makes "never refit" enforceable if a consumer ever does appear. What
      changes is one line of `DeployedFit.payloads`, and it changes on #34.

      **Four live sentences rested on the retired reason and have been corrected** (the two
      module docstrings were fixed by #48's own session; these were not): `deploy.py`'s payload
      invariant, `tests/surrogate/test_predict.py`'s `test_the_stored_scaler_is_never_applied`
      docstring, and two passages in `kanban-hardening/README.md`. #76's box list carried the
      same false consumer and is corrected there. `CONTEXT.md`'s **Artifact version** entry still
      reads "a model, its correction, its scaler and a manifest" — true of `v1`/`v2` and boxed on
      #34 to change with the payload.

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

- 2026-09-12: **Decided: the payload leaves the next version's contract.** The reasoning that
  mattered is reusable. A payload set kept honest by the rule "every key has a declared reader"
  fails *silently* when a reader is retired, because the key stays, the docstring stays, and the
  tests — which construct their own bundles — keep passing. Nothing goes red. The only thing that
  caught it was #48's session noticing its own consequence, and even that session corrected two
  docstrings and missed four more sentences. **When a justification is retired, the grep is the
  work**; correcting the module that lost its reason is the easy half. See
  [[when-a-finding-removes-a-reason-grep-for-what-rested-on-it]] in spirit: two of the four hits
  here were load-bearing claims (`deploy.py`'s invariant, #76's box), not prose.

  The decision itself turned on a stated invariant rather than on taste, which is why it was
  quick. `DeployedFit.payloads` had already written down the rule the payload set exists to obey.
  Once the rule is in the code, a violation of it is a fact, and the remedy is bounded — find a
  reader or drop the key. Preferences did not have to be argued. (by @assistant)
