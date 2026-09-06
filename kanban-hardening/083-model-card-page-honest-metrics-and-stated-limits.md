---
id: 83
status: backlog
priority: High
blocked_by: [29, 30, 82]
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

- [ ] Random-split metrics and **leave-one-alloy-class-out** metrics shown together, at the same scale
- [ ] Bootstrap confidence intervals shown, not just point metrics
- [ ] The training data described: rows, unique canonical compositions, alloy families, element coverage,
      temperature range
- [ ] The applicability domain stated in terms a reader can apply to their own candidate
- [ ] **The material-versus-system caveat** — comparing a material wt% to a DOE onboard-storage target is
      a two-step overstatement
- [ ] A link to `docs/REPORT-RECONCILIATION.md`, so the previously published figures are not silently inherited
- [ ] The known limits stated plainly, including no pressure data and therefore no reversible-versus-maximum
      capacity distinction
- [ ] The artifact version and training date

- [ ] **State the two descriptor-level filler values (from #18 and #19).** `dev_Gordy_electonegativity`
      cannot be computed for 266 of 1,279 rows from the citable Oliynyk edition, and
      `dev_voro_coord_divi_mol_vol` rests on `voro_coord = 1.0` for gadolinium — a placeholder, not
      a measurement: every other element in the JARVIS table sits between 3 and 12, and Gd is hcp
      with twelve nearest neighbours. Gd appears in **18 of the 1,279** rows. Neither is a bug and
      neither moves parity; both are limits a reader forming a belief about the model should be
      told, in the same paragraph as the no-pressure-data limit

- [ ] **Two limits this card owes, both measured and both already public (from #25).** First, one
      of the 14 declared features rests on filler: the JARVIS table stores `voro_coord = 1.0` for
      `Cs` and `Gd` where every other element is 3 to 12, and gadolinium is in **18 of the 1,279
      curated rows (1.4 %)**, so `dev_voro_coord_divi_mol_vol` is computed from a placeholder for
      those rows. #25 kept the feature — all five folds selected it, and hand-removing a
      unanimously-selected feature after seeing the result is the decision this phase exists to
      remove — on the condition that the model card states it. Second, **the feature set is not a
      stable object**: every one of the 21 candidates was selected by some fold and only 14 by all
      five, so "the model uses these 14 features" is a statement about a consensus, not a discovery
      about hydrogen storage. `reports/feature_selection/old_vs_new.md` is the source for both

- [ ] **Three R² values, and a sentence that says which is which** (raised 2026-09-06). The card
      already asks for random-split and leave-one-class-out side by side; a third reading now
      exists and is easy to conflate with the first. **The procedure** scores R² 0.7481
      [0.6889, 0.7985] wt% out-of-fold over five models (`reports/model/evaluation.md`). **The
      deployed model** — one model, scored once on 254 held-out `test` rows — scores R² **0.7071**,
      RMSE 0.5420, MAE 0.3117. That second figure is computed by gate AC-1 as a side effect of
      proving reproducibility and **is currently published nowhere**: it lives in the gate's message
      and in the gitignored `artifacts/gate-results.json`. `evaluation.md` promises it in its own
      words ("the artifact reading … is a claim about *a model*, and it arrives with card #34"), so
      this card is where the promise is kept. Report it beside 0.7481 with the reason they differ:
      the deployed model grows on **701** rows where each CV fold was cut from 893

- [ ] **The near-ambient temperature bin is the weakest and the table already says so** (raised
      2026-09-06 from the committed `reports/model/evaluation-subgroups.csv`, out-of-fold, wt%):
      **(195, 293] K → R² 0.187, 95 % CI [−0.012, 0.423]** — the interval includes zero — against
      0.657, 0.717, 0.757 and 0.772 for the four warmer bins. That is the regime a practical storage
      material has to operate in, and it is where the model is worst. It is not a defect, it is a
      result, and it is sitting in a committed CSV that no prose mentions. State it in the limits
      with its confidence interval, not as a rounded point estimate

- [ ] **The band is wide relative to the physics, and that is the honest reading.** The calibrated
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

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_model_card.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S6, R4

## Narrative

- 2026-09-04: One box added by #18 — two descriptor-level filler values a reader must be told
  about, both measured during S3 (by @assistant)

- 2026-09-02: Created for Phase H (by @assistant)
