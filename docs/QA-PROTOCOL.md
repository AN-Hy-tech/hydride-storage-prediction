# QA protocol

What a card must prove before it may be called done.

This exists because every card on the board carries a `## Runnable check`, and nothing otherwise says
what that check has to *cover*. Without a standard, a check degenerates into `import hydms` and the
phase ships a green build over untested code — which is close to what happened before: the archival
pipeline has two files named `test_*.py` and neither is a test.

Scope: `hydms/`, `tests/`, `app/` and `scripts/`. `Machine_Model/` is archival and out of scope
([FREEZE.md](FREEZE.md)).

---

## 1. The four kinds of test, and when each applies

| Kind | Answers | Use it when |
|---|---|---|
| **Golden** | "Does this still produce the value it produced before?" | A transformation with a known, stable output — loaders, the merge, splits, the featuriser |
| **Metamorphic** | "Do two related inputs stand in the right relation?" | There is no oracle. Permutation, scaling, whitespace, monotonicity — see card #74 |
| **Contract** | "Does the boundary keep its promise?" | Anything with an external consumer — the prediction contract, the API, the batch writer |
| **Sentinel** | "Is the defect still absent?" | A leak was removed and must stay removed. Marked `leak`; gate HG-1 |

A sentinel is the one kind that is written *against* a specific past failure. It must be demonstrated
to go **red** when its defect is reintroduced, and the demonstration recorded in the card's
`## Narrative`. A sentinel nobody has seen fail is an assumption with a test's name on it.

Since card #71 that demonstration is also **executable**, and the narrative note is no longer the
only record of it. Every sentinel in `hydms/qa/sentinels.py` carries `Reproduction` pairs — the leak
in miniature, which must raise, beside the corrected version of the same thing, which must not — and
gate HG-1 runs all of them. A one-time demonstration decays silently the moment somebody loosens an
assertion to make a build pass; this one goes red instead, naming the leak. **A new sentinel adds a
reproduction pair, not just a test**, and the corrected twin must differ from the leaky case only in
the defect. A clean twin that also changes the shape of the data proves nothing: it passes for the
wrong reason, and the sentinel is then measuring its fixture rather than its subject.

The second half of a sentinel's life is being pointed at the real thing. Sentinels are written in
stage S1, against miniatures, because the modules they guard do not exist yet; each names the module
it expects, and HG-1 turns **red** the moment that module appears with nothing wired to it. That is
deliberate — it is the only reliable way a guard written six weeks early becomes a guard at all.

---

## 2. What each layer must prove

| Layer | A card here is not done until it has shown |
|---|---|
| **L0 Foundation** | Config resolves with no absolute path. Seeds reproduce. The artifact manifest round-trips. Every gate registered here can **fail**, demonstrated. The whole chain runs end to end on a committed fixture, inside the fast lane, and twice with one seed gives one answer (#73). |
| **L1 Data** | Row counts at every stage, asserted not assumed. The merge is keyed: reordering an input never changes the answer *silently*, and a row it cannot key makes it fail. No canonical composition spans two splits. Held-out targets **and feature values** are byte-identical before and after any screening stage. |
| **L2 Descriptors** | Parity with CBFV to 1e-9 across all 1,279 formulae (AC-2). Permutation and scale invariance. Both element tables are exercised — a single-table result cannot pass. |
| **L3 Surrogate** | The scaler is fitted exactly once and never refitted downstream. No fold is both tuned on and scored on. The test split is never passed to `fit`. Quantile column order asserted by position. Conformal coverage within a few points of nominal (AC-3). |
| **L4 Screens** | Every screen returns a verdict **with a reason**; no silent drop. Boundary cases on each window are covered, both sides. |
| **L6 Delivery** | The result type cannot be constructed without an interval and a domain verdict (HG-2). The API's answer equals the library's for the same input (HG-3). Every refusal reason code is reachable and asserted. |
| **L7 Evidence** | Every number quoted in prose traces to an artifact that exists and currently holds that value. |

---

## 3. Definition of done

A card moves to `done` only when all of these hold.

- [ ] Its `## Runnable check` passes **and could fail** — you have seen it red at least once.
- [ ] Every box under `## Done when` is ticked, or the card says explicitly why one was dropped.
- [ ] Tests cover the failure the card exists to prevent, not merely the happy path.
- [ ] `ruff check` and `mypy` are clean.
- [ ] Coverage has not fallen.
- [ ] `python scripts/check_board.py --root .` and `python scripts/check_freeze.py` pass.
- [ ] `## Narrative` records anything the card taught you — especially anything that contradicts a
      document. Those notes are what the ADRs (#36) and the Chapter 1 revision (#37) are written from.
- [ ] No number was copied into prose that a test does not check.

---

## 4. Reviewer checklist

Read the test first, then the code. Ask:

1. **Would this test fail if the feature were broken?** Delete a line of the implementation in your
   head. Does something go red? If not, the test is describing, not checking.
2. **Does any held-out data influence anything before it is scored?** This is the question the phase
   exists for. Follow val and test through every stage of the diff.
3. **Is a fitted object fitted more than once?** Scalers, selectors, encoders. Fit belongs to training.
4. **Does a number in the prose match the artifact it claims to come from?** Open the CSV.
5. **Is a boundary asserted on both sides?** A window test that only checks the inside is half a test.
6. **Does a failure say what to do?** An assertion message that reads `assert False` costs the next
   person an hour.
7. **Has anything crossed a layer boundary?** ML logic in a route handler, a path literal in the
   surrogate, a screen that reaches into the model.

---

## 5. Rules with no exceptions

**A gate must be able to fail.** Before registering a gate, make it red on purpose and record that you
did. `hydms/gates/` returns SKIPPED for an unimplemented gate, never PASSED — a gate that cannot
distinguish "checked and fine" from "not checked" is worse than no gate, because it reports safety it
has not established.

**Held-out data is read once, at the end.** It is never used to choose a hyperparameter, a stopping
iteration, a feature set, a model, or an ensemble member — and its labels are never rewritten. Every
one of those was a real defect in the archival pipeline; the list with line numbers is
[PHASE-H-RUNBOOK.md](PHASE-H-RUNBOOK.md) §1.

**Grouping uses the canonical composition key, never the raw formula string.** 1,149 formula strings
in this dataset describe 1,115 materials. Splits, folds, and any `group_by` use the canonical key.

**No prediction leaves the system without an interval and a domain verdict.** Enforced by the type,
not by convention (#75), and gated by HG-2.

**A test may not be weakened to make a build pass.** Lowering the coverage floor, deleting an
assertion, or adding an `xfail` is a review conversation, and the reason goes in the card's narrative.

**A sentinel's subject is checked when the subject moves, not only when it disappears.** A sentinel
asserts a relationship *about a named object*. Section 1 already covers the case where that object
does not exist yet — HG-1 goes red the moment a named module appears with nothing wired to it. It
does not cover the case that actually happened: the object is present, wired, working, and has
**quietly stopped being the thing that ships**.

> **Measured, 2026-09-05 20:24 to 2026-09-06 01:45 — five hours and twenty-one minutes, ten
> commits.** The L11 sentinel pointed at `model.final_fit` and its assertion was *true*. Meanwhile
> the object that shipped had become `deploy.deployed_fit`, grown on 701 rows against `final_fit`'s
> 873. HG-1 read **13/13 PASSED** throughout. No test caught it; a person did, and only because
> they ran a command that had never been run.

So: **whenever a fit, a split or an artifact acquires a second definition, re-aim every sentinel
that names the old one in the same commit** — and say in the card's narrative which sentinels were
re-aimed and why. The structural defence is stronger than the procedural one and is what was
actually done here: put the definition in **one module that both callers call**, so a sentinel
aimed at it cannot drift onto a different object without somebody deleting that module. Prefer
that. This rule is for the window before it exists.

---

## 6. Running the checks

```bash
# Fast: no environment needed, stdlib only
python scripts/check_board.py --root .
python scripts/check_freeze.py --base origin/main

# Tests run inside the pinned environment; the suite imports the scientific stack
conda run -n Project python -m pytest -q
conda run -n Project python -m pytest -m leak -q         # HG-1 sentinels only
conda run -n Project python -m pytest --cov              # NOT YET: see the note below

# Lint and types run OUTSIDE it, deliberately: they need no project environment, and the CI
# fast lane stays free of conda (card #68).
ruff check hydms/ tests/ scripts/
mypy
```

> **The lint versions are pinned exactly in CI, and must match this machine.**
> `.github/workflows/ci.yml` installs `ruff==0.8.4` and `mypy==1.13.0`, not the `dev` extra's
> floors. On a floor, the fast lane's first run installed a newer ruff, which raised SIM905,
> RUF005 and RUF100 on code the local ruff passes, and warned that `PD901` — sitting in
> `[tool.ruff.lint]`'s ignore list — had been removed. RUF100 makes the two versions mutually
> unsatisfiable rather than merely stricter: it calls a `# noqa: E402` unused where the older
> ruff requires it. So "the local command fails on exactly what CI fails on" holds only while
> the versions match. Upgrading is a deliberate commit that bumps the pin and fixes what the
> new version finds — never a floor left to drift. Card #6.

> **The coverage line does not run yet.** Neither `pytest-cov` nor `coverage` is installed in
> `Project`, so `--cov` exits with `unrecognized arguments: --cov` and the floor in `pyproject.toml`
> is unenforceable *anywhere* today. Both are declared in the `dev` extra and nothing installed them.
> Where they get installed is card **#86**'s decision, not a `pip install`: adding a package to
> `Project` invalidates `environment.lock.yml`, which exists to reproduce the published numbers.

Two environment facts that will otherwise cost you an afternoon, both from
[ENVIRONMENT.md](ENVIRONMENT.md): the interpreter is **3.10.13**, so `tomllib` is unavailable and
`tomli` is the fallback; and `requirements-lock.txt` carries a hand-applied fix that regenerating it
silently undoes.

---

*Card #70. The layer table's guarantees come from the leak inventory in
[PHASE-H-RUNBOOK.md](PHASE-H-RUNBOOK.md) §1 — each row exists because something in that table went
wrong at that layer.*
