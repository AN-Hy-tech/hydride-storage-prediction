---
id: 18
status: backlog
priority: High
blocked_by: [17]
assignee: "@amirhossein"
tags: [p1, l2, R3]
---

# Composite descriptors (_divi_ and _mult_)

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** How two element properties combine into one derived property.

## Why this exists

Six of the 22 features are composites: `avg_polzbl_divi_atom_mass`,
`dev_bp_divi_atom_mass`, `dev_atom_mass_mult_therm_cond`, `dev_voro_coord_divi_mol_vol`,
`range_first_ion_en_mult_X`, plus `avg_is_alkaline`.

**The open risk (R3):** whether the composite is formed *before* the statistic
(element-wise product, then average) or *after* (average each, then multiply). These give
different numbers. Ticket 8's spike output settles it; this ticket implements the answer and
the parity gate (21) proves it.

## Done when

- [ ] Composite construction order matches the spike's finding and is stated in the module docstring
- [ ] Both orders implemented behind a flag during development, with the wrong one deleted before merge
- [ ] Composite names parse from a declarative spec, not hard-coded branches
- [ ] Unit test pins each of the six composites against a hand-computed value

- [ ] **Answered by #16 before this card started: the composites are table columns.** Card #8
      recorded them as descriptors CBFV *synthesises*, appearing in no table header. They are
      per-element columns of NIST's `Elements.json` and of CBFV's copy alike --
      `polzbl_divi_atom_mass`, `atom_mass_mult_therm_cond`, `bp_divi_atom_mass`,
      `first_ion_en_mult_X`, `voro_coord_divi_mol_vol` -- and each equals the arithmetic of its
      parts to 1e-9, asserted in `tests/descriptors/test_element_data.py`. So the form is
      **statistic-of-composite**, by construction rather than by experiment: a composite is a
      property *of an element*, and the statistic is taken over it. PRD risk **R3** is settled.
      What is left for this card is reproducing the statistic, not choosing the form

## Runnable check

```bash
python -m pytest tests/descriptors/test_composites.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — R3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
