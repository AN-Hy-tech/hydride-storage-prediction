---
id: 20
status: done
priority: High
blocked_by: [17, 18, 19]
assignee: "@amirhossein"
tags: [p1, l2, S3, S12]
---

# featurize() — the descriptor layer's public interface

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** Everything above: tables, statistics, composites and column order.

## Job story

When I have a list of candidate formulas, I want one function call that returns model-ready features, so I can screen candidates without reassembling the training pipeline.

## Why this exists

The deep interface the rest of the system sees:

```python
featurize(formulas: Sequence[str], temperatures: ArrayLike) -> DataFrame  # 22 columns
```

One call. No CSV in, no CSV out. Architectures A and B both call this per batch of
candidates, so it must be batched — memo 4.3 practical check 3 warns explicitly against
per-formula loops.

Formula parsing via `pymatgen.core.Composition` (MIT, already a dependency).

## Done when

- [x] Single public function; everything else in the layer is private — `featurize()` and the
      exception it raises. `hydms/descriptors/featurize.py` exports two names and both are
      part of one interface; every helper is underscored
- [x] Batched: 10k formulae in one call, not 10k calls — **0.31 s**, against 0.21 s for the
      1,278 featurisable curated rows. Element symbols are interned once and each of the 19
      properties becomes a single fancy-index, so the per-row Python work is the parse and
      nothing else. #22 owns the benchmark that keeps it honest
- [x] Invalid formulae are reported with their index, never silently dropped — **and neither
      is anything else**. Every offender in the batch is named at once, with its label, and
      the call raises rather than returning a shorter frame: a matrix with fewer rows than it
      was given is how features come to be joined to the wrong compositions
- [x] Output passes `assert_contract` (19) by construction — and is *asserted* to, on the way
      out. "By construction" is a claim a rewrite can quietly break; the check costs a
      microsecond
- [x] **The parser is `hydms.data.load.parse_formula`, not `pymatgen.core.Composition`.** The line
      above naming pymatgen predates #9, which built the validated grammar this project uses —
      periodic-table membership, strictly positive amounts, non-empty result — and asserted it at
      parity with CBFV over all 1279 + 772 formulae. #87 then built the canonical key on that same
      function. Adding pymatgen here would make three parsers with three ideas of what a formula is,
      and the differences would show up as compositions that featurise but cannot be keyed. Check
      whether pymatgen is even in `environment.lock.yml` before assuming it is available —
      **it is**, `pymatgen=2024.11.13`, which makes this a decision rather than an accident:
      the parser is ours because the grammar, the canonical key and the parity claim are all
      built on it, not because pymatgen was missing
- [x] **Creating `hydms/descriptors/featurize.py` turns gate HG-1 red until #12 wires L13.** The L13
      sentinel (written by #87) names that module as its subject and has no `live` hook yet, so the
      moment the module exists the audit reports `L13 [unwired] #12`. That is the mechanism working;
      coordinate with #12 rather than deleting the sentinel — **it happened exactly as written.**
      HG-1 is 4/13 and red, and eight tests across `tests/gates/` and `tests/leaks/` are red with
      it, including `test_l13_is_guarded_and_waits_on_the_featuriser`, whose own docstring
      predicted its death. The subject was not re-aimed and the sentinel was not deleted. #12 is
      `doing`, is now unblocked, and takes the tree green at 5/13

- [x] **Two obligations the contract hands this card (from #19).** First, `temperature(K)`
      is `int64` in the raw file and `float64` in the contract, so this function owes the cast —
      `assert_contract` refuses the integer column by name, and a candidate at 313.5 K would
      otherwise truncate to 313 in silence. Second, call
      `hydms.descriptors.contract.CONTRACT.computability(composition)` *before* building a row:
      seven of the 22 are not computable for every composition, and a featuriser that emits NaN
      instead of refusing is one median-fill away from a number that looks like a measurement.
      The verdict names the blocking element and distinguishes a missing element from an empty
      published cell, which is what the index-reporting box above needs. **Both done, and the
      refusal is larger than the card implies: 266 of the 1,279 curated rows** — 265 for Gordy
      alone and `Eu1Ni5` for seven features at once — so the full 22 cannot featurise the
      training set at all. Drop `dev_Gordy_electonegativity` and the remaining 21 cover
      **1,278 of 1,279**. That pair of numbers is the trade #24/#25 make, and it is pinned in
      `tests/descriptors/test_featurize.py` rather than described

- [x] **Read the published composite column; never derive it from its parts (from #18).** The five
      composite properties in the 22 are per-element columns of the JARVIS table, and CBFV reads
      those columns — so the column is what parity means (#21). On those five the two routes are
      the same double for all 82 elements that carry them, but eleven of the table's 156 composite
      columns are *not* the arithmetic their names claim, so this is a rule rather than a
      preference. Call `hydms.descriptors.composites.require_self_consistent("jarvis", props)` on
      the composite properties this function is about to featurise: it raises naming the column and
      the element, and it is cheap enough to run once per property set — run once per table
      per call, **before any row is built**, so an empty batch refuses too. Pinned with a
      contract over `avg_atom_mass_mult_voro_coord`, one of the eleven

- [x] **Not asked for, and it moved #17's module: a batch of one was not the same arithmetic
      as a batch of many.** Found by the test that asserts a composition does not depend on
      what it was batched with. Transposed to element-leading, a *single* composition leaves
      the reduction axis contiguous, so numpy sums it pairwise after all — and its contiguous
      sum switches from a plain loop to an eight-accumulator unrolled one at exactly eight
      elements. Measured over 200 random compositions per arity: bit-identical up to arity 7,
      and from **arity 8** a lone composition disagrees with itself inside a batch by up to
      **5.5e-12** on `avg` and `dev`. **Eleven of the 1,279 curated rows are that wide**, and
      featurising one formula alone is exactly what the app (#82) and AC-4's round-trip (#33)
      do. `statistics()` now reduces a duplicated pair and discards the copy, so the property
      holds at every arity; #17's own test used arity 5 and is widened to 10, where deleting
      the fix turns it red. No committed number moves — every existing pin is a batch

- [x] **Not asked for: the tables are an argument, because #21's requirement is a requirement
      on *this* interface.** #21 says the gate "must read: the featuriser reproduces CBFV to
      1e-9 **given the same table**" — the two Oliynyk editions differ on eight of the thirteen
      properties, so a comparison against the shipped table measures the tables, not the code.
      That cannot be arranged from outside a featuriser that resolves its own tables, and every
      other function in this layer already takes its table as a parameter. So `featurize(...,
      tables=...)` exists, defaults to the shipped cited ones, and two siblings gained the
      minimum to support it: `FeatureContract.computability(..., tables=)`, so the verdict is
      about the numbers actually used rather than about the shipped hole, and
      `PropertyTable.of()`, so a caller builds one without reaching through a frozen
      dataclass's underscored field. Both are boxed on #21 with what it has to do

## Runnable check

```bash
python -m pytest tests/descriptors/test_featurize.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, S12

## Narrative

- 2026-09-04: **Landed.** `hydms/descriptors/featurize.py` + `tests/descriptors/test_featurize.py`,
  52 tests. Suite 554, of which **546 pass and 8 fail — all eight are HG-1, on purpose** (below).
  ruff 0.8.4 and mypy 1.13.0 clean. Four things this card taught, and one of them changed a module
  that was already `done`.

  **A batch of one was not the same arithmetic as a batch of many, and only from eight elements
  up.** The test that says a composition does not depend on its batch went red on the ten-element
  HEA in the fixture set. The cause is one layer down: #17 established that the reduction must run
  down the leading axis because numpy sums the *fast* axis pairwise — but a batch of **one**,
  transposed, leaves the leading axis contiguous too, and numpy's contiguous sum switches from a
  plain loop to an eight-accumulator unrolled one at exactly eight elements. Measured over 200
  random compositions per arity: identical to the bit up to arity 7, and from arity 8 a lone
  composition disagrees with itself inside a batch by up to 5.5e-12 on `avg` and `dev`. That is
  three orders inside AC-2's 1e-9, so it would never have failed a gate — it would have made a
  single-formula prediction (#82) and AC-4's round-trip (#33) disagree with the training matrix
  for the eleven curated rows of eight elements or more, quietly, forever. Fixed in
  `stats.statistics` rather than worked around here, because that is where the axis decision
  lives: a lone composition is duplicated, the pair is reduced, the copy discarded. #17's own test
  passed throughout because its arity was 5; it is now 10, and deleting the fix turns it red.

  **The refusal is much larger than "seven features are not always computable" sounds.** Counted
  as *rows a caller loses*, the full 22-feature contract cannot featurise 266 of the 1,279 curated
  rows — 265 for `dev_Gordy_electonegativity` alone and `Eu1Ni5` for seven at once — so the
  published feature set cannot be built from the citable tables at all. The number that matters to
  #24/#25 is the other one: without Gordy, the remaining 21 cover **1,278 of 1,279**. One feature
  is the whole difference between 1,278 rows and 1,013, and both numbers are now pinned rather
  than described.

  **#21's requirement turned out to be a requirement on this module's interface.** "The featuriser
  reproduces CBFV given the same table" cannot be arranged from outside a function that resolves
  its own tables, so `tables=` is a parameter — which then forced the honest version of the
  computability verdict, because asking the *shipped* table whether a composition is featurisable
  while reading CBFV's would refuse the 266 rows the gate exists to compare. `computability` takes
  the same tables, and `PropertyTable.of` exists so #21 does not build one through an underscored
  dataclass field. This is the layer's existing convention (`disagreements`, `require_coverage`
  and `require_self_consistent` all take their table), not a new one.

  **The value pin found nothing wrong, which is worth saying.** All 22 columns against CBFV's own
  output over the sixteen fixture formulae, with CBFV's own table supplied: worst 4.547e-13
  absolute, 6.828e-15 relative. The assembly — right statistic, right property, right table, right
  column — was correct first time, and the residue is the element order #17 already measured. That
  is a 16-formula pin and not the gate; #21 still owns 1,279 formulae and an output that names the
  offending column.

  **HG-1 is red and that is the mechanism, not a regression.** `L13 [unwired] #12 —
  hydms.descriptors.featurize now exists and this sentinel is still pointed at a miniature of it.`
  Eight tests fail with it, including one whose docstring predicted its own death. The subject was
  not re-aimed and nothing was deleted. #12 is `doing` and unblocked; it owes the `live` hook and
  takes HG-1 to 5/13. (by @assistant)

- 2026-09-04: One box added by #18: composite columns are read, not derived, and eleven of the
  table's 156 are not their own arithmetic — the guard to call is named in the box (by @assistant)

- 2026-09-03: Two boxes added by #87. The card's "formula parsing via `pymatgen.core.Composition`"
  line is now the odd one out — #9 owns the grammar and #87's key is built on it — and creating this
  module is what makes the L13 sentinel demand its live hook (by @assistant)

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
