---
id: 14
status: done
priority: P4
blocked_by: [13]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# CleanLab screening as a data-layer stage

**Stage S2 — Data layer** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** Which **training** rows are label-suspect, and the record of
> what was removed. Held-out labels are not this module's to touch.

## Why this exists

The audit's fourth broken link: `Boruta_FeatEng.py:23-25` reads `data/splits/` — the
**pre-CleanLab** splits — while its own comment claims it reads managed data. The effective
pipeline bypassed CleanLab entirely, contradicting `README.md` step 4 and `REPORT.md` 3.2.

The domain memo supplies the physics: sloping plateaus make measured capacity depend on
measurement pressure, and pressure is absent from the dataset. That is a better account of
what CleanLab detects than 'some experiments are wrong'.

**Amended for Phase H — scope narrowed, and this is the important part of the ticket.** The archival
`CleanLab.py` does not remove rows. At `:90`, reached for validation and test at `:96-97`, it does this:

```python
managed_df['target'] = np.where(outliers_mask, y_pred, y)
```

**Every held-out label whose residual exceeds the threshold is replaced by the model's own
prediction.** Points so replaced have residual exactly zero by construction, so any R² or RMSE computed
downstream is measured partly against synthetic targets. That is leak **L3**, and it is more severe
than any of the three the PRD names. It is inert today only because nothing reads `CleanLab.py`'s
output — and this ticket, as originally written, is the one that would have wired it in.

So: this stage may **drop or reweight training rows only**. Validation and test targets are immutable
as they pass through it. Porting the `manage_outliers` behaviour is not in scope and would be a defect.

## Done when

- [x] Feature selection (24) consumes CleanLab's output, closing the bypass
- [x] **The stage drops or reweights training rows only** — no label is ever rewritten, on any split
- [x] **Validation and test targets are byte-identical before and after this stage** — asserted, and
      covered by the L3 sentinel in ticket 71
- [x] Held-out **feature** values are byte-identical too. The recovered `Outliers_Management.py:60-72`
      clipped val/test features using their own residuals — leak L10, the same defect on the other
      side of the table. If this stage grows any outlier handling, that is where it comes back
- [x] The **L3 sentinel** and the **L10 sentinel** (ticket 71) are wired to this module — `live`
      checks in `hydms/qa/sentinels.py` calling `hydms.qa.assert_holdout_unchanged` on the real
      stage, once for `y` and once for `X`. Gate HG-1 goes red once `hydms/data/screening.py` exists
      without them
- [x] Removed rows written to a report, not silently dropped — **with their reason and their
      label-quality score, not their residuals.** A residual needs a fitted model and a feature
      matrix; the stage has neither, and inventing one here is how `CleanLab.py` ended up fitting
      a `HistGradientBoostingRegressor` inside a data-cleaning script. `Screening.report()` carries
      label, kind, split, removed, quality, reason; `Screening.counts()` carries the per-split
      totals
- [x] Counts recorded per split for the Chapter 1 revision (37)
- [x] Module docstring records the counter-caution: removing real measurements in underrepresented regimes flatters metrics
- [x] **Decide what happens to the one byte-identical duplicate row.** `hydride_data.csv` rows 687
      and 694 are identical across all six columns — `La0.9Ce0.1Ni5`, AB5, Extracted, 1.40 wt%,
      373 K, same citation URL. One measurement recorded twice. This stage is the only one entitled
      to drop a row, so the decision is yours: drop it, or keep it and say why. It is *not* one of
      the six genuine replicates — those are seven `(Composition, temperature(K))` pairs in total,
      six of which carry different targets from different citations and belong in the data (measured
      by #10, which refuses to key on that pair for exactly this reason). Left in, it is one
      material contributing twice to whichever split it lands in; under #87's canonical key both
      copies land in the same split, so this is a weighting question, not a leak

- [x] **One row's formula is missing a decimal point, and nothing has ever noticed.**
      `Mg0853Ni0.125La0.022` (one row of `hydride_data.csv`) parses as magnesium with an amount of
      **853**, so its atomic fractions are Mg 0.9998, Ni 1.5e-04, La 2.6e-05 — essentially pure Mg.
      The intended composition is plainly `Mg0.853Ni0.125La0.022`, since 0.853 + 0.125 + 0.022 = 1.000
      exactly. It passes #9's schema (a positive amount on a real element), it passes CBFV, and its
      feature vector is that of pure magnesium rather than of a Mg-Ni-La alloy. Found by #87, whose
      key surfaced it as the only fraction in either raw file below 1e-4. Decide what screening does
      with it — flag, drop, or correct in a documented correction layer, since the raw files in
      `data/raw/` are kept byte-identical to their source (#107) — and say so out loud; do **not** repair it silently in a loader

- [x] **Both decided rows land in `train` under #13's split, so the stage is entitled to act.**
      Measured, not assumed — and the general case is a real code path with a test: a finding on a
      held-out row is recorded with `removed=False` and the row stays exactly where it is.
      Removing it would be the mirror image of L3, improving a held-out set by touching it
- [x] **The duplicate: dropped, and found structurally.** `DataFrame.duplicated(keep="first")`
      rather than a hard-coded row number, so a new duplicate is found rather than missed and the
      decision survives a re-export. There is no information in the second copy and keeping it
      weights that one measurement double in its split and in every fold
- [x] **`Mg0853Ni0.125La0.022`: dropped from training and named, not corrected.** The correction
      is unambiguous (0.853 + 0.125 + 0.022 = 1.000 exactly) and would be the better fix — but it
      cannot happen *here*. The canonical key, the split and the class join are all computed
      upstream, so by the time screening sees the row it has already been keyed and split as
      essentially pure magnesium. A correction layer must sit above `hydms/data/load.py`, whose
      stated contract is that it normalises nothing, and moving that line is a decision rather
      than a repair made in passing. **#9 decided against it on 2026-09-12** — the loader
      normalises nothing, and the row stays dropped-and-named rather than corrected. `MALFORMED_FORMULAE` declares the string and
      the reason; a test asserts the string is still in the file, because a declaration about a
      row that no longer exists is a decision nothing enforces
- [x] **Reweighting is declined, with a reason.** The card allows "drop or reweight". The only
      weighting the archival pipeline had is `Catboostmodel.py:516-518` —
      `np.where(np.expm1(y) > 3, 2.0, 1.0)`, target-conditioned with a hand-tuned threshold, which
      is leak **L12**. Choosing a weighting policy is #26's decision, made with the surrogate in
      view; a weight vector invented here would be a second answer. The stage drops
- [x] **No label is rewritten on *any* split, which is stronger than L3.** `CleanLab.py` rewrites
      training labels too, at `:64` and `:80` — `cleaned_y_train` is `predicted_label` wherever
      CleanLab flagged an issue. That is not L3, since a training label is not a measurement
      anyone scores against, but it is the same reflex. `screen` only ever *selects* rows, and
      asserts it: `assert_holdout_unchanged` is called a third time over every surviving row
- [x] **The bypass is closed, and CleanLab is now called from one place.** `label_issues(X, y)`
      is that place — a function of this module, not of #24's, because *which rows are
      label-suspect* is what this card owns; #24 only supplies the matrix and the rows. It
      cross-fits `RandomForestRegressor(max_depth=selection.boruta_max_depth)` so the model
      judging labels is the same family as the one judging features rather than a second,
      unrelated choice, and it is deterministic under `pipeline.yaml`'s seed — measured, the
      same 27 of 893 flagged twice. **It returns two of CleanLab's four columns.**
      `find_label_issues` also returns `predicted_label`, which is `CleanLab.py:90`'s leak in
      raw form; there is now no object in this module a caller could reach one through, which
      is stronger than a rule saying not to use it

- [x] **Three curated rows are physically impossible, and the stage already removes the two it
      is allowed to touch** (added 2026-09-07 by #48; decided 2026-09-12). A composition's
      hydrogen capacity is bounded by `H/M_max * 1.008 / mean atomic mass`, and under the most
      generous defensible H/M these three exceed their own bound:

      | formula | class | split | reported wt% | implied H/M |
      |---|---|---|---|---|
      | `Ce1Ni3Cr2` | AB5 | train | 5.19 | **3.606** |
      | `Ce1Ni4Zr1` | AB5 | train | 4.94 | **3.807** |
      | `Ce1Ni4Cr1` | AB5 | val | 4.73 | **3.339** |

      `LaNi5H6` is H/M **1.0**. No AB5 intermetallic holds three and a half hydrogens per metal
      atom, so these are transcription or unit defects rather than unusual materials. Two of the
      three cite the same paper (`10.1016/j.jallcom.2006.05.013`).

      **The decision: no physical-plausibility filter in the data layer. The ceiling stays an L4
      screen.** What settled it was measuring the premise instead of implementing the box.
      Running this stage's real path over the 893 training rows:

      | formula | kind | label quality | rank |
      |---|---|---|---|
      | `Ce1Ni3Cr2` | `label-quality` | 3.07e-08 | **1 of 893** |
      | `Ce1Ni4Zr1` | `label-quality` | 3.42e-08 | **2 of 893** |
      | `Ti1.1Cr1Mn1V0.255Fe0.045` | `label-quality` | 4.26e-04 | 11 of 893 |

      **CleanLab already removes both**, and ranks them the two least plausible labels in the
      training set — knowing nothing about hydrogen, mass, or the ceiling. So a declared
      ceiling-based drop would change nothing for the two rows it could legally act on, and for
      the third it would *break* this stage's contract: `Ce1Ni4Cr1` is in `val`, and a finding
      on a held-out row is reported with `removed=False` and left where it is. Acting on it is
      the mirror image of L3, which is the leak this whole phase exists to remove.

      Two things worth keeping, neither of which becomes a rule:

      - **The independent agreement is evidence, not a reason to merge the two mechanisms.** The
        ceiling is arithmetic over element masses at L4; CleanLab is a cross-fitted judgement at
        L1. They reached the same two rows by unrelated routes. Collapsing them into one check
        would cost that corroboration and would make the data layer import from L4, inverting
        the layering the board is cut along.
      - **The quality score preserves the distinction the ceiling test encodes.** The fourth
        over-ceiling row, `Ti1.1Cr1Mn1V0.255Fe0.045`, is Sahlberg's limit to within a rounding —
        a real material, over by less than 0.01 — and it scores four orders of magnitude higher
        than the two defects and ranks 11th rather than 1st or 2nd. That is the screening
        docstring's own counter-caution holding up: a flagged row is often a correct measurement
        the features cannot express. **Do not turn 3e-08 into a threshold.** It is an
        observation about this data at this seed, and nothing in the code reads it.

      `tests/screens/test_applicability.py` still asserts the set of four over-ceiling rows
      exactly, and still should: it is measuring the **curated record**, which is unchanged.
      Screening marks and drops per fit; it does not edit the curated file.

- [ ] **An impossible label sits in `val` and is not removable** (raised 2026-09-12, boxed on
      #83). `Ce1Ni4Cr1` at 4.73 wt% is H/M 3.339, and it is in the validation split, so it feeds
      early stopping and every validation figure this project reports. L3 forbids touching it,
      and that is the right rule — but a number computed partly against an impossible label is a
      stated limit, not a clean metric. It belongs in the model card's limits section rather than
      in a silent removal. **Boxed on #83**; this card carries no further action. Not an unfreeze
      condition.

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/data/test_clean.py -q
conda run --no-capture-output -n Project python -m pytest tests/leaks/test_l3_l10_holdout_immutability.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-09-03: Box added by #87. The canonical key made one bad row visible: `Mg0853Ni0.125La0.022` is
  a missing decimal point that parses as Mg-853, and it is the only atomic fraction below 1e-4 in
  either raw file. It is a features defect rather than a label defect, so it is not what CleanLab
  detects — but this is the stage that decides what happens to a row nobody can trust (by @assistant)

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Amended for Phase H. The audit found `CleanLab.py:90` overwrites validation and test ground-truth
  labels with the model's own predictions (leak L3) — worse than any leak the PRD names, and inert only
  because its output is an orphan. This ticket was the one that would have connected it. Scope is now
  explicitly drop-or-reweight, training rows only (by @assistant)

- 2026-09-03: Box added by #10. Rows 687 and 694 of `hydride_data.csv` are byte-identical across
  all six columns — one `La0.9Ce0.1Ni5` measurement at 373 K recorded twice, same citation. Found
  while measuring whether `(Composition, temperature(K))` could serve as the merge key; it cannot,
  and six of the seven repeats on that key are genuine replicates. This one is not, and this stage
  is the only one entitled to drop a row. (by @assistant)

- 2026-09-05: **Closed by #24, in the same commit that opened it.** `hydms.data.screening.label_issues`
  makes the CleanLab call and `hydms.surrogate.selection.select_features` consumes it, so the
  `Boruta_FeatEng.py:23-25` bypass is gone: the rows the three selection stages fit on are the rows
  this stage left. Two things worth keeping.

  **The call belongs here even though only #24 can make it.** The tempting shape was a CleanLab
  helper inside the selector, since the selector is what has a feature matrix. But the question
  *which rows are label-suspect* is this card's `Owns` line, and splitting it across two modules
  would have put the judgement in the surrogate layer and the record of it in the data layer.
  `label_issues` therefore takes a matrix and a target — it is impossible to point at the whole
  dataset by accident, because it has no split argument and no loader — and `screen` stays the
  only thing entitled to act on the verdict.

  **It runs inside the folds, not once over the training split.** That was not obvious: this is a
  data-layer stage and #15's golden tests pin `screened.rows_out` as a single number. But screening
  fitted over the whole training split would mean an outer fold's training rows were chosen with
  that fold's held-out rows in view — L6's shape one level down — so the selector calls it on the
  rows *it* owns. The per-split counts #37 and #15 read still come from one pipeline-level `screen`
  call over the whole frame; that call describes the dataset, and the fold-level call is the one
  that changes a model. Re-measure `rows_out` and `removed` on #15 against the pipeline-level call.
  (by @assistant)

- 2026-09-03: Contract and structural screening landed; **status `doing`, not `done`** — the
  CleanLab call itself needs #24's feature matrix. `hydms/data/screening.py` — `screen`,
  `Screening`, `Finding`, `MALFORMED_FORMULAE`; 18 tests in `tests/data/test_clean.py`. The
  **L3 and L10 sentinels are wired**, so `audit()` now reports L3, L8, L9 and L10 green — the
  four the runbook's S2 exit check names. Three things this card taught:

  **The live hook needed no invented heuristic, only the strongest possible input.** CleanLab
  cannot run without features, so the obvious move was to stand in a plausible scorer. Instead the
  hook passes `label_issues = True` for **every** row — a method that condemns the whole dataset.
  Under it a correct stage drops every training row and leaves every held-out row byte-identical,
  which is maximal pressure on the contract and zero invention. Cached, like `_l9_real_frames`.

  **Both decided rows landing in `train` is luck, so the held-out path is a real code path.** If
  the duplicate had landed in test, the contract would have forbidden removing it. That case is
  implemented and tested rather than left to be discovered by a future re-split.

  **The correction that is right is in the wrong place.** `Mg0.853Ni0.125La0.022` is plainly what
  was meant, and screening is downstream of keying and splitting, so a correction applied here
  would arrive after the row had already been keyed and split as pure magnesium. Dropped and
  named instead, with the correction-layer decision boxed on #9 rather than half-made here.
  (by @assistant)

- 2026-09-12: **The box asked for a filter; the measurement said one already exists.** The card
  posed its own question well — "whether CleanLab already flags them" — and answering it first
  cost one run and removed the entire implementation. CleanLab ranks the two impossible training
  rows **1st and 2nd of 893** on label quality, with no notion of hydrogen, mass, or a ceiling.

  Two things worth keeping. First, the *third* row is the one that teaches the rule: it is in
  `val`, so the correct action is none, and a filter built for the two train rows would have been
  reached for the third by whoever wrote it next — which is L3 in reverse. A finding's split is
  part of the finding. Second, the fourth over-ceiling row is a **real material** at the physical
  limit and CleanLab flags it too, four orders of magnitude higher and eight ranks later. The
  quality score happened to preserve a distinction the arithmetic makes explicitly. That is
  corroboration between two unrelated mechanisms, and it is worth more than either alone — which
  is the argument against collapsing them into one check, quite apart from the layering. (by @assistant)
