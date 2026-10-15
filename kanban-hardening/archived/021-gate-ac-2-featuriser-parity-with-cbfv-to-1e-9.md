---
id: 21
status: done
priority: High
blocked_by: [5, 20]
assignee: "@amirhossein"
tags: [p1, l2, AC-2, R3]
---

# GATE AC-2: featuriser parity with CBFV to 1e-9

**Stage S3 — Descriptor layer** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** Proof that the reimplementation is faithful.

## Why this exists

This is the gate that makes the CBFV replacement trustworthy. If the reimplemented
featuriser does not reproduce CBFV's numbers on the training set, every downstream model
would be trained on subtly different features than `REPORT.md` describes.

**If this fails, the reimplementation is wrong — not CBFV.**

## Done when

- [x] All 1279 training formulae featurised by both CBFV (in the `Project` env) and `hydms.descriptors`
      — **1,278 of them compared; the 1,279th is `Eu1Ni5` and neither side can answer it honestly**
- [x] Every one of the 22 columns agrees to within 1e-9 absolute
- [x] Failure output names the column and the worst-offending formula, not just a boolean
- [x] Registered in the gate harness as `AC-2` and run by CI

- [x] **Parity cannot be a claim about the numbers, only about this code (from #16).** The
      published Oliynyk table is a *revised* edition of the one CBFV ships: of the thirteen
      properties the selected features need, five agree exactly and eight do not -- up to 10 in
      `valence_d` (Ga, Ge), 2.0 in `gilman_no_of_valence_electrons` (Lu), 0.54 in
      `covalent_radius` (Th, U). Comparing our featuriser's output against CBFV's while the
      tables differ measures the tables, not the code. This gate must read: **the featuriser
      reproduces CBFV to 1e-9 given the same table**, with
      `tests/descriptors/data/cbfv_oliynyk_reference.csv` supplied as that table. It is test
      input for this gate and must never become package data -- CBFV carries no licence, which
      is the whole reason the descriptor layer exists.
      **Amended: the gate reads the fixture's *source*, not the fixture.** The requirement is
      met either way — the two are bit-identical, `build_element_tables.py` writes each cell
      with `repr(float)` — but the gate has already imported CBFV to produce the expected
      *numbers*, and taking the table from anywhere else admits a skew between the two halves
      of one comparison, which would surface as a parity failure rather than as the stale
      fixture it is. It also keeps package code out of `tests/`. The fixture stays what the
      tests use, since they cannot import CBFV, and a new test pins it against the installed
      table cell by cell so it cannot go stale in silence

- [x] **Parity through this project's parser cannot be bit-exact, and the reason is the element
      order (from #17).** `hydms.data.load.parse_formula` returns elements sorted by symbol;
      CBFV keeps its parse order. The statistics accumulate sequentially, so a different order
      rounds differently — measured over all 1,279 formulae and the nineteen properties the 22
      features need, that alone moves a cell by up to **2.274e-13** (oliynyk) and **3.638e-12**
      (jarvis, `atom_mass_mult_therm_cond`, `Pr0.8Ce0.3Cu5`). Both are ~3 orders inside the 1e-9
      this gate asserts, so the tolerance holds comfortably — but it must be *stated* as the
      reason the gate is a tolerance rather than an equality, because `hydms.descriptors.stats`
      **is** bit-identical to CBFV when handed CBFV's own element order (measured: 0.0 over both
      tables, all five statistics, every cell). If this gate ever fails by ~1e-12, suspect the
      order before suspecting the arithmetic

- [x] **This gate cannot detect a wrong-axis reduction, and #17 found one that would matter.**
      AC-2 compares 22 columns. Reducing the composition batch over its fast axis instead of its
      leading one costs up to 2.274e-12 on those 22 — which passes — while costing **2.794e-09
      on `bp_mult_mp`**, over tolerance, on a property no selected feature uses. So a featuriser
      with a real numerical defect passes this gate today and fails it the moment #25 re-runs
      selection onto a different property. `tests/descriptors/test_stats.py` guards the axis
      directly (padding a batch must change nothing *exactly*); this box exists so that guard is
      not deleted as redundant when this gate goes green

- [x] **No europium-containing formula may be compared at all.** CBFV drops Eu from its JARVIS
      index and answers anyway, substituting an all-zero property vector; `element_data.py`
      raises. A refusal and a number are not comparable, so `Eu1Ni5` must be excluded from the
      parity set **explicitly and with the reason recorded**, not filtered out quietly

- [x] **This gate also cannot see the seven features that are not computable everywhere
      (from #19).** CBFV's copy of the Oliynyk table supplies `gordy_en` for **all twenty-one**
      elements the citable 2024 revision leaves blank — Ce 4.5734, Hf 6.3704, Pr 4.6395, and the
      rest — so the reference table this gate is required to use has no hole in it at all. The
      shipped featuriser, reading the citable table, cannot produce `dev_Gordy_electonegativity`
      for **266 of 1,279 rows**, and cannot produce any of the six JARVIS features for `Eu1Ni5`.
      This gate will be green throughout. It is the second defect AC-2 structurally cannot
      detect, after the wrong-axis reduction above, and for the same reason both times: the gate
      measures agreement with CBFV on the rows and columns CBFV can answer. Say so in the gate's
      own output — a line naming how many rows the shipped tables could *not* have featurised —
      so a green AC-2 is never read as "the featuriser can produce all 22 for every row"

- [x] **The seam this gate needs exists, and it is a parameter (from #20).**
      `featurize(formulas, temperatures, *, contract=None, tables=None)`. Pass
      `tables={"oliynyk": <CBFV's copy>}` and both the numbers **and the computability verdict**
      come from that table — which is what makes the 266 Gordy rows comparable here even though
      the shipped featuriser refuses them. Build the table with
      `PropertyTable.of(name, citation, values)` and **spell its properties the way the contract
      does** (`gordy_en`, not `Gordy_electonegativity`): `PUBLISHED_SPELLING` inverted is the map,
      and `tests/descriptors/test_featurize.py`'s `cbfv_oliynyk` fixture is the eleven lines that
      do it. The jarvis half needs no override — CBFV's `jarvis.csv` *is* NIST's file

- [x] **Compare in one batch, not row by row (from #20).** A lone composition and a batched one
      agreed only up to arity 7 before this card fixed `statistics()`; they now agree at every
      arity, and the fix is one `np.repeat` that a later "simplification" could remove without
      any gate noticing. Featurising all 1,279 formulae in a single call is both the faster route
      and the one that cannot be affected by it. Excluding `Eu1Ni5` stays a deliberate,
      recorded exclusion (box above), not a filter

- [x] **A 16-formula version of this gate already passes (from #20).** All 22 columns against
      `cbfv_statistics_reference.csv`, with CBFV's table supplied: worst **4.547e-13** absolute
      and **6.828e-15** relative — three orders inside the 1e-9 this gate asserts. So the
      expected outcome here is green, and what this card adds is the other 1,263 formulae, the
      failure output that names the column and the row, and the line stating how many rows the
      *shipped* tables could not have featurised at all

## Runnable check

```bash
python -m hydms.gates run AC-2
```

## Traces to

`docs/PRD-inverse-design.md` — AC-2, R3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: **Landed green, and the expected outcome was the least interesting thing about it.**
  `hydms/gates/ac2_featuriser_parity.py` + `tests/gates/test_ac2_parity.py`. Suite **577**, ruff
  0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, the fast lane exits 0 with
  AC-2 the first `PASSED` row it has ever had. **Worst cell over all 22 columns and all 1,278
  comparable rows: 2.7285e-12** on `dev_atom_mass_mult_therm_cond` at `Mg0.7Li0.2Cu0.1` — 4007.280600000002
  against 4007.280599999999 — against a tolerance of 1e-9, with seven columns bit-identical. The
  16-formula figure #20 measured was 4.547e-13; scaling to 1,279 formulae moved it by half an order
  and nothing else. `python -m hydms.gates run AC-2` takes **1.5 s**.

  **The exclusion is derived from both sides, and CBFV's half of it was worth measuring.** The card
  says no europium formula may be compared and that the exclusion must be recorded rather than
  filtered. Hard-coding `"Eu"` would have satisfied the letter of that. Instead a row is excluded
  when *this layer* refuses it (`FeatureContract.computability` against the tables the gate is
  actually using) **or** when CBFV lists it in the `skipped` array `extract_features_cbfv.py` never
  read — and the result states both counts separately, because the case worth seeing is the two
  disagreeing. Today they are the same single row, `Eu1Ni5` at index 516, and the gate says so
  rather than assuming it. Measured while writing it: **CBFV's `jarvis.csv` has 82 elements, not
  85 — europium is not in the file at all** — and CBFV nevertheless *emits a full row for it*,
  `avg_atom_mass` = 48.911, which is `(0×1 + 58.6934×5)/6`. The all-zero property vector the
  contract's docstring describes is now confirmed by arithmetic rather than by inference.

  **The gate reads CBFV's table, not the committed fixture, and that is a correction to a box.**
  Both boxes and #20's handoff prescribed `tests/descriptors/data/cbfv_oliynyk_reference.csv`. The
  numbers are identical either way — measured, zero differing cells over every element and every
  one of the thirteen properties, because the fixture was written with `repr(float)` — but the gate
  imports CBFV *anyway*, to produce the expected values, so sourcing the table from a second place
  admits a version skew between the two halves of one comparison and would report it as a parity
  failure. Reading the fixture's source removes the possibility, and keeps package code from
  reaching into `tests/`. What the fixture loses in exclusivity it gains in being checked: a new
  test pins it against the installed table cell by cell, so the file the whole descriptor layer
  leans on can no longer go stale in silence.

  **Overriding the JARVIS table too changes nothing at all, which is a result.** #16 recorded that
  our `jarvis.csv` and CBFV's agree to 7.3e-12, and the worst offender in this comparison is a
  JARVIS composite of magnitude ~4e3 — so it was reasonable to suspect the residue was table skew.
  It is not. Supplying CBFV's own JARVIS copy as well leaves the worst gap at **2.7285e-12, same
  column, same formula, to the digit**. The whole disagreement is #17's element order, exactly as
  the card predicted, and the box that says "if this gate ever fails by ~1e-12, suspect the order
  before the arithmetic" is now a measurement rather than a guess.

  **A green gate that could not say what it does not establish would have been the wrong gate.**
  Two of the card's boxes are about AC-2's blind spots, and both are lines of the result: what was
  excluded and why, and that the *shipped* tables could not have featurised **266 of 1,279** rows
  at all — 265 for `dev_Gordy_electonegativity` alone, one for seven features at once. Writing them
  found that `_report.py` printed multi-line detail only for `FAILED` and `ERRORED` rows, so both
  lines existed only in the JSON. They now print for any status. That also unhides HG-1's per-leak
  listing, which had been invisible in the terminal for the same reason.

  **Landing the first real gate broke six tests that were never about it.** `tests/gates/` used the
  literal string `AC-2` wherever it needed "a criterion nobody has written yet" — four strictness
  tests in `test_harness.py` and two in `test_cli.py` — so a passing AC-2 turned tests about the
  harness into tests about featuriser parity, failing for a reason none of them was asking about.
  They now take an `unwritten` fixture (`tests/gates/conftest.py`) that asks the registry which
  gates are still `Pending`, and it asserts non-empty, so when the phase finishes they disappear
  loudly rather than passing over an empty selection. Four doc comments that used AC-2 as the
  standing example of an unimplemented gate were repointed at HG-2.

  **The vacuous pass has its own test.** The exclusion is derived, so a broken computability verdict
  could in principle exclude everything and leave the gate comparing zero rows and reporting green.
  It reports red, and `test_a_comparison_over_nothing_is_a_failure_not_a_pass` is the demonstration.
  The `docs/QA-PROTOCOL.md` §5 red demonstration proper perturbs one cell of `range_Mulliken_EN` by
  1e-8 and requires the failure to name the column *and* `Mg1.5Ni1`; its twin perturbs by 1e-11 and
  requires green, so the gate is a threshold rather than a hair trigger.

  **What AC-2 still cannot see is unchanged and now stated in three places.** The wrong-axis
  reduction (2.794e-09 on `bp_mult_mp`, a property no selected feature uses) is guarded by
  `tests/descriptors/test_stats.py` and not by this gate; the Gordy hole is invisible here by
  construction. The licence-boundary test was widened from `hydms/descriptors/` to all of `hydms/`
  and now names this module as the single permitted importer of CBFV — a boundary only checked
  where nothing had ever wanted to cross it was not a boundary. (by @assistant)
