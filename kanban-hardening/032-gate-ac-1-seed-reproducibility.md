---
id: 32
status: done
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

- [x] Pipeline run twice with the same seed produces identical metrics
- [x] Comparison is on the metrics table, not on model file bytes (which may differ)
- [x] Any nondeterministic step is identified and either seeded or documented as unavoidable
- [x] **The `thread_count` question is settled by measurement, and the answer was "neither
      option, because the premise is false" (2026-09-06).** Both branches of the struck box below
      assumed the deployed fit might not be thread-invariant. It is. Fitting the deployed
      configuration over the real matrix at `thread_count` **1, 4 and 20** produced the same
      2,584 trees, the same best iteration 2583, the same conformal correction `+0.037355`, and
      a **bit-identical** head matrix over all 1,279 rows — so every metric agreed to the last
      digit and `max|Δ|` was exactly `0.0`. Under `Lossguide` with a Bayesian bootstrap, on this
      configuration, thread count does not reach the model.

      So: **`thread_count` stays out of `model.FIXED`.** Pinning it would change nothing
      measurable, would cap the parallelism of a 1 h 41 m run, and would not buy cross-machine
      determinism anyway — the instruction set is not something a CatBoost parameter pins. And
      **no re-run of `calibrate --save` is owed**: the struck box warned that pinning would change
      the fitted model, and nothing was pinned. `artifacts/v1` is untouched.

      **AC-1 varies the thread count instead of holding it constant**, because the stronger
      claim turned out to be free: `THREAD_COUNTS = (1, None)` — one thread and every core — and
      the two runs must still agree exactly. A gate that held it constant would stay green on a
      machine where the property had quietly stopped holding.
      `tests/gates/test_ac1_reproducibility.py::test_thread_count_is_not_in_the_fixed_parameters`
      is where a future edit to `FIXED` trips on this decision.

- [x] ~~**Two runs on one machine hold `thread_count` constant, and that may not be the property
      #34 needs (from the 2026-09-05 run).**~~ **ANSWERED by the box above.** Kept in full,
      because a measurement is only legible beside the question that asked for it.
      `model.FIXED` pins `grow_policy`, `bootstrap_type`, `task_type`, `verbose` and
      `allow_writing_files` — **not `thread_count`** — so CatBoost takes all available cores.
      Under `Lossguide` with a Bayesian bootstrap that was not *known* to be thread-invariant,
      and this gate's own home is #7's slow lane on `windows-latest`, which has a different core
      count from the maintainer's machine. The question was framed as a choice: **does AC-1 vary
      `thread_count` as well as repeat the seed, or does `thread_count` join `FIXED` and the
      question go away?** — the first a stronger claim and a slower gate, the second one line
      that "changes the fitted model if the algorithm is not already thread-invariant, which is
      the very thing nobody has measured". Somebody measured it, and the algorithm is.

- [x] Registered as `AC-1` and run by the CI slow lane

**What a green AC-1 does not establish**, stated because the gate says it in every result and a
reader of this card should not have to run it to find out: the **hyperparameter search** is not
repeated. Two nested runs are 3 h 22 m, which would put this gate in a lane nobody would run, so
it fits at the configuration `reports/model/model-chosen.csv` already records and establishes
that *the model this project ships* is reproducible. Optuna's sampler is seeded from the same
`seed`; that half is guarded by `tests/surrogate/test_model.py`.

## Runnable check

```bash
python -m hydms.gates run AC-1
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1

## Narrative

- 2026-09-06: Settled by measuring the premise rather than by choosing between the two options the
  card offered. Both options — "pin `thread_count` into `FIXED`" and "have AC-1 vary it" — were
  framed as a trade between a stronger claim and a slower, machine-dependent gate. The trade does
  not exist: three fits of the deployed configuration at 1, 4 and 20 threads are bit-identical in
  their heads over all 1,279 rows, so varying the thread count costs nothing and pinning it buys
  nothing. The general lesson is the one card #29 wrote down in a different shape — an inherited
  decision can dissolve when you measure what both of its options assume. The measurement cost
  four fits, about six minutes; deciding it by argument would have cost either a re-run of
  `calibrate --save` or a gate that could only ever be run on one machine. (by @assistant)
- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
