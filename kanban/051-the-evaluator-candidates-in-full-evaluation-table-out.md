---
id: 51
status: backlog
priority: High
blocked_by: [28, 45, 46, 47, 48, 49, 50]
assignee: "@amirhossein"
tags: [pa, l4, S3, AC-7]
---

# THE EVALUATOR — candidates in, full evaluation table out

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** Everything needed to judge a candidate: prediction interval, all screen verdicts, novelty, cost.

## Job story

When I have a batch of candidate compositions, I want one call that returns every number needed to judge them, so both the enumerator and the evolutionary search share exactly one evaluation path.

## Why this exists

**The deep module of this project, and the reason tickets are cut by layer.**

Architecture A and Architecture B differ only in how candidates are *proposed* and how the
results are *selected*. The evaluation between those two steps is identical. Written once
here, both architectures consume it:

```python
evaluate(formulas, temperatures) -> DataFrame
# p10, p50, p90, lcb, interval_width, elmd_distance, nearest_known,
# cost_per_kg, hhi, <one verdict column per screen>, admissible
```

Had tickets been cut by phase, this would have been written for A and rewritten for B, and
the second copy would have drifted.

## Done when

- [ ] One public function composing the surrogate and every screen
- [ ] Returns one row per candidate with every intermediate value visible — nothing hidden
- [ ] `admissible` is a derived column, never a filter applied inside the evaluator
- [ ] Batched throughout; meets the throughput budget measured in ticket 22
- [ ] Adding a new screen requires no change to this function's signature

## Runnable check

```bash
python -m pytest tests/screens/test_evaluate.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, AC-7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
