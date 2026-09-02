---
id: 33
status: backlog
priority: High
blocked_by: [5, 28]
assignee: "@amirhossein"
tags: [p1, l3, AC-4]
---

# GATE AC-4: known alloys round-trip through predict()

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the screening path and the training path agree.

## Why this exists

Ten known training alloys fed through `predict()` must reproduce the trained model's
predictions on those same rows.

This catches the two silent failure modes that would otherwise poison every candidate list:
**a refit scaler, and a reordered feature matrix.** Neither raises an error on its own.

## Done when

- [ ] Ten training rows selected across different alloy classes
- [ ] Predictions via the screening path match the training-time predictions to floating tolerance
- [ ] Failure output shows per-feature values from both paths so the mismatch is diagnosable
- [ ] Registered as `AC-4` and run by CI

## Runnable check

```bash
python -m hydms.gates run AC-4
```

## Traces to

`docs/PRD-inverse-design.md` — AC-4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
