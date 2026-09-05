---
id: 34
status: backlog
priority: High
blocked_by: [31, 32, 33]
assignee: "@amirhossein"
tags: [p1, l3, S1]
---

# Train and publish artifacts v1

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The first promoted artifact version.

## Why this exists

The moment Architecture A becomes possible. Everything downstream pins this version.

Promotion requires the gates to pass — this ticket is blocked on 31, 32 and 33 for exactly
that reason.

## Done when

- [ ] Full pipeline run from `data/raw/` produces `artifacts/v1/`
- [ ] Manifest complete: git SHA, seeds, package versions, feature contract, gate results
- [ ] All Phase 1 gates pass and are recorded in the manifest
- [ ] `current` points at `v1`

## Runnable check

```bash
python -m hydms.pipeline run --promote && python -m hydms.gates run --all
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-05: **Persist-vs-refit resolved — persist. (Canonical record; #32 owns the refit side.)** `v1` is
  trained once by the slow lane (#7), frozen, and promoted; every consumer — `predict()`, the screens, the
  search, and gates AC-2/3/4 — reaches the model only through `artifacts.load(version)` (#4), never by
  retraining. This is the target state whose *absence* audit finding §2.2.1 describes ("nothing on disk, must
  re-run"), and it is what makes card #23's "fit the scaler once, never refit" enforceable rather than
  aspirational: the fitted RobustScaler, the MAPIE calibrator, the splits and the feature contract are all part
  of the frozen bundle, so nothing is left downstream to re-derive. Refit-always was the rejected alternative —
  it would void the artifact store (#4), collapse the fast/slow CI split (#6/#7), make versioned promotion and
  one-line rollback meaningless, and leave AC-4 (#33) with no fixed prediction to round-trip against. What
  persistence does **not** buy is a black box: `v1` is the source of truth for the *numbers*, but the pipeline
  that produced it must stay runnable — which is exactly what AC-1 (#32) enforces. This decision is a candidate
  for a sixth ADR under #36 (as hard to reverse and as re-litigable as the five already listed); flagged there,
  not yet acted on, since #36 is blocked on this card. (by @assistant)
