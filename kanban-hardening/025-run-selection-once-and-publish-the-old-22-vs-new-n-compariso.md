---
id: 25
status: backlog
priority: High
blocked_by: [24]
assignee: "@amirhossein"
tags: [p1, l3, S7, R4]
---

# Run selection once and publish the old-22 vs new-N comparison

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Which features the corrected pipeline actually selects, and how that differs.

## Why this exists

Phase 1's scope decision was: re-run selection **once**, accept the outcome, do not
re-benchmark 13 models. This ticket is that single run plus its honest write-up.

If the new set is close to the old, Chapter 3 is validated for free. If it is not, that is a
finding, and the comparison table is the evidence either way.

## Done when

- [ ] Selection run once with a fixed seed
- [ ] `reports/feature_selection/old_vs_new.md` tabulates: kept, dropped, newly added
- [ ] The feature contract (19) regenerated from the result
- [ ] No re-running until a better set appears — the first result stands

- [ ] **Regenerate the contract, never hand-edit it (from #19).**
      `FeatureContract.from_names(selected)` rebuilds names, order, table attribution and
      dtypes from the selected names alone — verified injective over both tables (5 statistics
      × 537 properties = 2,685 names, all distinct; no property name is shared between the
      tables). The old-22-vs-new-N comparison must also report **computability**, not only
      importance: the old 22 contain one feature that costs 266 of 1,279 rows and six that cost
      one row, and a new set that avoids them is better on an axis SHAP does not measure

- [ ] **If the candidate pool widens beyond the old 22, exclude the eleven JARVIS columns that are
      not their own arithmetic (from #18).** Every `*_mult_voro_coord` column is `0.0` for Cs and
      Gd — formed as though `voro_coord` were 0, while the base column stores 1.0 — so a feature
      selected from that family is correct for 101 elements and zero for two.
      `hydms.descriptors.composites.disagreements("jarvis")` lists them.
      **And whether `dev_voro_coord_divi_mol_vol` should survive at all is this card's call:**
      `voro_coord = 1.0` is a placeholder (every other element is 3 to 12; Gd is hcp with twelve
      neighbours) and Gd is in 18 of the 1,279 rows, so that feature is built on filler for those
      rows. Nothing forces a decision — CBFV reads the same column, so parity is unaffected — but
      it belongs in the old-vs-new write-up beside computability

- [ ] **The Gordy trade, as rows rather than as a feature (from #20).** With the published 22,
      `featurize` refuses **266 of the 1,279** curated rows and the training matrix cannot be
      built at all. Drop `dev_Gordy_electonegativity` and the remaining 21 cover **1,278 of
      1,279** — everything but the single europium row. So the decision this card makes is not
      "is Gordy predictive?" but "is Gordy worth 265 rows?", and selection must be run on the
      set it can actually featurise. Both numbers are pinned in
      `tests/descriptors/test_featurize.py`

- [ ] **The first real run is done and its tables are on disk (from #24) — read them before you
      re-run anything.** `python -m hydms.surrogate.select` at the configured budget, five outer
      folds, ~50 min, writing `reports/selection/` (gitignored; publishing it into the repo is
      this card's job). **`selection-per-fold.csv`**:

      | fold | rows offered | fitted | removed | flagged | selected |
      |---|---|---|---|---|---|
      | outer-0 | 708 | 635 | 73 | 71 | 20 |
      | outer-1 | 716 | 571 | 145 | 144 | 16 |
      | outer-2 | 721 | 704 | 17 | 15 | 18 |
      | outer-3 | 717 | 671 | 46 | 45 | 18 |
      | outer-4 | 710 | 654 | 56 | 54 | 19 |

- [ ] **"The 22 features" was never a stable object, and this is the number that says so.** Under
      the group-aware fold cut, **every one of the 21 candidates is selected by some fold** — the
      union is the whole pool — while only **14 are selected by all five**. `dev_Covalent_Radius`,
      `range_Mulliken_EN` and `range_first_ion_en_mult_X` make four folds; `avg_polzbl_divi_atom_mass`
      and `range_Density_(g/mL)` three; `range_heat_of_vaporization_(kJ/mol)_` two;
      `range_Atomic_Weight` **one**. A feature chosen by one fold of five is a finding about which
      rows were held out, not about hydrogen storage. **The consensus 14** are the `avg_`/`dev_`
      set plus `range_Mendeleev_Number`, `range_specific_heat_(J/g_K)_` and `temperature(K)`;
      `selection-stability.csv` is the full table. Deciding what the published set *is* —
      consensus, union, or a threshold in between — is this card's call, and `FoldSelection` offers
      the readings side by side rather than choosing one
- [ ] **Per-fold selection is larger than the whole-split run, which is the opposite of the naive
      expectation.** Each fold selects 16–20 of 21. A single unscreened pass over all 893 training
      rows — #24's cost probe, not a result — selects **14**: 13 Boruta-confirmed plus
      `temperature(K)`, with the VIF loop dropping nothing. Fewer rows make Boruta less able to
      *reject* against its shadow features, so running selection honestly is not merely a
      different answer, it is a **less selective** one. Whatever the write-up concludes, it must
      not present the new N beside the old 22 as though both were produced under the same
      statistical power
- [ ] **Compare against the leaking shape deliberately, not by accident.**
      `python -m hydms.surrogate.select --once` reproduces the archival whole-training-split
      selection and says in its own output that it is leak L6. **Nobody has run it with screening
      on yet** — the 14 above is the unscreened probe — so this card owes that run before it uses
      it as the "old" column. And the published 22 came from a candidate pool this project cannot
      featurise, so a like-for-like old-vs-new needs `--all-features` as well; the write-up owes a
      sentence saying which comparison each column is

## Runnable check

```bash
python -m hydms.surrogate.select --emit-comparison
```

## Traces to

`docs/PRD-inverse-design.md` — S7, R4

## Narrative

- 2026-09-04: One box added by #18 — eleven JARVIS composite columns disagree with their own
  parts, and one selected feature rests on a placeholder `voro_coord` (by @assistant)

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
