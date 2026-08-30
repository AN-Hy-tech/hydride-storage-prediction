---
id: 44
status: backlog
priority: High
blocked_by: [3]
assignee: "@amirhossein"
tags: [pa, l4, S3]
---

# Screen interface: a verdict with a reason, never a silent drop

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What it means to admit or reject a candidate.

## Why this exists

Memo 4.2 says the failure modes of this architecture must be *visible and debuggable*: you
should be able to print a candidate, its features, its prediction, its uncertainty and its
filter verdicts.

So a screen never silently removes a row. It returns a verdict and a reason, and filtering
happens afterwards, explicitly.

```python
class Screen(Protocol):
    name: str
    def verdict(self, candidates: DataFrame) -> DataFrame: ...  # passed: bool, reason: str
```

## Done when

- [ ] `Screen` protocol defined with `name`, `verdict()` and a declared reason vocabulary
- [ ] Verdicts are returned as columns; no screen mutates or drops rows
- [ ] A composite runner applies all screens and produces one verdict table
- [ ] Every rejection carries a human-readable reason string

## Runnable check

```bash
python -m pytest tests/screens/test_protocol.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
