---
id: 83
status: doing
priority: High
blocked_by: [29, 30, 82, 89, 103, 105]
assignee: "@amirhossein"
tags: [ph, l6, S6, R4]
---

# Model-card page: honest metrics and stated limits

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** What the model is, how well it actually does, and the three ways a reader is most likely to overstate it.

## Why this exists

The interface is where a reader will form a belief about how good this model is. If the
only numbers on offer are the random-split ones, they will form the optimistic belief — the same one
`REPORT.md` published and the artifacts in this repository contradict.

This page is the counterweight, and it must survive contact with a reader who does not want to read it.
Three overstatements to pre-empt: the random-split number as *the* number, a material wt% compared to a
DOE system target, and the published figures inherited as though nothing had changed.

## Done when

- [x] Random-split metrics and **leave-one-alloy-class-out** metrics shown together, at the same scale
- [x] Bootstrap confidence intervals shown, not just point metrics
- [x] The training data described: rows, unique canonical compositions, alloy families, element coverage,
      temperature range
- [x] The applicability domain stated in terms a reader can apply to their own candidate
- [x] **The material-versus-system caveat** — comparing a material wt% to a DOE onboard-storage target is
      a two-step overstatement
- [x] A link to `docs/REPORT-RECONCILIATION.md`, so the previously published figures are not silently inherited
- [x] The known limits stated plainly, including no pressure data and therefore no reversible-versus-maximum
      capacity distinction
- [x] The artifact version and training date

- [x] **State the two descriptor-level filler values (from #18 and #19).** `dev_Gordy_electonegativity`
      cannot be computed for 266 of 1,279 rows from the citable Oliynyk edition, and
      `dev_voro_coord_divi_mol_vol` rests on `voro_coord = 1.0` for gadolinium — a placeholder, not
      a measurement: every other element in the JARVIS table sits between 3 and 12, and Gd is hcp
      with twelve nearest neighbours. Gd appears in **18 of the 1,279** rows. Neither is a bug and
      neither moves parity; both are limits a reader forming a belief about the model should be
      told, in the same paragraph as the no-pressure-data limit

- [x] **Two limits this card owes, both measured and both already public (from #25).** First, one
      of the 14 declared features rests on filler: the JARVIS table stores `voro_coord = 1.0` for
      `Cs` and `Gd` where every other element is 3 to 12, and gadolinium is in **18 of the 1,279
      curated rows (1.4 %)**, so `dev_voro_coord_divi_mol_vol` is computed from a placeholder for
      those rows. #25 kept the feature — all five folds selected it, and hand-removing a
      unanimously-selected feature after seeing the result is the decision this phase exists to
      remove — on the condition that the model card states it. Second, **the feature set is not a
      stable object**: every one of the 21 candidates was selected by some fold and only 14 by all
      five, so "the model uses these 14 features" is a statement about a consensus, not a discovery
      about hydrogen storage. `reports/feature_selection/old_vs_new.md` is the source for both

- [x] **Three R² values, and a sentence that says which is which** (raised 2026-09-06). The card
      already asks for random-split and leave-one-class-out side by side; a third reading now
      exists and is easy to conflate with the first. **The procedure** scores R² 0.7481
      [0.6889, 0.7985] wt% out-of-fold over five models (`reports/model/evaluation.md`). **The
      deployed model** — one model, scored once on 254 held-out `test` rows — scores R² **0.7071**,
      RMSE 0.5420, MAE 0.3117. That second figure is computed by gate AC-1 as a side effect of
      proving reproducibility. **Publishing it moved to #103 on 2026-09-24** (the maintainer's call,
      so #37 would not wait on #82's Streamlit pin). It is committed in
      `reports/model/artifact-score.csv`, generated from the sealed gate record. This page reads it
      from there and owes only the *showing*. `evaluation.md` promises it in its own words ("the
      artifact reading … is a claim about *a model*, and it arrives with card #34"), and #103 kept
      the publishing half of that promise. Report it beside 0.7481 with the reason they differ:
      the deployed model grows on **701** rows where each CV fold was cut from 893

- [x] **The near-ambient temperature bin is the weakest and the table already says so** (raised
      2026-09-06 from the committed `reports/model/evaluation-subgroups.csv`, out-of-fold, wt%):
      **(195, 293] K → R² 0.187, 95 % CI [−0.012, 0.423]** — the interval includes zero — against
      0.657, 0.717, 0.757 and 0.772 for the four warmer bins. That is the regime a practical storage
      material has to operate in, and it is where the model is worst. It is not a defect, it is a
      result, and it is sitting in a committed CSV that no prose mentions. State it in the limits
      with its confidence interval, not as a rounded point estimate

- [x] **The band is wide relative to the physics, and that is the honest reading.** The calibrated
      interval averages **0.8630 wt%** at ~80 % coverage — about ±0.43 wt%. Intermetallics generally
      deliver under 2 wt% usable capacity under practical pressure and temperature swings, so the
      band is a large fraction of the signal for the family this dataset is densest in. Read
      correctly it says the model discriminates **between families rather than between fine
      composition tweaks within one**, which for a screening tool feeding an optimiser is
      acceptable; read carelessly it says the model is precise. Pair it with the existing
      not-a-constant caveat (`expm1` is convex, so `+0.037355` in `log1p` space is a wider band at a
      high prediction) and with coverage being **0.7795 against a nominal 0.80** — under, not over,
      by about 0.8 of a binomial standard error

- [ ] **Measure and publish the per-row calibrated interval width distribution** (added
      2026-09-07 by #48). `reports/model/conformal-coverage.csv` carries only the **mean** width
      (0.8951 wt%); no committed table holds the widths themselves. Two things need it. The model
      card has to state what a band typically looks like, not just what it covers on average — the
      width is not constant, because the conformal correction is a constant in `log1p` space and
      `expm1` stretches it more at a high prediction than at a low one. And `domain.
      max_interval_width_wt_pct` is currently **1.12 wt%**, derived as the training target's own
      standard deviation (a band wider than the marginal spread has told the caller nothing), which
      is a defensible derivation but **not a calibration**: nobody can yet say what fraction of
      real predictions that threshold refuses

      **2026-09-26, still open.** No committed table holds per-row widths:
      `conformal-rows.csv` is row accounting, not widths. Producing one means predicting a
      population through the promoted bundle, and choosing that population is a decision: the
      172 calibration rows, the 131 early-stopping rows, or the training rows, never `test`.
      The page states the mean (0.8630 wt%, from the artifact score) and that the band widens
      with the prediction. The distribution is what is owed

- [x] **One validation row carries a physically impossible label, and the limits section has to
      say so** (added 2026-09-12 by #14's decision). `Ce1Ni4Cr1` is recorded at 4.73 wt%, which
      is H/M **3.339** against `LaNi5H6`'s 1.0 — no AB5 intermetallic holds that much hydrogen,
      so the label is a transcription or unit defect rather than an unusual material. It sits in
      **`val`**, so it feeds early stopping and every validation figure this page reports.

      It is deliberately **not** removed: L3 says a finding on a held-out row is reported and
      left where it is, and #14 measured that the two sibling rows in `train` are already the two
      lowest-quality labels of 893 and are dropped there. So the honest statement is not "the
      data is clean" but "one validation row is known-bad, we can name it, and the rule that
      forbids touching held-out data is worth more than the row". Say both halves — a limits
      section that names the defect without naming the reason reads as an oversight.

      The arithmetic and the other two rows are in #14's box; the L4 ceiling screen that catches
      this class at serve time is #48's. Not an unfreeze condition.

- [x] **The parity figure's second panel has no data on disk, and this page must not ship with
      one panel** (added 2026-09-12 by #81). The first box above asks for random-split and
      leave-one-class-out metrics "together, at the same scale", and
      `hydms.figures.charts.parity()` makes that structural: it refuses a figure with fewer than
      two readings, because a parity plot of one protocol is the optimistic number on its own
      page. What it cannot supply is the second reading. `hydms.surrogate.train` writes
      `evaluation.out_of_fold` — 893 scored rows — and `hydms.surrogate.loco` writes four tables
      and that is not one of them, so `reports/loco/` holds ten class averages and no scored
      rows. **Card #98** adds the table; it needs a LOACO run, which is the maintainer's.

      Until then this page shows the per-class R² comparison, which *is* the right evidence for
      AC-6's claim and the wrong evidence for a scatter: it can say a family transfers badly, not
      where. Do not relax `parity()` to draw the one panel it can. Not an unfreeze condition.

      **2026-09-25, #98's code landed; the panel now waits only on the run.** `loco` writes the
      scored rows as `reports/loco/loco-out-of-fold.csv` — same columns as
      `model-out-of-fold.csv`, class in `fold` — and refuses to write a partial one. What is
      missing is the file itself: the only full LOACO run (2026-09-06) predates the table, so
      it takes one more, ~4 h, which the maintainer runs. When the file is committed,
      `tests/test_figures.py::test_the_committed_loco_run_keeps_every_scored_row` stops skipping
      and this box can be ticked the moment the page draws both panels from it.

      **2026-09-25, the file is committed (#98 `done`).** `reports/loco/loco-out-of-fold.csv`,
      893 rows, `probe` false, and the figures test now runs. Nothing now blocks this box but
      the page. Caption the LOACO panel with its run date: the seeded run is not reproducible
      run to run (#104), so the panel is *one* run's rows, not a fixed fact.

      **2026-09-26, drawn.** Both panels come from `GET /v1/evidence/parity` (893 rows each).
      The caption gives the run date as *not recorded* and names the tables by commit
      (`d8734ec`, labelled as a commit), and it cites #104. With one reading absent the page
      draws no figure and says why. `parity()` was not relaxed

- [x] **Every chart on this page comes from `hydms.figures`, none from a local helper** (added
      2026-09-12 by #81). The five builders exist so that this page and #82's cannot draw the
      same quantity two different ways, which is the drift a per-page chart helper always
      reaches. The parity plot and the domain strip are this page's; `prediction_band` and
      `temperature_sweep` are #82's; `nearest_neighbours` is shared. A chart this page needs that
      `hydms.figures` does not have is a builder added *there*, with its guards, not a matplotlib
      call added here

      **2026-09-26.** The page's one chart is `hydms.figures.charts.parity`, drawn by
      `render`. `domain_strip` takes a `PredictionResult`: it places *a candidate*, so it has
      nothing to draw on a page with no candidate. The domain is stated as four rules a reader
      can apply, read from `/v1/model`'s screen limits. The page file's imports are held to
      `client`, `modelcard_page` and `render` by a test

- [x] **The page gets its evidence from the service, through an Evidence Reader** (added
      2026-09-26; ADR 0007; blocked on #105's run record). A reader in `hydms/evidence/`,
      standard library only, returns `Score` objects (CONTEXT.md, **Score**): `reading` is
      `procedure | artifact | transfer`; then the value, the interval **or** the stated reason it
      has none, and the run record. It reads and never computes. It refuses a probe's tables, and a
      missing score comes back absent with its reason. The service reads it **once at startup**
      and serves `GET /v1/evidence` (scores) and `GET /v1/evidence/parity` (scored rows), with an
      evidence digest in `/health`. `app/main.py` stays at its three allowed imports. Regenerate
      `docs/API.md` with `apidoc --probe --emit`. The reader maps `evaluation-metrics.csv`'s
      `reading = out-of-fold` to `procedure` in one place, because the LOACO rows are out-of-fold
      too
- [x] **The transfer score gets a bootstrap interval, computed by `loco --emit` and not by the
      reader** (added 2026-09-26). The interval resamples canonical groups over the 893 committed
      LOACO rows, as `evaluate` does, and needs no fit. It writes a table with a byte test and a
      caveat column: it prices the sampling of materials, **not** run-to-run variation (#104). The
      artifact score carries no interval, with its reason: it is scored once on the test split,
      which only AC-3 reads
- [x] **Rename `artifact-score.csv`'s `reading` column to `description`** (added 2026-09-26). It
      holds a sentence ("R² of the median head…"), which is a third meaning of the word, in the file
      the reader maps into `Score.reading`. Change `hydms.evidence.artifact_score`, regenerate with
      `--emit`, and update its test
- [x] **Move `hydms/evidence/reconciliation.py` onto the reader** (added 2026-09-26). It is exempt
      from #105's direct-read test until this box is ticked
- [ ] **OPEN, waiting on #104's diff: does a transfer Score show one run or a spread over repeats?**
      Until #104 answers, the caption names the run by its commit. The committed run has no
      **Run date**

      **2026-09-26, the diff is in, and it points to one run.** #104 found that the drift came
      from label screening (a parallel forest) and fixed it. Screening off, three probes were
      byte-identical. If the maintainer's next full LOACO run reproduces on a repeat, a Score is
      one run, and a spread over repeats would price nothing. Close this once that repeat
      agrees; if it does not, #104 has a new finding and this stays open

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_model_card.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S6, R4

## Narrative

- 2026-09-26: Built, and left `doing` on two boxes: the per-row width table and the OPEN
  question, which now waits on #104's repeat. What landed:
  `hydms/evidence/reader.py` (standard library only) returns `Score`s for the three readings,
  serving an absence with its reason and never omitting it; probe records are refused through
  `provenance.read`. The service reads it once at startup. `GET /v1/evidence` and
  `GET /v1/evidence/parity` are new, and `/v1/health` carries `evidence_sha256`.
  `loco --emit` writes `reports/loco/loco-intervals.csv`: macro R2 0.2559 [0.1166, 0.3235],
  resampling canonical groups within each family, with a caveat column naming #104. The
  model card gained `trained_ranges.corpus` (780 compositions, 50 elements) and
  `min_transfer_r2` in the domain limits. `hydms/delivery/modelcard_page.py` decides every
  sentence, and `app/pages/1_Model_card.py` renders it (it ran under `AppTest`). Reconciliation
  now reads through the reader and regenerates byte-identical, and `hydms/evidence` joined
  #105's direct-read test. `docs/API.md` was re-probed against `v3`: only the capture time,
  the health digest, the new limit, the corpus block and the two routes moved. Two things
  learned. The committed `loco-run.csv` did not change in the 2026-09-25 run (same settings,
  pre-#105 format), so the run's commit is read off its scored table, not its record. And the
  numbers the page types (the Gordy filler, Gd, selection stability, `Ce1Ni4Cr1`) are
  `LIMIT_FACTS`, each recomputed from its source by a test. (by @assistant)

- 2026-09-04: One box added by #18 — two descriptor-level filler values a reader must be told
  about, both measured during S3 (by @assistant)

- 2026-09-02: Created for Phase H (by @assistant)

- **#89 is now a blocker, because one of the boxes above cannot be ticked without it
  (added 2026-09-11).** *Done when* requires "a link to `docs/REPORT-RECONCILIATION.md`", and that
  file does not exist — #89 writes it. A card cannot close on a dead link, and
  `scripts/check_board.py` validates relative Markdown links, so writing the link early turns the
  board red rather than shipping a broken page. The edge costs nothing now that #89 no longer
  waits on #34. (by @assistant)
