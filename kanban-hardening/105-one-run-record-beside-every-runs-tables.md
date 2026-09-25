---
id: 105
status: todo
priority: High
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l3, l7, AC-6]
---

# One run record beside every run's tables

**Stage S4 — Surrogate layer** · **L3 Surrogate / L7 Evidence** · Estimate: 1 d

> **Owns (hidden behind this module):** Which run wrote a directory of tables: its protocol,
> whether it was a probe, its seed, the code and packages it ran on, and its **run date**. Also the
> one rule for reading that back, so no consumer parses `probe` on its own.

**This card is NOT an unfreeze condition.** It came out of the 2026-09-26 architecture review and
grilling (ADR 0007). The unfreeze condition is fixed and stays fixed.

## Why this exists

"Is this directory a result, and from which run?" has four answers today, and in one place no
answer at all:

- `evaluate` reads `probe` with `bool(...)` on pandas, AC-6 with `in ("true", "1", "yes")`, and
  `tests/test_figures.py` with its own check.
- **`domain.transfer_table` does not check at all.** It reads `reports/loco/loco-per-class.csv`
  and never asks whether a probe wrote it. A `loco --trials 1` without `--report` writes into
  `reports/loco/`, so a following `domain --emit` puts probe transfer scores into the **served**
  domain reference. Only AC-6, a different module, would go red.
- **No run record carries a date or a commit.** `loco-run.csv` and `model-run.csv` hold only
  settings. #83's caption needs the run date (CONTEXT.md, **Run date**), and git gives only the
  commit date, which the glossary now forbids using as one.

`hydms.artifacts.manifest` already captures git state and package versions, for a model artifact.
Nothing captures them for a run.

## Decided (2026-09-26 grilling; do not reopen without new evidence)

- **A new module, `hydms/provenance.py`, using only the standard library.** It imports
  `describe_git` and `resolved_packages` from `manifest`. It is not under `hydms/artifacts/`,
  because a run record is never a model's. It does not import pandas, so a gate can read through
  it.
- **Same file, more columns.** The single-row `*-run.csv` keeps its name and existing columns. Add
  `run_id` (a random UUID; nothing keys on it across machines), `protocol`, `started_at`,
  `finished_at`, `elapsed_s`, `git_sha`, `code_modified` (checked **at start**), `python`,
  `platform`, `cpu_count`, the thread settings in force (CatBoost `thread_count`, the OMP/MKL
  environment variables), and one `pkg_<name>` column per package that can move a number: numpy,
  pandas, scikit-learn, catboost, optuna, cleanlab, mapie, boruta.
- **`protocol` and `probe` are different fields.** `protocol` is the kind of run: random split,
  leave-one-class-out. `probe` is the reduced budget.
- **The reader refuses a probe** when a result is asked for, and says so. A record written before
  this card has no run date and is read as *not recorded*. It is never backfilled from git.
- **The gates read through it.** AC-6's own probe parse goes, and so does its "restated, a test
  asserts agreement" constant for the record's schema.

## Done when

- [ ] `hydms/provenance.py`: write and read a run record, standard library only, with round-trip
      tests. The tests include a record with no date (not recorded), a probe (refused), an absent
      file (absent, not "full"), and `probe` spelled every way pandas and `csv` can write it
- [ ] `train` and `loco` write it, with `started_at` taken **before** the fit and `code_modified`
      read **at start** (a run dirties its own stamp otherwise)
- [ ] `evaluate`, AC-6, `tests/test_figures.py` and `domain.transfer_table` read through it. A
      test seeds a probe record under `reports/loco/` and asserts that `domain --emit` **refuses**
- [ ] A source-parsing test (the `test_api.py` `_FORBIDDEN` pattern) fails when a module in
      `hydms/delivery`, `hydms/screens`, `hydms/figures`, `hydms/gates` or `app/` reads a
      `*-run.csv` other than through this module
- [ ] Every other command that writes committed evidence under `reports/` writes a record:
      `evaluate`, `select`, `comparison` and `calibrate`'s report tables. One box each if they
      split
- [ ] **The Chapter 1 paragraph on the two LOACO runs** dates them by commit, labelled as the
      commit. Neither run has a run date. The chapter is the author's hand-written text, so this is
      a wording change the author reads, not a regeneration
- [ ] **`evaluation.md`'s stamp is the time of the emit**, not of the run (`evaluate --emit`
      stamps `datetime.now()` and the current sha). State the run record's run date beside it,
      regenerate, and update the byte test
- [ ] The committed `loco-run.csv` and `model-run.csv` are **not** rewritten. They gain the new
      columns only when the maintainer's next real run replaces them. **This card must land before
      that run**; #104 will likely call for one

## Runnable check

```bash
conda run -n Project python -m pytest tests/test_provenance.py tests/gates/test_ac6_loco.py tests/screens -q
```

## Traces to

`docs/adr/0007-evidence-is-served-not-read-by-the-page.md`; `CONTEXT.md` — **Run record**,
**Run date**, **Probe**; card #83 (the page and its caption), card #104 (whose repeats each need a
record), card #98 (the run that showed the record has no date)

## Narrative

- 2026-09-26: Filed from the architecture review (candidate 1 of 4, "Strong") and the grilling
  that followed. Decisions Q4, Q5, Q13, Q14 and Q15 of that session are recorded above. Not started:
  the maintainer asked for it to be handed to the next session. (by @assistant)
