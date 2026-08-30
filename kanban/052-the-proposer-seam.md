---
id: 52
status: backlog
priority: High
blocked_by: [51]
assignee: "@amirhossein"
tags: [pa, l5, S3, S5]
---

# The Proposer seam

**Phase A — Screen-and-Rank** · **L5 Search** · Estimate: 0.5 d

> **Owns (hidden behind this module):** How candidates come into existence — and nothing else.

## Why this exists

The seam that makes Architecture B an implementation rather than a project:

```python
class Proposer(Protocol):
    name: str
    def propose(self, spec: SearchSpec) -> Iterator[Batch]: ...
```

`Enumerate` (53) is the first implementation, `Evolve` (59) the second. The descriptor
inversion contrast experiment from PRD 7.1 becomes a third, nearly free.

**Deletion test:** deleting this protocol would force the enumeration and evolution paths to
each re-derive the evaluation and reporting stack. It concentrates complexity rather than
moving it.

## Done when

- [ ] `Proposer` protocol with `propose()` yielding batches of (formula, temperature)
- [ ] `SearchSpec` captures family, element sets, temperature range and budget
- [ ] The runner is proposer-agnostic: swapping implementations is a config key
- [ ] A trivial fixture proposer exists for testing the downstream path without a real search

## Runnable check

```bash
python -m pytest tests/search/test_proposer_protocol.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, S5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
