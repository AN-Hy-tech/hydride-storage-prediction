---
id: 16
status: done
priority: High
blocked_by: [8]
assignee: "@amirhossein"
tags: [p1, l2, S12]
---

# Element property tables with cited provenance

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** The numeric element properties, and where each came from.

## Why this exists

CBFV carries **no licence at all** (`spdx_id` null on GitHub and PyPI), is unmaintained
since 2022 and will break under NumPy 2.x. Under a GPL-3.0 deliverable it cannot be
vendored. The replacement sources the tables from citable, redistributable publications:

- Oliynyk elemental properties — Lee et al. 2024, *Data in Brief* 53, 110178
- JARVIS descriptors — Choudhary et al. 2020, *npj Comput. Mater.* (NIST)

Depends on ticket 8 having named which tables are actually needed.

## Done when

- [x] Tables stored as versioned CSV under `hydms/descriptors/data/` with a `SOURCES.md` citing
      each. `oliynyk.csv` (85 × 99) from Lee et al. 2024 via Mendeley `bt6gv5z6yv`, CC BY 4.0;
      `jarvis.csv` (103 × 438) from NIST's `usnistgov/jarvis` `Elements.json`, a US-government
      work. Both are **derived**, not transcribed: `scripts/build_element_tables.py` builds them
      from the published files and is the audit trail. Values written with `repr(float)`, which
      round-trips exactly, so the CSV *is* the number rather than a rendering of it
- [x] Loader validates element coverage against the **55** elements present in the dataset —
      not 54. `REPORT.md` §2.3 and the PRD's dataset table both say 54; counted from the parsed
      compositions of all 1279 rows the answer is 55, seven of them appearing exactly once
      (N, Eu, Lu, Pb, Au, Os, Re). Measured by #9 and asserted in `tests/data/test_load.py`;
      recorded as a disagreement on #89. A table validated against 54 would pass while one
      element silently had no properties. `require_coverage()` derives the set from the loader
      rather than taking a number, and it reports **every** gap rather than the first — and it
      immediately found that **neither published table covers all 55**, in two different places
- [x] A missing element for a requested property raises, never silently yields NaN. **The box
      was aimed at the wrong symptom and the real one is worse.** CBFV does not yield NaN: asked
      for `Eu1Ni5` it substitutes an all-zero property vector and emits a full row of plausible
      numbers, naming the formula only in a `skipped` list nobody read. And the sources spell
      "no value" two ways — Oliynyk leaves 421 cells empty, JARVIS writes **-9999.0** in 9130 of
      45114. Both collapse to a hole at read time and every access to one raises
- [x] No CBFV import anywhere in `hydms/descriptors/` — asserted by a test, not by habit. CBFV
      is imported in exactly one place in the repository, `build_element_tables.py`'s
      `--cbfv-reference` path, which writes the AC-2 fixture and is never run by CI

- [x] **NumPy cannot currently be imported anywhere under `hydms/`, and this card is where that
      stops.** Applied, with the cost written into `pyproject.toml` beside it: numpy becomes
      `Any`, so mypy no longer checks dtype or shape in the layer with the most array code —
      the same trade already made for pandas, scipy and scikit-learn, but a worse one, because
      numpy's stubs are good. Both better answers were considered and rejected as larger than
      this card: vendored stubs pinned to the 1.26 line (a new committed dependency that
      drifts), and a second mypy target inside `Project` (which breaks the conda-free lane's
      promise to report when the environment is broken). The block carries the exit condition —
      delete it if the lint lane ever runs on a 3.10 interpreter with numpy 1.26 present.
      `mypy` now reports 40 source files with numpy genuinely imported under `hydms/`.
      The original analysis follows, and was correct:

      mypy runs outside the `Project` environment by design (the conda-free lint lane,
      #68, `docs/QA-PROTOCOL.md` §6), so it resolves numpy from the machine's 3.13 site-packages,
      whose `__init__.pyi` uses PEP 695 `type` statements that `python_version = "3.10"` rejects as
      a **syntax** error. That aborts the *entire* run — `Found 1 error in 1 file (errors prevented
      further checking)` — not just the importing file, and `ignore_missing_imports` does not
      suppress it. #71 sidestepped it with stdlib `random`, #11 with `math.log1p`; the descriptor
      layer cannot sidestep it.
      **A remedy was tested on 2026-09-03 and works** — verified by adding a numpy-importing module
      under `hydms/descriptors/` and running the real `mypy` invocation, which reported
      `Success: no issues found in 40 source files`:

      ```toml
      [[tool.mypy.overrides]]
      module = ["numpy", "numpy.*"]
      follow_imports = "skip"
      follow_imports_for_stubs = true
      ignore_missing_imports = true
      ```

      That block is now in `pyproject.toml`, with the cost and the exit condition beside it.

- [x] **Handed to #18 and PRD risk R3 — the composite question is answered by the source data.**
      Card #8 recorded that the five JARVIS composites are "composite descriptors CBFV
      *synthesises*" and "appear in no table header". They do appear: `polzbl_divi_atom_mass`,
      `atom_mass_mult_therm_cond`, `bp_divi_atom_mass`, `first_ion_en_mult_X` and
      `voro_coord_divi_mol_vol` are per-element **columns** of both NIST's `Elements.json` and
      CBFV's copy of it, and each equals the arithmetic of its parts to 1e-9 (asserted in
      `tests/descriptors/test_element_data.py`). So the form is **statistic-of-composite** by
      construction, not by numerical experiment: the composite is a property of an element and
      the statistic is taken over it. #18 inherits the answer instead of the question

- [x] **Handed to #19 — two of the 22 features cannot be computed from the citable sources.**
      `dev_Gordy_electonegativity` needs `gordy_en`, which the published Oliynyk table supplies
      for 34 of the 55 elements and leaves blank for 21 — Ce, Dy, Er, Eu, Gd, Hf, Ho, Ir, Lu,
      Nd, Os, Pr, Pt, Re, Sm, Ta, Tb, Th, Tm, U, W, which is nearly the rare-earth set and so
      most of the AB5 and AB2 chemistry here. And every JARVIS feature is unavailable for
      europium, whose properties NIST marks -9999. The contract must record which features are
      computable for which compositions, or #24/#25 must re-run selection without them

- [x] **Handed to #21 — AC-2 is a claim about this code, not about these numbers.** The Oliynyk
      list was revised for 2024: five of the thirteen needed properties agree with CBFV exactly
      and eight do not, by up to 10 (`valence_d`, Ga and Ge). Parity to 1e-9 against the shipped
      table is therefore impossible by construction. AC-2 must read *the featuriser reproduces
      CBFV to 1e-9 **given the same table***, and `tests/descriptors/data/cbfv_oliynyk_reference.csv`
      exists to be that table — test input for one gate, never package data. Separately, no
      Eu-containing formula can be compared at all: this layer refuses where CBFV returns a
      number, and a refusal and a number are not comparable

- [x] **Handed to #89 — the published feature matrix has a corrupted row.** `Eu1Ni5`, row 516,
      `H2_W% (max)` 1.2, AB5. Its six JARVIS features were computed with europium contributing
      an all-zero property vector. Verified by arithmetic: CBFV emits
      `avg_polzbl_divi_atom_mass = 0.096547`, and (5/6) x (polzbl_Ni / atom_mass_Ni) =
      0.096546914. That feature is the highest-SHAP feature in the whole model

## Runnable check

```bash
python -m pytest tests/descriptors/test_element_data.py -q && ! grep -rn 'import CBFV' hydms/
```

## Traces to

`docs/PRD-inverse-design.md` — S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-03: Two boxes added while closing S2. The element count is **55**, not the 54 this card
  asked the loader to validate against — measured by #9, and a table checked against 54 would pass
  while one element silently had no properties. And the numpy/mypy wall that #71 and #11 both
  sidestepped now has a *tested* remedy recorded above; it is left unapplied because choosing it,
  and stating what it costs, belongs to this card. (by @assistant)

- 2026-09-03: Landed. `hydms/descriptors/element_data.py`, two committed tables built by
  `scripts/build_element_tables.py`, `data/SOURCES.md`, and 20 tests in
  `tests/descriptors/test_element_data.py`. The numpy override is applied and mypy now checks
  40 files with numpy imported under `hydms/`. Five things this card taught, three of them
  corrections to what it was written believing.

  **The licence problem had a clean answer for one table and a hard one for the other.** CBFV's
  `jarvis.csv` turns out to *be* NIST's `Elements.json` -- 438 properties both sides, agreeing
  to 7.3e-12 over every shared element, which is four orders inside AC-2's tolerance. So the
  JARVIS half is not a reimplementation at all, it is the same public-domain table read from
  its source. The Oliynyk half is not: the 2024 publication is a **revised** edition and
  disagrees with CBFV on eight of the thirteen properties the features need. There is no
  version of this card that both ships the citable table and matches CBFV to 1e-9, so the
  conflict went to a decision rather than a workaround, and AC-2 was reinterpreted as a claim
  about the code given a fixed table. #21 carries it.

  **The card's third box was aimed at the wrong failure.** It asked that a missing element
  "raises, never silently yields NaN". CBFV does not yield NaN -- it yields a *number*. Asked
  for `Eu1Ni5` it substitutes an all-zero property vector, emits a full row of plausible
  values, and reports the formula only in a `skipped` list that `extract_features_cbfv.py`
  never read. A NaN would have been the merciful version: it propagates and gets noticed.

  **Both published tables have holes, and they spell them differently.** Oliynyk leaves cells
  empty; JARVIS writes -9999.0, in 9130 of its 45114 cells. The first draft of the loader read
  -9999 as a measurement, and the tests caught it -- which is the only reason this note is a
  design decision rather than a bug in the surrogate three cards from now. Both spellings
  collapse to a hole at read time, so no code past the reader has to know the difference.

  **Sourcing from the publication does not conjure the measurement.** The first version of
  `SOURCES.md` claimed europium was fixed here because NIST has 103 elements to CBFV's 82. It
  is not: NIST keeps the europium row and marks seven of the nine needed properties -9999. What
  changed is that the pipeline now says so. Corrected in the document and pinned by a test,
  because a provenance file that overstates its source is worse than none.

  **The gaps are shaped badly.** `gordy_en` is missing for 21 of 55 elements and they are
  almost exactly the rare earths -- the AB5 and AB2 chemistry this dataset is built on. A
  feature computable for some compositions and not others is worse than one that is simply
  unavailable: it becomes a column of NaNs downstream unless something refuses early. #19 now
  carries a list rather than an impression. (by @assistant)
