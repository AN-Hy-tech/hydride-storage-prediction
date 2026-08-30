---
id: 15
status: backlog
priority: High
blocked_by: [13, 14]
assignee: "@amirhossein"
tags: [p1, l1, AC-1]
---

# Data-layer golden tests

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the rebuilt data layer reproduces the documented dataset exactly.

## Why this exists

The point of the rewrite is that it produces the *same* dataset as the archived scripts,
so `REPORT.md`'s numbers stay attributable. This is the test that proves it.

## Done when

- [ ] Golden test asserts 1279 raw rows and 1149 unique formulae
- [ ] Golden test asserts split sizes 896 / 136 / 247
- [ ] Golden test asserts the 10 alloy classes with expected counts
- [ ] Any deviation fails with a diff, not a bare assertion error

## Runnable check

```bash
python -m pytest tests/data/test_golden.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
