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
