---
id: 87
status: backlog
priority: High
blocked_by: [10]
assignee: "@amirhossein"
tags: [ph, l1, AC-1, AC-6]
---

# Canonical composition key and Alloy_class reconciliation

**Stage S2 — Data layer** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** What it means for two rows to describe the same material — the identity every split, every fold and every group-by depends on.

## Why this exists

The existing split protocol groups on the **raw formula string**, and asserts that no
formula spans two splits. That assertion passes. It is also not the property anyone wants.

Measured on the real data: 1,279 rows carry 1,149 distinct formula strings but only **1,115 distinct
normalised compositions**. Sixteen of those compositions — 35 rows — land in more than one split under
the published seed. `Ce1Mg12` is in test while `Mg12Ce1` is in validation: the same measurement, the
same 6.0 wt%, the same 598 K, written two ways. `Pr1Co5` and `Pr1Co5 ` differ by a trailing space.
Since every selected feature is a composition statistic plus temperature, these rows have byte-identical
feature vectors up to temperature. That is leak L8.

Separately, `Alloy_class` is destroyed at `extract_features_cbfv.py:19-21`, which is why no
leave-one-alloy-class-out validation exists anywhere in the repository. Restoring it is what unblocks
AC-6 — and five compositions carry conflicting class labels, so the join needs a decision, not a merge.

## Done when

- [ ] `hydms/data/canonical.py` produces a stable key from element fractions, insensitive to element
      order, formula scaling, whitespace and case
- [ ] The key is used as the split key **and** the cross-validation group key
- [ ] `Alloy_class` is re-joined on the canonical key
- [ ] The **5 compositions carrying conflicting class labels** are reconciled by a stated rule, and the
      rule is recorded in the narrative
- [ ] The reconciliation is reproducible: the same input gives the same labels
- [ ] A test asserts that the 16 known cross-split collisions now share one key
- [ ] Canonicalisation never silently merges two genuinely different materials — asserted on the full dataset
- [ ] **Account for the collapse in three steps, not one.** Measured by #9: whitespace alone takes
      1149 formula strings to **1142** — 34 strings carry a trailing space, 9 an internal one, and 7
      of the padded forms already have an unpadded twin in the file. Element order and scaling take
      it the rest of the way to 1115. A canonical key that reports only the endpoint hides which
      normalisation did what, and the whitespace step is the one a downstream `str.strip()` could
      silently reproduce elsewhere
- [ ] **Reuse `hydms.data.load.parse_formula` rather than writing a second parser.** It is already
      the validated grammar — periodic-table membership, positive amounts, non-empty result — and is
      asserted at parity with CBFV over all 1279 + 772 formulae. Two parsers is two grammars
- [ ] **The two class vocabularies are not nested.** `hydride_data.csv` has 10 classes including
      HEA/LEA/MEA; ML-HydPARK's `Material_Class` has 9 and splits AB2 into `AB2(C14)` and
      `AB2(C15)`. Neither is a subset of the other, so the re-join needs a stated mapping, not a
      merge. Both closed sets are declared in `hydms/data/load.py`
- [ ] **L13 has no sentinel and this card owes one.** `extract_features_cbfv.py:19-21` drops every
      object column but `Composition`, destroying `Alloy_class` and with it every hope of
      leave-one-alloy-class-out validation (AC-6). Once the class is re-joined on the canonical key,
      add the **L13 sentinel** to `hydms/qa/sentinels.py`: `Alloy_class` survives featurisation for
      every row. Until it exists, HG-1 cannot report green

## Runnable check

```bash
conda run -n Project python -m pytest tests/data/test_canonical.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S2; `docs/PRD-inverse-design.md` — AC-1, AC-6

## Narrative

- 2026-09-02: Created for Phase H after the audit quantified the collision: 1,149 raw strings
  collapse to 1,115 normalised compositions, and 16 of them (35 rows) span two splits. Also blocks
  AC-6, because `Alloy_class` has to exist before it can be held out (by @assistant)
