---
id: 86
status: backlog
priority: High
blocked_by: [6, 72, 79]
assignee: "@amirhossein"
tags: [ph, l0, HG-4]
---

# GATE HG-4: CI fast lane with the delivery suite and hygiene

**Stage S8 — Evidence and close** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What every push must survive before it is allowed to be called green.

## Why this exists

The fast lane today runs one stdlib-only script over the board and the prose. That was the
right seed while no package existed; it is not sufficient once a prediction service does.

This card brings the delivery suite, the freeze check, and the lint and type gates into the same lane —
without dragging in the conda rebuild, which stays in the slow lane precisely because the environment
takes minutes and around eight gigabytes to construct.

## Done when

- [ ] The fast lane runs `check_board.py`, `check_freeze.py`, the test suite, ruff, mypy and the
      coverage floor
- [ ] ruff and mypy run in #6's **conda-free** `hygiene` job, not inside the `Project`
      environment — they need no project dependencies and #68 established that the fast lane
      builds none
- [ ] `pytest-cov` is available wherever the floor is enforced. It is declared in the `dev`
      extra and installed nowhere: neither it nor `coverage` is in `Project` today, so
      `pytest --cov` fails outright and the floor in `pyproject.toml` is currently
      unenforceable. Decide where it gets installed rather than inheriting the gap
- [ ] It runs the gates that do not require a retrain, against the published artifact
- [ ] It stays comfortably under the existing timeout
- [ ] The conda rebuild remains in the slow lane
- [ ] A failure names which gate failed, not merely that something did
- [ ] **Decide whether `openpyxl` is added, or the HyStor spreadsheet stays unread.** Card #9 left
      `Machine_Model/data/raw/HyStor_27_7_24 (1).xlsx` without a loader because reading it needs
      `openpyxl`, which is in neither `environment.lock.yml` nor the machine interpreter, and adding
      a package invalidates the lock. The cost of saying no is low — the file is one sheet of 1283
      rows over the same six columns as `hydride_data.csv`, which is its downstream, and nothing in
      the repository has ever read it. This is the same decision as `pytest-cov` above, so make both
      once rather than twice
- [ ] Registered in the gate harness as HG-4

## Runnable check

```bash
python scripts/check_board.py --root . && python scripts/check_freeze.py --base origin/main
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8, HG-4

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
- 2026-09-02: Two prerequisites recorded while landing #5. The lint/type lane is conda-free
  (see #6's amendment the same day), and the coverage floor cannot be measured anywhere right
  now — `pytest-cov` and `coverage` are both absent from `Project`, so `pytest --cov` exits
  with `unrecognized arguments: --cov`. Installing into `Project` invalidates
  `environment.lock.yml`, so where the floor is measured is a decision this card owns.
  (by @assistant)
