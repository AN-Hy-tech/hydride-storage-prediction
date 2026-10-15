---
id: 107
status: doing
priority: P1
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l0, l1, l7]
---

# Drop Machine_Model and every wrong address, result, and document it left behind

**No stage** · **L0 Foundation, L1 Data, L7 Evidence** · Estimate: 1 d

> **Owns (hidden behind this module):** Where the project's raw data and its evidence live, so that nothing in the working tree depends on the archival pipeline.

**This card is NOT an unfreeze condition.**

## Why this exists

`Machine_Model/` is the pipeline behind `REPORT.md`, and both are shown wrong (`docs/FREEZE.md`
§ Why). Keeping them in the tree tells every reader they are current. `hydms/` is the project.
But three things the correct project still uses physically live under `Machine_Model/`, so a plain
delete would break it:

| Lives in `Machine_Model/` | Read by | Decision (maintainer, 2026-10-15) |
|---|---|---|
| `data/raw/` — `hydride_data.csv` and its three upstream sources | `paths.raw`, every loader, the suite | **Move** byte-identical to `data/raw/`; drop `data/database/combined_dataset.csv` (unread) |
| `reports/feature_selection/feature_selection_report.csv` | `tests/descriptors/test_contract.py` | **Copy** into `tests/descriptors/data/` as a fixture |
| `reports/benchmarked_model/*.csv` + `REPORT.md` | `hydms.evidence.reconciliation`, which generates `docs/REPORT-RECONCILIATION.md` | **Archive** the generated page unchanged in `docs/archive/`; delete the generator and its tests |

## Done when

- [ ] Tag `machine-model-archive` names the last commit holding `Machine_Model/` and `REPORT.md`,
      and is pushed; every archived citation can name it.
- [x] Raw data moved byte-identical (`sha256` before = after); `paths.raw` and every reader repointed;
      the suite reads the same 1,279 rows.
- [x] The feature-selection report is a test fixture and `test_contract.py` reads it there.
- [x] `REPORT-RECONCILIATION.md` is in `docs/archive/`, unchanged except a header naming the tag;
      its generator and tests are gone, and nothing links the old path.
- [ ] `Machine_Model/` and `REPORT.md` are deleted; `pyproject.toml`, `.graphifyignore`,
      `scripts/check_board.py` and `tests/test_tooling.py` carry no exclusion for them.
- [ ] `README.md` reports only what `hydms/` produces; `CLAUDE.md`'s authority row 5, its "Two code
      trees" invariant and its anti-pattern line are repointed.
- [ ] `docs/PRD-inverse-design.md` §7.2 is **not** edited (still frozen); the PRD's stale reference
      is named in this card instead.
- [ ] `git grep -n Machine_Model` returns only archive prose, the frozen PRD and `research/`.

## Runnable check

```bash
! git grep -n "Machine_Model" -- . ':!docs/archive' ':!docs/PRD-inverse-design.md' ':!research' ':!kanban-hardening/archived' && python -m pytest -m "not slow" -q
```

## Traces to

`docs/FREEZE.md` § Why and § Denied paths; #89 (the reconciliation it archives); #95.

## Narrative

- 2026-10-15: **The blocker is lifted, and only that one.** By the maintainer's decision,
  `REPORT.md` and `Machine_Model/` are off `DENIED` in `scripts/check_freeze.py`, recorded in
  `docs/FREEZE.md` § Denied paths. Phase H stays in force. Two consequences for this card's list:
  `docs/PRD-inverse-design.md` is **still denied**, so its §7.2 row cannot be repointed here (say so
  beside it, or bring that decision back to the maintainer); and `CLAUDE.md`'s anti-pattern line
  "editing … `REPORT.md` or `Machine_Model/`" is now stale and is one of the addresses to repoint.
  The card still lacks *Done when* and *Runnable check*; write them before moving it to `doing`.
  (by @assistant)
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
