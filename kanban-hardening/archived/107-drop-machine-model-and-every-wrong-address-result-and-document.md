---
id: 107
status: done
priority: P1
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l0]
---

# Drop Machine_Model and every wrong address, result, and document it left behind

## Narrative

- 2026-10-15: Handoff for next session, written after making the repo public. `Machine_Model/` is
  the wrong pipeline — confirmed by this branch's own audit (`docs/FREEZE.md`,
  `docs/REPORT-RECONCILIATION.md`): it produced the numbers `REPORT.md` quotes, those numbers
  don't match the committed CSVs, `CleanLab.py` has a label-leak bug, and the pipeline can't run
  end to end. `hydms/` is the correct, going-forward project. Next session: delete
  `Machine_Model/` entirely (`src/`, `data/`, `notebooks/`, `reports/`), tag the last commit that
  has it first (e.g. `git tag machine-model-archive`) so every citation below stays recoverable,
  then repoint every wrong address that currently assumes it exists — `CLAUDE.md`'s document-map
  link and "Two code trees" invariant, closed kanban card #2's done-criterion
  ("`Machine_Model/src/` is unmodified"), `docs/PRD-inverse-design.md` §7.2's rejected-alternative
  row, `hydms/__init__.py` and `hydms/descriptors/FEATURE_PROVENANCE.md`'s provenance citations,
  and `scripts/spike_feature_provenance.py`, which reads `Machine_Model/` files at runtime and will
  crash once they're gone — and once the pipeline is gone, drop every wrong result and wrong
  document built on it: `REPORT.md`'s body (already caveated here, not yet removed) and `README.md`
  should report only what the corrected, verified pipeline under `hydms/` actually produces, with
  nothing left claiming numbers that were never reproduced. **The blocker, and the reason this is
  a card and not a same-session edit:** `docs/FREEZE.md`'s own deny-list currently forbids touching
  `Machine_Model/**` and `REPORT.md` for exactly this reason ("rewriting it orphans every published
  number", PRD §7.2) and `scripts/check_freeze.py` will fail CI the moment a diff touches either
  path — so the deny-list itself needs a deliberate, recorded decision to lift before deleting
  anything, the same weight `FREEZE.md` already asks for adding to it ("do not add to DENIED to
  express a preference" cuts both ways on removing from it). Fold this into existing open work
  rather than duplicate it: **#99** (P1 — a `REPORT.md` number quoted as current in live
  docstrings) and **#95** (the freeze is unenforced on `main`; partly addressed this session by
  making this branch the GitHub default, but `main` itself still carries no `check_freeze.py`).
  (by @assistant)
- 2026-10-15: Done, after the maintainer approved amending the deny-list. Tagged `machine-model-archive`
  at e92539b. **The handoff missed one thing:** `hydms` read its input data from
  `Machine_Model/data/raw/`, so the four source files moved to `data/raw/` rather than going with
  the rest. The reconciliation module, its test and `docs/REPORT-RECONCILIATION.md` went with
  `REPORT.md`, since they had nothing left to reconcile; the model card cites them at the tag.
  Card #2 lives in `archived/`, not the frozen board, so `kanban/**` was never touched; the PRD's
  §7.2 row is recorded as superseded in `FREEZE.md` rather than edited, because the PRD stays
  frozen. #99 closed in the same change; #95 is unaffected. (by @assistant)
