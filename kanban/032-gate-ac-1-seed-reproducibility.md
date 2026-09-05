---
id: 32
status: backlog
priority: High
blocked_by: [5, 26]
assignee: "@amirhossein"
tags: [p1, l3, AC-1]
---

# GATE AC-1: seed reproducibility

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the same seed produces the same numbers.

## Why this exists

PRD acceptance criterion 1. Without this the whole reproducibility claim is unverified,
and the artifact manifest's recorded seeds are decorative.

## Done when

- [ ] Pipeline run twice with the same seed produces identical metrics
- [ ] Comparison is on the metrics table, not on model file bytes (which may differ)
- [ ] Any nondeterministic step is identified and either seeded or documented as unavoidable
- [ ] Registered as `AC-1` and run by the CI slow lane

## Runnable check

```bash
python -m hydms.gates run AC-1
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-05: **The single sanctioned refit (persist-vs-refit, AC-1 side; canonical record on #34).** Everything
  downstream *loads* the frozen `v1`; AC-1 is the one path that deliberately *refits* — it re-runs training
  end-to-end twice from the same seed and asserts the **metrics tables** match. Two honest refits may differ in
  model bytes (CatBoost threading is not bit-deterministic), which is why the done-criterion compares the metrics
  table, not model bytes. Note precisely what AC-1 does and does not claim: it verifies the *procedure* is
  reproducible from seed, not that the promoted `v1` is bit-reproducible. Its refits are throwaway — never
  `save()`d, never promoted, never `load()`ed by any consumer. This is the guard that stops persistence from
  degrading into the audited sin (§2.2.1) of published numbers with no runnable pipeline behind them. (by @assistant)
