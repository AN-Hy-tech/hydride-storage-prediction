---
id: 24
status: backlog
priority: High
blocked_by: [14, 20, 88]
assignee: "@amirhossein"
tags: [p1, l3, S1]
---

# Port feature selection, inside the folds, reading CleanLab output

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How 282 candidate features become the selected set, and the
> guarantee that the rows used to choose them are never the rows used to score them.

## Why this exists

**Corrected for Phase H — the five-stage description was wrong.** `REPORT.md` 3.3 describes
VarianceThreshold, a correlation filter at |r| > 0.1, RandomForest importance > 0.005, Boruta, then
SHAP + VIF. This ticket originally repeated that. **It exists in neither selector.** There is no
correlation filter and no 0.005 threshold anywhere in the codebase, and SHAP is computed post-hoc for
reporting, never used as a filter. What actually exists:

- `Boruta_FeatEng.py` — **the live selector**, three stages: `VarianceThreshold(0.001)` with
  `temperature(K)` force-kept, then `BorutaPy` over a depth-6 RandomForest, then iterative VIF at
  threshold 30 protecting the must-keeps.
- `Feature_selection.py` — **dead code**: it reads `data/augmented/`, whose writer was deleted in
  `5c3bcb1`, and writes an output nothing consumes. Six stages, including MI and RFECV.

Port the live selector. Do not port a description.

**Two behavioural changes.** It reads CleanLab's output (ticket 14) rather than the raw splits, closing
the bypass. And it runs **inside the training folds** of ticket 88's protocol, not once over the whole
training set — the archival code fits Boruta and VIF on all 896 training rows and then reports a
cross-validated score over those same rows, so every fold's held-out data helped choose the features
being scored. That is leak **L6**, the PRD's second named leak.

Both changes mean the result may differ from the archived 22, which is the point; ticket 25 records the
difference.

## Done when

- [ ] The three live stages ported with thresholds from config, not literals
- [ ] `temperature(K)` is force-kept through variance and VIF, as in the archival selector
- [ ] Input is CleanLab-screened training data
- [ ] **Selection runs inside the training folds** of ticket 88 — never once over the whole training set
- [ ] Val and test are untouched at every stage
- [ ] Perturbing test rows leaves the selected feature set identical — the L6 sentinel in ticket 71
- [ ] That **L6 sentinel** is wired to this module — a `live` check in `hydms/qa/sentinels.py`
- [ ] **The training matrix is assembled by `hydms.data.metadata.with_features`, not by a
      `concat` here (#12).** It joins the record to the matrix by label, refuses a matrix on
      another index, and calls `refuse_non_features` before the join and
      `assert_metadata_survives` after it. One thing to know before the first call:
      `temperature(K)` is a column of the raw file *and* one of the 22 features, so the record
      and the matrix both carry it — `with_features` takes the matrix's `float64` copy (card
      #19's cast) and refuses if the record's `int64` values disagree, which is the check that
      the features were built from *these* rows
      calling `hydms.qa.assert_selection_ignores_holdout` on the real selector. Gate HG-1 goes red
      once `hydms/surrogate/selection.py` exists without one
- [ ] Stage-by-stage feature counts logged for the Chapter 1 revision
- [ ] The card's own description matches the code that exists, not `REPORT.md` 3.3

- [ ] **`avg_is_alkaline` is constant over the training split (from #23).** Measured while fitting
      the scaler on the real 1,278 x 21 matrix: its inter-quartile span over the 893 training rows
      is exactly zero, so `RobustScaler` substitutes a scale of 1.0 and the scaled column is all
      zeros. `VarianceThreshold(0.001)` should drop it, and the point of the box is that the
      archival run's own stage-by-stage counts do not say whether it did — so record the verdict
      rather than assume it. `hydms.surrogate.FittedScaler.degenerate` names such features at fit
      time, which is the only moment a scale of 1.0 is still distinguishable from an IQR that
      genuinely equals 1.0

- [ ] **Selection now has a cost to weigh that the old run never faced (from #19).**
      `dev_Gordy_electonegativity` is not computable from the citable Oliynyk table for
      **266 of 1,279 rows / 236 of 1,115 compositions** (21 elements have no `gordy_en`), and
      the six JARVIS features are not computable for the single europium row `Eu1Ni5`. CBFV's
      own table has neither hole, so the published run selected `dev_Gordy_electonegativity`
      without ever meeting this. Two options, and this card measures rather than guesses:
      carry the feature and drop 266 rows from any fold that needs it, or drop the feature and
      keep every row. The loss is concentrated — AB5 91/196 (46.4%) and MIC 54/127 (42.5%),
      against AB2 34/371 (9.2%) and LEA 0/26 — so dropping the rows is not neutral with respect
      to AC-6's leave-one-class-out folds. `hydms.descriptors.contract.CONTRACT.computability()`
      answers per composition; call it rather than re-deriving the element lists

## Runnable check

```bash
python -m hydms.surrogate.select --config hydms/config/pipeline.yaml
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Corrected for Phase H. The 'five-stage selection with a correlation filter' this card described is
  from REPORT.md 3.3 and matches neither selector: the live one (`Boruta_FeatEng.py`) has three stages
  and no correlation filter, and `Feature_selection.py` is dead code reading a directory whose writer
  was deleted in 5c3bcb1. Also now blocked on 88, because running selection inside the folds is what
  closes leak L6 (by @assistant)
