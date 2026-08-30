---
id: 46
status: backlog
priority: High
blocked_by: [20, 44]
assignee: "@amirhossein"
tags: [pa, l4, S3, AC-8]
---

# Valence-electron-concentration window screen

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** The VEC design windows and the fact that they are family-specific.

## Why this exists

Published design criteria for AB2-type hydrogen storage alloys include **VEC 6.2-6.5**;
BCC alloys report a best capacity/cyclability compromise in **VEC 4.75-5.0**.

**These windows are family-specific — memo 5.1 warns explicitly against applying one
globally.** A single global VEC filter would be a physics error, not just an
over-restriction.

## Done when

- [ ] VEC computed from composition, not looked up
- [ ] Windows declared per family in config with their literature source cited inline
- [ ] Applying a window to the wrong family raises rather than silently passing
- [ ] Feeds acceptance criterion AC-8's top-20 check

## Runnable check

```bash
python -m pytest tests/screens/test_vec.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, AC-8

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
