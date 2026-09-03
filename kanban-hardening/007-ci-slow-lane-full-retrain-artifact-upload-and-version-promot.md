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

- [ ] **This lane must run on `windows-latest`, and it is now the only lane that rebuilds the
      pinned environment.** #6 measured that `environment.lock.yml` cannot be restored on Linux:
      it pins conda build strings and is win-64 by construction — `vc`, `vs2015_runtime`, four
      `m2w64-*`, `ucrt`, `win_inet_pton`, 85 Windows build strings across 253 lines — and
      `requirements-lock.txt` carries `pywin32==308`. `docs/ENVIRONMENT.md` already said the
      solve fails on a different OS; the fast lane therefore installs from `pyproject.toml`
      instead and never touches the lockfile. The consequence lands here: **nothing in CI
      currently proves `Project` still recreates.** A lockfile that has quietly stopped working
      would not be discovered until someone needed it, which is precisely when it is most
      expensive. Budget for it — `windows-latest` bills at 2× minutes on a private repository,
      the environment is 8.2 GB against a 10 GB per-repository cache budget, and
      `docs/ENVIRONMENT.md` puts a cold rebuild appreciably over its warm 7 minutes. A weekly
      schedule is the right cadence for that cost; a per-push one is not

## Runnable check

```bash
gh workflow run retrain.yml --ref main
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
