---
id: 98
status: doing
priority: Normal
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l3]
---

# The LOACO run discards its own per-row predictions

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 0.25 d of code, plus one run

> **Owns (hidden behind this module):** Whether the honest protocol leaves evidence anyone can
> plot, or only a number anyone can quote.

**This card is NOT an unfreeze condition.** It was found on 2026-09-12 by #81, which needed
per-row leave-one-alloy-class-out predictions to draw the second parity panel and found that
`reports/loco/` does not hold any. The unfreeze condition is fixed and stays fixed.

## Why this exists

`hydms.surrogate.train` and `hydms.surrogate.loco` call the same `nested(...)` with the same
contender, so both produce an `Evaluation` carrying `out_of_fold` — *"one row per scored row per
contender: what the truth was and what that fold's model said about it"*. `train` writes it:

```python
# hydms/surrogate/train.py:369-378
tables = dict(zip(TABLES, (..., evaluation.out_of_fold, _run(...)), strict=True))
```

`loco` writes four tables and that is not one of them:

```python
# hydms/surrogate/loco.py:595-600
tables = {
    TABLES[0]: table,              # per-class metrics
    TABLES[1]: once,               # the summary AC-6 reports
    TABLES[2]: _chosen(evaluation),
    TABLES[3]: _run(cfg, settings, len(evaluation.outer), probe=probe),
}
```

So the honest protocol — the one whose whole point is that it scores a *held-out family* — leaves
ten aggregate rows and no scored rows, while the optimistic protocol leaves 893 of them. Every
consumer that wants to look at the two side by side is stuck with a number.

**What it already costs.** Card #81's `parity()` requires at least two readings by construction,
because a parity plot of one protocol is the optimistic number on its own page. That refusal is
correct and stays; what it means today is that **the figure the model card (#83) is supposed to
carry cannot be built from committed evidence**, and the refusal's own message says so. The
per-class R² table is the right evidence for AC-6's claim and the wrong evidence for a chart: it
cannot show *where* the model fails a family, only that it does.

**The code change is small; the run is not.** `loco` fits ten class folds and the last measured
budget is in `loco-chosen.csv` — 25 trials per class, 1652 s on the first alone. Nothing here
should start that: the maintainer runs the heavy fits. Land the code, verify at probe budget, and
hand over one command.

## Done when

- [x] `hydms.surrogate.loco` writes `evaluation.out_of_fold` as a fifth table, named to match
      `train`'s convention. Check first that the contender is built with `ScoringTask.keep` set —
      `Evaluation.out_of_fold` is *"empty unless a contender used `ScoringTask.keep`"*, so if the
      LOACO path does not set it, the table is the second half of this card rather than the first
- [x] `--emit` is untouched. `loco.md` is generated from the tables it already reads; a new table
      it does not read must not change a published byte, and the drift test says so
- [x] Verified at **probe** budget — the run that proves the table appears, its columns, and that
      its row count matches `rows_scored` summed over the classes. Not a full fit
- [x] The real run is handed over as one command with its measured cost beside it, not started
- [x] A box on **#83** records that the model card's second parity panel waits on that run, so a
      page is not shipped with one panel and a caption explaining the absence
- [x] `tests/test_figures.py::test_the_committed_loco_tables_hold_no_per_row_predictions` is
      updated when the file lands. It asserts the gap as a **measurement** today; it is the test
      that says the gap closed. *Rewritten ahead of the file as
      `test_the_committed_loco_run_keeps_every_scored_row`: it skips, naming the run, while the
      file is absent, and asserts the whole record once it is committed. Left as it was, its
      `not exists` would have gone red on the maintainer's commit for doing the right thing.*
- [ ] **The full LOACO run is done and `reports/loco/loco-out-of-fold.csv` is committed** — the
      maintainer's; the card stays `doing` until then. From the repository root in PowerShell,
      with sleep disabled (`docs/RUNNING-THE-FIT.md` Step 10). **The last one took 4 h 07 m.**

      ```powershell
      & C:\Users\Asus\miniconda3\envs\Project\python.exe -u -m hydms.surrogate.loco --target capacity | Tee-Object -FilePath .\reports\_loco-run.log
      & C:\Users\Asus\miniconda3\envs\Project\python.exe -m hydms.surrogate.loco --emit
      git diff --stat reports/loco/
      & C:\Users\Asus\miniconda3\envs\Project\python.exe -m pytest tests/surrogate/test_loco.py tests/test_figures.py -p no:cacheprovider
      ```

      Exit 0 with a new 893-row `loco-out-of-fold.csv` is success. Exit 1 means the four AC-6
      tables were written and the per-row one withheld; stderr says why. The run is seeded, so the
      diff *should* show one new file and nothing else. If any of the four tables moved, commit
      them after `--emit` anyway and record it here: that is an AC-1 finding, not a failed run.
      Then `git add reports/loco/` by name and commit; the figures test stops skipping.

## Runnable check

```bash
conda run -n Project python -m hydms.surrogate.loco --budget
conda run -n Project python -m pytest tests/surrogate/test_loco.py tests/test_figures.py
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S4, S7; `docs/PRD-inverse-design.md` — AC-6

## Narrative

- 2026-09-12: Filed by #81. The chart vocabulary was written against the committed evidence rather
  than against the card's prose, which is how the gap surfaced: the card says the parity plot
  carries "the leave-one-alloy-class-out version beside it at the same scale", and the two readings
  turn out to be stored at two different grains — 893 scored rows on one side, ten class averages
  on the other. `parity()` refuses a single-panel figure and names this card in the refusal, so the
  gap is reported at the point of use rather than discovered by whoever builds the page. Filed
  rather than fixed in place because #30 is `done` and reopening it would make `check_board.py`
  fail on a blocker that is no longer done. (by @assistant)
- 2026-09-25: **Code landed; the card stays `doing` on the run.** The first box's worry did not
  materialise: `nested_scores` hands every contender a `_keeper` on every outer fold and
  `capacity_contender` forwards `task.keep`, so the LOACO path was already filling
  `Evaluation.out_of_fold` and dropping it at the write. The change is one table,
  `loco-out-of-fold`, kept **outside** `TABLES` on purpose: `--emit` reads exactly `TABLES` and
  refuses a partial set, so adding it there would have left every checkout without the file unable
  to rebuild a `loco.md` that never quotes it. Two things beyond the card. (1) `loco.out_of_fold()`
  counts the kept rows against `rows_scored` per model and refuses a short record, because an empty
  frame writes as a valid CSV and a chart of the families that happened to be kept looks like a
  chart of all of them. (2) That refusal **never costs the run**: it fires after hours of fitting,
  so the four AC-6 tables are written regardless and only the per-row one is withheld, with a new
  exit code 1 and the reason on stderr.
  **Probe, into the scratchpad and never `reports/`:** `--trials 1 --no-screening`, 10 class folds
  in **12.3 min**, exit 0. `loco-out-of-fold.csv` came back with **893 rows**, matching
  `rows_scored` class by class (0 mismatches), the same 13 columns as `model-out-of-fold.csv` and
  **the same 893 row labels** — so the two protocols now sit at one grain, and `parity()` built both
  panels (893 beside 893) from them. `--emit` on the probe directory ran clean with the fifth file
  present. Probe numbers, not a result: macro R2 0.3168, weighted 0.2436, worst Mg -0.2561.
  `parity()`'s refusal message was reworded — it said `loco` *does not write* the rows, which
  stopped being true today; it now names the file and the run that writes it. (by @assistant)
