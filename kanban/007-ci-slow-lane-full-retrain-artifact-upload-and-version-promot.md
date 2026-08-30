---
id: 7
status: backlog
priority: Normal
blocked_by: [4, 6]
assignee: "@amirhossein"
tags: [p0, l0, S1]
---

# CI slow lane: full retrain, artifact upload and version promotion

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** How a new artifact version is produced and promoted.

## Why this exists

Retraining is expensive, so it is manually dispatched and scheduled weekly rather than run
per push. This is the promotion path: a full run produces `v{N+1}`, the gates run against
it, and it is promoted only on a full pass.

**Rollback:** promotion is a manifest pointer, so reverting to the previous version is a
one-line change, not a retrain.

## Done when

- [ ] `.github/workflows/retrain.yml` on `workflow_dispatch` and a weekly schedule
- [ ] Runs the full pipeline end-to-end from `data/raw/`
- [ ] Uploads `artifacts/v{N}/` as a workflow artifact
- [ ] `hydms.gates run --all` decides promotion to `current`
- [ ] A failed gate leaves the previous version as `current` and marks the run failed

## Runnable check

```bash
gh workflow run retrain.yml --ref main
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
