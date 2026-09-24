---
id: 100
status: doing
priority: High
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l6]
---

# A render test passes alone and fails after the slow tests

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 0.25 d

> **Owns (hidden behind this module):** Whether the full suite can be believed when it is red.

**This card is NOT an unfreeze condition.** It was filed on 2026-09-12 by #81, whose own code is the
subject. Filed rather than reopening #81: that card is `done`, and ~~`scripts/check_board.py` refuses
a `done` card carrying an unticked box~~ — the same reason #97 was filed rather than reopening #25.

> **Correction, 2026-09-13: `check_board.py` does no such thing.** It has no checkbox rule at all —
> its docstring lists what it promises and boxes are not among it, and nothing in `scripts/` or
> `tests/` reads a `- [ ]`. Five `done` cards (#1, #14, #30, #34, #86) carry **eleven** unticked
> boxes between them right now and `python scripts/check_board.py` prints `OK   100 cards`. Filing a
> new card instead of reopening a closed one is a good **convention** — it keeps a closed card's
> history intact — but it is a convention, and six cards plus `kanban-hardening/README.md` state it
> as a mechanical check. Recorded, with the evidence, as a box on **#68**, which owns the checker.

**It is `High` because a red full suite is the first thing the next session meets, and ~~nothing in
CI will ever mention it~~.** ~~The workflow runs `-m "not slow"`, which passes.~~

> **Correction, 2026-09-13: CI mentioned it on every push, and nobody read the message.** The
> workflow does run `-m "not slow"` — and that lane was **failing on the runner** from #81 until the
> repair, while passing on this machine. See the last narrative entry: the fast lane is red in CI on
> the one completed run before the repair and green on the run after it. "Only in a full run" was a
> property of this laptop, never of the defect.

## Why this exists

`tests/test_figures.py::test_every_figure_renders_in_both_themes` fails, in both its `light` and
`dark` parametrisations, **only in a full run**:

| Command | Result |
|---|---|
| `pytest tests/test_figures.py` | **55 passed**, 4.4 s |
| `pytest -m "not slow"` | **1526 passed**, 4 deselected, 13 m 32 s |
| `pytest` (full) | **2 failed, 1527 passed**, 28 m 52 s |

~~The fast lane contains the failing test and passes, so **the trigger is one of the four `slow`
tests**~~ — **that inference was tested and is false.** It was the obvious one: the fast lane is
the full suite minus the four `slow` tests, all four of which sort before `tests/test_figures.py`
in collection order, so "the slow tests are the difference" looked like arithmetic. It is not:

| Command | Result |
|---|---|
| the four slow files **plus** `tests/test_figures.py` | **134 passed**, 16 m 28 s |

So **neither half reproduces it**. The fast lane passes without the slow tests; the slow tests pass
with the figures tests and without the rest of the suite. Whatever this is needs the *combination*
— or it is not deterministic at all, and 29 minutes of accumulated process state (memory, open
handles, a library's globals set by a test in neither group) is the actual variable. Do not
re-derive the arithmetic above; it has been walked.

**What is already ruled out, so nobody re-walks it:**

| Hypothesis | Checked | Result |
|---|---|---|
| One of the four `slow` tests is the trigger | `pytest tests/data/test_golden.py tests/gates/test_ac1_reproducibility.py tests/surrogate/test_loco.py tests/surrogate/test_selection.py tests/test_figures.py` | **134 passed.** Not it — this is the hypothesis this card was filed on |
| `shap` flips the matplotlib backend | `import shap; matplotlib.get_backend()` | It **does** — `qtagg` — and `matplotlib.use("Agg", force=True)` still switches back and `save()` renders fine. Not it on its own |
| A TensorFlow-importing test first | `pytest tests/data/test_golden.py tests/test_figures.py -k "renders or twenty"` | **3 passed.** Not it |
| The test's own `tmp_path` / path length | names are short; the isolated run writes the same files | Not it |
| **Another process running the suite at the same time** | never checked | **Open, and it is the one variable this table has never listed.** Every row above is a hypothesis about state *inside* one interpreter. On 2026-09-13 two full runs overlapped on this machine for about eighteen minutes with neither session aware of the other, which is how the gap was noticed. No claim that it caused the original red run — see the third narrative entry — but nothing excludes it either, and it is free to control for |

**The traceback was lost and that is the first thing to get back.** The full run was piped through
PowerShell's `Select-Object -Last 15`, which kept the summary and discarded every `FAILED` block.
Because no subset reproduces, **the only command known to produce the failure is the full run
itself** — 29 minutes, output redirected to a file, and then read the traceback. Budget for that
rather than trying to find a cheaper reproduction first: two have already been tried and both were
green.

~~**Before spending it, rule out a flake.**~~ **It was spent, and it is a flake.** A second full
run — 29 minutes, `--tb=long`, redirected to a file, on the same commit with a clean tree — came
back **1530 passed, 27 m 29 s, exit 0**. No failure, no traceback, nothing to read. So the two full
runs disagree, and this is **intermittent**: it belongs beside #97 in kind — a named symptom with
no named trigger — and the repair below was made on the defect's *shape* rather than on a
traceback, which is the close this card's own third box provides for.

| Command | Result |
|---|---|
| `pytest` (full), second run, same commit | **1530 passed**, 27 m 29 s — **green** |

Two things that fell out of the second run and are worth more than the run itself:

- **The collected count is 1530, and the original red run reported 1529** (2 failed + 1527 passed).
  The fast lane's own arithmetic agrees with 1530 (1526 passed + 4 deselected). So the red run was
  a test *short*, which a pure ordering effect does not explain and which nobody has accounted for.
- **There is no test-randomisation plugin.** Installed plugins are `anyio`, `dash` and `cov` only,
  so collection order is deterministic and the two runs really did execute the same tests in the
  same order to different ends. That is what makes "intermittent" the honest word rather than
  "order-dependent", which is what this card is still named after.

**The repair that is probably right, and must not be applied as a guess.** ~~probably right~~ —
**applied, on the last clause of this paragraph rather than the first.**
`hydms/figures/render.py` imports `matplotlib.pyplot` and calls `matplotlib.use("Agg",
force=False)` — a library mutating global interpreter state, which is exactly the shape that makes
a test order-dependent. The pyplot-free API (`matplotlib.figure.Figure` plus
`FigureCanvasAgg`) needs no backend, mutates nothing global, and removes the `plt.close()`
bookkeeping with it. If the traceback points there, that is the fix. If it points somewhere else,
**do that instead** — and the pyplot removal is still worth doing, on its own merits, in the same
commit.

There was no traceback to point anywhere, so it was done on its own merits and is **not claimed as
a fix**. What can be said exactly: the two lines removed were the only process-wide state the
rendering path touched, so the class of defect the card describes is no longer *possible* by that
route. Whether it was ever that route is unknown and now unknowable. One detail the paragraph
above gets slightly wrong in passing: `FigureCanvasAgg` is not needed either. `Figure.savefig`
attaches whatever canvas the output format calls for, so the import list is one name, not two.

## Done when

- [x] A **second full run** says whether this is deterministic or intermittent, and the answer is
      written here. One observation is one observation — **intermittent: 1530 passed, 27 m 29 s**
- [ ] The traceback is in hand from a run that actually failed, not inferred and not from a subset.
      `pytest --tb=long` with the output redirected to a file — no subset reproduces it, so the
      29-minute run is the price.
      **This box cannot be ticked and is why the card is still `doing`.** Three runs have now been
      spent (16 m 28 s, 17 m 09 s, 27 m 29 s) and every one was green; there is no failing run to
      take a traceback from. It is left unticked rather than reworded, because a criterion edited
      until it passes is not a criterion. What would tick it: the next full run that goes red, with
      its output redirected to a file. **The trap this card was filed on is now disarmed** — the
      original traceback was lost to a truncating pipeline, so if a red run ever happens again, the
      `## Runnable check` above is the command that keeps it.

      **2026-09-13: a failing run does exist, and it is not on this machine.** CI run
      **`34716528657`** — the fast lane, red, 8 m 28 s, on the markdown-only commit `c270b1f`
      before the repair — is the only recorded failure this card has ever had, and its log still
      holds whatever pytest printed. It could not be fetched from here: `gh run view --log-failed`,
      `gh run view --log` and the job-logs API all redirect to
      `productionresultssa1.blob.core.windows.net`, which refuses the connection from this machine,
      and the check-run annotations carry only `Process completed with exit code 1`. **A browser
      can read it.** That is the cheapest remaining route to this box and it costs minutes, not a
      29-minute run:
      `https://github.com/AN-Hy-tech/hydride-storage-prediction/actions/runs/34716528657`
- [x] The **cause** is named in this card's narrative, or — if two full runs disagree — the card
      says plainly that the trigger is unnamed and the repair was made on the defect's shape
      rather than on its trigger. #97 is the precedent for that being an acceptable close.
      **The two full runs disagree. The trigger is unnamed.** The repair below was made on the
      shape
- [x] `hydms/figures/render.py` no longer imports `matplotlib.pyplot` and no longer calls
      `matplotlib.use()`. A library that renders to a file has no business choosing a backend
- [x] `tests/test_figures.py` no longer needs `matplotlib.use("Agg", force=True)` either. If the
      renderer needs no backend, neither does its test, and a test that sets one is a test that can
      mask the defect it is there to catch
- [x] **Green in a full run**, confirmed by `pytest` with no `-m`, and the count recorded. A fast-lane
      pass is what this defect already had.
      **1531 passed, 0 failed, 26 m 45 s (1605.16 s), exit 0** — 2026-09-13, 01:01:20 → 01:28:10,
      `--tb=long -rf` redirected to a file, over the repaired renderer and this card's own edits.
      **It is the only run on this card measured on a quiet machine**, checked before starting and
      after finishing: no other `python.exe` alive either side of it. The four earlier green runs
      all overlapped another session's (see the ruled-out table's last row).
      **1531 and not 1530** because the repair added
      `test_rendering_leaves_the_interpreter_as_it_found_it`; 1530 + 1 is the whole difference, and
      the arithmetic closing is worth more than the tick
- [x] A test that would have caught it. Ordering-dependence is invisible to every per-file run, so
      the check is either running the renderer after a deliberate global-state change, or removing
      the global state so there is nothing to depend on — the second box is the cheaper one and
      makes this box free.
      `test_rendering_leaves_the_interpreter_as_it_found_it` renders in a **subprocess** and asserts
      that a fresh interpreter finishes a `save()` with pyplot still unimported and the stored
      backend unmoved. The subprocess is not ceremony: in-process, pyplot is already imported and
      the backend already pinned by whatever ran earlier — including, before the repair, the smoke
      test forty lines above it — so an in-process spelling compares two identical values and
      passes against the very code it exists to reject. It was checked by reintroducing the three
      removed lines: it goes red, naming pyplot. 1.8 s, so no `slow` marker

## Runnable check

```bash
# The only command known to produce it. ~29 min. Redirect; never pipe through a truncating filter.
conda run -n Project python -m pytest --tb=long > full-run.txt 2>&1
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/QA-PROTOCOL.md` §6

## Narrative

- 2026-09-12: Filed by #81 at close. The failure is real and was found by the *full* suite after the
  fast lane had gone green twice — which is the argument for running the full one before a handoff
  even though it costs half an hour. Two things this already taught, before the cause is known.
  **Never pipe a suite run through `Select-Object -Last N`**: the summary survives and every
  traceback is discarded, which cost a 29-minute run and bought a line that said only which tests
  failed. And **CI would never have reported this** — the workflow runs `-m "not slow"` since #86
  re-aimed it at the 20-minute cap — so the lane that catches order-dependence is the one nobody
  runs on a push. That is not an argument for putting the slow tests back in CI; it is an argument
  for the full run being part of closing a card. (by @assistant)

- 2026-09-12 (same session, later): **the hypothesis this card was filed on is refuted.** Running
  the four `slow` files followed by `tests/test_figures.py` gives **134 passed in 16 m 28 s**. So
  the difference between the green fast lane and the red full run is *not* the slow tests, even
  though subtracting one set from the other is exactly what the marker does. Both halves are green
  and only the whole is red, which leaves a combination effect or a non-deterministic one — and a
  29-minute full run is now the only known reproduction. The card body carries the corrected
  reasoning and the ruled-out table.

  **Worth noticing about the shape of the mistake, because it is the cheap one to repeat.** "The
  fast lane is the full suite minus the four slow tests, the fast lane passes, therefore a slow
  test is the trigger" is set arithmetic, and it is *valid* — for a suite where tests do not
  interact. The premise it smuggles in is independence, which is the very thing an
  order-dependent failure denies. Filing the card on it was right (it was the one testable claim
  available); stating it as the diagnosis would not have been. (by @assistant)

- 2026-09-13 (a second session, concurrent with the one above): **it is intermittent, and the
  repair landed without a traceback.** Two runs were spent looking for one. The card's prescribed
  reproduction — the four `slow` files plus `tests/test_figures.py` — gave **134 passed in
  17 m 09 s**, independently reproducing the refutation the session above had just committed. The
  full suite then gave **1530 passed in 27 m 29 s, exit 0**, on the same commit with a clean tree.
  Three green runs, no failing one, so **there is no traceback to be had** and the second box stays
  unticked with the card `doing`.

  What was removed is the mechanism rather than the fault. `render()` called
  `matplotlib.use("Agg", force=False)` and imported `pyplot`; `save()` then had to `plt.close()`
  what pyplot had registered. That is two pieces of process-wide state — a current backend and a
  global figure list — read and written by a library whose whole job is to turn a description into
  a file. It is the only such state in the rendering path: matplotlib is named in exactly two
  places in the repository, and both were these. The pyplot-free object graph
  (`Figure` → `.subplots()` → `.savefig()`) needs neither, which is matplotlib's own
  recommendation for any non-interactive context. **This does not prove the intermittent failure is
  gone** — nothing could, without a reproduction — but it removes the only route by which one
  render could have depended on what ran before it.

  Two smaller things worth keeping. **The ambient backend on this machine is `qtagg`, not `Agg`**:
  PyQt5 is installed, so a bare `get_backend()` resolves to it and drags in the GUI toolkit. That
  is the condition `force=False` was quietly negotiating with, and it is why the old test had to
  pin `Agg` itself. And the guard added here was **checked against the code it rejects** before
  being trusted: the three removed lines were put back, the test went red naming pyplot, and they
  were removed again. Its first draft ran in-process and was *vacuous* — it sat below the smoke
  test that had already imported pyplot, so it compared two identical values and passed against the
  old renderer. Moving it into a subprocess is what made it a check rather than a decoration.
  (by @assistant)

- 2026-09-13 (a third session, concurrent with the second and unaware of it until afterwards):
  **a fourth full run, green — and the variable none of the three sessions was controlling for.**
  `conda run -n Project python -m pytest --tb=long`, redirected to a file as the runnable check
  says: **1530 passed, 102 warnings, 28 m 24 s (1704.35 s), exit 0**, 00:10:59 → 00:39:28, zero
  failure markers in 49 KB of output. No traceback, because nothing failed.

  **That run is not a clean observation, and how it got dirty is worth more than its result.** The
  working tree changed *underneath it*: `tests/test_figures.py` at 00:28:47, `hydms/figures/render.py`
  at 00:29:18, this card at 00:30:34 — the second session's repair, landing mid-run. Because
  `hydms/figures/__init__.py` does not import `render` and the test imports it lazily inside the
  test body, the run collected the **old** test module at startup — `matplotlib.use("Agg",
  force=True)` still in it — and then imported the **new** pyplot-free renderer off disk at ~00:36.
  So what it actually exercised was a hybrid nobody designed: the repaired renderer under the
  unrepaired test, at the end of a full suite. Green. Weak evidence for the repair, and no evidence
  at all about the defect.

  **The same applies to the run recorded above it.** The 27 m 29 s run is described there as "on
  the same commit with a clean tree". Git was clean and the commit was the same — but the machine
  was not its own. By arithmetic it started around 00:01:18 and the fourth run started 00:10:59, so
  they shared the CPU for roughly eighteen minutes. The post-repair run was launched at 00:30:44,
  nine minutes before the fourth ended. **Three of the four "independent" green runs on this card
  overlapped each other.**

  **What this does and does not license.** It does *not* say concurrency caused the original red
  run; there is no evidence either way, and by this card's own standard nothing can be claimed
  without a reproduction. What it says is narrower and still useful: the ruled-out table was
  complete only over hypotheses about a single interpreter, "what else was running" was never in
  it, and the signature fits the one thing this defect is known for — visible only in a run long
  enough to overlap something, invisible in every subset, never seen again. It is also the cheapest
  row in the table to control for: run the suite on a quiet machine and check first.

  One smaller thing the card lists as unexplained. **The red run being a test short (1529 against
  1530) does not need a theory.** Its three commands — the file alone, the fast lane, the full run
  — were run at different points while #81 was still being developed, so a one-test difference
  between them is ordinary, not a clue.

  **And the evidence against the row I just added, which belongs here rather than nowhere.** The
  quiet run took **26 m 45 s** against the contended **28 m 24 s** and **27 m 29 s** — a cost of
  one to two minutes, not the collapse two full suites sharing four cores might have suggested.
  So the machine was not being driven anywhere near its limit, and "the suite was starved of CPU
  or memory" is a *weak* reading of the original failure on this evidence. What survives is the
  narrow claim: two processes were reading and writing one working tree, that was never on the
  list, and it is now. It is a row to be excluded cheaply, not a suspect with a motive.
  (by @assistant)

- 2026-09-13 (same session, after the commit): **CI has been red since #81, and the repair turned it
  green. That is the closest thing to a reproduction this card has ever had, and it was never
  looked at.**

  | push | CI result |
  |---|---|
  | #97, the framing correction | success |
  | **#81 — the chart vocabulary** | **cancelled**, superseded by the next push five minutes later |
  | #100's refutation — **four markdown files, no code** | **failure**, 8 m 28 s, step `pytest — fast lane, with the coverage floor` |
  | #100's repair (this commit) | **success** |
  | the commit carrying this narrative — **prose only, as a control** | **success** |

  The last row is deliberate. A prose-only push re-runs the same lane over the repaired code, so a
  second green there separates "the repair fixed it" from "the one red was itself intermittent" as
  far as two observations can. **Two green after, one red before**, and the red is on a commit that
  changed no code. That is as far as the evidence goes; a third green would not change the shape of
  the argument, and nobody should spend pushes manufacturing one.

  Read that table twice. The commit that went red changed **no code at all**; it was simply the
  first run to *complete* after #81, because #81's own run was cancelled by it before reporting.
  So the red belonged to #81 from the start and was invisible for the same reason a cancelled run
  always is — `cancel-in-progress` renders an unreported result as a supersede rather than as a
  gap. Meanwhile this card's body says the fast lane **passes**. It does, locally: the exact CI
  command, `pytest -m "not slow" --cov`, was re-run here at the same commit and gave **1527 passed,
  4 deselected, coverage 89.34 % against the 80 % floor, exit 0, 14 m 09 s**. It was failing on the
  runner and passing on this machine, which makes it a **CI-only failure** in the sense
  a CI-only failure usually means: `pyproject` floors the `figures`
  extra at `matplotlib>=3.8`, so the runner resolves a version this machine does not have, and
  the runner has no GUI toolkit where this one has PyQt5 — which is the ambient `qtagg` backend
  the deleted `matplotlib.use("Agg", force=False)` was negotiating with.

  **What this licenses, and what it does not.** The only functional change between the red commit
  and the green one is the pyplot and backend removal, so the repair is now credited with fixing
  something real rather than only with removing a mechanism. But it is **one red and one green**,
  on a card whose entire subject is a failure that appears and disappears. It is evidence, not
  proof, and a card that has already been wrong once about set arithmetic should not be confident
  here either.

  **The correction that matters most is to this card's own framing.** "It fails only in a full run"
  was never a property of the defect; it was a property of *this machine*. The fast lane — twelve
  minutes, on every push, with the traceback printed — was going red the whole time in the one
  environment nobody was reading. Three sessions spent five runs of twenty-nine minutes each
  hunting a reproduction that CI was producing for free.

  **The traceback was not recoverable from here and that is a tooling limit, not a dead end.**
  `gh run view --log-failed`, `gh run view --log` and the job-logs API all redirect to
  `productionresultssa1.blob.core.windows.net`, which refuses the connection from this machine; the
  check-run annotations carry only `Process completed with exit code 1`. **A browser on the
  maintainer's machine can read it**, and run `34716528657` is still the only recorded failure this
  card has. (by @assistant)

- 2026-09-24: **Correction: this card has never failed on CI, and the 2026-09-13 entries above
  say it did.** The log of run `34716528657` is readable from this machine now
  (`gh api .../actions/jobs/103614691893/logs`), and its one failure is
  `tests/surrogate/test_comparison.py::test_the_published_document_is_the_one_this_code_generates`,
  which is **#97's** sort tie, not `test_every_figure_renders_in_both_themes`. Every red run on the
  branch has been read. They are #86's missing mypy stubs, #93's two tests, and #97's tie three
  times. **None is a render test.** So three claims made on 2026-09-13 fall:
  "CI mentioned it on every push" (it did not), "the fast lane was failing on the runner from #81
  until the repair" (it was failing on #97, intermittently), and in `kanban-hardening/README.md`,
  "the repair turned it green … the pyplot removal fixed something real" (the green was #97's tie
  going the right way). **What stands:** the local full-run failure was real, the second box is
  still unticked, and the repair is still a good change on the defect's shape. **What changes:**
  there is no traceback anywhere, the "cheapest remaining route" in the box above does not lead to
  one, and "only in a full run" is again the only thing known about the trigger.
  Not reworded above: a narrative records what a session believed, and the correction is appended.
  (by @assistant)
