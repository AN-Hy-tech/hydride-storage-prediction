---
id: 12
status: backlog
priority: High
blocked_by: [10, 87]
assignee: "@amirhossein"
tags: [p1, l1, S6, AC-6]
---

# Re-join Alloy_class on formula

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Which alloy family each row belongs to, and the resolution
> of the rows that claim two.

## Why this exists

`extract_features_cbfv.py:20-21` drops every object column except `Composition`, which
discards `Alloy_class` (AB2, AB, A2B, AB5, Mg, MIC, SS, LEA, MEA, HEA).

Both the applicability-domain screen (48) and leave-one-alloy-class-out CV (30) need it.
Without this, PRD acceptance criterion AC-6 is unreachable.

**Amended for Phase H.** The join key is the **canonical composition key** from ticket 87, not the raw
formula string. Joining on the raw string would re-import leak L8: `Ce1Mg12` and `Mg12Ce1` are the same
material and would receive class labels independently. Five compositions in the raw data carry
conflicting `Alloy_class` labels; ticket 87 owns that reconciliation, and this ticket consumes its
result rather than deciding again.

## Done when

- [ ] `Alloy_class` is joined on the **canonical key** from ticket 87, never the raw formula string
- [ ] `Alloy_class` carried through featurisation as metadata, not as a model feature
- [ ] It is never present in the feature matrix passed to the model
- [ ] Class distribution matches the raw 10 classes with no rows lost
- [ ] Rows with a missing class are labelled `UNKNOWN` rather than dropped
- [ ] **Consume #87's reconciliation; do not decide again.** `hydms.data.canonical.alloy_classes`
      already returns one label per row, reconciled on the canonical key by
      `ALLOY_CLASS_PRECEDENCE`, and `alloy_class_table` returns the same thing per composition with
      the evidence beside it. Ten canonical compositions carried more than one label and all ten are
      resolved there; 13 of 1279 rows are relabelled. A second reconciliation here is a second answer
- [ ] **Wire the L13 sentinel's `live` hook.** #87 wrote the sentinel — `assert_metadata_survives`,
      subject `hydms.descriptors.featurize` — and it is `pending` only because the featuriser does
      not exist. The moment #20 creates that module, HG-1 goes **red** (`unwired`) and stays red
      until this card gives the **L13 sentinel** a `live` check calling
      `hydms.qa.assert_metadata_survives` on the real featurisation path: `Alloy_class` present, one
      row per input row, every label unchanged. If #20 names the module differently, update the
      sentinel's `subject` string in the same commit
- [ ] **`UNKNOWN` is this card's word, and it is not in the vocabulary.** `reconcile_class` refuses
      a label outside the ten `hydride_data.csv` declares, because an eleventh class changes the fold
      structure of AC-6. Nothing in the curated file needs it — the class is complete on all 1279
      rows — so the `UNKNOWN` box above is about a *future* source. Whichever way it is settled, the
      closed set in `hydms/data/load.py` and `ALLOY_CLASS_PRECEDENCE` both have to learn the word

## Runnable check

```bash
python -m pytest tests/data/test_alloy_class.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S6, AC-6

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Amended for Phase H: the join key is the canonical composition key (ticket 87), not the raw
  formula string. Blocked on 87 for that reason, and because the five conflicting-label compositions
  have to be reconciled before any class-based grouping is meaningful (by @assistant)

- 2026-09-03: #87 landed and this card's input changed shape. The conflicting-label compositions are
  **ten**, not five — five raw formula strings already disagreed with themselves, and canonicalisation
  adds five more by merging spellings that were labelled independently (`Ce1Mg12` is MIC, `Mg12Ce1` is
  Mg). All ten are reconciled in `hydms/data/canonical.py` by a stated precedence, so this card
  consumes `alloy_classes()` rather than reconciling again. It also inherits the **L13 sentinel**:
  #87 wrote it, and it turns from `pending` to a guard only when this card carries the class through
  featurisation and gives it a `live` hook. `hydms/qa/leaks.py` now records L13 as closed by #12 for
  that reason (by @assistant)
