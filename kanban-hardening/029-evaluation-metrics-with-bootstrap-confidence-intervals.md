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
- [ ] Output is a structured table written to `reports/`, ready for the thesis
- [ ] SHAP and PDP are computed on train or a dedicated split, **never on test**. Leak L11:
      `benchmark_model_selection.py:1375,1383,1394` computed both on `X_test`, which makes REPORT §6.1
      a test-set artefact
- [ ] **L11 has no sentinel and this card owes one.** Once this card decides what the explainability
      record looks like, add the **L11 sentinel** to `hydms/qa/sentinels.py`: the record names no
      held-out split. Until it exists, HG-1 cannot report green

## Runnable check

```bash
python -m hydms.surrogate.evaluate --artifact current
```

## Traces to

`docs/PRD-inverse-design.md` — S6, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
