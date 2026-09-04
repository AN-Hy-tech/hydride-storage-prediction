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

- [ ] **Screen a batch, never a candidate at a time — and the cost is measured (from #22).**
      `featurize` has a **5 ms per-call floor** that does not depend on the batch size:
      `require_self_consistent` re-audits both element tables' composite columns on every call
      (#18's guard, and it is what stops a descriptor being silently zero for Cs and Gd). That
      is 2% of a ten-thousand-candidate batch and **57% of a batch of one**, so a runner that
      loops `for candidate in candidates: featurize([candidate], ...)` costs ~200× what the
      same work costs batched — before anything is screened. `docs/BENCHMARKS.md` has the
      table. If a genuinely per-candidate path is ever needed, the audit is a pure function of
      (table, properties) and can be memoised the way #22 memoised
      `PropertyTable.servable`; nobody should do that speculatively

## Runnable check

```bash
python -m pytest tests/screens/test_protocol.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
