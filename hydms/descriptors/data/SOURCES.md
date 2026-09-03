# Element property tables — where every number came from

Card #16. These two CSVs are the descriptor layer's only source of element properties. They
are **derived artifacts**: `scripts/build_element_tables.py` builds them from the files cited
below, and that script is the audit trail. Nothing in `hydms/` reads anything but these CSVs,
and nothing in `hydms/descriptors/` imports CBFV.

## Why not CBFV

The published pipeline featurised through [CBFV](https://github.com/kaaiian/CBFV) 1.1.0, which
**carries no licence at all** — `spdx_id` is null on both GitHub and PyPI, and under default
copyright that means all rights reserved. It has been unmaintained since 2022 and breaks under
NumPy 2.x. It cannot be vendored into a GPL-3.0 deliverable, which is why these tables are
sourced from publications that may be redistributed.

## The sources

| File | Source | Licence | Shape |
|---|---|---|---|
| `oliynyk.csv` | Lee, Chen, Garcia & Oliynyk (2024), *Data in Brief* **53**, 110178. [doi:10.1016/j.dib.2024.110178](https://doi.org/10.1016/j.dib.2024.110178) · data: [Mendeley `bt6gv5z6yv`](https://data.mendeley.com/datasets/bt6gv5z6yv/1), `oliynyk-elemental-property-list.xlsx` | CC BY 4.0 | 85 elements × 99 properties |
| `jarvis.csv` | Choudhary et al. (2020), *npj Comput. Mater.* **6**, 173. [doi:10.1038/s41524-020-00440-1](https://doi.org/10.1038/s41524-020-00440-1) · data: [`usnistgov/jarvis`](https://github.com/usnistgov/jarvis) → `jarvis/core/Elements.json` | NIST work; not subject to copyright in the US | 103 elements × 438 properties |

Column names are the published headers flattened to lowercase identifiers by
`build_element_tables.py::normalise` — the published headers carry embedded newlines, doubled
spaces and units, and are labels rather than keys. Values are written with `repr(float)`, which
round-trips exactly, so the CSV **is** the number rather than a rendering of it.

A **hole** is a cell the publication provides no value for. The two sources spell it
differently and `element_data.py` collapses both at read time, so nothing downstream has to
know which: Oliynyk leaves the cell **empty** (421 of them), JARVIS writes **-9999.0** (9130 of
its 45114 cells — a sentinel four orders below every real value in the columns that carry it).
A hole is not a zero, not a NaN and not -9999, and every access to one raises.

---

## JARVIS: the source is CBFV's source

`jarvis.csv` and CBFV's `jarvis.csv` are the same table. Both carry 438 properties, and over
every shared element the values agree to **≤ 7.3e-12** — CSV float round-trip, four orders
inside AC-2's 1e-9 tolerance. Two differences, both in our favour:

- **NIST has 103 elements; CBFV's copy has 82.** The 21 CBFV dropped are Ac, Am, At, Bk, Cf,
  Cm, **Eu**, Es, Fm, Fr, Lr, Md, No, Np, Pa, Pm, Po, Pu, Ra, Rn, Xe.
- **The five composites are table columns, not something CBFV synthesises.**
  `polzbl_divi_atom_mass`, `atom_mass_mult_therm_cond`, `bp_divi_atom_mass`,
  `first_ion_en_mult_X` and `voro_coord_divi_mol_vol` all exist per-element in both files.
  Card #8's method note says they "appear in no table's header"; that is wrong, and it settles
  PRD risk **R3** — the composite is a property of an element and the statistic is taken over
  it, so the form is *statistic-of-composite* by construction, not by numerical experiment.
  Card #18 inherits the answer rather than the question.

### Europium: the same gap, said out loud instead of filled in

`Eu` is absent from CBFV's `jarvis.csv` index. NIST's file keeps the europium row and writes
**-9999** across it: of the nine base properties the selected features need, only `atom_mass`
(151.964) and `X` (1.2) are real; `polzbl`, `therm_cond`, `bp`, `first_ion_en`, `voro_coord`,
`mol_vol` and `is_alkaline` are all sentinels, as are all five composites.

**So neither source can produce a JARVIS descriptor for europium.** That is worth stating
plainly, because the first version of this document claimed otherwise: sourcing from the
publication does not conjure the measurement, it only stops the pipeline pretending to have it.

The dataset contains one europium row — `Eu1Ni5`, row 516, `H2_W% (max)` 1.2, AB5. Asked to
featurise it, CBFV **substitutes an all-zero property vector**, emits a full row of plausible
numbers, and reports the formula only in a `skipped` list that `extract_features_cbfv.py` never
read. Verified by arithmetic: CBFV emits `avg_polzbl_divi_atom_mass = 0.096547` for `Eu1Ni5`,
while (5/6) × (polzbl_Ni / atom_mass_Ni) = 0.096546914 — europium contributing exactly nothing.
The published feature matrix therefore contains one row computed as though europium had zero
mass, zero polarizability and zero boiling point, and the single highest-SHAP feature in the
model is the one shown above.

`element_data.py` raises instead. What to *do* about the row — drop it, or find a source for
europium's polarizability — is not this card's: it belongs to **#19** and to the screening
stage. Gate **AC-2** additionally cannot compare any Eu-containing formula against CBFV, since
a refusal and a number are not comparable. Card **#21** carries that.

---

## Oliynyk: the published table was revised, and disagrees with CBFV

The 2024 publication is a **corrected** edition of the property list CBFV shipped. Over the 55
elements this dataset uses, of the thirteen properties the 22 selected features need:

| Property (CBFV spelling) | Published column | max abs difference | differs on |
|---|---|---:|---|
| `Pauling_Electronegativity` | `pauling_en` | **0** | — |
| `specific_heat_(J/g_K)_` | `specific_heat_j_g_k` | **0** | — |
| `heat_of_vaporization_(kJ/mol)_` | `heat_of_vaporization_kj_mol` | **0** | — |
| `Mendeleev_Number` | `mendeleev_number` | **0** | — |
| `Number_of_unfilled_s_valence_electrons` | `unfilled_s` | **0** | — |
| `Zunger_radii_sum` | `zunger_radii_sum` | 5e-3 | 9 elements |
| `Density_(g/mL)` | `density_g_ml` | 8e-3 | Li |
| `Atomic_Weight` | `atomic_weight` | 2e-2 | 9 elements |
| `Mulliken_EN` | `mulliken_en` | 0.32 | Th, U |
| `Covalent_Radius` | `covalent_radius` | 0.54 | Th, U |
| `gilmor_number_of_valence_electron` | `gilman_no_of_valence_electrons` | 2.0 | Lu |
| `valence_d` | `valence_d` | 10.0 | Ga, Ge |
| `Gordy_electonegativity` | `gordy_en` | — | **empty for 21 of the 55** |

Five of thirteen agree exactly. The rest are revisions, and they are the reason AC-2 had to be
read as a statement about code rather than about numbers: **the featuriser must reproduce CBFV
to 1e-9 given the same table.** `tests/descriptors/data/cbfv_oliynyk_reference.csv` holds
CBFV's values for exactly that purpose — test input for one gate, never package data.

### `gordy_en` is empty for the rare earths, and one of the 22 features needs it

`dev_Gordy_electonegativity` is a selected feature. The published table has a `Gordy EN` column
and supplies it for **34** of the 55 elements this dataset uses. The **21** it does not are:

> Ce, Dy, Er, Eu, Gd, Hf, Ho, Ir, Lu, Nd, Os, Pr, Pt, Re, Sm, Ta, Tb, Th, Tm, U, W

which is almost exactly the rare-earth set — the AB5 and AB2 chemistry this dataset is largely
made of. CBFV's copy has a value for all 55. So the feature is computable for some compositions
and not others, which is worse than a clean absence: it is the shape of gap that becomes a
column of NaNs somewhere downstream if nothing refuses early.

This is not a defect in the loader; it is a gap in the literature the project chose to stand
on, and it is why `element_data.py` distinguishes a hole from an absent element. Cards **#19**
(the 22-feature contract) and **#24/#25** (re-running selection) carry the decision: drop the
feature and re-run selection, or find a second citable source for Gordy electronegativity.
`tests/descriptors/test_element_data.py` pins the list of 21 so the decision is made against
data rather than an impression.

---

## Rebuilding

```bash
# The two source files, fetched once (both are public):
#   https://data.mendeley.com/datasets/bt6gv5z6yv/1  -> oliynyk-elemental-property-list.xlsx
#   https://raw.githubusercontent.com/usnistgov/jarvis/master/jarvis/core/Elements.json
python scripts/build_element_tables.py --oliynyk oliynyk-elemental-property-list.xlsx \
                                       --jarvis Elements.json

# The two CBFV fixtures. Both need the `parity` extra, neither is run by CI, and neither
# needs the downloads above -- they are built from CBFV's own installed copy, so a fixture
# stays regenerable on a clean clone.
conda run -n Project python scripts/build_element_tables.py \
       --cbfv-reference tests/descriptors/data \
       --cbfv-statistics tests/descriptors/data
```

`--oliynyk` and `--jarvis` go together and may be omitted entirely; a run that would build
nothing is refused. The two fixtures are:

| Fixture | Card | Holds |
|---|---|---|
| `cbfv_oliynyk_reference.csv` | #16 | CBFV's own values for the 13 Oliynyk properties, so AC-2 can compare code rather than tables |
| `cbfv_statistics_reference.csv` | #17 | CBFV's `avg`/`dev`/`range`/`max`/`min` over 16 formulae spanning arity 2–10 × the 19 needed properties of **both** tables — 1,520 statistics. It is what keeps "`dev` is CBFV's fraction-weighted mean absolute deviation, not a standard deviation" a check rather than a claim |

The build script is stdlib-only: `openpyxl` is not in the pinned environment and adding it is
card #86's decision, not one to make in passing.
