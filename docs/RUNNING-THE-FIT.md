# Running the fit, step by step

**Who this is for.** Whoever sits down to produce the numbers Chapter 1 will quote. It assumes you
can open a terminal and run a command, and nothing else. Every step says what to type, what you
should see, and what to do when you see something else.

**What you are about to do.** Three commands, and they answer three different questions:

| | Command | What it produces | Cost |
|---|---|---|---|
| **Step 4** | `hydms.surrogate.train` | The **estimate**: how well this pipeline does, from five outer folds | **1 h 41 m**, measured |
| **Step 5** | `hydms.surrogate.calibrate` | The **deployed model**: one fit, its band, its explanation, saved as an artifact | about 2 minutes |
| **Step 6** | `hydms.surrogate.evaluate` | The **document**: intervals around Step 4's numbers | about a minute |

> **You may not need Step 4.** Steps 4 and 5 are independent. The cross-validation scores every
> number Chapter 1 quotes and takes no part in building the deployed model; the deployed model is
> built from the configuration Step 4 wrote into `model-chosen.csv`, which is **committed in this
> repository**. So if the estimate you want is the one already in `reports/model/`, skip to Step 5
> — it is two minutes, and re-running Step 4 would reproduce numbers you already have.

> **The single most important rule on this page: run the _training_ command (Step 4) once.**
>
> If you run it twice — once "to see", once "for real" — Chapter 1 ends up describing a different
> model from the one that ships, and there is no way to tell afterwards which numbers belong to
> which. That is the whole reason card #29 exists. If a run fails, that is fine: fix it and run
> again. Just never run a *second* one because the first was untidy.
>
> **Step 5 carries no such rule.** It is cheap, deterministic, and can be re-run as often as you
> like — with one caveat, in Step 5 itself: each `--save` writes a *new* artifact version, because
> a version is written once and never edited.

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

You may still want to clear the directory first, for a different reason: it can hold local probe
output from earlier calibration runs. Those are cost-check numbers, not results, and they must not
be committed at Step 8 — where you stage by name precisely so they aren't. (The three
`conformal*.csv` files were exactly this until Step 5 existed to produce them for real: they sat
untracked while three committed documents quoted their row counts.)

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

**Do not skip this.** It is the cheapest possible insurance: it runs the *entire* cross-validation
path — matrix, folds, tuning, scoring, every table — at a tiny budget. If something is broken, you
find out in ten minutes instead of at minute 110 of the real run.

**Skip it if you are skipping Step 4.** It smoke-tests the cross-validation, which is the only
expensive thing here. Step 5 is its own two-minute smoke test.

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.train --target capacity --trials 2 --report .\reports\_smoke
```

Two flags to understand:

- `--trials 2` runs 2 hyperparameter trials instead of 25. Same code, ~1/12th the work.
- `--report .\reports\_smoke` sends the output to a **scratch** directory, so it cannot be confused
  with the real run's tables. This is important — see the warning in Step 7.

**What you should see.** The first line is the loudest thing on the page:

```text
PROBE: 2 trial(s) against the configured 25. These numbers are a cost check, not a result.
1278 row(s) x 14 feature(s) (dev_Zunger_radii_sum, ...); 893 in 'train'
nested cross-validation: 5 outer fold(s) in 10.4 min
  catboost-multiquantile: ... r2=0.7457 ...
deployed configuration: the one 'outer-0' chose, on its inner-fold objective 0.11882. It is
written to model-chosen.csv and read from there by `python -m hydms.surrogate.calibrate`, which
builds the deployed fit itself — this command does not.
wrote ...\model-per-fold.csv
... (six `wrote` lines in total)
```

**Do not write that `r2=0.7457` down anywhere.** It is a probe number. The command says so itself,
on its own first line, because a probe's output files look *exactly* like a real run's.

**If it finishes with six `wrote` lines, you are ready.** Delete the scratch directory:

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

The last thing you should see is **six** `wrote ...` lines. Then check the exit code:

```powershell
echo $LASTEXITCODE
```

| Code | Meaning | What to do |
|---|---|---|
| **0** | The run finished and everything was written | Go to Step 5 |
| **2** | The *invocation* was wrong — bad config, unwritable path. Nothing was fitted | Read the error, fix it, run again. You have lost nothing |

---

## Step 5 — Build the deployed fit

This is the model that ships. It is a **different fit** from anything Step 4 made, and the
difference is deliberate: it carves a calibration slice out of the training rows *before* growing a
tree, so that the conformal band can be estimated on rows the trees never saw. A band calibrated on
rows the model was fitted on under-covers exactly where it claims not to.

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.calibrate --target capacity --save
```

**About two minutes.** It reads `model-chosen.csv` for the configuration — the one an outer fold's
search chose on its *inner*-fold objective, never on a score anybody published — makes one fit,
calibrates it, explains it, and saves it.

**You can run this without running Step 4**, as long as `reports/model/model-chosen.csv` is on disk.
It is committed, so on a fresh checkout it already is.

**What you should see:**

```text
1278 row(s) x 14 feature(s); 893 in 'train'
deployed configuration: the one 'outer-0' chose, on its inner-fold objective 0.11850
calibration carve: 172 row(s) held out of 873 screened training row(s); the trees grow on 701
conformal correction +0.0xxxxx in model space, from 172 calibration row(s), for a 0.8 band ...
  on the calibration rows — raw coverage is a held-out measurement, calibrated coverage is
  nominal by construction:
    interval_coverage: 0.6xxx -> 0.8xxx (+0.1xxx)
  the test split was not read. Coverage on held-out data is gate AC-3's (card #31) ...
  explained on 701 row(s) the trees grew on — never on a held-out split (leak L11): ...
wrote ...\conformal.csv
... (five `wrote` lines in total)
saved v1: conformal, model, scaler — **no gate report**, so it cannot be promoted and predict()
refuses it. Card #34 records the gates; read it back meanwhile with
hydms.artifacts.store.load('v1', require_gates=False).
```

### Three things to read carefully

1. **`the trees grow on 701`, not 893.** That is the price of a calibrated band, and it is not a
   defect. The cross-validation in Step 4 scored folds cut from all 893 training rows, so the
   deployed model grows on fewer rows than the estimate was made with. That asymmetry is real and
   `conformal-rows.csv` publishes it. **Report it beside the score, never separately.**
2. **`raw` coverage is the honest number; `calibrated` is nominal by construction.** The calibrated
   figure on those rows is 0.8 *because the constant was fitted to make it 0.8*. It says nothing
   about generalisation. Coverage on genuinely held-out data is gate AC-3's job — card #31 — and
   this command deliberately does not touch the test split.
3. **`saved v1` — and it cannot be promoted.** The version carries **no gate report**, so
   `predict()` refuses it and `promote()` refuses it. That is correct: nobody has certified this
   model yet. Card #34 owns turning it into something promotable.

### Exit codes

| Code | Meaning | What to do |
|---|---|---|
| **0** | Fitted, calibrated, explained, saved | Go to Step 6 |
| **2** | The invocation or the calibration was wrong. Nothing was saved | Read the error and fix it. You have lost two minutes |
| **3** | The fit and its calibration are on disk, but SHAP/PDP failed — `model-shap.csv` and `model-pdp.csv` are empty | The calibration is intact. Raise the SHAP failure as its own problem |

### If you run it more than once

Each `--save` writes a **new** version — `v1`, then `v2` — because an artifact version is written
once and never edited. That is a feature, not a leak: two versions on disk is a fact you can see,
where one silently overwritten version is not. Re-running without `--save` costs nothing and
overwrites only the CSVs.

---

## Step 6 — Put intervals on the numbers

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

## Step 7 — Look at the document before you commit it

```powershell
code .\reports\model\evaluation.md
```

Check four things:

1. **No warning banner at the top.** A banner means a probe produced it (see Step 6).
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

## Step 8 — Commit the results

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
    "reports/model/model-run.csv"
    "reports/model/conformal.csv"
    "reports/model/conformal-coverage.csv"
    "reports/model/conformal-rows.csv"
    "reports/model/model-shap.csv"
    "reports/model/model-pdp.csv"
    "reports/model/evaluation-metrics.csv"
    "reports/model/evaluation-subgroups.csv"
    "reports/model/evaluation.md"
)
git add $files
```

**If you skipped Step 4**, stage only what Steps 5 and 6 rewrote — the `conformal*` trio, the two
explainability tables, and the three evaluation files. Leave Step 4's tables alone: they are the
committed record of the run that produced them, and re-staging identical bytes is noise while
re-staging *different* bytes means you re-ran something you meant to skip.

```powershell
git status --short
```

Read that `git status` output before committing. Every staged line should be one of the files above.
If anything else is staged, unstage it with `git restore --staged <file>`.

**`artifacts/v1/` is not on that list and must not be.** `artifacts/` is gitignored: a fitted
booster does not belong in git history, and the artifact is reproducible from the committed tables
in about two minutes. What travels between machines is card #7's CI upload, not a commit.

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

## Step 9 — Close the loop

1. **Add a `## Narrative` entry** to the card the run belonged to, with the headline numbers, the
   artifact version, and the date. Card #29 owns the cross-validation numbers; card #34 owns the
   artifact.
2. **Check the board still validates:**
   ```powershell
   python scripts\check_board.py --root .
   ```
3. **Tell #34 which version to promote**, by name. #34 does not fit its own model: it records a
   gate run against the version Step 5 saved and promotes that. If Step 5 was run more than once,
   say *which* version — `artifacts/` holds every save and only the manifest says which is which.
4. **Note the saved version's limits where they will be read.** It carries no gate report, so
   `predict()` and `promote()` both refuse it. That is the correct state until the gates have run
   against it, and it is not something to work around.

5. **Certify it, when there is something to certify** (added 2026-09-06):
   ```powershell
   conda run --no-capture-output -n Project python -m hydms.surrogate.promote --dry-run
   ```
   This **fits nothing**. It reads the version Step 5 saved, runs every registered gate against it,
   and prints the table. Add `--version v2` to certify a version other than the newest. Drop
   `--dry-run` and, *only if every criterion passed*, it writes a new version carrying the report
   and points `current` at it — a new version because a manifest is sealed when it is written, so
   the report of a run against `v1` cannot go into `v1`.

   **Expect it to refuse, and expect that to be correct.** `promote` requires every registered
   criterion to have passed and counts `SKIPPED` as not-passed. As of 2026-09-06 that is **5 passed,
   7 skipped**. The refusal names each one and the card that owes it.

   **Three of the seven are out of this phase's reach, and there is one supported way past them.**
   AC-5, AC-7 and AC-8 belong to phases the freeze has stopped, so no Phase H work makes them
   green. Card #34 settled how to proceed: name them, one at a time, to `--waive`.

   ```bash
   python -m hydms.surrogate.promote --waive AC-5 --waive AC-7 --waive AC-8
   ```

   The waiver is written into `artifacts/current.json`, never into the manifest — the promoted
   version's embedded report still records all three as `SKIPPED`, and `hydms.artifacts.waived()`
   is what reads the decision back. A **failed** criterion can never be waived, and neither can one
   that passed.

   **Do not waive AC-6, HG-2, HG-3 or HG-4.** They are skipped today and every one of them is work
   this phase owes (#30, #77, #79, #86), so waiving one would be waiving the work rather than the
   scope. `tests/artifacts/test_waiver_scope.py` derives which criteria a frozen phase owns and
   pins the answer; the command prints each waiver's owning card so you can see which board it is
   on. Until those four land, the command still refuses — by design, and now for a reason the
   phase can actually act on.

   Runs AC-1, which fits twice: about **two minutes**, most of the command's wall time.

---

## Step 10 — Leave-one-alloy-class-out, when you have another half day

**This is a second heavy run, not a variation on the first.** Ten class folds where Step 4 has
five, so the same nested search costs about **twice** what Step 4 did. Cost it before you start
it:

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.loco --budget
```

It fits nothing and reads the fit times Step 4 already measured. On this machine it reports
**4.7 h** — 10 class folds x 3 inner x 25 trials = 750 tuning fits at 22.6 s each.

Then, in a terminal you can leave open, the same way as Step 4:

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.loco --target capacity
conda run --no-capture-output -n Project python -m hydms.surrogate.loco --emit
```

The first writes four tables into `reports/loco/`; the second rebuilds `loco.md` from them. As
in Step 7, **read the document before committing it**: no probe banner at the top, ten classes
in the per-class table, and a `Random split` row that is populated rather than blank.

**What this number is for, and what it is not.** It is the extrapolation figure — how the model
does on a family it has never seen — and it is **expected to be much worse** than the
random-split R² Step 4 produced. That gap is a finding about hydride chemistry and about what
the inverse design may safely propose (card #48); it is not a fit to go back and improve. AC-6
asks only that the two numbers be published side by side, which is why the summary table carries
both in one row and the gate fails if either is missing.

Then commit `reports/loco/` **by name** and re-run the gate:

```powershell
conda run --no-capture-output -n Project python -m hydms.gates run AC-6
```

Until the run has happened it reports `SKIPPED` and names this command; afterwards it passes on
the committed tables, and Step 9's promotion has one fewer criterion outstanding.

---

## What the tables are

Six from Step 4, five from Step 5, three from Step 6 — all into `reports/model/`.

**Step 4 — the estimate:**

| File | What it holds |
|---|---|
| `model-per-fold.csv` | One row per outer fold: its scores **and its training-set size**, which is part of why folds disagree |
| `model-record.csv` | The averaged score per model, with the feature set named |
| `model-chosen.csv` | The hyperparameters each fold's search settled on |
| `model-fits.csv` | Every fit: which rows it grew on, stopped on, was scored on, and how long it took. This is what `--budget` reads next time |
| `model-out-of-fold.csv` | **One row per training row**: the truth and what the model that had *not* seen it predicted. Everything in Step 6 is computed from this |
| `model-run.csv` | One row saying whether this was a full run or a probe. Step 6 reads it and refuses to publish a document that does not say |

**Step 5 — the deployed model:**

| File | What it holds |
|---|---|
| `conformal.csv` | The conformal correction: one number, the band it targets, and how many rows produced it |
| `conformal-coverage.csv` | Raw against calibrated coverage on the calibration rows. The **raw** column is the real measurement |
| `conformal-rows.csv` | The row accounting the carve implies: 893 train, 20 screened out, 172 calibration, 701 grown on |
| `model-shap.csv` | Feature importance per quantile head, with a `computed_on` column. **Of the deployed fit** — it moved here from Step 4 when the deployed fit did |
| `model-pdp.csv` | Partial-dependence curves, same |

**Step 6 — the document:** `evaluation-metrics.csv`, `evaluation-subgroups.csv` and `evaluation.md`.

**Step 10 — leave-one-alloy-class-out**, into `reports/loco/`:

| File | What it holds |
|---|---|
| `loco-per-class.csv` | One row per alloy class: R², MAE, **`rows_scored` and `compositions_scored` beside them**, and `estimable` with the reason when R² is undefined rather than bad |
| `loco-summary.csv` | The row AC-6 is about: the macro average, the support-weighted one, the worst and best class, and the **random-split number beside them**. Neither figure can be published here without the other |
| `loco-chosen.csv` | The hyperparameters each class fold's search settled on |
| `loco-run.csv` | Full run or probe. AC-6 reads it and **fails** on a probe's tables, which are the same shape as a real run's |

---

## Things that go wrong, and what they mean

| What you see | What it means | What to do |
|---|---|---|
| `command not found: conda` | You are in Git Bash | Use PowerShell |
| The command prints nothing at all | `--no-capture-output` is missing | Add it |
| `PredictionError: nothing is promoted` | You used `--artifact current` | That flag is the *second* reading and needs card #34. Run `evaluate` **without** it |
| `ModelError: the settings carry no target column` | Settings were built by hand somewhere | A code bug, not an operator error. Report it |
| `run: unknown` in Step 6 | No `model-run.csv` beside the tables | You are pointed at the wrong directory, or at output from before this feature existed |
| `run: PROBE ...` in Step 6 | Those tables came from a reduced run | Point `--report` at the real directory |
| Exit code 3 from Step 5 | The fit and its calibration worked; SHAP did not | Keep the calibration. Raise the SHAP failure separately |
| `ArtifactError: ... v1 already exists` | You ran Step 5 with `--save` twice | Expected — a version is written once. Save again and it writes `v2`, or drop `--save` |
| `GatesIncomplete` from anything that predicts | The saved version carries no gate report | Correct behaviour, not a fault. Card #34 records the gates |
| It has printed nothing for an hour | Normal (see Step 4) | Check CPU is climbing in a second window |

---

## The one thing to remember

Everything on this page is cheap and repeatable **except Step 4**. Steps 2, 3, 5, 6, 7 and 8 can be
redone as often as you like. Step 4 happens once, and the numbers Chapter 1 quotes describe *that*
run.

**Step 5 is not part of that rule, and it matters that it is not.** The deployed model is rebuilt
from Step 4's committed `model-chosen.csv` in about two minutes, and rebuilding it cannot move a
single number Step 6 published — the estimate comes from five outer-fold models that no deployed
fit takes any part in. So a mistake in the deployed fit is cheap to correct, which is exactly what
you want of the artifact that ships.

Related: [PHASE-H-RUNBOOK.md](PHASE-H-RUNBOOK.md) for why each of these guards exists,
[../kanban-hardening/029-evaluation-metrics-with-bootstrap-confidence-intervals.md](../kanban-hardening/029-evaluation-metrics-with-bootstrap-confidence-intervals.md)
for the decisions behind the numbers, and [ENVIRONMENT.md](ENVIRONMENT.md) when the environment
misbehaves.
