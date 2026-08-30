---
id: 8
status: backlog
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

- [ ] CBFV run over ~20 training formulae once per `elem_prop` in {magpie, oliynyk, jarvis, mat2vec, onehot}
- [ ] Each result's column names diffed against the 22 in `reports/feature_selection/feature_selection_report.csv`
- [ ] `hydms/descriptors/FEATURE_PROVENANCE.md` maps all 22 features to a named table and statistic
- [ ] **STOP GATE:** if any of the 22 is unaccounted for, this fails and tickets 16-21 stay blocked

## Runnable check

```bash
python scripts/spike_feature_provenance.py --check-all-22
```

## Traces to

`docs/PRD-inverse-design.md` — R3, AC-2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
