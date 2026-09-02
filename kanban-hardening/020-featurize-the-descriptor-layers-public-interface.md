---
id: 20
status: backlog
priority: High
blocked_by: [17, 18, 19]
assignee: "@amirhossein"
tags: [p1, l2, S3, S12]
---

# featurize() — the descriptor layer's public interface

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** Everything above: tables, statistics, composites and column order.

## Job story

When I have a list of candidate formulas, I want one function call that returns model-ready features, so I can screen candidates without reassembling the training pipeline.

## Why this exists

The deep interface the rest of the system sees:

```python
featurize(formulas: Sequence[str], temperatures: ArrayLike) -> DataFrame  # 22 columns
```

One call. No CSV in, no CSV out. Architectures A and B both call this per batch of
candidates, so it must be batched — memo 4.3 practical check 3 warns explicitly against
per-formula loops.

Formula parsing via `pymatgen.core.Composition` (MIT, already a dependency).

## Done when

- [ ] Single public function; everything else in the layer is private
- [ ] Batched: 10k formulae in one call, not 10k calls
- [ ] Invalid formulae are reported with their index, never silently dropped
- [ ] Output passes `assert_contract` (19) by construction

## Runnable check

```bash
python -m pytest tests/descriptors/test_featurize.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
