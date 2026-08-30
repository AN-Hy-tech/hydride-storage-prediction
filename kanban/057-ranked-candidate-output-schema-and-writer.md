---
id: 57
status: backlog
priority: High
blocked_by: [55]
assignee: "@amirhossein"
tags: [pa, l6, S3, AC-7]
---

# Ranked-candidate output schema and writer

**Phase A — Screen-and-Rank** · **L6 Delivery** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What a published candidate list contains.

## Why this exists

Acceptance criterion AC-7: **no candidate is reported without both its ElMD distance to
the nearest known alloy and its conformal interval width.** Enforcing that in the writer,
rather than trusting the caller, is what makes the criterion structural.

## Done when

- [ ] Schema declared and validated before writing; a missing required column raises
- [ ] ElMD distance and interval width are non-nullable
- [ ] Header records artifact version, git SHA, run parameters and timestamp
- [ ] Both CSV (for the app) and a Markdown table (for the thesis) are emitted from one source

## Runnable check

```bash
python -m pytest tests/delivery/test_output_schema.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, AC-7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
