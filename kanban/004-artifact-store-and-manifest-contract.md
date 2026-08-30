---
id: 4
status: backlog
priority: High
blocked_by: [2, 3]
assignee: "@amirhossein"
tags: [p0, l0, S1, AC-1]
---

# Artifact store and manifest contract

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** What a trained artifact is, where it lives, and what is recorded alongside it.

## Why this exists

The audit's first finding: **no trained artifacts exist on disk**. The model, the fitted
scaler and the splits were never persisted, so Architecture A's 'load the fitted scaler, do
not refit' step had nothing to load.

An artifact version is this project's equivalent of a deployment environment: `v1` is
promoted to by passing gates, and later phases pin the version they consume.

## Done when

- [ ] `artifacts/v{N}/` layout defined and documented
- [ ] `manifest.json` records git SHA, all seeds, resolved package versions, the feature list and gate results
- [ ] `hydms.artifacts.save(...)` / `.load(version)` are the only ways in and out
- [ ] Loading a version whose gate results are incomplete raises rather than returning a model

## Runnable check

```bash
python -m pytest tests/artifacts -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
