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

- [x] **Decided 2026-09-12: no correction layer. This module never changes a value it was
      given, and the "normalises nothing" contract stands.** `Mg0853Ni0.125La0.022` is a missing
      decimal point — 0.853 + 0.125 + 0.022 = 1.000 exactly, so the intended formula is
      unambiguous — and the row still arrives untouched. #14 drops it from training and names it
      in `MALFORMED_FORMULAE`, which records the intended formula **in prose** so the reading is
      not lost; what it does not do is apply it.

      This was posed together with #14's three physically impossible rows as one question: **may
      the data layer change a value it was given?** Answering it needed the two halves measured
      rather than argued, and both came back against the correction table.

      **The payoff is one row.** A cited correction applied between `load_*` and `canonical_key`
      would fix the Mg row properly — it is keyed and split as essentially pure magnesium today,
      so a repair anywhere later arrives too late. But that is the *whole* benefit: one training
      row out of 893. #14's rows do not add to it, because they are the other kind of defect —
      **detectably wrong, not repairably wrong.** We can show 5.19 wt% is impossible for an AB5;
      we cannot recover what it should have been. A correction table can only carry corrections
      it can justify, so those three get exclusion, never a value — and #14 measured that the
      screening stage already removes the two it is allowed to touch.

      **The cost is a kind of error this phase exists to remove.** A correction layer would be
      the first place in the pipeline entitled to rewrite a given value, and a rewritten value is
      trusted by everything downstream while being checked by nothing but its own unit test —
      the same unfalsifiability that decided #23 against an unread payload. The failure mode is
      not a wrong entry today; it is that the source CSV and what the model trains on stop being
      the same thing, silently, and no gate can see the difference.

      **The asymmetry that makes the rule safe rather than merely strict.** Declaring and
      dropping loses a row and says so in the report. Rewriting keeps a row and says so nowhere
      the pipeline can check. This project catches bugs by refusing, not by repairing, and the
      fourth over-ceiling row shows why the instinct to repair is dangerous here:
      `Ti1.1Cr1Mn1V0.255Fe0.045` is over its ceiling by less than 0.01 and is a **real material
      at Sahlberg's limit**. Any rule confident enough to correct the Ce-Ni rows is confident
      enough to corrupt that one.

      If a future re-export of `hydride_data.csv` fixes the typo at source, the row arrives
      correct and nothing here needs to change — which is the outcome this decision is holding
      the place for. Reopen only with a source-level fix, or with a card that needs that row
      specifically and can say why one row is worth the contract.

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

- 2026-09-12: **Decided: no correction layer.** The question was posed as a design question and
  resolved as an accounting one. The correction table's entire benefit was a single training row
  out of 893, because #14's three rows turned out to be the other kind of defect — detectable,
  not recoverable — and a table can only carry what it can justify. Against one row: making this
  module the first place in the pipeline entitled to rewrite an input.

  The general shape is the same one #23 hit the same day. A value that is written and then read
  by nothing that can contradict it is unfalsifiable, whether it is a scaler payload or a
  corrected formula. This project's mechanism is refusal, not repair, and declare-and-drop is the
  refusing version of the same knowledge: `MALFORMED_FORMULAE` still records that the intended
  formula is `Mg0.853Ni0.125La0.022`, so nothing was lost except the temptation to apply it.
  If a re-export fixes the typo at source, the row simply arrives correct. (by @assistant)
