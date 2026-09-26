---
id: 73
status: done
priority: Normal
blocked_by: [28, 69]
assignee: "@amirhossein"
tags: [ph, l0, S1, AC-1]
---

# End-to-end smoke pipeline on a sampled fixture

**No stage — slots in where its blockers allow** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** Proof that raw data reaches a prediction in one command, fast enough to run on every push.

## Why this exists

The audit's second finding was that the pipeline does not run end to end at all — four
broken links, including a featurisation input with no producer anywhere in the repository's history.
A full retrain is far too slow for the CI fast lane, so the guard against that regression is a smoke
run over a small sampled fixture: every stage executes, in order, on real data shaped like the real
thing, in under a minute.

This is not a performance test and not an accuracy test. It answers one question — *does the chain
still connect?* — which is exactly the question the repository could not answer before this phase.

## Done when

- [x] A committed fixture sampled from `data/raw/`, small enough to run the whole chain in ≤ 60 s —
      `hydms/pipeline/smoke-fixture.csv`, 235 rows, **12.1 s** for the whole chain. It is
      *generated*, not curated: `python -m hydms.pipeline.smoke --emit` samples it by a
      deterministic stride over a sorted key, and a test asserts the committed bytes are what that
      command produces
- [x] The fixture preserves the shapes that matter — 10 alloy classes, 42 compositions measured
      more than once, 15 spelled more than one way. `check_fixture()` **refuses** a fixture that
      has lost one of them, at emit time and again at the start of every run: such a fixture still
      runs, which is the danger, because the run then proves less than it claims
- [x] One command runs the whole chain on the fixture — `python -m hydms.pipeline.smoke`. **In the
      live order, which is not the order this box was written in**; see the narrative
- [x] No absolute path appears anywhere in the run — checked twice: a rooted-path scan over the
      module and the fixture, and the whole chain re-run from a different working directory with
      the digest compared
- [x] The run is wired into the CI fast lane — by construction, and asserted: the `suite` job runs
      `python -m pytest` over the whole tree with no `-m` deselection, and no test in this file
      carries the `slow` marker (read off the collected items, not grepped)
- [x] Running it twice with the same seed produces identical output — `SmokeRun.digest()`, every
      stage's shape and every predicted number at full `repr` precision, with every wall-clock
      number and the artifact version excluded

## Runnable check

```bash
conda run -n Project python -m pytest tests/test_smoke_pipeline.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1; `docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)

- 2026-09-07: **Closed. The chain connects, in 12.1 s.**

  **The card's arrow order is the archival one, and the live pipeline's is different — so the
  smoke runs the live one.** The box reads `load → merge → canonicalise → split → screen →
  featurise → select → fit → predict`; what runs is `load → canonicalise → split → featurise →
  merge → screen → select → fit → predict`. Two arrows moved and both moves are a leak fix rather
  than a preference. **Canonicalisation precedes the split** because the split groups on the
  canonical composition and not on the formula string (L8). **The merge follows featurisation**
  because the merge this pipeline has is `with_features` — the label-addressed join of the
  descriptor matrix back onto the record, where `Alloy_class` survives (L13) and where
  `merge_datasets.py:46`'s positional `concat` used to be (L9). Running a sequence the pipeline
  does not have would have proved nothing about the pipeline that ships.

  **`merge_features` still has no production caller.** Card #10's keyed merge is exercised only by
  the L9 sentinel's `live` hook. That is not this card's to fix — the live pipeline reads one
  source file, so there is nothing at the top of the chain to key-merge — but it is worth knowing
  that "the keyed merge" and "the merge stage the pipeline runs" are two different functions.

  **Three budgets, each named where it is set, and each changes how well a stage runs and not
  which stages run.** Boruta at `SENTINEL_BUDGET`; CatBoost at a fixed cheap configuration rather
  than an Optuna search; and two the card did not anticipate:

  - **`SMOKE_SPLIT`.** `pipeline.yaml` cuts 5x5 strata over 1,115 compositions. 173 compositions
    do not fill 25 strata: the *second* cut runs over the 30 % the first held out, so a stratum of
    five contributes one and a half to it and `StratifiedShuffleSplit` raises on a class with one
    member. 3x3 bins with `min_stratum_size` 10 fixes it. The fractions, the seed, the grouping and
    the L8 disjointness check stay the real ones.
  - **`SMOKE_FOREST_TREES`.** The screening stage was **18.5 s of a 21 s run** — `label_issues`
    defaults to the archival selector's 100-tree forest and CleanLab cross-fits it five times.
    Twenty trees, same depth, same seed, same cross-fit: 9.5 s, and the whole run 12.1 s. Almost
    the entire budget was going to the one stage whose verdict this run does not read.

  **The fixture had to be filtered to what the contract can serve.** The first emitted fixture
  contained `Eu1Ni5`, and four of the fourteen `SELECTED` features are empty cells in the `jarvis`
  table for Eu — so the run died at featurisation on a defect of a published table rather than on
  a broken link. `sample()` now applies the same `computability(...).complete` filter
  `capacity_matrix` does before it fits.

  **The rooted-path check needed a lookbehind.** A drive letter is *one* letter, and the fixture's
  `Citation` column is full of DOIs: `[A-Za-z]:[\/]` matched `https:/` eighty times. A check that
  cries wolf gets deleted, so the pattern is narrow and says in a comment which three things it
  deliberately does not match.

  19 tests, `tests/test_smoke_pipeline.py`, 40 s for the file (five chain runs). ruff and mypy
  clean. (by @assistant)
