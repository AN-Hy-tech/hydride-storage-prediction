---
id: 93
status: backlog
priority: High
blocked_by: [86]
assignee: "@amirhossein"
tags: [ph, l4]
---

# Two tests that fail only on the CI runner

**Stage S8 — Evidence and close** · **L4 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Whether this project's numerical claims hold on a machine that is not the maintainer's.

**This card is NOT an unfreeze condition.** It was found by #86 and is filed so it has an owner,
not to widen `docs/FREEZE.md`. The unfreeze condition is fixed and stays fixed.

## Why this exists

On 2026-09-12 card #86 made the CI fast lane finish for the first time — it had been timing out
at 20 minutes on every push since long before that card, so **no run had ever reached the summary
line that names a failure**. The first run that did, `34696231293`, named two:

```
FAILED tests/surrogate/test_conformal.py::test_calibration_moves_coverage_toward_nominal
  - assert 0.021428571428571352 <= (0.014285714285714346 + 1e-09)
FAILED tests/surrogate/test_predict.py::test_the_width_is_the_calibrated_span_and_varies_row_to_row
  - assert False
2 failed, 1440 passed, 9 skipped, 4 deselected in 761.01s (12:41)
```

**Both pass on the maintainer's machine.** The same commit, the same test selection, run locally:
`1451 passed, 4 deselected in 19 m 36 s`. So this is not a regression in the code — it is the
first time anything has asked these two questions on hardware that is not a twenty-core Windows
box, and the answer came back different.

The first failure is the informative one. `0.0214` against `0.0143` is a **gap in coverage
distance from nominal** — the test asserts calibration moves coverage *toward* the nominal level,
and on the runner it moved it further away. That is a claim about a fitted model, and the model is
CatBoost's.

**The obvious suspect is already written down, and it is not thread count.** AC-1's module
docstring records a real measurement: at `thread_count` 1, 4 and 20 the deployed fit gives the
same trees, the same best iteration, the same conformal correction and a bit-identical head
matrix — *on this machine*. It also says, in as many words, that this buys no cross-machine
determinism because "the instruction set is not something a parameter pins". Linux/x86-64 with a
different BLAS and a two-core runner is exactly the case that measurement did not cover.

So the question this card answers is: **is the difference a property of the platform, or a
property of a test that was overfitted to one machine's arithmetic?** Those need different fixes
and only one of them is a tolerance change.

## Done when

- [ ] Each failure is reproduced with its actual numbers, not inferred. The cheapest route is a
      `workflow_dispatch` or a throwaway branch that runs only these two files and prints the
      fitted quantities — the conformal correction, the raw and calibrated coverage, the widths —
      rather than only the assertion
- [ ] **Say which of the two explanations holds, with evidence.** Either the fit differs across
      platforms (then the claim the test makes is too strong and must be restated as what is
      actually guaranteed), or the fit agrees and the test's own arithmetic is what differs (then
      it is a tolerance, and `1e-09` on a *coverage difference* is the thing to justify — this
      repository's stated tolerance is 1e-12 for float comparison, and neither number is that)
- [ ] **Do not simply widen the tolerance to green the lane.** A coverage claim that only holds
      on one machine is a finding about the surrogate, and AC-3 is the gate that would inherit
      it. If the honest answer is "calibration does not reliably move coverage toward nominal on
      a small calibration set", that sentence belongs in the record, not under a looser `assert`
- [ ] `test_the_width_is_the_calibrated_span_and_varies_row_to_row` fails on a bare `assert
      False`, which says nothing. Give it a message carrying the widths it saw, whatever the
      diagnosis — a red test that does not report its measurement costs the next person the run
      again, and on this lane a run is thirteen minutes
- [ ] The CI fast lane is green, so **#86's last box can be ticked**

## Runnable check

```bash
gh run list --limit 5
conda run -n Project python -m pytest tests/surrogate/test_conformal.py tests/surrogate/test_predict.py
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8; gate AC-3 (card #31) inherits whatever this concludes

## Narrative

- 2026-09-12: Created by the #86 session. Filed rather than fixed because #86 owns the *lane*
  and this is a claim about the *surrogate*, and because diagnosing it properly needs a CI round
  trip per attempt. Worth recording how invisible this was: the two failures had been happening
  on every push for an unknown length of time, showing only as `F` characters in a progress line
  of a job that was then killed before it could say what they were. Nothing in the repository
  could have told you. See [[a-workflow-that-passes-locally-may-never-have-run]]. (by @assistant)
