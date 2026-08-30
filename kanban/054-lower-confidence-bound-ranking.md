---
id: 54
status: backlog
priority: High
blocked_by: [51]
assignee: "@amirhossein"
tags: [pa, l5, S3, R1]
---

# Lower-confidence-bound ranking

**Phase A — Screen-and-Rank** · **L5 Search** · Estimate: 0.5 d

> **Owns (hidden behind this module):** How admissible candidates are ordered.

## Why this exists

Memo 4.4: ranking by predicted mean is 'the single most likely way this project produces
nonsense', because a global optimiser will find and exploit regions where a tree ensemble is
confidently wrong.

Ranking on the LCB penalises uncertainty automatically, with no extra machinery. The
surrogate already emits `lcb` as a first-class column (28) so no caller can rank on the mean
by accident.

## Done when

- [ ] Ranking uses the `lcb` column; the mean is available for reporting but never for ordering
- [ ] Ties broken deterministically so runs are reproducible
- [ ] A test asserts that a high-mean, wide-interval candidate ranks below a lower-mean, tight-interval one
- [ ] Ranked output retains every evaluation column

## Runnable check

```bash
python -m pytest tests/search/test_rank.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
