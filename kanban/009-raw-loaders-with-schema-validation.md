---
id: 9
status: backlog
priority: High
blocked_by: [3]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# Raw loaders with schema validation

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** The shape and dtypes of each raw source, and what a valid row is.

## Why this exists

Four raw sources: `hydride_data.csv` (1279 x 6), `hydride_prefeaturizing.csv`,
`ML-HYDPARK_v0.0.5.csv` (772 rows) and the HyStor spreadsheet, each with its own column
names and conventions.

Validation belongs here so no later layer has to defend against a malformed row.

## Done when

- [ ] `hydms/data/load.py` exposes one loader per source, each returning a validated frame
- [ ] Schemas declared explicitly (names, dtypes, allowed ranges, nullability)
- [ ] A violation raises with the offending rows named, never silently coerces
- [ ] Row counts asserted against documented values (1279 hydride_data, 772 ML-HydPARK)

## Runnable check

```bash
python -m pytest tests/data/test_load.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
