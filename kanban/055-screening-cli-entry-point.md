---
id: 55
status: backlog
priority: High
blocked_by: [53, 54]
assignee: "@amirhossein"
tags: [pa, l5, S3]
---

# Screening CLI entry point

**Phase A — Screen-and-Rank** · **L5 Search** · Estimate: 1 d

> **Owns (hidden behind this module):** How a researcher actually runs a screen.

## Why this exists

The command that makes Architecture A real:
`python -m hydms.search.run --proposer enumerate --family AB2`

It composes proposer, evaluator and ranker, and writes the ranked output. Because the
proposer is a seam, the same command runs Architecture B by changing one flag.

## Done when

- [ ] CLI takes family, proposer, artifact version, budget and output path
- [ ] Pins an explicit artifact version; refuses to run against an unpromoted one
- [ ] Progress reporting for long runs, with the candidate count known up front
- [ ] Run parameters written into the output's header so a result is self-describing

## Runnable check

```bash
python -m hydms.search.run --proposer enumerate --family AB2 --artifact current
```

## Traces to

`docs/PRD-inverse-design.md` — S3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
