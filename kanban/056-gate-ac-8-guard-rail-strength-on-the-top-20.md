---
id: 56
status: backlog
priority: High
blocked_by: [5, 55]
assignee: "@amirhossein"
tags: [pa, l5, AC-8, R1]
---

# GATE AC-8: guard-rail strength on the top 20

**Phase A — Screen-and-Rank** · **L5 Search** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Whether the guard rails are strong enough to trust the output.

## Why this exists

PRD acceptance criterion 8, fixed before results are seen: **at least half of the top 20
must fall inside the applicability-domain ceiling and inside the family-specific VEC
window.** If fewer do, the guard rails are too weak — tighten and re-run.

Memo 4.5 says to budget two or three such iterations and to **report them as a result, not a
setback**. This gate is what makes that loop bounded rather than open-ended.

## Done when

- [ ] Gate measures the fraction of the top 20 inside both the AD ceiling and the VEC window
- [ ] Passes at >= 50%; failure reports the actual fraction and which constraint each failing candidate violated
- [ ] Each tightening iteration is logged with its settings, so the sequence is reportable
- [ ] Registered as `AC-8` and run by CI

## Runnable check

```bash
python -m hydms.gates run AC-8
```

## Traces to

`docs/PRD-inverse-design.md` — AC-8, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
