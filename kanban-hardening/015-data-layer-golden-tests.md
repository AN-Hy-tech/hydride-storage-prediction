---
id: 15
status: backlog
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

- [ ] **Owed to S4 — this card is not done, and `check_board.py` is right about why.** #14 is
      `doing`: the CleanLab call needs #24's feature matrix. The moment it lands, `label_issues`
      starts firing and `screened.rows_out` / `screened.removed` **will move** — so the golden
      record is not yet a record of the finished layer. When #24 lands, re-measure those two facts
      and record the pre-CleanLab values beside them, the same way `split_rows.published_*` records
      the pre-#13 split. Nothing else in the record should move; if something does, that is the
      finding

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/data/test_golden.py -q
```

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
