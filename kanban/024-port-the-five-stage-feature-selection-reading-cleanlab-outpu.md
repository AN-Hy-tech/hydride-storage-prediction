---
id: 24
status: backlog
priority: High
blocked_by: [14, 20]
assignee: "@amirhossein"
tags: [p1, l3, S1]
---

# Port the five-stage feature selection, reading CleanLab output

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How 282 candidate features become the selected set.

## Why this exists

VarianceThreshold, correlation filter, RandomForest importance, Boruta, then SHAP + VIF.
Port from `Feature_selection.py` and `Boruta_FeatEng.py`, preserving the thresholds.

**The behavioural change:** it now reads CleanLab's output (ticket 14) rather than the raw
splits, closing the bypass. That means the result may differ from the archived 22 — which is
the point, and ticket 25 records the difference.

## Done when

- [ ] All five stages ported with thresholds from config, not literals
- [ ] Input is CleanLab-screened training data
- [ ] Selection runs on training data only; val and test are untouched
- [ ] Stage-by-stage feature counts logged for the Chapter 1 revision

## Runnable check

```bash
python -m hydms.surrogate.select --config hydms/config/pipeline.yaml
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
