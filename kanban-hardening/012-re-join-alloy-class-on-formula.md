---
id: 12
status: doing
priority: High
blocked_by: [10, 87]
assignee: "@amirhossein"
tags: [p1, l1, S6, AC-6]
---

# Re-join Alloy_class on formula

**Stage S2 — Data layer** · **L1 Data** · Estimate: 0.5 d

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

- [x] `Alloy_class` is joined on the **canonical key** from ticket 87, never the raw formula string
- [ ] `Alloy_class` carried through featurisation as metadata, not as a model feature
- [ ] It is never present in the feature matrix passed to the model
- [x] Class distribution matches the raw 10 classes with no rows lost — all ten present, 1279
      rows in and out, 13 relabelled: AB2 +3, A2B +5, MEA −1, LEA −2, MIC −5. Asserted class by
      class in `tests/data/test_metadata.py`, not as a total, because a total hides two classes
      trading rows
- [x] **Settled: a row with a missing class *refuses*, and there is no `UNKNOWN`.** Neither
      labelled nor dropped — `with_metadata` raises and names the row. `Alloy_class` is complete
      on all 1279 curated rows, so nothing needs the word; an eleventh label is not free, since
      it changes the fold structure of AC-6 and would be a fold whose members share only the
      property that nobody labelled them. A future source with gaps is a deliberate decision, and
      `hydms.data.load.HYDRIDE_ALLOY_CLASSES` and `ALLOY_CLASS_PRECEDENCE` must learn the word in
      the same commit. Reasoning in `hydms/data/metadata.py`'s docstring
- [x] **Consume #87's reconciliation; do not decide again.** `hydms.data.canonical.alloy_classes`
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
- [x] **The boundary is the deliverable, and it has two lists, not one.**
      `hydms/data/metadata.py` declares `metadata_columns()` — `Composition`, `Alloy_class`,
      `Dataset`, `Citation`, `canonical_key`: what a featuriser must carry through, and what the
      L13 sentinel is handed — and `non_feature_columns()`, which is that list **plus the target
      in both spaces**. They are separate because a featuriser dropping `Alloy_class` costs AC-6,
      while a feature matrix *containing* `H2_W% (max)` costs everything at once and looks like an
      excellent model rather than like a bug. `refuse_non_features(X)` is the check, and it is
      deliberately on the matrix rather than on the featuriser: a column can arrive in `X` from a
      join or a `concat` long after featurisation
- [x] **AC-6 is feasible on this partition, counted in compositions rather than rows.** Folds
      group on the canonical key (#88), so rows are not the unit. Smallest class: `A2B` with 24
      compositions, `LEA` with 26, out of 1115. Ten held-out folds, none empty, none a single
      material. Asserted, because it is the reason this card exists
- [x] **Found and fixed in #87's module: the vocabulary guard was shadowed by a crash.**
      `alloy_class_table` ordered a composition's labels with `ALLOY_CLASS_PRECEDENCE.index`
      *before* calling `reconcile_class`, so an unrecognised label raised a bare
      `ValueError: tuple.index(x): x not in tuple` naming neither the label nor the row —
      `reconcile_class`'s careful refusal was unreachable from the conflicted path. Fixed by
      reconciling first; #87's now-stale "a missing class is card #12's to label UNKNOWN" message
      corrected in the same commit
- [ ] **Owed to S3 — this card is not done.** Three boxes above cannot close in the data layer:
      the class surviving featurisation, its absence from the feature matrix, and the L13 `live`
      hook. All three name `hydms.descriptors.featurize`, which #20 creates. When it does, HG-1
      goes red (`L13 [unwired] #12`) and this card finishes: a `live` check calling
      `hydms.qa.assert_metadata_survives(before, after, columns=hydms.data.metadata.metadata_columns())`
      on the real featurisation path, plus `refuse_non_features` called on what #20 returns

- [ ] **#20 landed, so the three boxes above are now unblocked — here is the shape (from #20).**
      `hydms.descriptors.featurize.featurize(frame["Composition"], frame["temperature(K)"])`
      returns the 22 columns **on the caller's index**, and refuses a repeated label precisely so
      the re-attachment cannot be ambiguous. The label-aligned join is therefore
      `pd.concat([metadata, features], axis=1)` — never a positional one — and
      `refuse_non_features(features)` passes by construction, since the frame is exactly the
      contract. Two practical notes for the `live` hook: the full 22-feature contract **refuses
      266 of the 1,279 curated rows** (the Gordy hole), so a hook that featurises real rows must
      either use a handful of well-covered formulae or pass a contract without
      `dev_Gordy_electonegativity`; and `featurize` raises rather than dropping, so
      `assert_metadata_survives` will be testing a stage that cannot lose a row silently — the
      thing it must still prove is that the class **arrives** on the other side

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/data/test_metadata.py -q
```

The module is `hydms/data/metadata.py`, not `alloy_class.py`: the secret it hides is the
boundary between the record and the model's input, and the alloy class is the column that
boundary exists for.

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

- 2026-09-03: Data-layer half landed; **status `doing`, not `done`**. `hydms/data/metadata.py` —
  `with_metadata`, `class_distribution`, `metadata_columns`, `non_feature_columns`,
  `refuse_non_features`; 21 tests in `tests/data/test_metadata.py`. Three things this card taught:

  **The card's `UNKNOWN` box asked for the wrong thing, and measuring said so.** The class is
  complete on all 1279 rows, so `UNKNOWN` would be a label with no members that nonetheless
  changes AC-6's fold count. Settled as a refusal at the door, which is what
  `ColumnSpec.allowed` already does one layer up.

  **Writing the refusal test found that the refusal did not work.** `alloy_class_table` sorted a
  composition's labels by `ALLOY_CLASS_PRECEDENCE.index` before `reconcile_class` validated them,
  so an out-of-vocabulary label crashed with `tuple.index(x): x not in tuple` — a message naming
  neither the label nor the row, with the good refusal sitting two lines below it, unreachable.
  Fixed in #87's module rather than boxed there, because "a bad class refuses at the door" is the
  decision *this* card is making and a bare `ValueError` is not a refusal.

  **The class is not the only thing that must not be a feature.** Splitting the declaration into
  `metadata_columns` (what must survive) and `non_feature_columns` (what must never be in `X`)
  came out of noticing that nothing in the repository stops the target reaching the feature
  matrix — a failure that would look like an excellent model. The two lists differ by exactly
  `H2_W% (max)` and `log_H2_W% (max)`. (by @assistant)
