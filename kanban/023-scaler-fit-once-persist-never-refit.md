---
id: 23
status: backlog
priority: High
blocked_by: [4, 13]
assignee: "@amirhossein"
tags: [p1, l3, AC-4]
---

# Scaler: fit once, persist, never refit

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The feature scaling transform and the fact that it belongs to the trained model.

## Why this exists

Memo 4.3 practical check 2 names refitting the scaler on candidates as a *silent
correctness bug*. `RobustScaler` is fit on training data only and then persisted with the
model.

Guard structurally: the loaded scaler should expose `transform` and not `fit`.

## Done when

- [ ] `RobustScaler` fit on train only, persisted into the artifact directory
- [ ] The load path returns a transform-only wrapper; calling `fit` on it raises
- [ ] Scaler is versioned with the model, never re-derived from candidate data
- [ ] Test asserts scaling a candidate batch twice yields identical output

## Runnable check

```bash
python -m pytest tests/surrogate/test_scaler.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — AC-4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-05: The persist-vs-refit decision (record on #34) is what turns this card's "never refit" from a hope
  into a structural fact: the scaler is frozen inside `v1` and consumers only ever `load()` it, so the
  transform-only wrapper here has an actual object to be. AC-4 (#33) is the runtime guard that no one silently
  refits it. (by @assistant)
