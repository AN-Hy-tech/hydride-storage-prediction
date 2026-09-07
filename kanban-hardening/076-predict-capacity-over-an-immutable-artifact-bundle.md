---
id: 76
status: backlog
priority: High
blocked_by: [28, 48, 49, 75]
assignee: "@amirhossein"
tags: [ph, l6, S2]
---

# predict_capacity() over an immutable artifact bundle

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** Everything between a formula string and a trustworthy answer: parsing, canonicalisation, featurisation, column order, scaling, quantile assembly, conformal widening, the domain check and the novelty distance.

## Why this exists

This is the phase's one genuinely deep module. Its interface is a single call:

```python
predict_capacity(formula: str, temperature_k: float) -> PredictionResult
```

Everything the audit found dangerous lives behind that signature — the scaler that must not refit, the
column order that must not drift, the interval that must not be dropped. If any of it leaks upward into
the API or the app, it will be duplicated between them, and the two copies will disagree.

The artifacts load **once**, as an immutable version-stamped bundle. A prediction path that can silently
pick up a different model between two calls cannot honour AC-4, and cannot be reasoned about at all.

## Done when

- [ ] `hydms/delivery/predict.py` exposes `predict_capacity()` and nothing else of substance
- [ ] An `ArtifactBundle` — model, scaler, feature contract, conformal calibration, AD reference set —
      loads once, is immutable, and carries the artifact version
- [ ] ~~The scaler is **used**, never fitted, on this path~~ — **the scaler is not used on the
      prediction path at all (from #26 and #28).** CatBoost splits on thresholds and `FittedScaler`
      is affine, so #26 fits on raw features and records that in `QuantileModel.feature_names`;
      applying the persisted scaler on the way in feeds the model a matrix it was never fitted on.
      This box is right that it is never *fitted* and wrong about where it is used: its consumer is
      #48's distance-based applicability domain, which reads it with
      `hydms.surrogate.scaler.scaler_from(bundle)`. `hydms/surrogate/predict.py` proves the
      negative rather than promising it — `test_the_stored_scaler_is_never_applied` stores a scaler
      that raises on `transform` and demands identical numbers
- [ ] **The surrogate half of the bundle already exists: wrap it, do not re-load it (from #28).**
      `hydms.surrogate.predict.load_surrogate(version=, store=)` returns a frozen `Surrogate` that
      holds the model, the correction and the featurisation contract, is pinned to one version,
      refuses a version whose gates are unestablished, and is memoised by `(store, version)` — the
      immutability this box asks for. `ArtifactBundle` is that plus the AD reference set and the
      ElMD reference set. A second unpickle of the same booster is what the "loads once" box is
      trying to prevent, and calling `artifacts.load` again here is how it comes back
- [ ] **"No global mutable state" needs a stated exception, or it is already false (from #28).**
      `hydms.surrogate.predict._LOADED` is a module-level memo of immutable, content-addressed
      objects; the promotion pointer is deliberately not cached, so rollback still takes effect on
      the next call. Decide whether this layer inherits that cache or holds the bundle itself, and
      say which in the ADR (#85) — two caches for one artifact version is the failure
- [ ] Feature column order is asserted against the contract, not assumed
- [ ] **An unparseable formula has no screen code, and `INDETERMINATE` is the answer (from #75).**
      The delivery vocabulary is `ADMITTED` + the union of the configured screens' `reasons` +
      `INDETERMINATE`, so "this string does not parse" and "the `oliynyk` table has no mass for this
      element" have no code of their own — and `featurize` raises before any screen has seen the
      candidate. Two orderings work and this card picks one: **screen before featurising**, or catch
      `FeaturisationError` and map it to a `Refusal` carrying `INDETERMINATE` with the parse error's
      own sentence as the explanation. #48's applicability screen already emits `INDETERMINATE` for
      exactly this case, so the second keeps one vocabulary; the first keeps one code path. Whichever
      is chosen, say so in the ADR (#85)

- [ ] **A missing value in the formula column is not always unparseable, and one spelling of it is
      real chemistry** (added 2026-09-07 by #49's QA pass). `None` and `np.nan` are refused on this
      path — the latter only because `str(nan)` happens to parse to nothing — but `str(pd.NA)` is
      `<NA>`, which ElMD read as **nitrogen** until #49 cross-checked it against
      `hydms.data.load.parse_formula`, and **`"NaN"` is a valid formula to both parsers**: sodium
      and nitrogen. So a missing value stringified into the formula column can arrive as a
      well-formed composition that no guard downstream can distinguish from chemistry, and it
      would be answered with a confident capacity, an interval and a novelty distance. This card
      owns "everything between a formula string and a trustworthy answer", so **the null check
      belongs here, before the string reaches any parser** — a null is a `Refusal`, not a formula.
      #84 inherits the same obligation for CSV upload, where the value arrives from a user's file
- [ ] The domain verdict (#48) and the ElMD distance (#49) are computed on every call
- [ ] Predictions are returned in wt%, back-transformed, with the interval transformed consistently
- [ ] No absolute path, no network call, no global mutable state
- [ ] Ten known training alloys reproduce the trained model's predictions on those rows (AC-4)
- [ ] **The trained-temperature bound is `hydms.screens.temperature_window()` (#44) — used, not
      re-written.** This layer owns no comparison against `domain.temperature_min_k/max_k`: it runs
      the screens and reads the verdict, so the refusal path and the screening path cannot disagree
      about what is in range. Read the domain verdict off `Verdicts`, and note that a screen may
      answer `INDETERMINATE`, which is a refusal and not a pass.

- [ ] **Decide whether the domain reference is pinned into the bundle** (added 2026-09-07 by
      #48). `hydms/screens/domain-reference.json` holds the numbers the applicability-domain
      screen judges against: the trained capacity range, the 5.19 wt% cross-family ceiling, the
      fourteen feature spans and the ten per-class transfer figures. It sits beside the module,
      regenerated by `python -m hydms.screens.domain --emit`, because those are properties of the
      **curated data** rather than of any one fit — the same reasoning that keeps `reports/loco/`
      committed and read rather than refitted.

      **The risk that argues the other way is real and belongs to this card.** A promoted artifact
      version is sealed; the reference is not. So a served `v2` could in principle be screened
      against a reference measured from data it was never fitted on, and nothing would say so.
      Either pin a copy into the bundle beside the scaler and the feature contract, or make the
      manifest record the reference's digest so a mismatch is detectable — but do not leave it
      implicit. Note the ordering constraint: this screen reads a **prediction**, so
      `predict_capacity()` predicts first and screens second, and the point estimate it bounds is
      the median head, not the lower confidence bound (the LCB is the ranking key and is
      deliberately conservative — bounding it would let a wide-banded unphysical claim through)

- [ ] **Decide whether `delivery_screens()` gains the novelty screen, and accept what it costs**
      (added 2026-09-07 by #49). #49 has landed: `hydms.screens.novelty.novelty_screen()` returns a
      screen whose verdict frame carries `novelty.distance` and `novelty.nearest`, spelled exactly
      as `hydms.delivery.contract.Novelty` needs them. It is deliberately **not** in
      `delivery_screens()` yet, because adding it is this card's call, not #75's.

      **The cost is a hard dependency.** ElMD is the optional `novelty` extra, and unlike MAPIE it
      is on the prediction path — a candidate formula has to be parsed onto the modified-Pettifor
      scale before any distance exists. Putting the screen in `delivery_screens()` means an
      installation without `[novelty]` can no longer predict *at all*, rather than predicting
      without a distance. CI now installs it, so the suite will not notice the difference; a
      deployment might. The alternatives are to require the extra outright (simplest, and AC-7
      arguably demands it: "no candidate is published without an ElMD distance"), or to let
      `PredictionResult.novelty` stay `None` when the extra is absent — which is the field's
      documented meaning, and is also how a promise quietly becomes optional. Say which in the
      ADR (#85).

      Two smaller notes it inherits. The reference set is `hydms/screens/novelty-reference.json`,
      780 training compositions and a computed ceiling, and it is **the same pin-or-digest question
      the box above asks about the domain reference** — answer both the same way. And the novelty
      screen's ceiling is *chemistry*, not the applicability domain: a candidate rejected by it
      must not be reported as out-of-domain (#48 measured why they are different)

- [ ] **The rule that turns several screen verdicts into one code and one sentence already exists
      — call it, do not re-derive it** (added 2026-09-07 by #90). `hydms.delivery.refusals.resolve()`
      takes the verdicts in run order and returns `(code, reason)`: the code is the **first
      rejecting** screen's, because run order is the only precedence declared *across* screens (the
      precedence *within* the domain screen is its own `_PRECEDENCE`), and the reason carries every
      rejecting screen's sentence joined by `"; "` — a candidate rejected by two rules and explained
      by one is the partial truth #44 exists to remove. `docs/REFUSALS.md` is generated through it,
      so a second composition rule here is how the catalogue and the API come to explain the same
      refusal differently, which is the defect #90 exists to make visible. If it belongs in
      `contract.py` rather than beside the catalogue, **move** it; do not copy it

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_predict.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6; `docs/PRD-inverse-design.md` — S2, AC-4

## Narrative

- 2026-09-02: Created for Phase H. Shaped with the `codebase-design` and
  `software-design-philosophy` vocabulary: this is the deep module, and the API and app above it are
  deliberately thin transports (by @assistant)

- 2026-09-04: #44 landed the screen contract, so the domain verdict this card must carry has a
  shape: `apply_screens(candidates, screens)` returns one row per candidate with a code and a
  sentence per screen, and nothing is filtered until `Verdicts.select` is called. (by @assistant)
