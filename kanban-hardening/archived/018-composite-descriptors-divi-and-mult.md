---
id: 18
status: done
priority: High
blocked_by: [17]
assignee: "@amirhossein"
tags: [p1, l2, R3]
---

# Composite descriptors (_divi_ and _mult_)

**Stage S3 — Descriptor layer** · **L2 Descriptors** · Estimate: 1 d

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

- [x] Composite construction order matches the spike's finding and is stated in the module
      docstring — `hydms/descriptors/composites.py`, first section. **Statistic-of-composite**,
      and the module says both why (a composite is a property *of an element*, so there is
      nothing to choose) and what the alternative would have cost: over the sixteen fixture
      formulae, statistic-of-composite agrees with CBFV to at worst **9.1e-13** while
      composite-of-statistic is wrong by between **1.8%** (`avg_first_ion_en_mult_X`) and a
      factor of **65** (`dev_bp_divi_atom_mass`). Some of it is structural rather than large:
      `range(a)/range(b)` is not a range of anything, and on a two-element composition
      `dev_voro_coord_divi_mol_vol` computed the wrong way is exactly zero
- [x] ~~Both orders implemented behind a flag during development, with the wrong one deleted
      before merge~~ — **no flag was written.** #16 had already settled the form from the source
      data, so the remaining question was numerical size, not choice, and that is answered by
      measuring rather than by shipping two code paths. The rejected order is **kept as a
      negative test** instead of deleted: `test_the_statistic_is_taken_over_the_composite_and_
      not_the_other_way_round` asserts that composite-of-statistic *fails* to reproduce CBFV, by
      at least 1e-2 relative on every one of the five. Deleting it would have left nothing to
      stop a later "simplification" putting it back
- [x] Composite names parse from a declarative spec, not hard-coded branches — `INFIXES` is the
      whole specification (two entries) and `decompose()` is a parse rather than a guess.
      **That is a measured property of the source, not an assumption:** 156 of JARVIS's 438
      columns carry an infix and `oliynyk` carries none; no name carries two infixes; every one
      of the 156 splits into two names that are themselves columns of the same table; and none
      splits two ways. A name that *is* ambiguous is refused, and so is a feature name that
      reaches `decompose()` with its statistic still attached — `avg_polzbl_divi_atom_mass`
      splits into `avg_polzbl` and `atom_mass`, and guessing there would featurise from the
      wrong pair of properties
- [x] Unit test pins each of the six composites against a hand-computed value —
      `test_each_selected_jarvis_feature_matches_a_hand_computed_value`, six parametrised
      cases × five statistics on `Mg2Ni1`, where the fractions are 2/3 and 1/3 and the closed
      forms are `avg = (2a+b)/3`, `dev = (4/9)|a-b|`, `range = |a-b|`. Every expected value is
      exact decimal arithmetic from the two element values — not numpy, and not the code under
      test — and the element values are themselves asserted against the table first, so a table
      revision breaks the test at the value it changed. Agreement is 1.9e-16 relative at worst

- [x] **Answered by #16 before this card started: the composites are table columns.** Card #8
      recorded them as descriptors CBFV *synthesises*, appearing in no table header. They are
      per-element columns of NIST's `Elements.json` and of CBFV's copy alike --
      `polzbl_divi_atom_mass`, `atom_mass_mult_therm_cond`, `bp_divi_atom_mass`,
      `first_ion_en_mult_X`, `voro_coord_divi_mol_vol` -- and each equals the arithmetic of its
      parts to 1e-9, asserted in `tests/descriptors/test_element_data.py`. So the form is
      **statistic-of-composite**, by construction rather than by experiment: a composite is a
      property *of an element*, and the statistic is taken over it. PRD risk **R3** is settled.
      What is left for this card is reproducing the statistic, not choosing the form

- [x] **Not asked for, and the reason this module is more than a docstring: eleven of JARVIS's
      156 composite columns are not the arithmetic their names claim.** All eleven are the
      `*_mult_voro_coord` family and all are wrong on exactly two elements, Cs and Gd, where
      every one of them is `0.0` — formed as though `voro_coord` were 0, while the `voro_coord`
      column stores `1.0` and `voro_coord_divi_mol_vol` uses that 1.0. The published file
      contradicts itself. The five selected composites are clean (the published column and the
      arithmetic of its parts are the same double on all 82 elements that carry them), so the
      rule *read the published column, never a derived value* costs nothing today — but
      `require_self_consistent()` is now the guard a caller runs before featurising with a
      composite nobody has audited, and #25's re-selection can widen the pool onto one of the
      eleven. Boxed on #20 (call it) and #25 (exclude them)

- [x] **`voro_coord = 1.0` for Cs and Gd is a placeholder, and it reaches a selected feature.**
      Every other element in the table sits between 3 and 12; gadolinium is hcp with twelve
      nearest neighbours. Gd appears in **18 of the 1,279** curated rows and
      `dev_voro_coord_divi_mol_vol` is one of the 22, so those rows carry a descriptor built on
      a filler value. Nothing to fix here — CBFV reads the same column, so parity is unaffected
      — but it is a limitation the model card must state. Boxed on #83, and on #25 for whether
      the feature survives re-selection

## Runnable check

```bash
python -m pytest tests/descriptors/test_composites.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — R3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: **Landed.** `hydms/descriptors/composites.py` + `tests/descriptors/test_composites.py`,
  21 tests. Board 20/89 done; suite 502; ruff and mypy clean; `audit()` unchanged at 4/13 — no
  sentinel names this module, and L13 still waits on `hydms.descriptors.featurize` (#20).

  **The card's remaining work was smaller than its boxes and its finding was somewhere else.**
  R3 was already settled by #16 and the statistic was already built by #17, so "implement the
  answer" amounted to a parse, a pin and an audit. The audit is what earned the module. I went
  looking for the thing the by-construction argument assumes — that a column named `a_divi_b`
  *is* `a/b` — and checked it across all 156 composite columns instead of the five in play.
  **Eleven fail.** They are one family, `*_mult_voro_coord`, and two elements, Cs and Gd, where
  the products were formed as though `voro_coord` were 0 while the base column says 1.0 and the
  `_divi_` column agrees with the 1.0. A published table contradicting itself about two elements
  is not something a tolerance would ever have surfaced: the disagreement is a relative 1.0.

  **The five selected composites are clean, and knowing that is what makes the rule cheap.**
  Published column and derived value are the same double on all 82 elements carrying them — so
  "read the column, never derive" costs nothing today and is purely about the eleven. It is
  worth stating in that direction: a rule with no present cost is easy to lose, and the reason
  to keep it is not parity with CBFV (which is unaffected either way for these five) but that
  the next selection run can land on a column where the two disagree entirely.

  **`voro_coord = 1.0` is not a measurement.** Every other element in the table is between 3 and
  12, and Gd — hcp, twelve nearest neighbours — is in 18 of the 1,279 rows through a selected
  feature. This is the same shape as #11's published-`log`-column finding and #19's missing
  column order: the archival inputs are thinner than they look, and the honest response is to
  say so on the model card rather than to repair somebody else's file.

  **What I did not do.** No flag, and no dead code path. The card asked for both orders behind a
  flag with the loser deleted; the loser is instead *pinned as failing*, which is strictly
  stronger — deleting a rejected implementation leaves no evidence that it was rejected, and the
  two orders are one refactor apart in code and four orders apart in the answer. Also left
  alone: `tests/descriptors/test_element_data.py`'s composite check carries a `b != 0.0 else 0.0`
  branch that no element on the committed table reaches. It is #16's file and it passes; the
  same claim is now made here over all 156 columns, with a refusal in place of the silent zero.
  (by @assistant)
