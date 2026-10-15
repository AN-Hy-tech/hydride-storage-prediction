---
freeze: in-force
declared: 2026-09-02
phase: H
---

# Implementation freeze — Phase H

**Status: IN FORCE.** While this file's frontmatter says `freeze: in-force`, CI rejects any change
outside the hardening scope. To lift it, see [Unfreeze condition](#unfreeze-condition) — changing the
frontmatter is the mechanical act, but it is only honest once every condition below is met.

---

## Why

The forward model's published numbers cannot be defended. Three findings decided this. Card #107
has since deleted the report and its pipeline; every path below resolves at git tag
`machine-model-archive` (commit `e92539b`), under the pipeline's own directory.

1. **The published numbers are contradicted by CSVs committed in this repository.**
   `REPORT.md` claims the stacking ensemble scores Val R² 0.939 / Test R² 0.892.
   `reports/benchmarked_model/stacking_results.csv` records CV 0.344 / Val 0.377 /
   Test 0.376. REPORT §4.4's paired t-test (t = −2.102, p = 0.037) is recorded in
   `ttest_best_vs_ensemble_abs_error.csv` as t = −8.168, p = 1.65e-14, against a different best model.
   §3.2's CleanLab row counts (886/131/239) are refuted by
   `temperature_subgroup_performance_expanded.csv`, which sums to the full 247 test rows.
   **The published pipeline is not the committed pipeline.**

2. **`src/CleanLab.py:90` overwrites validation and test ground-truth labels with the
   model's own predictions.** It is inert today only because nothing reads its output. Card #14 as
   originally written would have wired it in.

3. **The pipeline cannot be run end to end.** `jarvis_filtered_features.csv` has no producer in the
   repository or in any commit in its history; `Feature_selection.py` reads a directory whose writer
   was deleted in `5c3bcb1`; `merge_datasets.py:46` joins three feature frames by positional `concat`
   after `reset_index(drop=True)`, so a single skipped row silently attaches every feature to the
   wrong composition.

The stated objective for this phase is a user-facing interface that predicts gravimetric capacity.
Building that interface on the current pipeline would take numbers optimistic by an unknown margin and
present them to users as trustworthy. **That is the specific failure this freeze exists to prevent.**

The full leak inventory is in [PHASE-H-RUNBOOK.md](PHASE-H-RUNBOOK.md) §1.

---

## What is frozen

The inverse-design programme: thermodynamics (PT), screen-and-rank (PA) and the multi-objective EA
(PB). Its board is [../kanban/](../kanban/) and its specification is
[PRD-inverse-design.md](PRD-inverse-design.md). Neither is edited while this freeze holds.

### Denied paths

`scripts/check_freeze.py` fails the build if a change touches any of these:

| Path | Why |
|---|---|
| `kanban/**` | The frozen board. No card may be created, edited, or moved off `backlog` |
| `docs/PRD-inverse-design.md` | The frozen programme's specification |
| `research/**` | New memos are research effort spent outside the phase |

**Removed 2026-10-15, by the maintainer's decision:** `REPORT.md` and the archival pipeline's
directory. Both were protected as the archival record behind the published numbers. That record
is shown wrong (§Why) and is reconciled beside it ([archive/REPORT-RECONCILIATION.md](archive/REPORT-RECONCILIATION.md)), so
card #107 deleted the pipeline and the results built on it; tag `machine-model-archive` names the
last commit holding them intact, so every citation stays recoverable. **Only the deny-list changed:** Phase H stays in
force, and the three paths above stay frozen.

### Everything else is allowed

**The deny-list above is the whole of the freeze** (decided 2026-09-12, card #72), and it is short
on purpose: an allow-list would have to be widened every time hardening work reached an unlisted
file, turning the one document meant to resist widening into the most-widened one. **Do not add to
`DENIED` to express a preference** — a protected path needs a reason of the same kind as the three:
it belongs to the frozen programme or to the published record.

**#44, #48 and #49 were pulled out of the freeze.** They were tagged `pa`, but they are what lets
the interface refuse instead of guessing, so they live in `kanban-hardening/`.

---

## Unfreeze condition

Fixed now, before results are seen, so it cannot be softened later. All four must hold:

- [x] **Every gate green.** HG-1 … HG-4 and the inherited AC-1, AC-2, AC-3, AC-4, AC-6.
      (AC-5 is thermodynamic and AC-7/AC-8 are inverse-design; they stay frozen.)
      **Met 2026-09-12**: 9 passed, 0 failed, and the three skips are exactly AC-5, AC-7, AC-8,
      named as waivers at promotion. Re-check (~3 min, fits nothing):
      `python -m hydms.surrogate.promote --dry-run --waive AC-5 --waive AC-7 --waive AC-8`.
- [x] **An artifact version promoted** — card #34, **met 2026-09-12**. `current` points at `v3`,
      with the three waivers recorded beside the pointer. `artifacts/` is gitignored, so the
      version is on one machine; making it portable is #7's and does not reopen this bullet.
- [x] **`docs/API.md` published** — card #80, **met 2026-09-12**. Generated
      (`python -m hydms.delivery.apidoc --emit`, byte-asserted), examples captured against `v3`.
- [x] **The Chapter 1 revision written** — card #37: what exists, what was wrong, what it is now.
      **Met 2026-09-24:** [chapter1-revision.md](chapter1-revision.md), accepted by the author.

When all four hold: set `freeze: lifted` in this file's frontmatter, record the closing date below,
and the PA/PB board resumes.

**All four hold since 2026-09-24, and the freeze is held anyway, by the maintainer's decision**,
until the interface (S7) is finished and the open findings
([PHASE-H-FINDINGS.md](PHASE-H-FINDINGS.md)) have been triaged. Meeting the condition *permits*
lifting; it does not require it. This is not a new condition, and nothing is added to the list.

> **This list is not a plan.** It says only when the *frozen* programme may resume. The phase's
> objective is §Why's: a user-facing interface that predicts gravimetric capacity. Ask the
> findings index what comes next; ask this file only whether the other board may reopen.

**Closed:** _(not yet — held by decision, 2026-09-24)_

The history behind each bullet is archived verbatim in
[archive/PHASE-H-STAGES-CLOSED.md](archive/PHASE-H-STAGES-CLOSED.md). If CI rejected your change,
this file is why: `scripts/check_freeze.py` runs on every pull request. The active board is
[../kanban-hardening/](../kanban-hardening/).
