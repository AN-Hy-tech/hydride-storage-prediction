---
id: 19
status: backlog
priority: High
blocked_by: [8]
assignee: "@amirhossein"
tags: [p1, l2, AC-2]
---

# The 22-feature contract

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The exact feature names, their order, and their dtypes.

## Why this exists

Column order is a silent-failure surface: a model trained on one order and fed another
produces plausible, wrong numbers. Acceptance criterion AC-4 exists precisely to catch it.

This module is the single source of truth for the feature list, consumed by the featuriser,
the scaler and the predictor alike.

## Done when

- [ ] Feature names, order and dtypes declared in one place
- [ ] `assert_contract(df)` raises on missing, extra, reordered or wrongly-typed columns
- [ ] The contract is written into the artifact manifest so a model records what it expects
- [ ] After feature selection re-runs (25), the contract is regenerated rather than hand-edited

## Runnable check

```bash
python -m pytest tests/descriptors/test_contract.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — AC-2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
