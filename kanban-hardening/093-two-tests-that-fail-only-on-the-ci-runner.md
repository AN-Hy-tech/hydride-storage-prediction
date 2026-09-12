---
id: 93
status: doing
priority: High
blocked_by: []
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

- [x] Each failure is reproduced with its actual numbers, not inferred. **Reproduced 2026-09-12,
      and not on a runner.** Two independent CI runs (`34696231293`, `34697694205`) print the same
      digits, so the runner is deterministic run to run. Then a throwaway venv **on the
      maintainer's own Windows box**, built on the versions CI resolved, reproduced both failures
      exactly — see the table below. The diagnostic route the box suggests was not needed and the
      round trip it budgets for is not the cost of this bug
- [x] **Say which of the two explanations holds, with evidence.** **Neither, and the dichotomy had
      a false premise.** The fit does differ, so the first explanation is closer — but the
      variable is not the platform. It is the **dependency resolution**: `suite` runs
      `pip install -e ".[dev,uq,novelty,api]"`, which resolves `pyproject.toml`'s **floors**, not
      `requirements-lock.txt`'s pins. `catboost>=1.2` resolved to **1.2.10**; the `Project`
      environment holds **1.2.8**, and 1.2.10 fits a different tree. Same box, same instruction
      set, same BLAS, different wheel, both failures:

      | | `Project` env — win, cb 1.2.8 | throwaway venv — win, cb 1.2.10 | CI runner — linux, cb 1.2.10 |
      |---|---|---|---|
      | raw coverage | 49/56 = 0.875 | 44/56 = 0.7857142857142857 | 0.7857142857142857 |
      | calibrated coverage | 0.8214285714285714 | 0.8214285714285714 | 0.8214285714285714 |
      | conformal correction | −0.016076918528258766 | +0.004202829215724568 | — |
      | trees | 7 | 9 | — |
      | widths, wt% | 1.2297, 0.1671, 0.1573 | 1.3731404613150833, −0.09442177798242923, −0.02975993899460505 | 1.373140, −0.094422, −0.029760 |

      The runner also carried scikit-learn 1.7.2 and pandas 2.3.3 against 1.6.1 and 2.3.1 here;
      the venv carried all three bumps, so CatBoost is the suspect by role rather than by
      elimination. It does not change the conclusion: **nothing here is a property of Linux, of a
      two-core runner or of an instruction set.** AC-1's docstring is right that its
      thread-invariance measurement buys no cross-machine determinism, and it was the wrong
      suspect for this
- [x] **Do not simply widen the tolerance to green the lane.** No tolerance was widened, and
      `1e-09` was never the question. The first assertion compared a **constant to a variable**.
      Calibrated coverage on the calibration rows is `ceil((n + 1) * level) / n` =
      `ceil(57 * 0.8) / 56` = **46/56 = 0.8214285714285714** on all three configurations, to every
      digit, because split CQR takes the correction to be the k-th smallest conformity score and
      exactly k of n rows then sit inside the widened band. It does not know what the fit did. The
      **raw** coverage does — 49/56 here, 44/56 there — so `|calibrated − nominal| <=
      |raw − nominal|` was an assertion that the *uncalibrated* heads are worse than the conformal
      overshoot, which is a property of CatBoost and not of the calibration.

      **And the claim is not one conformal prediction makes.** It promises coverage ≥ nominal, not
      coverage nearer nominal; on a finite calibration set the guaranteed value overshoots by up
      to `(1 + level) / n`, here 1.8/56 = 0.032. Whenever the raw band is already inside that
      overshoot the old test *must* fail. It failed on the runner because the runner's raw band
      was **better**, not worse. The sentence the box asks for belongs in the record and is now in
      the test's own docstring; what is asserted instead is the rank identity, the `>= nominal`
      guarantee and the overshoot bound, all three of which are theorems and hold on every
      configuration measured. **AC-3 inherits nothing to weaken** — it measures coverage on the
      *test* split, which is generalisation; this test only ever measured arithmetic on the
      calibration rows
- [x] `test_the_width_is_the_calibrated_span_and_varies_row_to_row` fails on a bare `assert
      False`. Both tests now carry a `measured` string — coverages, counts, the rank, the
      correction, the raw crossings; the widths and the heads — so a future red reports its
      numbers. The `assert False` was
      `assert (frame[INTERVAL_WIDTH] > 0.0).all()`, and **that assertion contradicted a property
      the repository has already measured and decided not to repair.** Two of three candidates
      came back with an inverted band. `quantile_metrics` returns `crossings` precisely because
      "MultiQuantile fits the heads jointly but does not constrain them to be monotone …
      **measured at 23 % of rows on a small fit**, so this is a real number to report rather than
      a defensive zero" (`hydms/surrogate/model.py:1291`), and `hydms/surrogate/conformal.py`'s
      header states that **CQR's widening cannot repair a crossing**. The correction is +0.0061
      against crossings of −0.09 and −0.03; no constant closes those. Two of the three candidates
      (`Ti1Fe1`, `Mg2Ni1`) are outside the fixture's La–Ni training family, which is where
      crossing is likeliest — so the test asserted that three hand-picked extrapolation candidates
      all dodge a ~23 %-probability event, and passed here at about coin-flip odds. It now asserts
      that the width *is* the calibrated span and is not one constant, and a new deterministic
      sibling, `test_a_crossed_band_reaches_the_caller_unclipped`, pins the sign behaviour on the
      assembly step where no fit can move it
- [ ] The CI fast lane is green, so **#86's last box can be ticked**

## Runnable check

```bash
gh run list --limit 5
conda run -n Project python -m pytest tests/surrogate/test_conformal.py tests/surrogate/test_predict.py
```

Neither failure needs a runner to reproduce any more, and that is the cheap part of this card to
keep. A venv on the versions CI resolves reproduces both on Windows:

```bash
conda run -n Project python -m venv /tmp/ci-versions
/tmp/ci-versions/Scripts/python -m pip install "catboost==1.2.10" "scikit-learn==1.7.2" \
    "pandas==2.3.3" "numpy==1.26.4" "scipy==1.15.3" "mapie==1.5.0" "joblib==1.6.0" PyYAML pytest
/tmp/ci-versions/Scripts/python -m pip install --no-deps -e .
/tmp/ci-versions/Scripts/python -m pytest tests/surrogate/test_conformal.py tests/surrogate/test_predict.py
```

The resolved versions come from the run log: `gh run view <id> --log | grep "Successfully installed"`.

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8; gate AC-3 (card #31) inherits whatever this concludes

## Narrative

- 2026-09-12: Created by the #86 session. Filed rather than fixed because #86 owns the *lane*
  and this is a claim about the *surrogate*, and because diagnosing it properly needs a CI round
  trip per attempt. Worth recording how invisible this was: the two failures had been happening
  on every push for an unknown length of time, showing only as `F` characters in a progress line
  of a job that was then killed before it could say what they were. Nothing in the repository
  could have told you. See [[a-workflow-that-passes-locally-may-never-have-run]]. (by @assistant)

- 2026-09-12: Diagnosed. **The card's own "obvious suspect" paragraph above is wrong, and it is
  left standing because being wrong in a specific way is the lesson.** It reasoned from AC-1's
  thread-invariance measurement to Linux, BLAS and a two-core runner — a chain about *hardware*,
  every link of which is plausible and none of which was checked. The variable was the
  `pip install` line. `suite` installs from `pyproject.toml`'s floors (`catboost>=1.2`), not from
  `requirements-lock.txt`, and it resolved **catboost 1.2.10** against the `Project` environment's
  **1.2.8**. A venv on the resolved versions reproduces both failures on this Windows box, to
  every digit the runner printed. The first thing to read when a test fails only on CI is
  `Successfully installed`, not the runner's `uname` — and it costs one `gh run view`, not a round
  trip.

- 2026-09-12: What the two failures turned out to be, because neither is what the summary line
  suggested. **The first was a test comparing a constant to a variable.** Calibrated coverage on
  the calibration rows is the conformal rank over n, `46/56`, on every configuration measured —
  the machine-independent half — while the *raw* coverage, which is the fitted half, moved from
  49/56 to 44/56. The old assertion said "calibration moves coverage toward nominal", which
  conformal prediction does not promise: it promises coverage ≥ nominal, and the finite-sample
  overshoot means a raw band that is *already good* makes the assertion fail. The runner failed it
  by having a **better** uncalibrated model. **The second was a test contradicting a decision this
  repository had already made and measured.** Quantile crossing is counted by `quantile_metrics`
  at 23 % of rows, `conformal.py` says CQR cannot repair it, and the test demanded three
  extrapolation candidates all avoid it. See [[a-written-down-invariant-settles-a-design-question]]
  — both fixes were found by reading what the code already says it guarantees, not by choosing a
  tolerance.

- 2026-09-12: A finding this card does not own, filed as **#94**: a crossed band leaves
  `hydms.surrogate.predict` as a negative width by design, and
  `hydms.delivery.contract.Interval` then raises `ContractError` on `upper < lower`.
  `hydms/delivery/predict.py` never mentions crossing, so that is a **loud failure rather than a
  refusal with a reason code** — the one shape of answer this project has decided it does not
  give. Not an unfreeze condition; #77 and #90 are both `done`, so it gets a card rather than a
  box on a closed one. See [[write-findings-as-card-boxes]] and
  [[this-project-catches-bugs-by-refusing-not-logging]]. (by @assistant)

- 2026-09-12: The `blocked_by: [86]` edge was removed, and it is worth saying why rather than
  quietly deleting it. It pointed the wrong way. #86 **found** this card's subject, which is not
  the same as this card needing anything from #86 — everything needed to diagnose it was already
  written down in the failure block above — and #86's own last open box says "Blocked on #93". The
  graph therefore held shut the one card that could open it, while `check_board.py` refused to let
  it move to `doing` at all. See [[blocked-by-is-the-graph-runbook-arrows-are-prose]]: the edge to
  audit is the one the card's own Done-when cannot justify. (by @assistant)
