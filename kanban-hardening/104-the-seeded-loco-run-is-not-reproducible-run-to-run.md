---
id: 104
status: doing
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

- [x] **Localised by probe, not by reading.** Run `loco --trials 1 --no-screening --report <scratch>`
      twice (~12 min each) and diff the tables; then the same with screening on. Whichever arm
      differs names the step. Record both diffs here

      **2026-09-26, the four probes ran and screening is the step.** Each took **104–114 min**.
      The same no-screening probe took 12.3 min on 2026-09-25, and its tables are byte-identical
      to both of these. Per fold, 572 s against 60 s. The code did not change, so the time went
      to a machine busy with other work, and a probe's wall clock is no cost estimate unless the
      machine was idle. All four exited 0. Screening off ran at
      `d8734ec`, twice. Screening on ran at `1ac1f89` and `df10841`, whose only difference is
      `evaluate.py`'s emit date.

      | Arm | `loco-per-class` | `loco-summary` | `loco-out-of-fold` | `loco-chosen` |
      |---|---|---|---|---|
      | screening **off**, a vs b | identical | identical | identical | only `seconds` moved |
      | screening **on**, a vs b | **SS moved** | macro moved | moved | only `seconds` moved, **plus Mg's `objective`** |

      Screening on, the diffs were:

      - **SS** R² 0.79558 → **0.78408**, coverage 0.16438 → 0.13699, the same 69 rows scored
      - **macro R²** 0.26184 → 0.26069. Worst class (Mg, −0.26850) identical
      - **Mg's objective** 0.109968 → **0.109791** on identical parameters. With one trial,
        the parameters are Optuna's first sample every time, so only the inner fits moved

      These are the full run's two failures in miniature. Mg's *tuning* moved, and SS's *scoring
      fit* moved on a fixed configuration. Both screen their rows once per fold. Screening off,
      the protocol (Optuna, pruner, CatBoost, early stopping) reproduced every scored byte.

      **The cause, measured in-process.** `label_issues` called three times on SS's
      outer-training rows gave the same flagged set, but `label_quality` moved by up to
      **5.1e-4** between identical calls. With `n_jobs=1` on the forest, all three were
      **bit-identical**. scikit-learn's `ForestRegressor.predict` adds each tree's prediction
      into one array under a lock, in whatever order the threads finish
      (`sklearn/ensemble/_forest.py`, `_accumulate_prediction`). The sum's last digits therefore
      differ on every call. CleanLab sorts rows by that residual to pick the fraction it drops from
      its refits (`_find_best_k`), so a last-digit near-tie becomes a different drop set. From
      there the drift reaches the scores, and sometimes the verdict. CleanLab's own `KFold`
      takes `random_state=None` and draws from the global RNG that `CleanLearning(seed=...)`
      seeds. That is deterministic in one thread and was not the cause.
- [x] The step is **seeded** (and a test fails if it goes unseeded again), **or** it is recorded as
      unavoidable and the protocol reports a spread over repeats rather than one number

      **2026-09-26: made deterministic, not seeded, because no seed controls it.**
      `hydms.data.screening.label_issues` now builds its forest with `n_jobs=1` and **refuses**
      an `estimator` whose `n_jobs` is anything else. One thread costs 34 s a pass against 23 s
      on SS's rows, which is minutes on a run of hours. Three tests in `tests/data/test_clean.py`:
      the default forest reaches CleanLab on one thread (a spy, because the drift itself is
      intermittent and a repeat test could pass on the bug); a parallel estimator is refused;
      and two calls give `label_quality` equal bit for bit (equality, not 1e-12, because the
      drift starts at the last digit). The docstring's old "reproduces the verdict exactly,
      measured" held for one flagged set, not for the scores, and is corrected
- [ ] `hydms.surrogate.train` is checked for the same defect, at probe budget

      **Structurally covered, not yet measured.** `train` reaches screening through the same
      `capacity_contender` → `screened_rows` → `label_issues`, so the fix is the same line.
      So is `deployed_fit`, whose step 1 is the screen. AC-1 covers that and was green twice
      (#32, #34): on all 893 training rows the flagged set held still despite the drift. That
      was luck, not a guarantee. **Re-run with the fix on 2026-09-26: AC-1 passes, and every
      metric equals the sealed record in `reports/model/artifact-score.csv`** (R² 0.707064,
      RMSE 0.542028, correction +0.037355, 2,584 trees, 701 grown on). So the one-thread forest
      reproduces the promoted `v3` exactly, and the fix does not orphan the deployed artifact. What is owed is two `train --trials 1` probes into scratch,
      byte-diffed, with the fix in place. That is a heavy fit, and the maintainer runs it
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

- 2026-09-26: The four probes came back and localised the drift to label screening. The cause
  is a parallel forest's `predict`, whose sum depends on the order the threads finish. Fixed
  in `hydms.data.screening` by running that forest on one thread, with three tests. The fix
  changes which draw every screened fit gets, so the committed LOACO and random-split tables are
  one draw of the old spread, not what the fixed code reproduces. The maintainer's next full
  LOACO run is the first that should come back identical when repeated. Card stays `doing` on
  the `train` probe pair and on that rerun. Found on the way: these probes took ~110 min each
  against 12.3 min for the identical probe a day earlier, with byte-identical tables, so the
  machine was busy. (by @assistant)

- 2026-09-25: Filed by #98. The run was committed as it came back, per #98's box, and every
  generated consumer was regenerated from it. Nothing was re-aimed to make the old numbers stand:
  neither run is "the" number while the source of the spread is unknown. (by @assistant)
