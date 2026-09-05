# Running the fit, step by step

**Who this is for.** Whoever sits down to produce the numbers Chapter 1 will quote. It assumes you
can open a terminal and run a command, and nothing else. Every step says what to type, what you
should see, and what to do when you see something else.

**What you are about to do.** Two commands. The first fits the model — about **1 h 40 m**, measured. The second
puts a confidence interval around every number it produced — about a minute. Then you commit the
result so the thesis can cite a file rather than a memory.

> **The single most important rule on this page: run the training command _once_.**
>
> Card #34 will promote the shipped model from *this* run's output. If you run it twice — once "to
> see", once "for real" — Chapter 1 ends up describing a different model from the one that ships,
> and there is no way to tell afterwards which numbers belong to which. That is the whole reason
> card #29 exists. If a run fails, that is fine: fix it and run again. Just never run a *second*
> one because the first was untidy.

---

## Step 0 — Where you are, and what tool you are using

Two things about this machine that will waste an afternoon if you do not know them.

**Use PowerShell, not Git Bash.** `conda` is not on the PATH in the Bash tool here. Every command
on this page is a PowerShell command.

**Always pass `--no-capture-output`.** Without it `conda run` sometimes swallows all output and the
command looks like it did nothing.

So every command has the same shape:

```powershell
conda run --no-capture-output -n Project python -m <module> <flags>
```

`-n Project` is the conda environment the published results were produced under. It is **not** the
machine's default Python, which has a different NumPy major version and will crash. See
[ENVIRONMENT.md](ENVIRONMENT.md).

Check you are in the right place and the right environment:

```powershell
cd D:\Hydride_Machine_learning_project
```

```powershell
git branch --show-current
```

```powershell
conda run --no-capture-output -n Project python -c "import hydms, catboost; print('ok', catboost.__version__)"
```

You should see `feat/phase-h-emergency-hardening` and `ok 1.2.8`. If the import fails, stop —
nothing below will work, and the fix is in [ENVIRONMENT.md](ENVIRONMENT.md), not here.

---

## Step 1 — Make sure the working tree is clean

```powershell
git status --short
```

You want **no source file listed** — no `hydms/`, `tests/`, `docs/` or `scripts/` line.

**Why this matters and is not just tidiness.** The document the run produces gets stamped with the
current git commit, so a reader can tie a number back to the code that produced it. If the code is
uncommitted, that stamp reads `uncommitted changes to code` and the number is tied to nothing in
particular.

**`?? reports/model/` is fine, and you should expect to see it.** The stamp is computed from
`git status --porcelain`, which lists untracked files too — but it now excludes `reports/` and
`artifacts/`, because a run's own output is not the code that produced it
(`hydms.artifacts.manifest.OUTPUT_PATHS`). Before that exclusion existed, the eight CSVs Step 4
writes into that un-ignored directory marked the run's *own* document as uncommitted, and the check
in Step 6 could never pass.

You may still want to clear the directory first, for a different reason: it holds local probe output
from card #27's calibration runs. Those are cost-check numbers, not results, and they must not be
committed at Step 7 — where you stage by name precisely so they aren't.

```powershell
Remove-Item -Recurse -Force .\reports\model
```

Nothing is lost: `python -m hydms.surrogate.calibrate` regenerates them, and the run in Step 4
recreates the directory.

If you have uncommitted work **under a source directory**, commit or stash it before the run.

---

## Step 2 — Ask what it will cost, before paying it

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.train --target capacity --budget
```

`--budget` **fits nothing.** It reads the configuration, multiplies out the work, and (if a
previous run left a timing table on disk) tells you how long that many fits took last time.

You should see something like:

```text
5 outer x 3 inner x 25 trial(s) = 375 tuning fit(s), plus 5 refit(s) and one deployed fit
no fit has been measured on this machine: ...\model-fits.csv does not exist.
```

**Read that first line.** 375 + 5 + 1 = **381 fits**. That is the whole job. The second line just
says nobody has timed a fit on this machine yet — expected, and Step 3 fixes it.

**How long will it actually take?** **Measured, for real, on 2026-09-05: 1 h 41 m** (22:03:51 to
23:44:46) for the full 25-trial run on this machine. The 3.5 h figure still written in a few places
predates the search-space narrowing in card #29 and is now badly pessimistic.

**Do not trust `--budget`'s own projection, though — it multiplies the wrong population.** It reads
the mean of `model-fits.csv`, but that table holds only the **six scored fits** (five outer refits
plus the deployed one), which train on the *full* fold and are the most expensive fits in the job.
It then multiplies that mean by all 381. Neither correction is modelled: a tuning fit trains on an
inner fold, and Optuna **pruned 2 to 19 of the 25 trials** in each outer fold on the real run. On
2026-09-05 the mean scored fit was 22.6 s, so `--budget` would have projected ~2.4 h against an
actual 1.6 h of tuning — an overestimate of about 45 %. Use it to sanity-check the *fit count*,
which it gets exactly right; treat its hours as an upper bound.

---

## Step 3 — A ten-minute smoke test, into a scratch directory

**Do not skip this.** It is the cheapest possible insurance: it runs the *entire* code path —
matrix, folds, tuning, scoring, deployed fit, SHAP, every table — at a tiny budget. If something is
broken, you find out in ten minutes instead of at minute 110 of the real run.

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.train --target capacity --trials 2 --report .\reports\_smoke
```

Two flags to understand:

- `--trials 2` runs 2 hyperparameter trials instead of 25. Same code, ~1/12th the work.
- `--report .\reports\_smoke` sends the output to a **scratch** directory, so it cannot be confused
  with the real run's tables. This is important — see the warning in Step 6.

**What you should see.** The first line is the loudest thing on the page:

```text
PROBE: 2 trial(s) against the configured 25. These numbers are a cost check, not a result.
1278 row(s) x 14 feature(s) (dev_Zunger_radii_sum, ...); 893 in 'train'
nested cross-validation: 5 outer fold(s) in 10.4 min
  catboost-multiquantile: ... r2=0.7457 ...
deployed fit: the configuration 'outer-0' chose, on its inner-fold objective 0.11882
  grown on 873 row(s), stopped on 131 at iteration 8636 ...
  explained on 873 'train' row(s) — never on a held-out split (leak L11): 42 SHAP row(s), ...
wrote ...\model-per-fold.csv
... (eight `wrote` lines in total)
```

**Do not write that `r2=0.7457` down anywhere.** It is a probe number. The command says so itself,
on its own first line, because a probe's output files look *exactly* like a real run's.

**If it finishes with eight `wrote` lines, you are ready.** Delete the scratch directory:

```powershell
Remove-Item -Recurse -Force .\reports\_smoke
```

---

## Step 4 — The real run

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.train --target capacity
```

No `--trials`, no `--report`. Defaults mean: the full 25 trials, writing to `reports/model/`.

### Three things to expect, so you do not think it has hung

1. **It prints one line and then goes quiet for about an hour and a half.** After the
   `1278 row(s) x 14 feature(s)` line there is *no output at all* until the cross-validation
   finishes. This is normal. It is a known rough edge, not a fault.
2. **Leave the terminal open and do not background it.** A backgrounded `conda run` buffers its
   output and writes nothing until it exits, so you get no feedback either way.
3. **To check it is alive**, open a *second* PowerShell window and run:

   ```powershell
   Get-Process python | Select-Object Id, CPU, StartTime
   ```

   If `CPU` is climbing between checks, it is working. If it is frozen, something is wrong.

### What "finished" looks like

The last thing you should see is **eight** `wrote ...` lines. Then check the exit code:

```powershell
echo $LASTEXITCODE
```

| Code | Meaning | What to do |
|---|---|---|
| **0** | The run finished and everything was written | Go to Step 5 |
| **2** | The *invocation* was wrong — bad config, unwritable path. Nothing was fitted | Read the error, fix it, run again. You have lost nothing |
| **3** | The run finished and **its numbers are safe**, but SHAP/PDP failed. `model-shap.csv` and `model-pdp.csv` are empty | **Do not re-run the fit.** Go to Step 5; the scores are intact. Raise the SHAP failure as its own problem |

That code 3 exists on purpose: a failure in the cheap explainability step must never throw away two
hours of boosting.

---

## Step 5 — Put intervals on the numbers

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.evaluate --emit
```

**This fits nothing** and takes about a minute. It reads the tables Step 4 wrote and produces the
document. `--emit` is what regenerates the write-up; without it you get the CSVs only.

You should see:

```text
893 out-of-fold prediction(s) in 780 canonical group(s), 5 fold(s)
run: full — 25 trial(s), screening on
  r2 (wt%): 0.7xxx [0.6xxx, 0.7xxx]  |  rows: ...  |  folds: ...
  rmse (wt%): ...
  mae (wt%): ...
wrote ...\evaluation-metrics.csv
wrote ...\evaluation-subgroups.csv
wrote ...\evaluation.md
```

### The one line you must check

```text
run: full — 25 trial(s), screening on
```

If it says **`PROBE`** or **`unknown`**, you are pointed at the wrong tables — most likely a
leftover scratch directory. The generated document will also carry a large warning banner at the
top. Do not commit that; find the right directory and run again.

### Reading the three numbers on each line

Each metric prints **three** intervals, and they are three different questions:

- **`r2 (wt%)`** — resampling canonical **compositions**. This is the headline. "The same material"
  means the same canonical composition, never the same row, because two rows can describe one alloy.
- **`rows:`** — the same thing resampling rows instead. Published only so the choice above can be
  *checked* rather than believed. On this data the two barely differ.
- **`folds:`** — a cruder interval over the five fold scores.

**The trap:** the `folds` interval is usually the **narrowest**, and it is the *least* trustworthy —
part of what it measures is that different folds trained on different amounts of data, not the
model. The most confident-looking number is the worst one. That is why all three are printed.

---

## Step 6 — Look at the document before you commit it

```powershell
code .\reports\model\evaluation.md
```

Check four things:

1. **No warning banner at the top.** A banner means a probe produced it (see Step 5).
2. **`- Code:` shows a commit hash and `(code committed)`**, not `(uncommitted changes to code)`.
   If it says uncommitted, a **source** file was modified when the run started. The run's own
   output under `reports/` and `artifacts/` does *not* count and never did mean this — that was
   the defect card #29 found mid-run on 2026-09-05, when the check could not be satisfied at all.
   The numbers are still valid; what you lose is the ability to say exactly which code produced
   them.
3. **`- Run: full — 25 trial(s), screening on`**.
4. **The headline R² is lower than `REPORT.md`'s published 0.892.** This is the **expected result,
   not a failure.** The published number came from a pipeline with thirteen validation leaks; the
   whole point of this phase is that honest numbers are lower. A number that came out *higher*
   would be the alarming outcome.

---

## Step 7 — Commit the results

> **Never run `git add -A` or `git add reports/` here.** `reports/model/` also contains CSVs from
> earlier local probes. Committing those would put cost-check numbers into the repository looking
> exactly like results — which is the single failure this whole phase exists to remove.

Stage **by name**:

```powershell
$files = @(
    "reports/model/model-per-fold.csv"
    "reports/model/model-record.csv"
    "reports/model/model-chosen.csv"
    "reports/model/model-fits.csv"
    "reports/model/model-out-of-fold.csv"
    "reports/model/model-shap.csv"
    "reports/model/model-pdp.csv"
    "reports/model/model-run.csv"
    "reports/model/evaluation-metrics.csv"
    "reports/model/evaluation-subgroups.csv"
    "reports/model/evaluation.md"
)
git add $files
```

```powershell
git status --short
```

Read that `git status` output before committing. Every staged line should be one of the eleven files
above. If anything else is staged, unstage it with `git restore --staged <file>`.

Now write the commit message. Put it **outside the repository**, so it cannot itself be committed
by accident:

```powershell
notepad $env:TEMP\commit-message.txt
```

Then commit from that file:

```powershell
git commit -F $env:TEMP\commit-message.txt
```

```powershell
git push
```

**Use `-F`, not `-m`.** This project's commit messages are full of apostrophes (`the probe's`,
`#26's`), and a PowerShell here-string mis-parses them: git receives the fragments as filenames,
fails, and leaves the tree staged with nothing committed. It looks far worse than it is, and `-F`
sidesteps it entirely — along with `%`, `"` and `$`, which need no escaping in a file.

---

## Step 8 — Close the loop

1. **Tick the `OWED` box on card #29** — `kanban-hardening/029-…md` — and add a `## Narrative`
   entry with the headline numbers and the date.
2. **Move #29 to `done`** and check the board still validates:
   ```powershell
   python scripts\check_board.py --root .
   ```
3. **Tell #34 the run exists.** #34 promotes `artifacts/v1` **from this run's output**. It must not
   fit its own model.

---

## What the eight tables are

Written to `reports/model/` by Step 4.

| File | What it holds |
|---|---|
| `model-per-fold.csv` | One row per outer fold: its scores **and its training-set size**, which is part of why folds disagree |
| `model-record.csv` | The averaged score per model, with the feature set named |
| `model-chosen.csv` | The hyperparameters each fold's search settled on |
| `model-fits.csv` | Every fit: which rows it grew on, stopped on, was scored on, and how long it took. This is what `--budget` reads next time |
| `model-out-of-fold.csv` | **One row per training row**: the truth and what the model that had *not* seen it predicted. Everything in Step 5 is computed from this |
| `model-shap.csv` | Feature importance per quantile head, with a `computed_on` column |
| `model-pdp.csv` | Partial-dependence curves, same |
| `model-run.csv` | One row saying whether this was a full run or a probe. Step 5 reads it and refuses to publish a document that does not say |

Step 5 adds `evaluation-metrics.csv`, `evaluation-subgroups.csv` and `evaluation.md`.

---

## Things that go wrong, and what they mean

| What you see | What it means | What to do |
|---|---|---|
| `command not found: conda` | You are in Git Bash | Use PowerShell |
| The command prints nothing at all | `--no-capture-output` is missing | Add it |
| `PredictionError: nothing is promoted` | You used `--artifact current` | That flag is the *second* reading and needs card #34. Run `evaluate` **without** it |
| `ModelError: the settings carry no target column` | Settings were built by hand somewhere | A code bug, not an operator error. Report it |
| `run: unknown` in Step 5 | No `model-run.csv` beside the tables | You are pointed at the wrong directory, or at output from before this feature existed |
| `run: PROBE ...` in Step 5 | Those tables came from a reduced run | Point `--report` at the real directory |
| Exit code 3 | The fit worked; SHAP did not | Keep the numbers. Do **not** re-run the fit |
| It has printed nothing for an hour | Normal (see Step 4) | Check CPU is climbing in a second window |

---

## The one thing to remember

Everything on this page is cheap and repeatable **except Step 4**. Steps 2, 3, 5, 6 and 7 can be
redone as often as you like. Step 4 happens once, and everything downstream — the artifact, the
model card, Chapter 1 — describes *that* run.

Related: [PHASE-H-RUNBOOK.md](PHASE-H-RUNBOOK.md) for why each of these guards exists,
[../kanban-hardening/029-evaluation-metrics-with-bootstrap-confidence-intervals.md](../kanban-hardening/029-evaluation-metrics-with-bootstrap-confidence-intervals.md)
for the decisions behind the numbers, and [ENVIRONMENT.md](ENVIRONMENT.md) when the environment
misbehaves.
