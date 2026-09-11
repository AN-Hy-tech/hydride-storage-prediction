---
id: 10
status: done
priority: High
blocked_by: [9]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# Keyed merge replacing the positional concat

**Stage S2 — Data layer** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** How featurisation outputs are joined into one table.

## Why this exists

`merge_datasets.py:46` concatenates three featurisation outputs with `pd.concat(axis=1)`
— **positionally, with no join key**. If any featuriser drops, reorders or skips a row, the
features silently belong to the wrong composition and every downstream number is wrong with
no error raised.

This is the highest-severity correctness defect in the audit.

## Done when

- [x] Merge joins on a key, never on position. The key is a **parameter**, not a constant, so
      when #87 replaces the raw formula string with the canonical composition key the caller
      hands that column to `merge_features` and this module does not change
- [x] **The key this box originally named is not unique on the spine, and the module is shaped
      around that.** "Joins on formula, and temperature where the row is a measurement" reads as
      if `(Composition, temperature(K))` identified a row. Measured on `hydride_data.csv`: 1279
      rows carry only **1272** distinct pairs. Six of the seven repeats are independent replicates
      with different targets and different citations and belong in the data. So the **spine's
      index label is the row identity**, a block is *looked up* from it, and a repeated block key
      is refused — a block built row-wise on that key and joined back takes 1279 rows to **1293**
- [x] Row count and key-set asserted equal before and after the join
- [x] Any unmatched key on either side raises with the keys listed — a spine key with no block row
      (a featuriser that skipped a composition) **and** a block row nothing asked for (a block
      built from different data). An inner join hides the first, a left join hides it as NaN
- [x] Regression test feeds a deliberately reordered input and asserts alignment still holds
- [x] The **L9 sentinel** (ticket 71) is wired to this module — it has a `live` check in
      `hydms/qa/sentinels.py` calling `hydms.qa.assert_merge_is_keyed` on the real merge, over the
      real 1279-row spine and two real per-composition blocks. HG-1 moved from
      `0/13 leaks guarded` to **1/13**, and L9 is the first leak in the phase to reach `green`
- [x] **A column name arriving twice raises.** Not in the original list, and it is the same class
      of defect one line further down: `merge_datasets.py:49` is
      `df_merged.loc[:, ~df_merged.columns.duplicated()]`, which keeps the *first* of two
      identically-named columns from different featurisers and discards the rest without a word.
      Which featuriser's `avg_atomic_mass` survived depended on the order the frames were listed in

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/data/test_merge.py -q
conda run --no-capture-output -n Project python -m pytest tests/data/test_merge.py::test_reordered_input_still_aligns -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1; `docs/PHASE-H-RUNBOOK.md` — S2, leak L9

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-03: Landed. `hydms/data/merge.py` — one public function, `merge_features(spine, blocks)`,
  and one small type, `FeatureBlock`. 27 tests in `tests/data/test_merge.py`, two more in
  `tests/leaks/test_l9_keyed_merge.py`. Four things this card taught:

  **The card's own join key is not a row identity, and measuring that first changed the design.**
  The box said "formula, and temperature where the row is a measurement". Measured: 1279 rows,
  1272 distinct `(Composition, temperature(K))` pairs. Seven pairs appear twice —
  `Mg0.95Ni0.05` @ 473 K at 5.00 and 5.41 wt%, `Ti0.5Zr0.5Mn1Cr1` @ 298 K at 1.82 and 2.18,
  `Ti0.8Zr0.2Mn0.8Cr1.0Fe0.2` and `Ti0.8Zr0.2Mn1.2Cr0.8` @ 293 K from HydPark *and* Extracted,
  `Ti1V1Nb1Ta1` and `Ti1V1Zr1Nb1` @ 298 K, all from different citations. Those six are
  independent replicates and belong in the data. Had the merge keyed rows that way it would have
  fanned the table out to **1293 rows**, counting seven measurements twice in every fold, every
  metric and every conformal calibration downstream — silently, because the result still looks
  like a table. So the spine keeps its rows and its index, a block is looked up *from* it, and a
  repeated block key is a refusal rather than a join. This is the second time a prescribed
  assertion has been aimed at the wrong symptom (#9 was the first).

  **Temperature is not a join key at all.** Every selected feature is a composition statistic or
  the temperature (the enabling fact, PRD §2.3), so every descriptor block is per-composition —
  1149 rows against the spine's 1279 — and the temperature is already a spine column sitting
  beside every row it belongs to. `FeatureBlock.key` is still a tuple, so a temperature-dependent
  block stays expressible if one ever appears, and the uniqueness check is what makes it safe.

  **One line below the leak is a second silent defect.** `merge_datasets.py:49` —
  `df_merged.loc[:, ~df_merged.columns.duplicated()]` — keeps whichever identically-named column
  arrived first. Two featurisers computing `avg_atomic_mass` differently is a decision for a
  human; the archival pipeline settled it by argument order. `merge_features` refuses, naming the
  columns. It was not on the card and it is fixed here rather than boxed elsewhere, because it is
  a defect this card's own output would otherwise reproduce.

  **The `unwired` mechanism worked exactly as #71 designed it.** Creating `hydms/data/merge.py`
  turned HG-1 red with `L9 [unwired] #10 -- guarded in name only` before a single wrong line had
  been written. The `live` hook runs the detector over the real spine and two real per-composition
  blocks in 0.07 s, and `audit()` stays under 0.05 s afterwards.

  **Seen red.** All six guards were neutralised one at a time and the suite went red each time:
  block-key uniqueness, two-way coverage, the null check, the column-collision check, the
  spine-index check, and the keyed join itself with the archival positional concat put back in its
  place. The file was restored and the suite is green. The live wiring was proved separately by
  monkeypatching `hydms.data.merge.merge_features`
  with the archival positional concat: `audit()` reports `L9 [broken] hydms.data.merge has leak L9`,
  which is the test that the sentinel watches the real function rather than a copy of it
  (`test_l9_goes_red_when_the_real_merge_stops_keying`).

  **Findings boxed elsewhere:** the byte-identical duplicate row pair on **#14**, the recount of
  key collisions under the canonical key on **#87**, and "compute the log target, never join it"
  on **#11**. (by @assistant)
