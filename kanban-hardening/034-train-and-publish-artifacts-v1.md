---
id: 34
status: backlog
priority: High
blocked_by: [31, 32, 33]
assignee: "@amirhossein"
tags: [p1, l3, S1]
---

# Train and publish artifacts v1

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The first promoted artifact version.

## Why this exists

The moment Architecture A becomes possible. Everything downstream pins this version.

Promotion requires the gates to pass — this ticket is blocked on 31, 32 and 33 for exactly
that reason.

## Done when

- [ ] Full pipeline run from `data/raw/` produces `artifacts/v1/`
- [ ] Manifest complete: git SHA, seeds, package versions, feature contract, gate results
- [ ] All Phase 1 gates pass and are recorded in the manifest
- [ ] `current` points at `v1`

## Runnable check

```bash
python -m hydms.pipeline run --promote && python -m hydms.gates run --all
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
