---
id: 5
status: backlog
priority: High
blocked_by: [2, 3]
assignee: "@amirhossein"
tags: [p0, l0, AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8]
---

# Gate harness: PRD acceptance criteria as runnable checks

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** What 'passing' means. Each PRD acceptance criterion becomes executable here.

## Why this exists

PRD section 10 fixes eight acceptance criteria *before* results are seen. This turns each
into a check that exits non-zero on failure, so they are enforced rather than remembered.

Individual gate implementations are separate tickets (21, 31, 32, 33, 41, 56); this builds
the harness, registry and reporting format they plug into.

## Done when

- [ ] `hydms/gates/` with one module per criterion and a shared `Gate` protocol
- [ ] `python -m hydms.gates run --all` executes every registered gate and prints a pass/fail table
- [ ] Each gate returns a structured result (name, passed, measured value, threshold, message)
- [ ] Gate results are written into the artifact manifest
- [ ] Unimplemented gates report `SKIPPED`, never `PASSED`

## Runnable check

```bash
python -m hydms.gates run --all
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
