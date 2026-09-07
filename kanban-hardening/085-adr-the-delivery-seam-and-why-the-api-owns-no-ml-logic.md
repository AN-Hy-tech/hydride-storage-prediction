---
id: 85
status: backlog
priority: Normal
blocked_by: [78]
assignee: "@amirhossein"
tags: [ph, l7, S7]
---

# ADR: the delivery seam, and why the API owns no ML logic

**Stage S8 — Evidence and close** · **L7 Evidence** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The record of the delivery layer's one hard-to-reverse decision.

## Why this exists

Two decisions in this layer are expensive to undo and will look arbitrary to a reader who
was not present: that `predict_capacity()` is a deep module rather than a set of helpers the callers
compose, and that Streamlit talks HTTP to the API rather than calling the library in-process.

Both were chosen for the same reason — one prediction path, one set of guard rails, one thing for HG-3
to check. That reasoning belongs in an ADR, because the next person to touch this layer will otherwise
see the HTTP hop as pointless overhead and remove it.

## Done when

- [ ] An ADR under `docs/adr/` in the project's established format
- [ ] It records the decision, its context, the alternatives, and the consequences
- [ ] It names what would justify reversing it
- [ ] It is written from the `## Narrative` notes on #76, #78 and #82, not from memory
- [ ] It is listed alongside the five ADRs in #36
- [ ] **It argues the seam from both sides, not one** (added 2026-09-07 by #91). The title says the
      API owns no ML logic; the same seam also means **the library owns no I/O**. #91 writes a
      prediction record on every served answer and the writing is the service's job, because a
      `predict_capacity()` that writes to disk on every call is untestable, breaks the batch path,
      and would make #76's memoised bundle do I/O from a function with no reason to. That is a real
      trade-off with a real alternative — the library could own its own record and guarantee one
      exists however it is called — so it belongs in this ADR rather than in a second one. Two ADRs
      about one seam is how a seam ends up with two stories

## Runnable check

```bash
python scripts/check_board.py --root .
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8; `docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
