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

The forward model's published numbers cannot be defended. Three findings decided this:

1. **The published numbers are contradicted by CSVs committed in this repository.**
   [REPORT.md](../REPORT.md) claims the stacking ensemble scores Val R² 0.939 / Test R² 0.892.
   `Machine_Model/reports/benchmarked_model/stacking_results.csv` records CV 0.344 / Val 0.377 /
   Test 0.376. REPORT §4.4's paired t-test (t = −2.102, p = 0.037) is recorded in
   `ttest_best_vs_ensemble_abs_error.csv` as t = −8.168, p = 1.65e-14, against a different best model.
   §3.2's CleanLab row counts (886/131/239) are refuted by
   `temperature_subgroup_performance_expanded.csv`, which sums to the full 247 test rows.
   **The published pipeline is not the committed pipeline.**

2. **`Machine_Model/src/CleanLab.py:90` overwrites validation and test ground-truth labels with the
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
| `REPORT.md` | The archival record of the forward model *as published*. It is history, not status, and is corrected **beside** rather than in place — see `docs/REPORT-RECONCILIATION.md` (card #89) |
| `Machine_Model/**` | The archival pipeline behind REPORT.md. Rewriting it orphans every published number (PRD §7.2) |

### Everything else is allowed

**The table above is the whole of the freeze.** `scripts/check_freeze.py` enforces a *deny*-list
— those five paths — and passes every other path in the repository. This section used to read as
an allow-list (`hydms/** · tests/** · app/** · kanban-hardening/** · scripts/** · .github/** ·
pyproject.toml · CLAUDE.md · README.md · docs/** except the PRD`), which a reader reasonably took
as exhaustive. It was not, and the gap was load-bearing: `environment.lock.yml`,
`environment.yml`, `requirements-lock.txt`, `CONTEXT.md` and `.graphifyignore` are all editable
and none of them was named, so a session reading only this file would have deferred card #1's
lock re-solve forever while a session reading only the script would have concluded this document
meant nothing.

**The deny-list is authoritative, and deliberately so** (decided 2026-09-12, card #72). A freeze
expressed as an allow-list has to be edited every time hardening work reaches a file nobody
listed in advance — which turns the one document that exists to *resist* widening into the most
frequently widened one, and makes each ordinary change an occasion to renegotiate the boundary.
Naming only what is protected inverts that: the five denied paths are the frozen programme and
its archival record, they are the freeze's entire purpose, and they do not grow as the phase
proceeds.

So: **do not add to `DENIED` to express a preference.** It is short on purpose. If a path needs
protecting it needs a reason of the same kind as the five — that it belongs to the frozen
programme or to the published record — not that changing it seems unwise.

### Three cards were pulled out of the freeze

**#44** (screen interface), **#48** (applicability-domain ceiling) and **#49** (ElMD novelty) were
tagged `pa` but are not inverse-design work: they are what lets the interface **refuse** to answer
instead of guessing. A predictor with no domain check is precisely the false-prediction machine this
phase exists to remove. They live in `kanban-hardening/`.

---

## Unfreeze condition

Fixed now, before results are seen, so it cannot be softened later. All four must hold:

- [x] **Every gate green.** HG-1 … HG-4 and the inherited AC-1, AC-2, AC-3, AC-4, AC-6.
      (AC-5 is thermodynamic and AC-7/AC-8 are inverse-design; they stay frozen.)
      **Met 2026-09-12: 9 passed, 0 failed, 3 skipped, 0 errored** — the three skips are exactly
      AC-5, AC-7 and AC-8, the three this bullet excludes in its own parenthesis, and they were
      named as waivers at the prompt rather than counted as passes. The four that must never be
      waived (AC-6, HG-2, HG-3, HG-4) came green with #30, #77, #79 and #86. Re-check with
      `python -m hydms.surrogate.promote --dry-run --waive AC-5 --waive AC-7 --waive AC-8`; it
      is ~3 minutes and fits nothing.
- [x] **An artifact version promoted** — card #34, **done 2026-09-12T17:37:26Z**. A trained
      model, scaler, feature contract and conformal calibration on disk, reachable by manifest
      pointer. *Written as `artifacts/v1` when this condition was fixed; the version to promote
      became **`v2`**, re-saved 2026-09-07 from a clean tree because v1's manifest records
      `code_modified: true` and a manifest is sealed when written. The requirement is unchanged —
      a promoted version — and is named by role here rather than by number so a re-save cannot
      look like a softening.* **What `current` points at is `v3`, and the role is still what is
      met:** a manifest is sealed when written, so the gate report could not be added to `v2`;
      `promote` wrote `v3` carrying the report and moved the pointer, leaving `v2` on disk as the
      record of the fit. `current.json` records the three waivers beside the pointer, which is
      where the decision to proceed lives — the embedded report still says `SKIPPED`.
      **Caveat that belongs here rather than only on the card: `artifacts/` is gitignored.** The
      promoted version exists on the maintainer's machine and nowhere else, so a fresh clone has
      no model and `predict()` refuses there. That is card #7's to fix and it does not reopen this
      bullet, which asks for a promoted version and not for a portable one.
- [x] **`docs/API.md` published** — card #80, **done 2026-09-12**. Every endpoint with a real
      request and a real response, what the interval is and is not, all nine reason codes with
      what a caller should do about each, the trained ranges, and the material-versus-system
      caveat. *It is **generated**, not written:* `python -m hydms.delivery.apidoc --emit`, with
      a test asserting the committed bytes are what the code produces. The examples are real
      exchanges captured against **`v3`** and carry that version on the page, because
      `--probe` needs an artifact and `--emit` must not — the same gitignored-path trap this
      file's own caveat above describes. Card #85's ADR landed with it at
      `docs/adr/0006-the-delivery-seam.md`, which #80's last box required.
- [ ] **The Chapter 1 revision written** — card #37: what exists, what was wrong, what it is now.

When all four hold: set `freeze: lifted` in this file's frontmatter, record the closing date below,
and the PA/PB board resumes.

**Three of four hold as of 2026-09-12.** The one that remains is the Chapter 1 revision, **#37**,
which waits on **#89** (`docs/REPORT-RECONCILIATION.md`) — and #89 has been unblocked since
2026-09-11. Nothing left in this condition needs a fit, a decision, or a run of the pipeline.

> **This list is not a plan, and it is not the measure of Phase H.** It says when the *frozen*
> programme may resume — nothing more. The phase's own objective is stated in §Why above: **a
> user-facing interface that predicts gravimetric capacity.** That is stage **S7** (#81–#84), it is
> not any of the four bullets, and the execution order in
> [PHASE-H-RUNBOOK.md](PHASE-H-RUNBOOK.md) §2 puts it before S8 in a chain — *"S2 and S3 are the
> only parallelism worth taking. Everything else is a chain."*
>
> So "#89 and #37 are all that is left" is true **of this condition** and false of the phase.
> Reading a short unfreeze list as a to-do list is how the interface this freeze was declared to
> protect gets treated as optional. Ask the runbook what comes next; ask this file only whether the
> other board may reopen.

**Closed:** _(not yet)_

---

## For the next session

If you are picking this up cold: the freeze is enforced, not remembered. `scripts/check_freeze.py`
runs on every pull request and `scripts/check_board.py` fails if a card under `kanban/` leaves
`backlog`. You do not need to hold this in your head — but you do need to know the freeze exists
before you wonder why your change was rejected.

The active board is [../kanban-hardening/](../kanban-hardening/). Start there.
