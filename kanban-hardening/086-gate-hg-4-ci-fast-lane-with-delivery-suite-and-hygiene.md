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
- [ ] It runs the gates that do not require a retrain, against the published artifact
- [ ] It stays comfortably under the existing timeout
- [ ] The conda rebuild remains in the slow lane
- [ ] A failure names which gate failed, not merely that something did
- [ ] Registered in the gate harness as HG-4

## Runnable check

```bash
python scripts/check_board.py --root . && python scripts/check_freeze.py --base origin/main
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8, HG-4

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
