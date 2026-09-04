---
id: 25
status: done
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

- [x] Selection run once with a fixed seed — the five-fold run card #24 left on disk, plus the two
      single passes this card owed: `--once` (screened, 21 candidates) and `--once --all-features`
      (screened, 22). Both are in `reports/selection/`, and the tables the write-up quotes are
      republished into `reports/feature_selection/` so the evidence travels with the claim
- [x] `reports/feature_selection/old_vs_new.md` tabulates: kept, dropped, newly added.
      **14 kept, 8 dropped, and "newly added" is structurally empty** — the candidate pool *is* the
      published 22, so old-versus-new is a subset relation and the document says so rather than
      printing a column of dashes. The directory is un-ignored by `/reports/*` plus a negation
      (a negation under an excluded directory has no effect — git never descends into one)
- [x] The feature contract (19) regenerated from the result —
      `hydms.descriptors.contract.SELECTED`, built by `FeatureContract.from_names` over the
      consensus 14. **`CONTRACT` is untouched, and that is a decision:** two contracts, not two
      versions of one. The published 22 stays the archival record, the candidate pool selection
      runs over, and what gate AC-2 checks parity across; `SELECTED` is what a model is fitted on
      from #26 onward
- [x] No re-running until a better set appears — the first result stands. Structural rather than
      resolved: `--emit-comparison` fits nothing and rebuilds the document from the tables on
      disk, so republishing never costs a run, and
      `test_the_published_document_is_the_one_this_code_generates` fails if the committed document
      and the committed tables ever disagree

- [x] **Regenerate the contract, never hand-edit it (from #19).** Done as above, and the
      computability axis is in the document as a measured table rather than a sentence:
      `hydms.surrogate.comparison.row_cost` charges each of the 22 the rows it alone makes
      unfeaturisable. **One feature costs 266 of 1,279 rows; six cost one row each, and it is the
      same row** — `Eu1Ni5`, whose europium the JARVIS table does not serve. So the consensus cut
      is **free** on this axis: the new 14 cover exactly what the 21-candidate pool covered, and
      the whole computability gain is #24's Gordy trade
- [x] **The eleven JARVIS composite columns are moot here, because the pool did not widen.** Every
      `*_mult_voro_coord` column is outside the candidate set and could not have entered it — a
      pool wide enough to reach them is 2,685 names and a different piece of work. Recorded in the
      document rather than silently skipped, next to the decision below
- [x] **`dev_voro_coord_divi_mol_vol` stays, and the write-up says what that costs.** The
      exposure is measured, not argued: the JARVIS table stores `voro_coord = 1.0` for `Cs` and
      `Gd`, and of the two only gadolinium is in this dataset — **18 of 1,279 rows (1.4 %)**
      compute that feature from filler. Against that, the feature is selected by all five folds.
      Removing a unanimously-selected feature by hand, after seeing the result, is the kind of
      decision this phase exists to remove rather than relocate. What follows is a statement, not
      a silence: **boxed onto #83**, the model card owes the sentence
- [x] **The Gordy trade, as rows rather than as a feature (from #20).** Settled by #24 — drop the
      feature, keep the rows — and this card ran the other side of it. **The 22-candidate pass
      does not select `dev_Gordy_electonegativity`.** Same 700-row pool, same seed, same budget as
      #24's controlled comparison, which confirmed it; the only difference is the 71 rows
      screening drops, and they reverse the verdict. Two single passes, opposite answers: the
      trade was settled on rows rather than on importance, and this is why it had to be
- [x] **The first real run's tables were read before anything was re-run (from #24).** The
      five-fold run was not repeated. What this card added was the two cheap-by-comparison single
      passes it owed, ~11 min each
- [x] **"The 22 features" was never a stable object, and this card chose what to publish: the
      consensus 14.** Every one of the 21 candidates is selected by some fold — the union is the
      whole pool, so the permissive reading performs no selection at all — and 14 by all five.
      The union, a threshold, and the "refit on all the training rows" reading (which would
      publish the whole-split 18) are each argued and rejected in the document's *What was
      considered and not done*. The consensus is a **strict subset** of the whole-split answer, so
      the conservative choice contradicts none of them
- [x] **The per-fold-versus-whole-split gap was confounded, and measuring the missing run
      corrected it.** #24's box read the whole-split run as selecting **14** against the folds'
      16–20 and concluded that fewer rows make Boruta less selective. That 14 was the *unscreened*
      probe. Screened — the run this card owed — the same whole-split pass selects **18**, inside
      the folds' own range. The direction still holds and the document still states it, but the
      size cannot be claimed from these runs: row count and screening move together in all three,
      and screening is not neutral thinning. **Within the folds the row count does not order the
      answers at all** — 571 rows → 16 features, 704 rows → 18, 635 → 20 — which is the evidence
      that the fold-to-fold differences are about *which* compositions were held out, and the
      argument for reading the consensus
- [x] **Compared against the leaking shape deliberately, both ways.** `--once` (screened, 21
      candidates, 864 rows fitted, 18 selected) and `--once --all-features` (screened, 22
      candidates, 629 fitted, 16 selected) are both in the document as *columns*, each labelled
      with what it is and is not — the second says in its own output that it is leak L6. The four
      things being compared nest: **consensus 14 ⊂ 22-candidate 16 ⊂ whole-split 18 ⊂ pool 21**,
      so the disagreement between the readings is about how far to cut, never about direction

## Runnable check

```bash
# Republish the write-up from the tables on disk. Fits nothing; seconds, not an hour.
conda run --no-capture-output -n Project python -m hydms.surrogate.select --emit-comparison

# The guards: the declared contract is the run's consensus, and the committed document is the
# one this code generates from the committed tables.
conda run --no-capture-output -n Project python -m pytest tests/surrogate/test_comparison.py -q
```

The two single passes this card owed, for the record — about eleven minutes each, and **not**
to be re-run to republish:

```bash
conda run --no-capture-output -n Project python -m hydms.surrogate.select --once
conda run --no-capture-output -n Project python -m hydms.surrogate.select --once --all-features
```

## Traces to

`docs/PRD-inverse-design.md` — S7, R4

## Narrative

- 2026-09-05: Landed. `hydms/surrogate/comparison.py` (the document, generated), `SELECTED` in
  `hydms/descriptors/contract.py`, `--emit-comparison` in `hydms/surrogate/select.py`,
  `reports/feature_selection/` published into the repository, 14 tests. Four things worth keeping.

  **The published set is the consensus 14, and the reason is the one thing this phase is about.**
  Every one of the 21 candidates is chosen by some fold, so the union performs no selection; a
  threshold would be a cut chosen after seeing where the features fell, which is the defect this
  phase exists to remove rather than relocate. The serious alternative was the *refit* reading —
  in nested CV the folds estimate the procedure and the deployed model refits the whole procedure,
  selection included, on all the training rows, which would publish the whole-split 18. It was
  rejected because Chapter 3 reports the feature set **as a finding**, and a set from a single fit
  carries no evidence about its own stability. The consensus is a strict subset of that 18, so the
  conservative choice contradicts nothing.

  **Two contracts, not two versions of one.** `CONTRACT` stays the published 22 — archival record,
  candidate pool, AC-2's parity set — and `SELECTED` is what a model is fitted on. Replacing
  `CONTRACT` would have made the next selection run circular (its own pool) and would have moved
  AC-2's parity check from 22 columns to 14 as a side effect nobody asked for.

  **A box on this card was wrong about the data, again, and the missing run is what caught it.**
  #24 recorded the whole-split run selecting 14 against the folds' 16-20 and read it as statistical
  power. That 14 was the *unscreened* probe; screened, the same pass selects **18** — inside the
  folds' own range. Row count and screening move together across all three runs, so the direction
  can be stated and the size cannot, and within the folds the row count does not order the answers
  at all (571 -> 16, 704 -> 18, 635 -> 20). That last number is the real argument for the
  consensus: what separates the folds is *which* compositions were held out.

  **The 22-candidate run does not select the feature that defines the 22.** Same 700-row pool,
  same seed, same budget as #24's controlled comparison, which confirmed `dev_Gordy_electonegativity`;
  the only difference is the 71 rows screening drops, and they reverse the verdict. #24 settled
  that trade on rows rather than on importance, and this is the measurement that shows it had to
  be settled that way.

  **The document is generated, and that is the point.** `--emit-comparison` fits nothing: it reads
  the tables the slow runs left and rebuilds the write-up in a second, and a test asserts the
  committed document is exactly what the committed tables produce. `REPORT.md` came to disagree
  with the CSVs beside it because no such check existed. (by @assistant)

- 2026-09-04: One box added by #18 — eleven JARVIS composite columns disagree with their own
  parts, and one selected feature rests on a placeholder `voro_coord` (by @assistant)

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
