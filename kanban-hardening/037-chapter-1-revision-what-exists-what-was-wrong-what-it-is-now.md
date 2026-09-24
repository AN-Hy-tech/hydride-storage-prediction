---
id: 37
status: doing
priority: High
blocked_by: [25, 29, 30, 34, 89, 103]
assignee: "@amirhossein"
tags: [p1, l7, S6, S7, R4]
---

# Chapter 1 revision: what exists, what was wrong, what it is now

**Stage S8 — Evidence and close** · **L7 Evidence** · Estimate: 2 d

> **Owns (hidden behind this module):** The written account of the starting line and the correction.

## Job story

When my supervisor asks what was wrong with the original pipeline, I want a written account with corrected numbers beside published ones, so I can present the audit as rigour rather than have it surface as a weakness in the viva.

## Why this exists

**The prose half of hardening Chapter 1.** Blocked on the code half because you cannot
honestly write 'here is what was wrong and here is the corrected number' before the
corrected number exists.

Covers: what the forward model is; the four broken pipeline links; the three validation
leaks; the corrected numbers beside the published ones with the reason for each change; and
the leave-one-alloy-class-out result.

Framed as a contribution, not an apology. A thesis that states its own validation limits is
stronger than one that does not.

## Done when

- [x] Draft chapter section in `docs/chapter1-revision.md`
- [x] Side-by-side table: published number, corrected number, which leak explains the change
- [x] Leave-one-class-out R2 reported beside random-split R2 with the Beltrame reference
- [x] Old-22 vs new-N feature comparison included
- [x] Every claim traceable to a report file produced by the pipeline, not to memory
      **Ticked 2026-09-24 by #103, criterion unchanged.** The three numbers that were marked † (the
      artifact score R² 0.7071 / RMSE 0.5420 / MAE 0.3117 from gate AC-1, and the test coverage
      0.7795 / width 0.8630 wt% from gate AC-3) now trace to the committed
      `reports/model/artifact-score.csv`. That table is generated from
      `reports/model/artifact-gates.json`, a verbatim copy of the gate records in the promoted
      `v3` manifest, stamped with the manifest's SHA-256. The chapter's † markers are gone. Still
      true and still stated in §1.R.8: the *model* is gitignored, so a clone can check the recorded
      numbers but cannot re-score them (card #7)

- [x] **A limitations-and-future-work section, and the measurement that makes it specific**
      (added 2026-09-06, after the LOCO run and a domain review with the maintainer). The chapter
      already owes the transfer number beside the random-split one. What it should also carry is
      **why** the worst fold is as bad as it is, because the answer is partly arithmetic and that
      is a stronger sentence than a low R2:

      **Mg fails partly by construction, not only by chemistry.** Measured over the 893 training
      rows: Mg median capacity **3.80 wt%** against **1.60** for every other class combined; Mg
      max **7.19** against a non-Mg max of **5.19**. **21 of 96 Mg rows sit above the entire
      non-Mg range** and 43 sit above its 99th percentile. A gradient-boosted tree predicts leaf
      averages of training targets, so it **cannot** produce a value above the range it was
      trained on -- hold out the only high-capacity family and those 21 rows are unreachable
      before any question of learning arises. That is the model class meeting the fold design,
      and no amount of tuning moves it.

      **State the unobserved confounder too.** Sloping PCT plateaus make measured capacity depend
      on the upper pressure of the measurement, and **this dataset carries temperature but not
      pressure**. Every HEA and BCC solid solution here is intrinsically prone to sloping
      plateaus. That is a ceiling on any model built from these columns, and it is the physical
      explanation for the label noise CleanLab flags -- better than "some experiments are wrong".

      **The future-work programme, ranked, all of it composition-only so it stays compatible with
      PRD 2.3's enabling fact.** Written down now because it cannot become a card while the
      freeze holds, and because deciding it *before* the next measurement is what keeps that
      measurement honest:

      1. **Re-test the Miedema descriptors under the fixed merge.** They were in the archival
         candidate pool -- `Miedema_deltaH_ss_min`, `_inter`, `_amor` at
         `Machine_Model/src/merge_datasets.py:28` -- but were joined at line 46 by the positional
         `concat` after `reset_index(drop=True)` that **is leak L9**. Their failure to survive
         selection is therefore not evidence they are uninformative; they may simply have been
         attached to the wrong compositions. Physically they are the right quantity: Miedema's
         rule of reversed stability is the semi-empirical account of the cross-family mechanism
         the model is missing.
      2. **Reparameterise the target to H/M**, converting to wt% analytically. H/M is bounded
         roughly 0.5 to 2.5 across every family here *including* Mg, so the held-out family stays
         in range and the arithmetic, not the tree, performs the extrapolation. The conversion is
         exact and needs no new data. Note that **mean atomic mass appears nowhere in the
         22-feature contract** -- only `range_atomic_weight` and mass-derived deviations -- so the
         model has never had the denominator of the wt% formula, and trees cannot divide.
      3. **Add composition-derived proxies for structure**: mean atomic mass, atomic size mismatch
         delta, VEC, mixing entropy. This is the admissible form of "add structural features" --
         C14-versus-C15 phase, lattice parameters and site geometry are genuinely predictive but
         are not computable for an alloy nobody has made, so using them would forfeit inverse
         design (PRD 7 already rejected descriptor inversion).
      4. **A base learner that can extrapolate** -- linear or physics-informed base with trees on
         the residuals -- which attacks the range ceiling directly rather than around it.

      **Rejected here, with reasons, so the chapter can say they were considered:** VAE, GAN and
      diffusion models (published materials generative models train on 10^4 to 10^6 examples
      against this dataset's 1,279); GNNs and foundation models (Matbench: descriptor ML stays
      competitive below ~10^4 samples); and more Optuna trials, which cannot touch the range
      ceiling that causes the worst fold.

      **And the protocol, which matters more than the list.** The transfer number is spent: it
      cost 4 h 07 m and each re-measurement costs the same. Running after change 1, looking, then
      running after change 2 is selecting on the held-out families -- leak L2 one layer up. So the
      whole change set is decided first, the acceptance rule is fixed before the run, and LOCO is
      run **once**, with both numbers reported old and new

## Runnable check

```bash
test -f docs/chapter1-revision.md
```

## Traces to

`docs/PRD-inverse-design.md` — S6, S7, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- **#89 is now a blocker (added 2026-09-11).** #89's own card says it plainly: "This document is
  what card #37 is written from." The reconciliation table is the evidence this revision cites for
  every "what was wrong" claim, so writing the chapter first would mean deriving those eight
  disagreements a second time, by hand, in prose nothing checks. The runbook's "#37 is unblocked on
  everything but #34" is corrected with this edge. (by @assistant)

- **2026-09-24: drafted, `doing` on one box.** `docs/chapter1-revision.md` is written from
  committed evidence only: `REPORT-RECONCILIATION.md` (#89) for what was wrong, the runbook's
  leak inventory, `reports/model/`, `reports/loco/` and `reports/feature_selection/`. Three things
  learned writing it. **(1) The old-22-vs-new-N box needed no run.** #25 had already committed
  the comparison, so the feared selection run was never owed. **(2) The Mg range arithmetic in
  the limitations box reproduces exactly from committed files:** `model-out-of-fold.csv` joined
  to `alloy_class_table(load_hydride_data())` gives 96 Mg rows, median 3.80 vs 1.60, max 7.19 vs
  5.19, 21 above the non-Mg max, 43 above its 99th percentile (3.90), and the ten class counts
  match `loco-per-class.csv`, so the join is the one LOCO folded on. The chapter cites the
  recipe. **(3) Two tables committed under `reports/model/` are easy to misquote as the
  artifact score.** `conformal-coverage.csv` reports R² 0.8255 and coverage 0.8081, but over the
  172 *calibration* rows, which a conformal correction is fitted on. The artifact score is
  0.7071 on 254 *test* rows and is committed nowhere, hence the open box above. The draft is the
  author's to revise: it is thesis prose, and the voice and the chapter numbering (1.R.x) are
  placeholders. (by @assistant)
