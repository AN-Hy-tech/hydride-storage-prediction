---
id: 12
status: backlog
priority: High
blocked_by: [10]
assignee: "@amirhossein"
tags: [p1, l1, S6, AC-6]
---

# Re-join Alloy_class on formula

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Which alloy family each row belongs to.

## Why this exists

`extract_features_cbfv.py:20-21` drops every object column except `Composition`, which
discards `Alloy_class` (AB2, AB, A2B, AB5, Mg, MIC, SS, LEA, MEA, HEA).

Both the applicability-domain screen (48) and leave-one-alloy-class-out CV (30) need it.
Without this, PRD acceptance criterion AC-6 is unreachable.

## Done when

- [ ] `Alloy_class` carried through featurisation as metadata, not as a model feature
- [ ] It is never present in the feature matrix passed to the model
- [ ] Class distribution matches the raw 10 classes with no rows lost
- [ ] Rows with a missing class are labelled `UNKNOWN` rather than dropped

## Runnable check

```bash
python -m pytest tests/data/test_alloy_class.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S6, AC-6

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
