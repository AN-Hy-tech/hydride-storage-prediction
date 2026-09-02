---
id: 10
status: backlog
priority: High
blocked_by: [9]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# Keyed merge replacing the positional concat

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** How featurisation outputs are joined into one table.

## Why this exists

`merge_datasets.py:46` concatenates three featurisation outputs with `pd.concat(axis=1)`
— **positionally, with no join key**. If any featuriser drops, reorders or skips a row, the
features silently belong to the wrong composition and every downstream number is wrong with
no error raised.

This is the highest-severity correctness defect in the audit.

## Done when

- [ ] Merge joins on `formula` (and temperature where the row is a measurement), never on position
- [ ] Row count and key-set asserted equal before and after the join
- [ ] Any unmatched key on either side raises with the keys listed
- [ ] Regression test feeds a deliberately reordered input and asserts alignment still holds
- [ ] The **L9 sentinel** (ticket 71) is wired to this module — give it a `live` check in
      `hydms/qa/sentinels.py` calling `hydms.qa.assert_merge_is_keyed` on the real merge. Gate HG-1
      goes red the moment `hydms/data/merge.py` exists without one, so this is not optional cleanup

## Runnable check

```bash
python -m pytest tests/data/test_merge.py::test_reordered_input_still_aligns -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
