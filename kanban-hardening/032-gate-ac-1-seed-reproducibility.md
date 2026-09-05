---
id: 32
status: backlog
priority: High
blocked_by: [5, 26]
assignee: "@amirhossein"
tags: [p1, l3, AC-1]
---

# GATE AC-1: seed reproducibility

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the same seed produces the same numbers.

## Why this exists

PRD acceptance criterion 1. Without this the whole reproducibility claim is unverified,
and the artifact manifest's recorded seeds are decorative.

## Done when

- [ ] Pipeline run twice with the same seed produces identical metrics
- [ ] Comparison is on the metrics table, not on model file bytes (which may differ)
- [ ] Any nondeterministic step is identified and either seeded or documented as unavoidable
- [ ] **Two runs on one machine hold `thread_count` constant, and that may not be the property
      #34 needs (from the 2026-09-05 run).** `model.FIXED` pins `grow_policy`, `bootstrap_type`,
      `task_type`, `verbose` and `allow_writing_files` — **not `thread_count`** — so CatBoost takes
      all available cores. Under `Lossguide` with a Bayesian bootstrap that is not guaranteed
      thread-invariant, and this gate's own home is #7's slow lane on `windows-latest`, which has a
      different core count from the maintainer's machine.

      **The #34 half of this box is gone; the gate half remains (2026-09-06).** #34's open decision
      is settled — the deployed fit is rebuilt from `model-chosen.csv` in two minutes by
      `calibrate --save`, so nothing is asking this gate to license an equality claim between two
      fits any more. What is still a real question is this gate's own subject: **does AC-1 vary
      `thread_count` as well as repeat the seed, or does `thread_count` join `FIXED` and the
      question go away?** The second is one line and makes the gate answerable on any machine; the
      first is a stronger claim and a slower gate. Note that adding `thread_count` to `FIXED`
      **changes the fitted model** if the algorithm is not already thread-invariant — which is the
      very thing nobody has measured — so it is a decision to take deliberately, and to re-run
      `calibrate --save` after, not a tidy-up.

- [ ] Registered as `AC-1` and run by the CI slow lane

## Runnable check

```bash
python -m hydms.gates run AC-1
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
