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
subject. Filed rather than reopening #81: that card is `done`, and `scripts/check_board.py` refuses
a `done` card carrying an unticked box — the same reason #97 was filed rather than reopening #25.

**It is `High` because a red full suite is the first thing the next session meets, and nothing in
CI will ever mention it.** The workflow runs `-m "not slow"`, which passes.

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

**The traceback was lost and that is the first thing to get back.** The full run was piped through
PowerShell's `Select-Object -Last 15`, which kept the summary and discarded every `FAILED` block.
Because no subset reproduces, **the only command known to produce the failure is the full run
itself** — 29 minutes, output redirected to a file, and then read the traceback. Budget for that
rather than trying to find a cheaper reproduction first: two have already been tried and both were
green.

**Before spending it, rule out a flake.** A single observation is one observation. If a second full
run is green, this is intermittent and belongs beside #97 in kind — an intermittent failure with a
named symptom and no named trigger — and the repair below is still worth making, on its own merits,
because a library that mutates global backend state is the shape that produces exactly this.

**The repair that is probably right, and must not be applied as a guess.**
`hydms/figures/render.py` imports `matplotlib.pyplot` and calls `matplotlib.use("Agg",
force=False)` — a library mutating global interpreter state, which is exactly the shape that makes
a test order-dependent. The pyplot-free API (`matplotlib.figure.Figure` plus
`FigureCanvasAgg`) needs no backend, mutates nothing global, and removes the `plt.close()`
bookkeeping with it. If the traceback points there, that is the fix. If it points somewhere else,
**do that instead** — and the pyplot removal is still worth doing, on its own merits, in the same
commit.

## Done when

- [ ] A **second full run** says whether this is deterministic or intermittent, and the answer is
      written here. One observation is one observation
- [ ] The traceback is in hand from a run that actually failed, not inferred and not from a subset.
      `pytest --tb=long` with the output redirected to a file — no subset reproduces it, so the
      29-minute run is the price
- [ ] The **cause** is named in this card's narrative, or — if two full runs disagree — the card
      says plainly that the trigger is unnamed and the repair was made on the defect's shape
      rather than on its trigger. #97 is the precedent for that being an acceptable close
- [ ] `hydms/figures/render.py` no longer imports `matplotlib.pyplot` and no longer calls
      `matplotlib.use()`. A library that renders to a file has no business choosing a backend
- [ ] `tests/test_figures.py` no longer needs `matplotlib.use("Agg", force=True)` either. If the
      renderer needs no backend, neither does its test, and a test that sets one is a test that can
      mask the defect it is there to catch
- [ ] **Green in a full run**, confirmed by `pytest` with no `-m`, and the count recorded. A fast-lane
      pass is what this defect already had
- [ ] A test that would have caught it. Ordering-dependence is invisible to every per-file run, so
      the check is either running the renderer after a deliberate global-state change, or removing
      the global state so there is nothing to depend on — the second box is the cheaper one and
      makes this box free

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
