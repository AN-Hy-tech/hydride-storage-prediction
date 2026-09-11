---
id: 76
status: done
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

- [x] `hydms/delivery/predict.py` exposes `predict_capacity()` and nothing else of substance
- [x] An `ArtifactBundle` — model, feature contract, conformal calibration, the screens and their references —
      loads once, is immutable, and carries the artifact version
- [x] ~~The scaler is **used**, never fitted, on this path~~ — **the scaler is not used on the
      prediction path at all (from #26 and #28).** CatBoost splits on thresholds and `FittedScaler`
      is affine, so #26 fits on raw features and records that in `QuantileModel.feature_names`;
      applying the persisted scaler on the way in feeds the model a matrix it was never fitted on.
      This box is right that it is never *fitted* and wrong about where it is used: its consumer is
      #48's distance-based applicability domain, which reads it with
      `hydms.surrogate.scaler.scaler_from(bundle)`. `hydms/surrogate/predict.py` proves the
      negative rather than promising it — `test_the_stored_scaler_is_never_applied` stores a scaler
      that raises on `transform` and demands identical numbers
- [x] **The surrogate half of the bundle already exists: wrap it, do not re-load it (from #28).**
      `hydms.surrogate.predict.load_surrogate(version=, store=)` returns a frozen `Surrogate` that
      holds the model, the correction and the featurisation contract, is pinned to one version,
      refuses a version whose gates are unestablished, and is memoised by `(store, version)` — the
      immutability this box asks for. `ArtifactBundle` is that plus the AD reference set and the
      ElMD reference set. A second unpickle of the same booster is what the "loads once" box is
      trying to prevent, and calling `artifacts.load` again here is how it comes back
- [x] **"No global mutable state" needs a stated exception, or it is already false (from #28).**
      `hydms.surrogate.predict._LOADED` is a module-level memo of immutable, content-addressed
      objects; the promotion pointer is deliberately not cached, so rollback still takes effect on
      the next call. Decide whether this layer inherits that cache or holds the bundle itself, and
      say which in the ADR (#85) — two caches for one artifact version is the failure
- [x] Feature column order is asserted against the contract, not assumed
- [x] **An unparseable formula has no screen code, and `INDETERMINATE` is the answer (from #75).**
      The delivery vocabulary is `ADMITTED` + the union of the configured screens' `reasons` +
      `INDETERMINATE`, so "this string does not parse" and "the `oliynyk` table has no mass for this
      element" have no code of their own — and `featurize` raises before any screen has seen the
      candidate. Two orderings work and this card picks one: **screen before featurising**, or catch
      `FeaturisationError` and map it to a `Refusal` carrying `INDETERMINATE` with the parse error's
      own sentence as the explanation. #48's applicability screen already emits `INDETERMINATE` for
      exactly this case, so the second keeps one vocabulary; the first keeps one code path. Whichever
      is chosen, say so in the ADR (#85)

- [x] **A missing value in the formula column is not always unparseable, and one spelling of it is
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
- [x] The domain verdict (#48) and the ElMD distance (#49) are computed on every call
- [x] Predictions are returned in wt%, back-transformed, with the interval transformed consistently
- [x] No absolute path, no network call, no global mutable state (one stated exception, above)
- [x] Ten known training alloys reproduce the trained model's predictions on those rows (AC-4)
- [x] **The trained-temperature bound is `hydms.screens.temperature_window()` (#44) — used, not
      re-written.** This layer owns no comparison against `domain.temperature_min_k/max_k`: it runs
      the screens and reads the verdict, so the refusal path and the screening path cannot disagree
      about what is in range. Read the domain verdict off `Verdicts`, and note that a screen may
      answer `INDETERMINATE`, which is a refusal and not a pass.

- [x] **Decide whether the domain reference is pinned into the bundle** (added 2026-09-07 by
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

- [x] **Decide whether `delivery_screens()` gains the novelty screen, and accept what it costs**
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

- [x] **The rule that turns several screen verdicts into one code and one sentence already exists
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

- 2026-09-11: **Closed. Three decisions were owed and all three turned out to be forced or already
  paid for, which is the finding.**

  **The INDETERMINATE ordering was not a choice.** The card offered "screen before featurising" or
  "catch `FeaturisationError` and map it". The first does not exist: `ApplicabilityDomain` judges a
  **prediction**, so it cannot run before one exists, and screening first would have meant two
  passes and a rule for merging their verdicts — a second composition rule, the exact defect #90
  exists to make visible. The path is null-check, featurise, predict, screen, resolve, answer, and
  a parse failure comes back as `INDETERMINATE` carrying the featuriser's own sentence.

  **The novelty screen is in `delivery_screens()`, and the cost the card warned about was already
  paid.** The stated price was making an optional extra mandatory — but `pyproject.toml` already
  says, in its own words, that `novelty` is "**not** a fit-time-only dependency, and CI installs
  it… ElMD is on the prediction path that AC-7 obliges to report a distance", and this project is
  GPL-3.0-or-later *because* ElMD is. So the only thing the screen's absence bought was a
  deployment where `PredictionResult.novelty` is permanently `None` — a field whose documented
  meaning is "not measured" quietly becoming "never measured". CI installs the extra, so no test
  would ever have shown the difference; only a deployment would, by answering AC-7 with a blank.
  The sequence #90 predicted then ran exactly as designed: the vocabulary widened on its own,
  `check_vocabulary` went red naming `beyond-known-chemistry` as declared-and-unreached, a probe
  was added, the byte-identity test went red, and `--emit` closed it. The page gained a row and a
  **sharper sentence for `unreadable-formula`** — #49's cross-check names the offending symbol
  where the domain screen could only say the ceiling was uncomputable.

  **The reference is digested, not pinned, and the binding is #91's.** Pinning is unavailable to
  `v1`/`v2`: a manifest is sealed when written and a re-save to add a field would look like a
  promotion. So the bundle does the half available today — it digests the reference **as loaded**
  and reports it (`ArtifactBundle.reference_digests`, SHA-256 per screen, duck-typed on
  `reference.to_json()` so the temperature window is absent rather than empty) for #78's
  `/v1/model` to state. The fit-time *binding* is boxed on #91, marked not an unfreeze condition.
  Both references answered the same way, as the card required.

  **The null-check box was aimed at a symptom #49 had already fixed.** Measured rather than
  implemented — every object null (`None`, `nan`, `pd.NA`, `pd.NaT`) is refused at *three*
  independent guards before any parser sees it, and every stringified null (`"nan"`, `"<NA>"`,
  `"None"`, `"NaT"`, `"N/A"`) is refused by the grammar, which names the offending character. A
  null check here would have duplicated three guards. **`"NaN"` is the sole survivor and must not
  be guarded**: it parses to sodium-plus-nitrogen in *both* parsers, so a blocklist here would
  refuse a real material. The obligation moves to the boundary that turns a missing value into
  text — #84's CSV reader and its `na_values` — and the measurement is pinned by a test that goes
  red naming the spelling that got through.

  **Two functions moved rather than being copied**, as the card's last box required.
  `resolve()` went to `contract.py` (it needs neither pandas nor the screens — it reads
  `ScreenVerdict`, the contract's own type) and `_verdicts_for` became
  `predict.screen_verdicts()`. The alternative was a production module importing
  `hydms.delivery.refusals` — a document generator with twelve probes and a Markdown writer in it
  — to borrow two functions. `refusals.py` now imports *them*, which makes the page a report on
  the delivery path rather than a thing beside it. One test moved with them:
  `resolve(())` raises `ContractError` now, not `CatalogueError`.

  **A stand-in in #90's tests had gone green for the wrong reason.** `_Extra` declared
  `beyond-known-chemistry` as its fictional "code the contract does not declare"; the moment the
  novelty screen landed, that code became real and both vocabulary-direction tests were asserting
  nothing. Re-aimed at `smells-wrong`, which no screen can overtake.

  **"Loads once" is worth 47 ms, not just AC-4.** Measured: `load_config()` is 14.4 ms and each of
  the three screens loads its own, so rebuilding them per call costs ~47 ms against ~4 ms to
  featurise one candidate. `delivery_screens()` therefore takes an optional `cfg` and the bundle
  holds the built screens. Its docstring's reason for *not* being a module constant still stands
  — a constant freezes whichever config was loaded first — and a bundle is the thing that may
  legitimately hold them, because it is already pinned to one version and `clear_cache()` drops it.

  **One guard was added that the card did not ask for.** `applicability_domain()` reads the median
  head from *config*'s `model.quantiles`; the artifact was fitted with its own. If they disagreed,
  the screen would find no prediction column and silently fall back to judging feature spans alone
  — dropping `above-physical-ceiling` and `out-of-domain`, the two rules that bound the number
  itself. That is a silent weakening of the guard rail the phase exists to install, so
  `load_bundle` raises `DeliveryError` instead.

  **One code is declared, documented and unreachable through this function, and it is stated
  rather than hidden.** `untrusted-family` needs an alloy-class label and a novel composition has
  none; supplying an unknown one would make the screen answer `indeterminate` for every novel
  candidate — the entire point of the exercise — for the wrong reason. Boxed on #77, which owns
  reachability, and pinned by a test here so a reader of `docs/REFUSALS.md` is not left to infer it.

  25 tests, `tests/delivery/test_predict.py`, 5.0 s. 251 in `tests/delivery` + `tests/screens`,
  14 s. Fast lane (`pytest -m "not slow"`) **1334 passed, 4 deselected, 872 s** — up from 1308 at
  #90, which is these 25 plus the thirteenth refusal probe. ruff and mypy clean. **Not run against
  a real artifact**: `v2` records no gate run, so `load_surrogate` refuses it — correctly, and
  that is #34's to close. (by @assistant)

- 2026-09-11: **QA pass. The one guard this card added was aimed one step away from its subject,
  and it was guarding one of the two columns it needed to.**

  `_check_heads` existed for a real and well-argued reason: `ApplicabilityDomain` is deliberately
  **partial** — it judges whichever of its signals a frame carries, because a caller screening a
  curated frame has an alloy class and a caller screening a prediction frame does not — so a
  column it cannot find does not raise, the rule simply does not run, and the screen answers
  `admitted` because nothing judged. It is the only screen in the set that can do that; the
  temperature window and the novelty screen both raise `ScreenError` on a missing column. A bundle
  is the first object that knows both what the screens will look for and what `_candidate` will
  write, so this layer is the only place the two can be made to agree.

  **It compared config's median head to the artifact's, and never read the screens it was handed.**
  Those are the same value on the default path — `load_bundle` builds the screens from that very
  config — which is precisely the path where the check is redundant. On the path where it could
  matter, an explicit `screens=` (a documented deployment parameter, and how #78 and every test
  here assemble a bundle), the configuration is no longer evidence about what the screens will
  read. Measured: a bundle assembled with the domain screen aimed at `q0.42` loaded without a
  murmur. The function already took `screens` and already iterated them — but only to compose the
  error message, never to decide.

  **And `width` had no check at all, which cost the third rule.** `high-uncertainty` is the only
  rule that reads the *band* rather than the number — the interval this function is about to
  report. `"interval_width"` is spelled independently in three places (`surrogate.predict`,
  `WIDTH_COLUMN` here, and the domain factory's own default), and a screen aimed elsewhere loses
  the rule in silence. Measured: a bundle with `width="band_width"` answered `PredictionResult`
  with `domain: admitted`, and nothing anywhere in the answer said the band had gone unjudged.
  That is the same silent weakening the median-head check was written against, one column over.

  `_check_columns` replaces it: it reads each screen's own `prediction` and `width` and requires
  them to name the columns `_candidate` actually writes, keeping `config` only to *explain* a
  mismatch (naming `model.quantiles` when the screen is the configured one tells a reader which
  end to move). `alloy_class` is the third optional input and is deliberately **not** required —
  that absence is this card's own decision, and it now has a test saying so, because a reader of
  `_REQUIRED_COLUMNS` would otherwise see two of three and wonder.

  **Two findings went to #77 rather than being fixed here**, both *wrong words* rather than wrong
  numbers. A formula that is not a string is told "the formula is empty" — false about the input,
  reachable through `from_dict` from any JSON or CSV transport, and an asymmetry visible within one
  `__post_init__`, since the temperature field one line below distinguishes its two arms. And
  `docs/REFUSALS.md` catalogues the *screens'* sentence for `unreadable-formula`, which this path
  cannot produce: `featurize` raises first, so a typed `LaNi5Xx2` comes back with the featuriser's
  sentence and zero verdicts. Both are the entry-point question #77 already owns for
  `untrusted-family`, found on two more rows.

  28 tests here now, 4.9 s. Fast lane (`pytest -m "not slow"`) **1337 passed, 4 deselected,
  643 s** — 1334 plus these three. ruff and mypy clean; gates 6 passed / 6 skipped, HG-1 green.
  (by @assistant)

- 2026-09-11: **The glossary still said this card was unbuilt, and nothing could have told us.**
  `CONTEXT.md`'s **Prediction** entry carried a *"State of the term"* block reading "**the
  domain-verdict half is not built yet** (cards #48, #49, #75, #76, gate HG-2)" — false on all
  four counts the moment this card landed, since `PredictionResult.interval` and `.domain` have no
  defaults and cannot be `None`. `grep -rln CONTEXT.md tests/ scripts/ hydms/` returns nothing: no
  test, no gate, no `--emit` reads that file, and `check_board.py` only resolves its links. So the
  one document written for a reader outside this room is the one document with no guard on it.

  Corrected in place, and the correction keeps the distinction the block existed to make: both
  halves are enforced **at the delivery layer**, while `hydms.surrogate.predict` alone still does
  not refuse an out-of-domain candidate — so "prediction" in the glossary's sense names what
  `predict_capacity()` returns, not what the surrogate does. What remains is #77's, and the block
  now says so.

  **`Artifact bundle` was added as a term**, beside `Artifact version` where the conflation would
  happen. A version is a sealed directory; a bundle is that plus the screens, their references and
  the digests of those references — and the two differ in exactly the way that matters twice over:
  the version is sealed and the reference is not (hence `reference_digests`, with the fit-time
  binding owed by #91), and the bundle is the only object that knows both what the screens read
  and what `_candidate` writes (hence `_check_columns` living there and nowhere else).

  The gap is now an anti-pattern in `CLAUDE.md` and a step in the end-of-card ritual, because the
  fix for a document nothing tests is a habit, not a check. (by @assistant)
