---
id: 106
status: todo
priority: Medium
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l3, l7]
---

# Selection evidence is dated by a file's mtime

**Stage S4 — Surrogate layer** · **L3 Surrogate / L7 Evidence** · Estimate: 0.5 d

> **Owns:** A run record for `python -m hydms.surrogate.select`, and what
> `--emit-comparison` publishes as the selection run's date.

**This card is NOT an unfreeze condition.** It is the half of #105's box *"every other command
that writes committed evidence under `reports/` writes a record"* that #105 split off, which that
box allowed ("one box each if they split"). #105 did `evaluate` and `calibrate`.

## Why this exists

`hydms.surrogate.select` writes its tables into `reports/selection/`, which is gitignored, and
writes no run record. `--emit-comparison` then publishes the committed evidence into
`reports/feature_selection/`, including `provenance.csv` (`dated`, `regenerated_by`). When that
stamp is absent, `Comparison.read` takes `dated` from **`_written_on(selection-per-fold.csv)`,
the file's mtime** (`hydms/surrogate/comparison.py`, the `dated=` argument of `Comparison.read`).
A copy, a checkout or a touch moves an mtime. It is the same inference CONTEXT.md's **Run date**
forbids for the commit date, arrived at by another route.

It is not urgent. The committed `provenance.csv` holds `dated,2026-09-05`, so the fallback is
not what the published `old_vs_new.md` reads today. It is what the *next* selection run's emit
would read if the stamp were missing.

## Done when

- [ ] `select` stamps `hydms.provenance.begin(...)` before the Boruta fit and writes
      `selection<suffix>-run.csv` beside the tables it writes. The suffix is the one already in
      its table names, so a probe (`--no-screening`, `--all-features`, `--once`) never
      overwrites a result's record
- [ ] `--emit-comparison` takes the run date from that record, through `hydms.provenance.read`.
      With no record, the date is **not recorded**, never an mtime. `_written_on` goes
- [ ] The committed `reports/feature_selection/` is not rewritten until a real selection run
      replaces it. Keep `old_vs_new.md`'s byte test green, or regenerate it and say why

## Runnable check

```bash
/c/Users/Asus/miniconda3/envs/Project/python.exe -m pytest tests/surrogate/test_comparison.py tests/surrogate/test_selection.py tests/test_provenance.py -q
```

## Traces to

Card #105 (the run record and its box); `CONTEXT.md` — **Run record**, **Run date**;
`hydms/provenance.py`

## Narrative

- 2026-09-26: Split from #105 while landing it. #105 built the record and wired `train`, `loco`,
  `evaluate` and `calibrate`. Reading `select` for the last box showed that its committed evidence
  is dated a different way, from an mtime, and deciding what replaces that is a question about
  `comparison.py`, not about the record. Kept apart so #105 could close and unblock #83, which
  needs only the train and loco records. (by @assistant)
