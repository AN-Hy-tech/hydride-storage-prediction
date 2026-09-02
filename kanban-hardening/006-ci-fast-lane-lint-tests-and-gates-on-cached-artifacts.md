---
id: 6
status: backlog
priority: High
blocked_by: [5]
assignee: "@amirhossein"
tags: [p0, l0, S1]
---

# CI fast lane: lint, tests and gates on cached artifacts

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** The per-push feedback loop.

## Why this exists

Full CI from the start was chosen. Retraining the surrogate is not a per-push job, so the
pipeline splits: this fast lane runs on every push and must finish in minutes, using the
published artifact version rather than training a new one. The slow lane is ticket 7.

## Done when

- [ ] `.github/workflows/ci.yml` runs on push and PR against `main`
- [ ] Steps: env from lockfile (cached), `ruff`, `mypy`, `pytest`, then `hydms.gates run --fast`
- [ ] Conda env cached by lockfile hash so a warm run is under ~5 minutes
- [ ] The workflow fails on any gate failure, not only on test failures

## Runnable check

```bash
gh workflow run ci.yml --ref main && gh run watch
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
