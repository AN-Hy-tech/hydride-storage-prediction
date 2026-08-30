# Feature provenance — which element-property table produces each selected feature

**Card #8, the provenance spike. Status: STOP GATE PASSED — all 22 accounted for.**
Resolved empirically on 2026-08-30 under the pinned `Project` environment (CBFV 1.1.0).
Reproduce with `python scripts/spike_feature_provenance.py --check-all-22`.

---

## The finding that matters

**The committed featurisation script is not what produced these features.**

`Machine_Model/src/extract_features_cbfv.py:31` calls `generate_features(..., elem_prop='magpie')`.
Magpie produces **none** of the 21 descriptors. Not one. The selected set is a mix of two other
tables:

| Table | Descriptors | Share |
|---|---:|---|
| `oliynyk` | 15 | the bulk of the set |
| `jarvis` | 6 | every composite, plus `avg_is_alkaline` |
| `magpie` | **0** | what the committed script says it used |

`oliynyk` is CBFV's *default* `elem_prop`, which makes the likely history legible: the run that
produced the published features used the default (or an explicit `oliynyk`), and the committed
line was changed afterwards — or the file was edited and never re-run. Either way the script in
the repository does not reproduce the repository's own results.

**Consequence for the reimplementation (cards #16–#21): the featuriser must source from two
tables, not one.** A single-table reimplementation cannot reproduce this feature set, and
AC-2 (parity with CBFV to 1e-9) would fail on the six JARVIS descriptors no matter how correct
the Oliynyk half was.

---

## The mapping

Statistic prefixes are CBFV's composition statistics over the element property named after them.

### From `oliynyk` (15)

| Feature | Statistic | Base property |
|---|---|---|
| `dev_Zunger_radii_sum` | dev | Zunger_radii_sum |
| `dev_Pauling_Electronegativity` | dev | Pauling_Electronegativity |
| `avg_valence_d` | avg | valence_d |
| `dev_specific_heat_(J/g_K)_` | dev | specific_heat_(J/g_K)_ |
| `dev_gilmor_number_of_valence_electron` | dev | gilmor_number_of_valence_electron |
| `dev_Covalent_Radius` | dev | Covalent_Radius |
| `range_Mulliken_EN` | range | Mulliken_EN |
| `range_specific_heat_(J/g_K)_` | range | specific_heat_(J/g_K)_ |
| `range_heat_of_vaporization_(kJ/mol)_` | range | heat_of_vaporization_(kJ/mol)_ |
| `dev_Gordy_electonegativity` | dev | Gordy_electonegativity *(sic — the typo is in the source table)* |
| `range_Mendeleev_Number` | range | Mendeleev_Number |
| `range_Density_(g/mL)` | range | Density_(g/mL) |
| `dev_heat_of_vaporization_(kJ/mol)_` | dev | heat_of_vaporization_(kJ/mol)_ |
| `range_Atomic_Weight` | range | Atomic_Weight |
| `avg_Number_of_unfilled_s_valence_electrons` | avg | Number_of_unfilled_s_valence_electrons |

### From `jarvis` (6)

Five of these are **composite** descriptors CBFV synthesises rather than reads: `a_divi_b` is a
ratio, `a_mult_b` a product. They appear in no table header, which is why this spike had to run
the featuriser instead of diffing CSV columns.

| Feature | Statistic | Base property | Form |
|---|---|---|---|
| `avg_polzbl_divi_atom_mass` | avg | polzbl / atom_mass | composite (ratio) |
| `dev_atom_mass_mult_therm_cond` | dev | atom_mass × therm_cond | composite (product) |
| `dev_bp_divi_atom_mass` | dev | bp / atom_mass | composite (ratio) |
| `range_first_ion_en_mult_X` | range | first_ion_en × X | composite (product) |
| `dev_voro_coord_divi_mol_vol` | dev | voro_coord / mol_vol | composite (ratio) |
| `avg_is_alkaline` | avg | is_alkaline | plain |

Note `avg_polzbl_divi_atom_mass` is the **highest-SHAP feature in the whole model** and it is a
JARVIS composite. The reimplementation cannot treat the JARVIS half as a minor tail.

### Passthrough (1)

| Feature | Origin |
|---|---|
| `temperature(K)` | Raw input column, carried into `X` by `extend_features=True`. Not a descriptor; no table produces it. Every table's output contains it, which is why it must be classified separately rather than attributed. |

**15 + 6 + 1 = 22.**

---

## Ambiguity check

No descriptor name is emitted by more than one table, so a name identifies its source uniquely.
`temperature(K)` is the sole multi-table hit, and it is a passthrough rather than a descriptor.

---

## Method

Rather than reading each table's CSV header — which would report every composite as unaccounted
and fail the gate for the wrong reason — the spike runs the real featuriser once per table with
**the exact arguments the original script used** (`drop_duplicates=False`, `extend_features=True`)
and diffs the emitted column names against the selected set.

Column counts emitted per table, 20 formulae: magpie 133, oliynyk 265, jarvis 2,629,
mat2vec 1,201, onehot 715. `random_200` is excluded — 200 randomly generated vectors can only
produce accidental matches.

## What this unblocks and what it constrains

- Cards #16–#21 may start. The tables to reimplement are **Oliynyk and JARVIS**.
- PRD §8 already names the citable sources: Oliynyk properties via
  [Lee et al. 2024](https://doi.org/10.1016/j.dib.2024.110178), JARVIS via
  [Choudhary et al. 2020](https://doi.org/10.1038/s41524-020-00440-1).
- Card #19's 22-feature contract should record the table alongside each name, so this finding
  cannot be lost again.
- The composite forms (`divi`, `mult`) must be reproduced **statistic-of-composite**, not
  composite-of-statistic. Risk R3 in the PRD names this ambiguity; the spike does not resolve
  it, and card #18 must settle it against CBFV numerically.
