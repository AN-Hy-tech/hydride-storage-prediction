---
id: 9
status: done
priority: High
blocked_by: [3]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# Raw loaders with schema validation

**Stage S2 — Data layer** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** The shape and dtypes of each raw source, and what a valid row is.

## Why this exists

Four raw sources: `hydride_data.csv` (1279 x 6), `hydride_prefeaturizing.csv`,
`ML-HYDPARK_v0.0.5.csv` (772 rows) and the HyStor spreadsheet, each with its own column
names and conventions.

Validation belongs here so no later layer has to defend against a malformed row.

## Done when

- [x] `hydms/data/load.py` exposes one loader per source, each returning a validated frame
- [x] Schemas declared explicitly (names, dtypes, allowed ranges, nullability)
- [x] A violation raises with the offending rows named, never silently coerces
- [x] Row counts asserted against documented values (1279 hydride_data, 772 ML-HydPARK)
- [ ] **The HyStor spreadsheet has no loader, and this box says why rather than hiding it.**
      `HyStor_27_7_24 (1).xlsx` needs `openpyxl`, which is in neither `environment.lock.yml`
      nor the machine interpreter, and adding a package invalidates the lock file — **#86**'s
      decision, boxed there. It is also not a fourth independent source: one sheet, 1283 rows,
      the same six columns as `hydride_data.csv` (headed `H2_W%` rather than `H2_W% (max)`),
      which is that file's upstream. Nothing in the repository or its history reads it. Reopen
      this box only if #86 adds the dependency **and** a card needs the four extra rows.

- [ ] **Decide whether a correction layer sits above this module, and if so, where.** #14 needs
      one and cannot host it. `Mg0853Ni0.125La0.022` is a missing decimal point — 0.853 + 0.125 +
      0.022 = 1.000 exactly, so the intended formula is unambiguous — and this loader's stated
      contract is that it **normalises nothing**, which is why the row arrives untouched. But the
      canonical key, the split and the class join all run *before* screening, so by the time #14
      sees the row it has already been keyed and split as essentially pure magnesium; a correction
      applied there arrives too late to matter. #14 therefore drops the row from training and names
      it in `MALFORMED_FORMULAE`. The open question is this card's: a declared, cited correction
      table read between `load_*` and `canonical_key` would fix the row properly, and it would also
      be the first place in the pipeline entitled to change a value it was given. That is a
      deliberate widening of this module's contract, not a repair made in passing

## Runnable check

```bash
python -m pytest tests/data/test_load.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-03: Landed. `hydms/data/load.py` — three loaders, a declarative schema, and a formula
  parser. 51 tests in `tests/data/test_load.py`. Five things this card taught:

  **CBFV's parser validates nothing, and the runbook's instruction was aimed at the wrong
  symptom.** S2's checklist said "assert `len(skipped) == 0` where the legacy code silently
  discarded CBFV failures". Measured against the installed CBFV: `skipped` is **empty** on all
  1279 rows, so that assertion would have passed vacuously and proved nothing. The real defect is
  upstream of `skipped`. `CBFV.composition.parse_formula` returns `{'Xx': 2.0}` for a
  non-existent element, `{}` for `Mg0`, `{'Mg': -1.0}` for `Mg-1`, and reads the annotation in
  `Hf2Cu (M)` as an element called `M`. Its `get_sym_dict` matches `[A-Z][a-z]*` against no
  element table at all and accepts `[-*\.\d]*` as an amount. Downstream, an unknown element
  *does* land in `skipped` — unread by `extract_features_cbfv.py` — and an empty composition
  kills `generate_features` with `ValueError: zero-size array to reduction operation maximum`,
  naming neither the row nor the file. So the guard is a real parser at the door, not a count
  afterwards: same grammar, plus a periodic-table check, a strictly-positive amount check and a
  non-empty result. Parity with CBFV is asserted over all 1279 + 772 formulae, so the tightening
  is provably a tightening and not a divergence. The runbook line has been corrected.

  **The dataset uses 55 elements, not the 54 `REPORT.md` and the PRD both state.** Counted from
  the parsed compositions and asserted in `test_every_formula_in_the_curated_dataset_parses`.
  Seven of them appear exactly once: N, Eu, Lu, Pb, Au, Os and Re. Boxed on
  **#89**, which owns the reconciliation; `REPORT.md` is deny-listed and is corrected beside,
  never in place.

  **34 formula strings carry trailing whitespace and 9 carry an internal space, and the loader
  leaves every one of them exactly as written.** `'Mg2Al3 '`, `'Ti1Mn1.5V0.425 Fe0.075'`. They
  parse correctly — CBFV's `\s*` and this parser's whitespace skipping agree — so they are not
  violations. But stripping them here would move the unique-formula count from **1149 to 1142**
  silently, and seven of the 34 already have an unpadded twin in the file. That collapse is
  card **#87**'s to make and to account for; a loader that quietly repairs its input hides the
  repair. Measured counts boxed on #87.

  **`log_H2_W% (max)` is exactly `log1p` of the target**, verified elementwise on all 1279 rows
  (`np.allclose`), and `log_transform_target.py:35` confirms it. Not `log(10y)`, not `log1p(10y)`.
  Boxed on **#11** so the transform is not re-derived from the histogram.

  **`Alloy_class` is validated against a closed set, deliberately.** An eleventh class arriving
  unannounced changes the fold structure of leave-one-alloy-class-out validation (AC-6), so it
  has to be a human decision rather than a pass-through. ML-HydPARK's `Material_Class` is a
  *different* closed set — it splits AB2 into C14/C15 polytypes and has no HEA/LEA/MEA — so the
  two vocabularies are neither subset nor superset of one another. That reconciliation is #87's.

  The temperature bounds in the schema are loose on purpose (0–5000 K, 0–100 wt%). They ask "is
  this a temperature at all?", not "is this inside the training span" — the second question is
  the refusal path's (#77) and its numbers live in `pipeline.yaml` under `domain`. A schema that
  encoded the training range would reject any new data by construction.

  **Seen red.** Each guard was neutralised in turn — the element check, the positive-amount
  check, the row-count assertion, the allowed-set check — and in every case the input the real
  test rejects was then accepted. `hydms.data.load` is not a sentinel subject, so HG-1 did not
  move: it still reports `0/13 leaks guarded in the pipeline`, which is correct until #10.
  (by @assistant)

- 2026-09-03: Box added by #14. That card had to decide what happens to the one row whose formula
  is missing a decimal point, and found the right fix is in the wrong place: correcting it must
  happen upstream of the canonical key, which means widening this loader's "normalises nothing"
  contract. #14 drops the row from training and names it; the correction-layer decision is
  recorded here rather than half-made there. (by @assistant)
