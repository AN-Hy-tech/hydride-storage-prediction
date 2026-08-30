---
id: 14
status: backlog
priority: High
blocked_by: [13]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# CleanLab screening as a data-layer stage

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** Which rows are label-suspect, and the record of what was removed.

## Why this exists

The audit's fourth broken link: `Boruta_FeatEng.py:23-25` reads `data/splits/` — the
**pre-CleanLab** splits — while its own comment claims it reads managed data. The effective
pipeline bypassed CleanLab entirely, contradicting `README.md` step 4 and `REPORT.md` 3.2.

The domain memo supplies the physics: sloping plateaus make measured capacity depend on
measurement pressure, and pressure is absent from the dataset. That is a better account of
what CleanLab detects than 'some experiments are wrong'.

## Done when

- [ ] Feature selection (24) consumes CleanLab's output, closing the bypass
- [ ] Removed rows written to a report with their residuals, not silently dropped
- [ ] Counts recorded per split for the Chapter 1 revision (37)
- [ ] Module docstring records the counter-caution: removing real measurements in underrepresented regimes flatters metrics

## Runnable check

```bash
python -m pytest tests/data/test_clean.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
