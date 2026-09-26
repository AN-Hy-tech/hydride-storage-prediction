---
id: 87
status: done
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
AC-6 — and **ten** canonical compositions carry conflicting class labels, so the join needs a
decision, not a merge. (The card was written expecting five, which is the count on the raw formula
string. Canonicalisation adds five more by merging spellings that were labelled independently; see
the narrative.)

## Done when

- [x] `hydms/data/canonical.py` produces a stable key from element fractions, insensitive to element
      order, formula scaling, whitespace and case — `canonical_key()`. Case is the one of the four
      that is only half decidable and the module says so: the output casing is the periodic table's,
      and a miscased *input* is refused rather than guessed at, because `co` is `Co` or `C`+`O`.
      Measured: no two of the 1149 strings differ by case alone, so the refusal costs nothing here
- [x] The key is used as the split key **and** the cross-validation group key — `group_keys(frame)`
      is the single seam, and the published split protocol is reproduced in
      `tests/data/test_canonical.py` to show it working as one: 16 canonical compositions straddle
      under the raw string, none under the key. The modules that will *call* it are #13 and #88, and
      both now carry a box naming the function
- [x] `Alloy_class` is re-joined on the canonical key — `alloy_class_table()` per composition with
      the evidence beside it, `alloy_classes()` per row for #12 to carry through featurisation
- [x] The **~~5~~ 10 compositions carrying conflicting class labels** are reconciled by a stated rule,
      and the rule is recorded in the narrative — `ALLOY_CLASS_PRECEDENCE`, most specific structural
      claim first, not a majority vote
- [x] The reconciliation is reproducible: the same input gives the same labels — asserted under a
      shuffled row order, because a rule that depends on which row came first is a rule nobody can
      re-derive
- [x] A test asserts that the 16 known cross-split collisions now share one key — and the six
      measured pairs from `tests/conftest.py`, and the 35 rows they carry
- [x] Canonicalisation never silently merges two genuinely different materials — asserted on the full
      dataset. `separation()` compares all 8920 comparable pairs over both raw files: the widest gap
      the key merged is 3.46e-05, the closest it did not is 1.01e-04, and the assertion is that the
      first is smaller than the second. It is also demonstrated red — at three significant digits the
      order reverses, which is a silent merge
- [x] **Account for the collapse in three steps, not one.** Measured by #9: whitespace alone takes
      1149 formula strings to **1142** — 34 strings carry a trailing space, 9 an internal one, and 7
      of the padded forms already have an unpadded twin in the file. Element order and scaling take
      it the rest of the way to 1115. A canonical key that reports only the endpoint hides which
      normalisation did what, and the whitespace step is the one a downstream `str.strip()` could
      silently reproduce elsewhere. Measured: 1149 → 1142 (whitespace) → 1121 (element order) →
      1115 (scaling), reported by `collapse()` and asserted step by step, whitespace anatomy included
- [x] **Reuse `hydms.data.load.parse_formula` rather than writing a second parser.** It is already
      the validated grammar — periodic-table membership, positive amounts, non-empty result — and is
      asserted at parity with CBFV over all 1279 + 772 formulae. Two parsers is two grammars — and the
      key inherits its refusals, which is how `Xx2` and `Mg0` stay refused at the door. #20 still
      names `pymatgen.core.Composition`; that card now carries a box saying not to
- [x] **The two class vocabularies are not nested.** `hydride_data.csv` has 10 classes including
      HEA/LEA/MEA; ML-HydPARK's `Material_Class` has 9 and splits AB2 into `AB2(C14)` and
      `AB2(C15)`. Neither is a subset of the other, so the re-join needs a stated mapping, not a
      merge. Both closed sets are declared in `hydms/data/load.py`. `ML_HYDPARK_CLASS_ALIASES` folds
      C14/C15 into AB2 and nothing consumes it: the curated class is complete on all 1279 rows.
      Measured, and the reason a casual join would have been a mistake — of the 378 canonical keys the
      two files share, **30 of the 377 that carry both labels disagree**
- [x] **L13 has no sentinel and this card owes one.** `extract_features_cbfv.py:19-21` drops every
      object column but `Composition`, destroying `Alloy_class` and with it every hope of
      leave-one-alloy-class-out validation (AC-6). Once the class is re-joined on the canonical key,
      add the **L13 sentinel** to `hydms/qa/sentinels.py`: `Alloy_class` survives featurisation for
      every row. Until it exists, HG-1 cannot report green. Landed: `assert_metadata_survives` (the
      seventh detector) plus the sentinel, subject `hydms.descriptors.featurize`, with two
      reproductions — the archival drop, and a row that loses its label while the column survives.
      It reports **`pending`**, not green: the featuriser does not exist yet, so `closed_by` moved to
      #12 and that card owes the `live` hook. The runbook's S2 exit line claiming L13 goes green at
      S2 has been corrected
- [x] **Recount the `(key, temperature)` collisions after canonicalisation, and confirm the class
      conflicts are the same five.** Two numbers measured by #10 on the **raw string** move when the
      key changes, and both matter downstream. First: 1279 rows carry 1272 distinct
      `(Composition, temperature(K))` pairs — seven repeats, six of them genuine replicates from
      different citations. Canonicalisation merges strings, so that count can only fall, and the new
      repeats are what #13's splits and #88's folds see as one material measured twice. Second: five
      *raw formula strings* already carry more than one `Alloy_class`, which is the same count this
      card states for canonical compositions. Either canonicalisation adds no new conflict — worth
      asserting rather than assuming — or the two fives are different sets and the reconciliation
      rule has more work to do than the box above implies.
      **Answered, and it is the second one.** `(key, temperature(K))`: 1272 distinct pairs become
      **1268** over 1279 rows — eleven repeats, four of them new, each being two spellings of one
      material measured at one temperature. Class conflicts: **5 raw strings become 10 canonical
      compositions.** The five raw ones are a strict subset — canonicalisation resolved none of them
      — and the five it adds are `Al0.5Mg0.5`, `Al0.6Mg0.4`, `Ce0.07692Mg0.9231`, `Ce0.1Mg0.9` and
      `Mg0.5Ni0.5`, each a pair of spellings that the file labelled independently

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

- 2026-09-03: Box added by #10. Two counts measured on the raw formula string that move, or need
  confirming, once the canonical key exists: 1272 distinct `(Composition, temperature(K))` pairs
  over 1279 rows, and **five** raw strings already carrying more than one `Alloy_class` — the same
  number this card states for canonical compositions. Canonicalisation can only merge, so the
  class-conflict count can only rise; that the two numbers match is either a fact worth asserting
  or a coincidence hiding a larger reconciliation. (by @assistant)

- 2026-09-03: **Landed.** `hydms/data/canonical.py`, `tests/data/test_canonical.py` (50 tests),
  `assert_metadata_survives` in `hydms/qa/detectors.py`, the L13 sentinel, and
  `tests/leaks/test_l13_class_survival.py`. Seven things worth keeping:

  **1. The resolution is a decision, and it was measured rather than picked.** Rounding is forced:
  the key must be a pure function of one formula string, because a candidate arriving at
  `predict_capacity()` has no corpus to be clustered against, and an identity that depends on which
  other rows happen to be present is not an identity. So the corpus-level property clustering would
  have given for free — *nothing merged is farther apart than something not merged* — is asserted
  instead, by `separation()`, over all 1784 distinct formula strings in both raw files. The sweep:

  | digits | compositions | widest merged | closest separated | safe |
  |---|---|---|---|---|
  | 3 | 1114 | 3.10e-04 | 1.98e-04 | **no** |
  | 4 | **1115** | 3.46e-05 | 1.01e-04 | yes |
  | 5 | 1116 | 3.15e-06 | 3.15e-05 | yes |

  Four is the only value that is both safe and reproduces the **1115** every document in this
  repository states. At five, `Ti0.2167V0.2167Nb0.2167Cr0.35` and
  `Ti0.216667V0.216667Nb0.216667Cr0.35` become two materials — the same alloy typed to two
  precisions, and the pair that decided the number.

  **2. Significant digits, not decimal places** — they group identically here and differ on one row.
  At four decimal places `Mg0853Ni0.125La0.022` renders as `La0`: an element claimed at zero, in a
  key `parse_formula` cannot read back. Also rejected: normalising by the largest amount instead of
  by the sum, which would have made the key an exact fixed point of itself, and which measurably
  merges a pair 3.15e-05 apart while separating one 3.15e-06 apart — the silent merge the key exists
  to prevent. The cost of that choice is that **a key is a label, not an input**: re-keying a key
  moves a final digit for 185 of 1784 formulae, because rounded fractions no longer sum to one. The
  test that matters asserts the moved digit never lands on *another* material's key.

  **3. `Alloy_class` is reconciled by precedence, not by majority.** `ALLOY_CLASS_PRECEDENCE` is
  `AB5 ≻ AB2 ≻ AB ≻ A2B ≻ Mg ≻ HEA ≻ MEA ≻ LEA ≻ SS ≻ MIC` — most specific structural claim first.
  The vocabulary is not one axis: four labels name a stoichiometric family, one names a chemistry,
  three count principal elements, two are catch-alls. So `Ti0.8Zr0.2Mn1Cr1` being both `AB2` and
  `MEA` is not a contradiction, it is two true statements, and AC-6 needs a partition. A majority
  vote was rejected because it counts *citations*: `Mg2Ni1` carries three `Mg` rows to one `A2B`,
  and Mg2Ni is the textbook A2B compound. Eight of the ten conflicts are ties in any case, so a
  majority rule would need a precedence to break them and would then be two rules where one will do.
  All ten resolutions are pinned individually in the test, and each is the label a metallurgist
  gives the material. 13 of 1279 rows change label.

  **4. The card's "same five" premise was wrong, in the direction the box anticipated.** Five *raw
  strings* carry two classes; ten *canonical compositions* do. The five raw ones survive unchanged
  and canonicalisation adds five more, each a pair of spellings the file labelled independently —
  `Ce1Mg12` is `MIC` while `Mg12Ce1` is `Mg`, the same 6.0 wt% at 598 K. Every document stating five
  has been corrected.

  **5. `(key, temperature(K))`: 1272 distinct pairs become 1268.** Eleven repeats, four of them new.
  #10 keyed the merge on the spine's index label because that pair was already not a row identity;
  canonicalisation makes it less of one, which is #13's and #88's to see as one material measured
  twice.

  **6. A data defect fell out.** `Mg0853Ni0.125La0.022` is a missing decimal point — 0.853 + 0.125 +
  0.022 = 1.000 exactly — so the row parses as Mg-853 and featurises as essentially pure magnesium.
  It passes #9's schema and it passes CBFV. It is the only atomic fraction below 1e-4 in either raw
  file, which is how the key found it. Boxed on #14; **not** repaired here, because `Machine_Model/`
  is read-only under the freeze and a loader that quietly fixes its input hides the fix.

  **7. The L13 sentinel is `pending`, not green, and that is the honest answer.** L13's site is the
  featuriser, so the sentinel's subject is `hydms.descriptors.featurize`. Pointing it at this
  module instead would have made it green today while guarding a different property — the class
  exists — leaving the drop itself unguarded. `closed_by` therefore moved from #87 to **#12**, which
  is the card that makes the class survive featurisation and owes the `live` hook; the runbook's S2
  exit line, which said L13 goes green at S2 because #87 owes the sentinel, has been corrected.
  `assert_metadata_survives` is the seventh detector and the first that asks whether a stage
  *carried something through* rather than whether it touched held-out data. (by @assistant)

- 2026-09-03: Corrected by #12. `alloy_class_table` ordered a composition's labels with
  `ALLOY_CLASS_PRECEDENCE.index` *before* calling `reconcile_class`, so an out-of-vocabulary label
  raised a bare `ValueError: tuple.index(x): x not in tuple` — naming neither the label nor the
  row, with `reconcile_class`'s careful refusal sitting two lines below, unreachable from the
  conflicted path. The guard was written and tested directly; nothing had ever driven a bad label
  through the table. Fixed by reconciling first. The missing-class message, which said "a missing
  class is card #12's to label UNKNOWN", was corrected in the same commit: #12 settled it as a
  refusal. (by @assistant)
