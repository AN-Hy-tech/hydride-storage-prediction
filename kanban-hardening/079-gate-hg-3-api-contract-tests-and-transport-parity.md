---
id: 79
status: backlog
priority: High
blocked_by: [78]
assignee: "@amirhossein"
tags: [ph, l6, HG-3, AC-4]
---

# GATE HG-3: API contract tests and transport parity

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** The guarantee that going over HTTP does not change the answer, and that the published contract does not change without someone noticing.

## Why this exists

AC-4 checks that known alloys round-trip through `predict()`. It says nothing about what
happens at the transport boundary, where a float can be truncated by serialisation, a column can be
reordered by a dict round-trip, and an interval can be dropped by a response model that forgot a field.

This gate extends AC-4 to the edge of the system: for the same input, the API's answer and
`predict_capacity()`'s answer must be the same answer. It also snapshots the OpenAPI document, so that
a breaking contract change is a visible diff rather than a surprise for whoever wrote a client.

## Done when

- [ ] For a fixed set of inputs spanning normal, boundary and refused cases, the API result equals
      `predict_capacity()`'s result — including the interval bounds, to full precision
- [ ] The OpenAPI document is snapshotted; a change to it fails the test until the snapshot is updated
      deliberately
- [ ] Every refusal reason code in #77 is reachable through the API and asserted
- [ ] Batch results are order-preserving and per-row refusals do not fail the whole request
- [ ] Registered in the gate harness as HG-3

## Runnable check

```bash
conda run -n Project python -m hydms.gates run HG-3
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6, HG-3; `docs/PRD-inverse-design.md` — AC-4

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
