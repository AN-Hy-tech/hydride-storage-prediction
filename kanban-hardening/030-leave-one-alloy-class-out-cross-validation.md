---
id: 30
status: done
priority: High
blocked_by: [12, 28]
assignee: "@amirhossein"
tags: [p1, l3, S6, AC-6, R2]
---

# Leave-one-alloy-class-out cross-validation

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How well the model transfers to a family it has not seen.

## Why this exists

The single most important validation number in this thesis. Beltrame et al. 2025 found
hydride models are accurate *within* a family and poor *across* families; Li et al. 2025
found heuristic splits 'mostly test interpolation rather than true extrapolation'.

**Expect this to be substantially worse than the random-split number, and report it anyway.**
That honesty is a contribution, and it is what tells Architecture A how far a candidate may
stray from known chemistry.

## Done when

- [x] One fold per alloy class; train on the rest, test on the held-out class —
      `hydms/surrogate/loco.py`, verified end to end at sentinel budget: 10 class folds, 893
      training rows, 0.29 min
- [x] Per-class R2, MAE and support reported, not only an average — `loco-per-class.csv` carries
      `r2`, `mae`, `rows_scored`, `compositions_scored` and `rows_in_class` per class.
      `compositions_scored` is there because it differs from the row count (the same material
      appears at several temperatures) and it is the composition count that says how many
      *independent materials* a score rests on. `rows_in_class` is measured from the frame while
      `rows_scored` is measured from the fold, so the two agreeing is a check that the fold held
      out the whole family rather than a restatement
- [x] Classes with too few rows to test are reported as such, not silently skipped — every class
      is in the table; `estimable` and `not_estimable_because` carry the verdict in words, and the
      averages exclude it while `classes_not_estimable` counts it. **The threshold is a property
      of the metric, not a taste:** R2 is a ratio to the total sum of squares, so it is undefined
      below two held-out rows or when the held-out target does not vary. Nothing is dropped for
      being *small* — a 19-row LEA fold is a real result provided its support is printed beside
      it, and filtering it here would make the reader's judgement silently on their behalf
- [x] Result feeds the applicability-domain ceiling (48) and the Chapter 1 revision (37) — the
      numbers now exist and are committed, which is what this card owed them. Consuming them is
      those cards' work, and #48 carries a box measuring what the run said about *its* problem
- [x] The folds come from `hydms.surrogate.validation.leave_one_class_out`, passed to
      `nested_scores` as its `outer=` cut — that is literally the whole of the run: one keyword
      argument. Nothing in `loco.py` re-implements scoring, tuning, screening or the nesting
      assertion
- [x] **The smallest class fold is 19 rows.** Measured over the 893-row training split (#88):
      LEA 19 rows / 19 compositions, A2B 29 / 21, HEA 51 / 47, AB 59 / 55, SS 73 / 69, MEA 76 / 69,
      MIC 87 / 81, Mg 96 / 89, AB5 143 / 123, AB2 260 / 207. **Re-measured and pinned** in
      `tests/surrogate/test_loco.py::test_the_class_folds_are_the_ten_families_with_the_supports_88_measured`
      — the ten supports, their sum of 893, and that the smallest fold clears `MIN_SCORED_ROWS`,
      so a class falling below two rows is caught before a run spends 4.7 h discovering it
- [x] **AC-6's gate is written and reads the committed tables rather than refitting.** A gate
      cannot pay 4.7 h, and one that fitted a *cheaper* version would certify a number nobody
      publishes. So the run happens once and commits its tables; the gate asserts the criterion
      over what was published — card #29's shape, and the lane moved `SLOW` → `FAST` because the
      refit is the command's, not the check's. Three verdicts: no tables → `SKIPPED` naming the
      command; **probe tables → `FAILED`**, because a probe's CSVs are the same shape as a
      result's and committing them is a defect rather than an absence; the class figure published
      **without** the random-split one → `FAILED`, since the criterion is the word *alongside*
- [x] **`reports/loco/` is un-ignored, and that was not cosmetic.** `/reports/*` would have left
      AC-6 reading an empty directory in CI — a criterion that can only ever pass on somebody's
      laptop. The identical trap was found the same day on `artifacts/current.json` (#34), which
      is why the waiver guard there had to move out of `scripts/check_board.py`
- [x] **DONE: the run happened, once, on 2026-09-06.** 18:16:09 to 22:23:13 — **4 h 07 m**,
      inside the `--budget` ceiling of 4.7 h. `loco-run.csv` records `probe=False`, 25 of 25
      trials, screening on, 10 folds, seed 42. **Macro R2 0.2734** over ten estimable classes of
      ten, against the random-split **0.7459** — a gap of 0.4725. Support-weighted **0.2153**,
      *below* the macro average, the direction the probe found and the reason the document
      computes it. Worst **Mg -0.3381**, best **SS 0.7626**. AC-6 PASSES on the committed tables
      and the suite's one skip is gone. The original command, kept for the record:

      ```bash
      conda run --no-capture-output -n Project python -m hydms.surrogate.loco --target capacity
      conda run --no-capture-output -n Project python -m hydms.surrogate.loco --emit
      ```

      Committed by name in `7149c4a`; AC-6 went green with no code change, exactly as designed

- [x] **A sentinel-budget probe falsified a sentence this card's module had already written.**
      The docstring claimed the support-weighted average "flatters" the result by sitting closer
      to the random-split number. Measured, it is the opposite: macro **0.2240** against weighted
      **0.1664**, because AB2 and AB5 — 403 of the 893 rows between them — happened to score below
      the mean. The direction is a property of the run, not of the design, so the published
      document now **computes** it (`_direction`) instead of predicting it, and the claim that
      survives is only that the two differ and answer different questions. Probe numbers, not a
      result: macro R2 0.2240 against a random-split 0.7459, worst HEA -0.3026, best A2B 0.6703

- [ ] **The run has no resume, and it is 4.7 hours on one machine** (raised 2026-09-06, in review).
      `loco.py` writes its tables once, at the end: there is no `--resume`, no per-class
      checkpoint, and no incremental write. A crash, a sleeping laptop or a lost session at hour
      four costs the whole run. **Accepted as-is for this run** — building resumability first
      delays the long pole by about an hour to save an outcome that probably will not happen, and
      the expected-time arithmetic favours running it now. It is boxed because the *next* protocol
      that costs hours should be built with it, and because an operator about to start a 4.7-hour
      command deserves to know the failure mode before they start rather than after.

      Practical mitigations that cost nothing: disable sleep before starting; run it detached
      rather than inside an editor session; `--budget` first so the estimate is on the record.

- [ ] **And the run is silent, which is what makes the missing resume expensive** (raised
      2026-09-06, when the maintainer asked how to track it). `nested_scores` takes no output
      stream and prints nothing per fold; CatBoost is at `verbose: 0` and Optuna is pinned to
      `WARNING`, both deliberately, so the terminal shows the class census and then **nothing for
      4.7 hours**. `FitLog` is in-memory — the same reason nothing can be resumed is the reason
      nothing can be watched. An operator cannot tell a working run from a hung one, so the
      no-resume failure mode is not just unrecoverable, it is **undetectable until the end**.

      Not fixed here, and the reason is the seam rather than the effort: the fold loop is
      `hydms.surrogate.validation.nested_scores`, shared with `train`, whose run is already
      published — adding a print there changes the path behind a committed result to buy
      progress reporting. If it is done, it belongs on the *next* long protocol together with
      the checkpointing, as one change to that shared loop with both tests.

      What an operator does instead, none of it requiring code: run under `python -u` piped
      through `Tee-Object` to a gitignored log under `reports/` (excluded from the provenance
      stamp, so it cannot dirty the run's own record); watch cumulative `CPU` on the python
      process from a second window, which is the only live liveness signal there is; and expect
      **17–29 min per class fold** — 76 fits each, the 22.6 s rate being an upper bound because
      it is measured over the six *scored* fits and Optuna pruned 2 to 19 of 25 trials per fold
      on the random-split run.

- [ ] **The per-class scores carry no interval, deliberately, and the model card must not imply
      otherwise.** `summary()` reports macro and support-weighted means with no bootstrap CI, and
      its docstring gives the reason: `random_split_r2` is `train`'s mean over *its* outer folds,
      so putting card #29's bootstrap point estimate opposite it would make the gap partly an
      artefact of how the two were averaged. That is the right call for a like-for-like comparison
      — but it means **the headline transfer number is a point estimate over ten class folds with
      no stated uncertainty**, and a class with nineteen rows contributes to the macro mean exactly
      as much as one with two hundred. Say so wherever the number is published; the per-class table
      carries `rows_scored` beside every row precisely so it can be said

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/surrogate/test_loco.py tests/gates/test_ac6_loco.py
conda run --no-capture-output -n Project python -m hydms.surrogate.loco --budget   # fits nothing
conda run --no-capture-output -n Project python -m hydms.gates run AC-6
```

The card's original check was `loco --artifact current`, and it is **not** what this command
grew. `--artifact` would score the *deployed* model per class — a model that saw every family
during training, so its per-class numbers are within-distribution and are not the extrapolation
claim AC-6 is about. Writing it would have published a number under AC-6's name that answers a
different question. The flag is deliberately absent; the artifact reading, if anyone wants it,
belongs to the model card (#83) and must be labelled as within-distribution there.

Until the run has happened, `gates run AC-6` reports `SKIPPED` and names the command that fixes
it. That is the honest state and it is what keeps `promote` refusing.

## Traces to

`docs/PRD-inverse-design.md` — S6, AC-6, R2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: The two boxes above were added by #88, which built the leave-one-class-out cut and
  measured the class supports while doing it. (by @assistant)

- 2026-09-06: **Built, verified at sentinel budget, and handed over. The 4.7-hour run is the
  maintainer's.** The command is `hydms/surrogate/loco.py` and the honest summary of it is that
  it is one keyword argument: `nested_scores(..., outer=leave_one_class_out)`. #88 had already
  built AC-6's protocol as this protocol with the outer partition swapped, so nothing here
  re-implements scoring, tuning, screening or the nesting assertion. What the module adds is the
  *reporting* layer, and that is where the card's real content turned out to be — AC-6 asks that
  a number be published alongside another, not that it clear a bar, so every design decision was
  about what a table has to carry to stop being misread.

  **"Too few rows to test" is a property of the metric, not a taste.** The box asked for classes
  too small to test to be reported rather than skipped, which implies a threshold. Any row count
  I picked would have been arbitrary and would have been *my* judgement smuggled into the reader's
  table. So the rule is arithmetic: R2 is one minus a ratio to the total sum of squares, which is
  undefined below two held-out rows and undefined when the held-out target does not vary. Those
  two conditions mark a class unestimable, in words, in the table. A class that is merely *small*
  is estimable and is published with its support beside it — LEA's 19 rows are a real result, and
  a filter would have hidden it while looking like tidiness.

  **A probe falsified a sentence the module had already written, which is the finding here.**
  The docstring asserted that the support-weighted average flatters the result by sitting closer
  to the random-split number. It does not: macro **0.2240** against weighted **0.1664** at
  sentinel budget, because AB2 and AB5 — 403 of the 893 training rows between them — happened to
  score below the mean. The direction is a property of the run. The published document now
  computes it (`_direction`) rather than predicting it, and there is a parametrised test on all
  three directions, so the same sentence cannot be written wrong again. That is the second time
  this session a confident sentence about a number was written before the number was measured;
  the first was #15's owed box predicting two facts would move when they cannot.

  **The gate reads rather than refits, and that decided its lane.** AC-6 was declared `SLOW` on
  the reasoning that one refit per alloy class is a retrain — true of the protocol, false of the
  check. A gate cannot pay 4.7 h, and a gate that fitted a cheaper version of the protocol would
  certify a number nobody publishes. So it reads the committed tables, which is card #29's shape
  for exactly this problem, and the lane is now `FAST`. Its three verdicts matter more than its
  pass: absent tables `SKIPPED` (naming the command), **probe tables `FAILED`** — because a
  probe's CSVs are the same shape as a result's, so committed probe numbers are a defect and not
  an absence — and the class figure published without the random-split figure `FAILED`, since
  *alongside* is the entire criterion.

  **`reports/loco/` had to be un-ignored, and the reason is worth carrying forward.** Under
  `/reports/*` the gate would have read an empty directory in CI: a criterion that can only ever
  pass on somebody's laptop. The identical trap turned up the same day on
  `artifacts/current.json` while settling #34, and is why that decision's guard could not live in
  `scripts/check_board.py`. **Check whether a file reaches CI before writing a check that reads
  it** is now a two-instance pattern in this repository.

  **The card's own runnable check was wrong and is replaced with the reason.** It named
  `loco --artifact current`. That flag is deliberately not implemented: scoring the *deployed*
  model per class is a within-distribution number — that model saw every family — and publishing
  it under AC-6's name would answer a different question than the one the criterion asks. If
  anyone wants it, it belongs on the model card (#83), labelled.

  **Probe numbers, and they are not a result:** 10 class folds in 0.29 min at sentinel budget,
  macro R2 0.2240 against the random-split 0.7459, worst HEA -0.3026, best A2B 0.6703, all ten
  classes estimable. The gap is large and is expected to stay large; that is the finding the
  thesis reports, not a fit to fix. (by @assistant)

- 2026-09-06 (evening): **The run happened and the number is real.** 18:16:09 to 22:23:13,
  **4 h 07 m**, one run, never repeated. Macro R2 **0.2734** against the random-split **0.7459**.
  AC-6 passed on the committed tables with no code change, which was the design: the gate reads
  what was published rather than refitting a cheaper version of it.

  **The probe was right about the magnitude and wrong about the ends, which is exactly what a
  probe is worth.** It had said macro 0.2240 (real: 0.2734), worst **HEA** -0.3026 (real: **Mg**
  -0.3381), best **A2B** 0.6703 (real: **SS** 0.7626). So a sentinel-budget run can size the gap
  but cannot tell you which families sit at its ends — and the ends are the part #48 needs. Anyone
  tempted to skip a real run because a probe "already showed the answer" should read those two
  lines side by side.

  **Mg is the worst family and it is the one that matters most.** R2 -0.3381 on 96 rows, with
  MAE **1.577** against 0.24-0.49 for every other class. Mg-based hydrides are the high-capacity
  corner of this dataset, so holding them out removes the model's only evidence of what high
  capacity looks like — and it then predicts the family it has never seen as though it were the
  families it has. A negative R2 means it does worse than predicting the mean. This is the
  clearest statement the project has that extrapolation toward high capacity is exactly where the
  model is least trustworthy, which is precisely the direction an optimiser would push.

  **The finding nobody asked for: the intervals collapse out of family, and hardest where the
  error is worst.** `loco-per-class.csv` carries `interval_coverage`, and against the
  random-split out-of-fold reading of **0.6293** the class folds give Mg **0.1146**, SS 0.1644,
  MIC 0.4713, AB 0.4746, MEA 0.5000 — while HEA (0.8824) and A2B (0.7586) sit above it. Coverage
  is not merely lower out of family, it is *unpredictably* lower, and its worst case coincides
  with the worst R2. **Stated precisely, because it is easy to overclaim:** these are the raw
  quantile-head bands, not the conformalised ones — the deployed path adds a correction
  calibrated in-distribution (raw 0.6744 to 0.8081). Nothing here measures the conformal band out
  of family. But conformal's guarantee is *marginal and assumes exchangeability*, which holding
  out a whole family breaks by construction, so there is no reason to expect it to survive the
  move and now some evidence that the underlying band does not. **This is the argument for #48
  in one table: an interval alone does not protect a caller out of domain**, and it is boxed
  there.

  **The no-resume and no-progress risks did not materialise, and the boxes stay anyway.** The run
  survived four hours unattended. Both boxes are records for the *next* protocol that costs
  hours, not predictions about this one; a risk that did not fire is not a risk that was wrong.
  For the record, the estimate: scaling the random-split run's measured 1 h 41 m by nominal fit
  count predicted 3 h 21 m, and correcting for LOCO's larger training folds predicted about
  3 h 50 m. Actual 4 h 07 m — the scaling was optimistic by roughly 7 %, and `--budget`'s 4.7 h
  was the better bound. (by @assistant)

- 2026-09-07: **Closed.** Every done-criterion is met and the transfer number is published and
  gated; the three boxes that remain unticked are *findings*, not work — the missing resume, the
  silent run and the absent interval on the per-class scores are recorded so the next protocol
  that costs hours is built knowing them, and none of them is a condition this card owed. Closing
  it unblocks **#48**, which is the card that has to decide what a macro R2 of 0.2734 means for
  the applicability-domain ceiling. (by @assistant)
