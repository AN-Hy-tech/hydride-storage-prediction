---
id: 84
status: backlog
priority: Normal
blocked_by: [82]
assignee: "@amirhossein"
tags: [ph, l6, S10]
---

# Batch CSV screening page

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The many-candidates journey, and the guarantee that a batch cannot launder a refusal into a number.

## Why this exists

A researcher with a list of candidate compositions should not paste them one at a time.
The risk a batch path introduces is that refusals become invisible: a spreadsheet of numbers with a few
blank cells reads as a spreadsheet of numbers.

Every row carries its own verdict out, and the download carries the same columns the single-prediction
path shows on screen. A downloaded result with no interval column would be the exact failure this phase
was built to prevent, one export away.

## Done when

- [ ] Upload a CSV of compositions and temperatures; a documented row limit; a schema error names
      the offending row
- [ ] Every output row carries the estimate, the interval, the domain verdict and the ElMD distance
- [ ] Refused rows are present in the output, marked as refused with their reason — never dropped and
      never blank
- [ ] A summary states how many rows were refused and why, before the user downloads anything
- [ ] The download includes the artifact version
- [ ] Results are sortable by interval width, so the least certain rows can be found

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_batch.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S10

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
