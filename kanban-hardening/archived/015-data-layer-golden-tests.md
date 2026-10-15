---
id: 15
status: done
priority: High
blocked_by: [13, 14]
assignee: "@amirhossein"
tags: [p1, l1, AC-1]
---

# Data-layer golden tests

**Stage S2 — Data layer** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the rebuilt data layer reproduces the documented dataset exactly.

## Why this exists

The point of the rewrite is that it produces the *same* dataset as the archived scripts,
so `REPORT.md`'s numbers stay attributable. This is the test that proves it.

## Done when

- [x] Golden test asserts 1279 raw rows and 1149 unique formulae — and the three further
      identity counts the collapse passes through: 1142 after whitespace, 1121 after element
      order, **1115 canonical compositions**. 1149 alone would not have caught L8
- [x] **Split sizes are 893 / 131 / 255, not 896 / 136 / 247, and the golden test pins both.**
      This box was written before #13 changed the split's unit from the formula string to the
      canonical composition. Asserting 896/136/247 now would be asserting that L8 is still
      present. The record therefore carries the current counts *and* the published ones, under
      `split_rows.published_*` with the card that superseded them, so restoring the old number
      is a visible failure rather than a silent regression to the leaky split. Compositions per
      split (780 / 111 / 224) are pinned too, because that is the number anything grouping cares
      about
- [x] Golden test asserts the 10 alloy classes with expected counts — the **reconciled** counts
      from #12 (AB2 371, A2B 32, MEA 109, LEA 26, MIC 127; the other five unmoved), the 13
      relabelled rows, and the smallest class at 24 compositions, which is what makes AC-6
      runnable at all
- [x] Any deviation fails with a diff, not a bare assertion error — `diff()` returns a table of
      fact, expected, actual for every disagreement, and its own failure path is tested: a
      changed fact appears, an *absent* fact appears as `<absent>`, and facts that agree do not

- [x] **Screening's output is pinned too, which the card did not ask for.** 1277 rows out, 2
      removed, and **zero removed from val or test** — the last is the one that matters, because
      it is leak L3's shape stated as a number rather than as a contract
- [x] **A golden record that stops covering a stage is worse than none**, so one test asserts
      the record still names every module of the layer. A vacuous pass reports agreement it
      never established (`docs/QA-PROTOCOL.md` §5)

- [x] **Owed to S4 — settled, and the owed measurement is now a second record, not a moved
      number.** The box read: when #24 lands, `label_issues` starts firing and
      `screened.rows_out` / `screened.removed` will move, so re-measure them with the
      pre-CleanLab values beside. What re-measuring found is that those two facts do **not**
      move, and that is the defect. `measure()` calls `screen(raw, split)` over the whole
      1,279-row frame with **no** `label_issues=`, because CleanLab needs a feature matrix the
      data layer does not build — so no verdict ever reaches that call and `screened.removed: 2`
      is permanently the exact-duplicate and the malformed formula. The pipeline's screening
      happens elsewhere, on training rows only, and removes **20 of 893**.

      So the pre/post pair is recorded over the population where the comparison is meaningful.
      `DEPLOYED_SCREENING` measures `hydms.surrogate.model.screened_rows` — the entry point
      `hydms.surrogate.deploy` calls, not a reimplementation — and pins 893 offered, 873 kept,
      20 removed, 18 flagged, with the same 893 rows through `screen()` with no verdict giving
      the pre-CleanLab 2. `test_the_deployed_removals_account_for_themselves` asserts
      `removed == flagged + removed_before_cleanlab`, which says both that every CleanLab flag on
      a training row was acted on and that no row was counted twice. The numbers reconcile with
      `reports/model/conformal-rows.csv` (893 / 20) from the run behind `artifacts/v1`.

      `GOLDEN` keeps its structural facts and gains `screened.label_quality_findings: 0`, so the
      record now *states* that the judgement stage contributed nothing to it instead of leaving a
      reader to infer 2 is what the pipeline drops
- [x] **Q8, inherited from #29: the 1,115-vs-1,114 off-by-one, closed by arithmetic.** CLAUDE.md
      states 1,115 canonical compositions; the modelling matrix carries 1,114 over 1,278 rows.
      #29 boxed it and guessed at temperature duplicates. That guess is wrong — both numbers count
      *compositions*, which temperature duplicates cannot change. The 21-feature contract refuses
      exactly one row, `Eu1Ni5` (europium blocks all six JARVIS features), and that row is the only
      row of canonical composition `Eu0.1667Ni0.8333`, so one row lost is one group lost. It is in
      `test`, which is why `split_rows.train` is 893 on both populations. Five facts and one
      equation now hold it: `modelling_rows`, `modelling_compositions`, `unfeaturisable_rows`,
      `unfeaturisable_compositions`, `unfeaturisable_rows_in_train`, and
      `test_the_off_by_one_against_the_modelling_matrix_is_the_one_unfeaturisable_row`

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/data/test_golden.py
```

Eight tests, ~20 s. Nearly all of it is the one `slow` test: CleanLab cross-fitting the
893 x 14 training matrix takes ~17.5 s, and the rest of the record is under a second. It is
marked `slow` and is still run by CI, which does not deselect the marker — the cost is real
and the guarantee is otherwise unchecked anywhere in the suite.

## Traces to

`docs/PRD-inverse-design.md` — AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-03: Landed. `tests/data/test_golden.py` — one `GOLDEN` record of 34 facts, `measure()`
  which runs the layer end to end, and `diff()` which reports disagreements as a table; 5 tests.
  Two things this card taught:

  **Half the card's numbers were aimed at the pre-#13 pipeline.** "Assert split sizes
  896/136/247" would, today, assert that leak L8 is still present. The record now holds both
  values — the current one and the published one under a `published_*` key with the card that
  superseded it — so the old number cannot be quietly restored and the new one cannot be mistaken
  for agreement with `REPORT.md`. That distinction, *facts that must not move* against *facts that
  moved on purpose*, is what the file is organised around.

  **A golden test's real failure mode is silence.** If `measure()` stops reporting a stage, a dict
  comparison passes while covering less; so `diff()` treats an absent fact as a difference, and a
  separate test asserts the record still names every module of the layer. Both failure paths are
  themselves tested, which is the only way a golden test earns the word. (by @assistant)

- 2026-09-03: **The file is written and green; the card stays `backlog`, and the board is what
  insisted.** `tests/data/test_golden.py` holds the record, `measure()` and `diff()`, and five
  tests pass — but `check_board.py` refuses both `done` and `doing` while blocker #14 is unfinished,
  which is the invariant working rather than an obstacle. It is right on the substance too: when
  #24 supplies the feature matrix, CleanLab starts flagging rows and two facts in the record
  (`screened.rows_out`, `screened.removed`) move. A golden record of a layer that is still
  changing is a record of a moment. Do not rewrite the file when this card is picked up — re-measure
  those two facts, record the pre-CleanLab values beside them the way `split_rows.published_*`
  records the pre-#13 split, and tick the boxes. (by @assistant)

- 2026-09-06: **Closed, and the owed box turned out to be aimed at the wrong symptom.** It
  predicted that `screened.rows_out` and `screened.removed` would *move* once #24 landed. They
  did not, and cannot: `measure()` calls `screen(raw, split)` with no `label_issues=`, so no
  CleanLab verdict has ever reached that call and 1277/2 is permanently the structural answer.
  The pipeline screens somewhere else entirely — `hydms.surrogate.model.screened_rows`, on
  training rows only — and removes **20 of 893**, eighteen of them CleanLab's. A golden record
  reporting 2 while the fit dropped 20 is the failure mode the 2026-09-03 note named ("a golden
  test's real failure mode is silence") arriving through a door that note did not watch: not a
  stage that stopped being measured, but a stage measured in a configuration nothing runs.

  **Two records, because there are two questions.** `GOLDEN` stays cheap and answers what the
  *stage* removes with no judgement to act on, and now says so as a fact —
  `screened.label_quality_findings: 0` — rather than leaving it to a comment nobody diffs.
  `DEPLOYED_SCREENING` answers what the *pipeline* removes, measured through the same public
  entry point `deploy` calls, and pins 893 / 873 / 20 / 18 against
  `reports/model/conformal-rows.csv`'s 893 / 20 from the `artifacts/v1` run. The pre-CleanLab
  value the box asked for is recorded over those same 893 rows rather than over the whole frame,
  so the pair is a comparison rather than two numbers that happen to both be 2 —
  `removed == flagged + removed_before_cleanlab` is asserted, which is what would catch a row
  counted twice or a flag not acted on.

  **The cost is the reason it was invisible, so it is paid rather than deferred.** CleanLab
  cross-fitting 893 x 14 takes ~17.5 s. Marked `slow`, but CI runs `python -m pytest` with no
  `-m` filter, so nothing deselects it; the marker is documentation of cost here, not an escape
  hatch. Leaving it out would leave the only check of what the deployed pipeline drops sitting
  in a committed CSV from one run.

  **#29's Q8 came here and closed by arithmetic.** 1,115 canonical compositions against the
  matrix's 1,114 over 1,278 rows is one row: `Eu1Ni5`, refused by the 21-feature contract
  because europium blocks all six JARVIS features, and the sole row of its canonical
  composition. Q8's own hypothesis — temperature duplicates — was wrong on inspection, since
  both counts are counts of compositions and duplicates cannot move either. It is in `test`,
  which is why 893 is the train size whichever population you count over. Five facts and an
  equation now hold it, so a second unfeaturisable row would go red rather than quietly
  re-open the question. (by @assistant)
