---
id: 37
status: backlog
priority: High
blocked_by: [25, 29, 30, 34]
assignee: "@amirhossein"
tags: [p1, l7, S6, S7, R4]
---

# Chapter 1 revision: what exists, what was wrong, what it is now

**Phase 1 — Hardening Chapter 1** · **L7 Evidence** · Estimate: 2 d

> **Owns (hidden behind this module):** The written account of the starting line and the correction.

## Job story

When my supervisor asks what was wrong with the original pipeline, I want a written account with corrected numbers beside published ones, so I can present the audit as rigour rather than have it surface as a weakness in the viva.

## Why this exists

**The prose half of hardening Chapter 1.** Blocked on the code half because you cannot
honestly write 'here is what was wrong and here is the corrected number' before the
corrected number exists.

Covers: what the forward model is; the four broken pipeline links; the three validation
leaks; the corrected numbers beside the published ones with the reason for each change; and
the leave-one-alloy-class-out result.

Framed as a contribution, not an apology. A thesis that states its own validation limits is
stronger than one that does not.

## Done when

- [ ] Draft chapter section in `docs/chapter1-revision.md`
- [ ] Side-by-side table: published number, corrected number, which leak explains the change
- [ ] Leave-one-class-out R2 reported beside random-split R2 with the Beltrame reference
- [ ] Old-22 vs new-N feature comparison included
- [ ] Every claim traceable to a report file produced by the pipeline, not to memory

## Runnable check

```bash
test -f docs/chapter1-revision.md
```

## Traces to

`docs/PRD-inverse-design.md` — S6, S7, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
