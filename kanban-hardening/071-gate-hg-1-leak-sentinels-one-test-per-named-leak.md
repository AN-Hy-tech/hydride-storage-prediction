---
id: 71
status: done
priority: High
blocked_by: [5, 69]
assignee: "@amirhossein"
tags: [ph, l0, HG-1, R4]
---

# GATE HG-1: leak sentinels, one test per named leak

**Stage S1 — QA foundation** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** The guarantee that a leak this phase removed stays removed.

## Why this exists

Thirteen leaks are catalogued in `docs/PHASE-H-RUNBOOK.md` §1. Removing them is stages S2
to S4. **Keeping them removed is this card**, and it is what makes the phase durable rather than a
one-time cleanup: without it, nothing stops a later session reintroducing the exact defect the phase
just spent forty days eliminating.

Each sentinel must pass **only because the leak is absent**. A test that would still pass with the leak
present is not a sentinel — it is decoration. Write each one so that deliberately reintroducing the
defect turns it red, and prove that by doing so once during development.

## Done when

- [x] **L1, L5** — the CatBoost `eval_set` identity is asserted to be the *validation* split;
      `use_best_model=True` with an empty or test eval set must raise
- [x] **L2, L4** — the model-selection record contains no test-split metric, and the reported score
      comes from folds disjoint from the tuning folds
- [x] **L3** — `y` for val and test is byte-identical before and after the CleanLab stage
- [x] **L6** — re-running selection with test rows perturbed produces an identical feature set
- [x] **L7, L8** — no canonical composition appears in two splits, and none in two CV folds
- [x] **L9** — a deliberately shuffled input frame makes the merge fail, not pass silently
      *(refined: a shuffle must not change the answer **silently**; the "must fail" belongs to the
      coverage half — a row the merge cannot key. Taking the sentence literally would produce a
      sentinel that is red against a correct keyed merge. See the narrative.)*
- [x] **L10** — held-out **feature** rows are byte-identical too. Not in the card as written; it is
      the same assertion as L3 applied to `X`, so it cost one more reproduction rather than a
      detector
- [x] Each sentinel has been shown to go **red** when its leak is reintroduced — and the
      demonstration is *executable*, not a one-time ritual: every sentinel carries a `Reproduction`
      whose leaky case must raise and whose corrected twin must not, and gate HG-1 runs every one of
      them on every build
- [x] Registered in the gate harness as HG-1 — a real gate, replacing the `Pending`
- [x] **L11, L12, L13 have no sentinel and that is now visible.** Each is a recorded `Deferral`
      naming the card that owes it (#29, #26, #87), each of those cards carries an unticked box, and
      HG-1 cannot report green until they exist

## Runnable check

```bash
conda run -n Project python -m pytest tests/leaks -q     # or -m leak, the same suite
conda run -n Project python -m hydms.gates run HG-1    # exits 1 until stage S4 closes
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1, HG-1; `docs/PRD-inverse-design.md` — R4

## Narrative

- 2026-09-02: Created for Phase H. The PRD names three leaks; the audit found thirteen. L3
  (CleanLab overwriting held-out labels) and L9 (positional concat) are the two that were not in the
  PRD and are the most severe (by @assistant)
- 2026-09-02: Landed. Ten sentinels, three recorded deferrals, one gate.

  **The problem this card had to solve first.** S1 runs before S2--S4, so every module a sentinel
  guards is unwritten. A sentinel that can only be written after the code it guards is a sentinel
  that gets written last, or never. The way out was to separate the *detector* from the *subject*:
  six assertions in `hydms/qa/detectors.py` that take row labels, a record of what a fit saw, or a
  callable — never a model — so all ten could be written and proved today.

  **Why the detectors are production code, not test helpers.** Several are the guard the runbook
  asks the pipeline itself to carry. Cards #10, #13, #14, #24, #26 and #88 now each carry a box
  telling them to call the same function, so the sentinel tests the real guard rather than a
  parallel copy that can drift.

  **The demonstration is executed, not remembered.** QA-PROTOCOL §1 asks that a sentinel be shown
  red once and that the showing be recorded here. Recording it is what this paragraph is; but a
  one-time demonstration decays silently, so each sentinel also carries `Reproduction` pairs — a
  leaky case that must raise and a corrected twin that must not — and HG-1 runs all of them every
  build. Weaken any detector and the gate names the leak.

  **The `unwired` trap, and why it matters more than the sentinels.** A sentinel written against a
  miniature guards nothing until it is pointed at the real module. Nobody would remember. So each
  sentinel names the module it expects (`hydms.data.merge`, `hydms.surrogate.validation`, ...) and
  HG-1 goes **red** the moment that module exists without a `live` hook. Demonstrated by hand:
  creating an empty `hydms/data/merge.py` turned HG-1 from SKIPPED to FAILED with
  `L9 [unwired] #10 -- hydms.data.merge now exists and this sentinel is still pointed at a miniature
  of it`, and back to SKIPPED when removed. If a later card renames its module, it updates the
  `subject` string; `test_inventory.py` asserts the parent package at least exists, so a typo
  cannot make a sentinel silently never wire up.

  **HG-1 is SKIPPED today, and that is the honest answer.** `0/13 leaks guarded in the pipeline`.
  Ten reproductions going red proves the detectors work; it says nothing about a pipeline that does
  not exist. A gate that confused those two claims would be the exact failure `hydms/gates/` was
  built to prevent. `python -m hydms.gates run HG-1` therefore exits 1 today, as the runbook §4
  promised it would.

  **Three findings that belong to other cards, now boxes there.**

  - **L10 is closed by nothing.** The runbook's stage headers say S2 closes L3/L8/L9/L13 and S4
    closes L1/L2/L4/L5/L6/L7/L11/L12. L10 appears in neither list — it is "closed" only by the
    accident that `Ashghal/Outliers_Management.py` is not being ported. That is not a closure, it
    is an absence, and it comes back the day anyone adds outlier handling. Boxed on #14.
  - **L11, L12 and L13 cannot be sentinelled yet** — each needs a decision the owning card has not
    made (what the explainability record is, what the weighting scheme is, what the class join
    produces). Boxed on #29, #26 and #87 with the assertion each will have to make.
  - **The card's L9 wording conflates two properties.** "A shuffled input frame makes the merge
    fail" is false of a correct keyed merge — joining by key is *what makes order irrelevant*. The
    detector asserts both real properties: reordering must not change the answer silently, and a row
    the merge cannot key must raise.

  **Two tooling facts, both costing the lint lane.** `numpy` cannot be imported anywhere under
  `hydms/` while mypy runs outside the `Project` environment: it resolves numpy from the machine's
  3.13 site-packages, whose `__init__.pyi` uses PEP 695 `type` statements that
  `python_version = "3.10"` rejects as a *syntax* error, aborting the entire run.
  `ignore_missing_imports` does not suppress it. This card sidestepped it with stdlib `random` for
  its one seeded shuffle — which is better anyway, since a reproduction must reproduce exactly
  regardless of NumPy version. `pandas` needed adding to the mypy override list; it was the first
  pandas import under `hydms/`. Both are now commented in `pyproject.toml`. (by @assistant)
