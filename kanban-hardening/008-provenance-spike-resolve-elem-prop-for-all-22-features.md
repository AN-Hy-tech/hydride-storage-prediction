---
id: 8
status: done
priority: High
blocked_by: [1]
assignee: "@amirhossein"
tags: [p0, l2, R3, AC-2]
---

# PROVENANCE SPIKE: resolve elem_prop for all 22 features

**Phase 0 — Foundation & provenance** · **L2 Descriptors** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Which element-property table each of the 22 selected features comes from.

## Why this exists

**Hard gate. Nothing in the descriptor layer may start until this passes.**

`extract_features_cbfv.py:31` calls `generate_features(..., elem_prop='magpie')`, but the 22
selected names are not Magpie names. They appear to split into ~15 Oliynyk-style
(`dev_Zunger_radii_sum`, `avg_valence_d`, `range_Mendeleev_Number`) and ~6 JARVIS-style
composites (`avg_polzbl_divi_atom_mass`, `dev_bp_divi_atom_mass`). `oliynyk` is CBFV's
*default* `elem_prop`, so the committed script may simply not be what was run.

You cannot reimplement a table you have not identified. Resolve it empirically.

## Done when

- [x] CBFV run over 20 training formulae once per `elem_prop` in {magpie, oliynyk, jarvis, mat2vec, onehot}
- [x] Each result's column names diffed against the 22 in `reports/feature_selection/feature_selection_report.csv`
- [x] `hydms/descriptors/FEATURE_PROVENANCE.md` maps all 22 features to a named table and statistic
- [x] **STOP GATE PASSED** — all 22 accounted for; tickets 16-21 are unblocked

## Runnable check

```bash
python scripts/spike_feature_provenance.py --check-all-22
```

## Traces to

`docs/PRD-inverse-design.md` — R3, AC-2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-08-30: **STOP GATE PASSED. The card's hypothesis was right, and the committed script is
  wrong.** `extract_features_cbfv.py:31` passes `elem_prop='magpie'`, but magpie produces **none**
  of the 21 descriptors. The selected set splits 15 `oliynyk` / 6 `jarvis`, with `temperature(K)`
  a passthrough that `extend_features=True` carries from the raw input and that no table produces.
  15 + 6 + 1 = 22. No descriptor name is emitted by more than one table, so a name identifies its
  source uniquely.

  `oliynyk` is CBFV's *default* `elem_prop` — confirmed from the function signature, not assumed —
  which makes the likely history legible: the run that produced the published features used the
  default, and the committed line was changed afterwards or never re-run. Either way the script in
  the repository does not reproduce the repository's own results.

- 2026-08-30: Method note — the spike runs the real featuriser rather than diffing table CSV
  headers, and that choice was load-bearing. Five of the six JARVIS features are composites CBFV
  *synthesises* (`avg_polzbl_divi_atom_mass`, `dev_bp_divi_atom_mass`, `dev_voro_coord_divi_mol_vol`,
  `dev_atom_mass_mult_therm_cond`, `range_first_ion_en_mult_X`) and appear in no table's header.
  Header-matching would have reported all five unaccounted and failed the gate for the wrong
  reason. There was also no cached featurisation output to inspect instead — `data/processed/`
  does not exist, confirming the audit's finding that outputs were never persisted.

- 2026-08-30: **Consequence for cards #16-#21: the featuriser must source from two tables.** A
  single-table reimplementation cannot satisfy AC-2's 1e-9 parity regardless of how correct it is.
  Note the single highest-SHAP feature in the whole model, `avg_polzbl_divi_atom_mass`, is a JARVIS
  composite, so the JARVIS half cannot be treated as an approximable tail. Card #19's feature
  contract should record the table beside each name so this finding cannot be lost again. Still
  open and explicitly *not* resolved here: whether composites are built statistic-of-composite or
  composite-of-statistic (PRD risk R3) — that is card #18's, to be settled numerically against
  CBFV. (by @assistant)
