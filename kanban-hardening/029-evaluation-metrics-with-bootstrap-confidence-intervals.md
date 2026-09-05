---
id: 29
status: backlog
priority: Normal
blocked_by: [28]
assignee: "@amirhossein"
tags: [p1, l3, S6, R4]
---

# Evaluation metrics with bootstrap confidence intervals

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How model quality is measured and reported.

## Why this exists

The domain memo 3.3 item 5 warns that at n=239 a test R2 of 0.916 carries a wide interval,
and that a bare point estimate should not be reported.

This module produces every number that goes into the Chapter 1 revision, so it must report
intervals alongside point estimates by default — not as an option.

## Done when

- [ ] R2, RMSE, MAE reported on both log and wt% scales
- [ ] Bootstrap confidence intervals (2000 resamples) accompany every point metric
- [ ] Metrics computed per split and per temperature subgroup

- [ ] **The per-fold table already carries its own row counts, and that is not decoration (from
      #26).** `hydms.surrogate.model` returns `rows_fitted` and `rows_scored` as metrics, so
      `Evaluation.per_fold` and `reports/model/model-per-fold.csv` put the fold sizes in the same
      table as the fold scores. Screening removes between 15 and 144 of a fold's ~710 training
      rows (#24), so part of any fold-to-fold spread is training size and not the model. A
      bootstrap CI over the folds that does not say so is a CI over two different things
- [ ] Output is a structured table written to `reports/`, ready for the thesis
- [ ] SHAP and PDP are computed on train or a dedicated split, **never on test**. Leak L11:
      `benchmark_model_selection.py:1375,1383,1394` computed both on `X_test`, which makes REPORT §6.1
      a test-set artefact
- [ ] **L11 has no sentinel and this card owes one.** Once this card decides what the explainability
      record looks like, add the **L11 sentinel** to `hydms/qa/sentinels.py`: the record names no
      held-out split. Until it exists, HG-1 cannot report green

- [ ] **Every reported number must name the feature set it belongs to (from #25).** There are now
      two, and they are not interchangeable: `SELECTED`, the consensus 14 a shipped model is fitted
      on, and the per-fold sets of **16-20** features that #25's five-fold run actually produced.
      A bootstrap interval over folds that each selected their own columns is an interval about a
      *procedure*; one over a fixed 14-column pipeline is about a model. Both are legitimate and
      they are different claims, so the record carries which — and the Chapter 1 revision (#37)
      quotes it from there rather than from a paragraph

## Runnable check

```bash
python -m hydms.surrogate.evaluate --artifact current
```

## Traces to

`docs/PRD-inverse-design.md` — S6, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
