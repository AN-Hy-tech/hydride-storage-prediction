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
- [ ] Stage-by-stage feature counts logged for the Chapter 1 revision
- [ ] The card's own description matches the code that exists, not `REPORT.md` 3.3

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
