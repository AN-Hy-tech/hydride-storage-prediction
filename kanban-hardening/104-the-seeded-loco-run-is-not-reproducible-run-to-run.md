---
id: 104
status: todo
priority: Normal
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l3, AC-1, AC-6]
---

# The seeded LOACO run is not reproducible run to run

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 0.5 d, plus probe runs

> **Owns (hidden behind this module):** Which step of the tuned, screened, nested protocol lets
> two runs with one seed produce different numbers — and whether that step can be seeded or must
> be reported as a spread.

**This card is NOT an unfreeze condition.** It was found on 2026-09-25 by #98's full LOACO run,
whose box said in advance that a moved table is "an AC-1 finding, not a failed run". The unfreeze
condition is fixed and stays fixed.

## Why this exists

`hydms.surrogate.loco` was run twice at full budget with seed 42 on code whose fit path had not
changed. Every commit to `hydms/surrogate`, `hydms/data` and `hydms/descriptors` between the two
runs is a docstring, a comment, or `loco`'s writing code:

| | 2026-09-06 (`7149c4a`) | 2026-09-25 (#98) |
|---|---|---|
| Macro R² | 0.2734 | **0.2559** |
| Weighted R² | 0.2153 | **0.1966** |
| Mg R² / coverage | −0.3381 / 0.1146 | **−0.5084 / 0.1354** |
| MEA R² | 0.1135 | **0.0933** |
| SS R² / coverage | 0.7626 / 0.1644 | **0.7780 / 0.2329** |
| The other seven families | — | **identical to every digit** |
| Wall clock | 4 h 07 m | 4 h 48 m (288.4 min) |

**Two different failures, and they point at different places.**

1. **Mg's search chose a different configuration.** `loco-chosen.csv`: nine class folds chose the
   same parameters with the same best objective to every digit; Mg's objective went 0.10925 →
   0.10871 with different parameters. So the *tuning* on Mg's nine training families saw different
   numbers.
2. **MEA and SS chose the *same* configuration and still scored differently.** Their chosen
   parameters and objectives are identical across the runs. So the *scoring fit* with fixed
   parameters on fixed families is not reproducible either — which AC-1 claims for the deployed
   fit, measured bit-identical at 1, 4 and 20 threads (#32).

AC-1 (#32) checks the **deployed** fit: one configuration, no search, no screening. It does not
cover the nested protocol, so this did not and could not trip a gate.

**What it costs.** The transfer number is quoted in the thesis (#37's chapter, now carrying both
runs), served by the domain screen (`domain-reference.json`, Mg's transfer in every
`untrusted-family` refusal) and published in `docs/API.md`. The *verdicts* did not move (Mg and HEA
are below `min_transfer_r2` in both runs) and every per-family rank ordering held, so no refusal
changed and no argument in `hydms/screens/domain.py` broke. The numbers did.

**Candidates, not conclusions.** Label screening (CleanLab) inside each fold, the early-stopping
folds, CatBoost under a configuration AC-1 never measured (MEA's is depth 15, 34 borders), and
Optuna's pruner. The random-split `train` run may carry the same defect; nobody has run it twice.

## Done when

- [ ] **Localised by probe, not by reading.** Run `loco --trials 1 --no-screening --report <scratch>`
      twice (~12 min each) and diff the tables; then the same with screening on. Whichever arm
      differs names the step. Record both diffs here
- [ ] The step is **seeded** (and a test fails if it goes unseeded again), **or** it is recorded as
      unavoidable and the protocol reports a spread over repeats rather than one number
- [ ] `hydms.surrogate.train` is checked for the same defect, at probe budget
- [ ] If the fix changes the numbers: the maintainer reruns LOACO, then `domain --emit`,
      `refusals --emit`, `reconciliation --emit`, `apidoc --probe --emit`, and the chapter's
      transfer table and its "moves between runs" paragraph are updated to match

## Runnable check

```bash
conda run -n Project python -m hydms.surrogate.loco --trials 1 --no-screening --report <scratch>/a
conda run -n Project python -m hydms.surrogate.loco --trials 1 --no-screening --report <scratch>/b
git diff --no-index <scratch>/a/loco-per-class.csv <scratch>/b/loco-per-class.csv
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1, AC-6; `docs/PHASE-H-RUNBOOK.md` — S4; card #32 (AC-1's
scope), card #98 (the run that found it)

## Narrative

- 2026-09-25: Filed by #98. The run was committed as it came back, per #98's box, and every
  generated consumer was regenerated from it. Nothing was re-aimed to make the old numbers stand:
  neither run is "the" number while the source of the spread is unknown. (by @assistant)
