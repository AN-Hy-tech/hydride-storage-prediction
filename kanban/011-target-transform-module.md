---
id: 11
status: backlog
priority: Normal
blocked_by: [9]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# Target transform module

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the modelled target is log1p(wt%) and how to get back to wt%.

## Why this exists

The target is `log1p(H2_W% (max))`, inverse `expm1`. That pairing is currently spread
across the pipeline, and `REPORT.md` 7.3 already flags that SHAP values were reported in log
space by mistake. One module owning both directions makes that error structurally hard to
repeat.

## Done when

- [ ] `to_model_space(wt_pct)` and `to_wt_pct(model_value)` are the only transform entry points
- [ ] Round-trip property test holds to floating tolerance across the data range
- [ ] Docstring states which `REPORT.md` metrics are in which space

## Runnable check

```bash
python -m pytest tests/data/test_target.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
