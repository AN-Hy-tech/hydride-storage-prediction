---
id: 19
status: done
priority: High
blocked_by: [8]
assignee: "@amirhossein"
tags: [p1, l2, AC-2]
---

# The 22-feature contract

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The exact feature names, their order, and their dtypes.

## Why this exists

Column order is a silent-failure surface: a model trained on one order and fed another
produces plausible, wrong numbers. Acceptance criterion AC-4 exists precisely to catch it.

This module is the single source of truth for the feature list, consumed by the featuriser,
the scaler and the predictor alike.

## Done when

- [x] Feature names, order and dtypes declared in one place — `hydms/descriptors/contract.py`,
      `CONTRACT: FeatureContract` over 22 `FeatureSpec`s, each carrying
      `(name, statistic, table, property)`. **The order is a declaration, not a recovery.**
      The order the published model was trained in was `selected_cols_final`
      (`Boruta_FeatEng.py:112`) and it is nowhere in this repository:
      `Machine_Model/data/processed_data/` was never committed, and every committed listing
      of the 22 is sorted by something else — `feature_selection_report.csv` by SHAP
      descending, `feature_importance.csv` alphabetically,
      `feature_target_pearson_corr.csv` by correlation. The module declares the
      SHAP-descending order because that is the one REPORT.md §3.2 prints, and the test
      asserts it against that CSV rather than against a retyped list. What protects AC-4 is
      that exactly one place declares an order, not that the order matches a history nobody
      kept
- [x] `assert_contract(df)` raises on missing, extra, reordered or wrongly-typed columns —
      all four reported *together*, plus a fifth the card did not ask for: duplicated column
      names, which pandas permits and which would make every other check ambiguous
- [x] The contract is written into the artifact manifest so a model records what it expects
      — **half of this landed; the other half is #4's and is boxed there.**
      `as_manifest()` / `from_manifest()` round-trip through JSON and are digest-checked, so
      a manifest whose names, order or dtype were edited after the fit is refused rather
      than believed. Nothing writes it yet: `hydms/artifacts/` is a docstring, card #4 is
      `backlog`, and embedding the payload is that card's job
- [x] After feature selection re-runs (25), the contract is regenerated rather than
      hand-edited — `FeatureContract.from_names(names)` rebuilds the whole contract from
      names alone, because a name carries its own provenance. Verified injective over
      everything either table could offer: 5 statistics × 537 properties = **2,685 names,
      2,685 distinct**, no collision; and the two tables share **no** property name, so a
      name resolves to a table unambiguously. Three JARVIS properties do begin with a
      statistic's spelling (`avg_ion_rad`, `max_oxid_s`, `min_oxid_s`), which is why the
      split is on the first underscore and not on any of the five prefixes.
      `from_names(CONTRACT.names) == CONTRACT` is a test

- [x] **Two of the 22 cannot be computed from the citable sources, and the contract has to
      say so per composition rather than per feature (from #16). Measured: it is seven, not
      two.**
      `dev_Gordy_electonegativity` needs `gordy_en`, which the published Oliynyk table
      supplies for 34 of the 55 dataset elements and leaves blank for 21: Ce, Dy, Er, Eu,
      Gd, Hf, Ho, Ir, Lu, Nd, Os, Pr, Pt, Re, Sm, Ta, Tb, Th, Tm, U, W. And all six JARVIS
      features are unavailable for europium, whose properties NIST marks -9999. The card
      counted those six as one; as columns they are six, and a caller asking "can I build
      this matrix?" needs six answers. Counted over all 1,279 curated rows:

      | feature | blocked by | rows | compositions |
      |---|---|---:|---:|
      | `dev_Gordy_electonegativity` | 21 elements | 266 of 1,279 | 236 of 1,115 |
      | the six JARVIS features, each | Eu | 1 | 1 |

      **The contract records computability**, so #24/#25 do not have to re-run selection
      without those features — but they now have the numbers to decide whether to.
      `CONTRACT.computability(composition)` returns a verdict before anything is computed,
      naming the blocking element and distinguishing "the table has no such element" from
      "the published table leaves the cell empty". The lists are pinned in
      `tests/descriptors/test_element_data.py` and the consequences in
      `tests/descriptors/test_contract.py`

- [x] **The Gordy hole belongs to the citable edition, not to CBFV — so gate AC-2 cannot
      see it.** CBFV's copy of the Oliynyk table supplies `gordy_en` for **all twenty-one**
      of the elements Lee et al. 2024 leave blank (Ce 4.5734, Hf 6.3704, Pr 4.6395, …,
      measured against `tests/descriptors/data/cbfv_oliynyk_reference.csv`). So the
      published model trained on a real Gordy number for every row, #21 runs its parity
      comparison against a table where no hole exists, and the 266 rows are a cost the
      reimplementation *acquires* by citing its sources properly. Boxed on #21, #24 and #25

- [x] **The loss falls on AB5 and MIC, not on "AB5 and AB2".** The card's box guessed
      "nearly the rare-earth set, and so most of the AB5 and AB2 chemistry". Rows losing at
      least one feature, by reconciled alloy class: AB5 91/196 (46.4%), MIC 54/127 (42.5%),
      HEA 20/77 (26.0%), AB 22/90 (24.4%), SS 19/103 (18.4%), MEA 12/109 (11.0%),
      A2B 3/32 (9.4%), **AB2 34/371 (9.2%)**, Mg 11/148 (7.4%), LEA 0/26. AB2 is the second
      *least* affected class and AB5 loses under half its rows. On the second source,
      ML-HYDPARK's 772 formulae, the same seven features cost 128 rows (16.6%)

- [x] **Every column is `float64`, including `temperature(K)`, which the raw file stores as
      `int64`.** Both loader schemas declare it `integer` and all 1,279 values are integral,
      so this is a real cast and not a formality: the applicability domain ships as a
      continuous bound (`temperature_min_k: 195.0`), a scaler returns floats, and a
      candidate evaluated at 313.5 K would truncate to 313 in an integer column.
      `assert_contract` refuses an `int64` temperature by name; #20 owes the cast

## Runnable check

```bash
python -m pytest tests/descriptors/test_contract.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — AC-2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: Landed. `hydms/descriptors/contract.py` and 42 tests in
  `tests/descriptors/test_contract.py`; 481 tests green, ruff 0.8.4 and mypy 1.13.0 clean,
  `audit()` unchanged at 4/13 — no sentinel names this module either, and L13 still waits on
  `hydms.descriptors.featurize` (#20). Four things this card taught, three of them
  corrections to its own instructions.

  **"Two of the 22" is seven.** The box was right about both causes and wrong about the
  count, because it folded the six JARVIS features into one — they do all fail on one
  element, europium, but a contract is a list of columns and a caller building a matrix
  needs six answers, not one. The measurement is in the box above and pinned by
  `test_seven_of_the_twenty_two_are_not_computable_everywhere`.

  **The hole is ours, not CBFV's, and that changes who can see it.** CBFV's copy of the
  Oliynyk table supplies `gordy_en` for all 21 elements the 2024 revision leaves blank. Gate
  AC-2 (#21) compares against that table by construction — #16 made it test input precisely
  because the two editions differ — so AC-2 will go green while the shipped featuriser
  cannot produce `dev_Gordy_electonegativity` for 266 of 1,279 rows. That is not a bug in
  the gate; it is the second thing this phase has found that AC-2 structurally cannot see,
  after #17's wrong-axis reduction. Both are now boxed on #21.

  **The card's guess at the shape of the loss named the wrong family.** It expected "most of
  the AB5 and AB2 chemistry". AB2 is the second least affected class at 9.2% and AB5 loses
  46.4% — under half. The pair that carries the loss is AB5 and MIC (42.5%). Worth saying
  because the sentence was a physical intuition about where rare earths live, and the
  measurement disagrees: the rare-earth-heavy rows in this dataset are AB5 and the
  intermetallic residue, not the Laves phases.

  **The order was never persisted, so the contract declares one rather than recovering it.**
  I went looking for `selected_train.csv` expecting to pin the training column order and
  found that `Machine_Model/data/processed_data/` is not in the repository at all, and that
  all three committed listings of the 22 are sorted by three different keys. There is no
  historical order to be faithful to. The module says so, and the test asserts the declared
  order against `feature_selection_report.csv` so that at least the *published* order cannot
  drift silently. This is the same shape as #11's finding about the published `log` column:
  the archival record is thinner than it looks, and a check written against a number that
  was never stored is a check against a memory.

  **One thing that was confirmed rather than corrected.** The naming rule — a feature is
  `f"{statistic}_{property}"` with a 13-entry alias map for CBFV's Oliynyk spellings — was
  assumed to be regenerable and turned out to be provably so: 2,685 possible names over both
  tables, all distinct, and no shared property name between the tables. #25 can rebuild the
  contract from names alone. (by @assistant)
