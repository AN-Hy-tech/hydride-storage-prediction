---
id: 21
status: backlog
priority: High
blocked_by: [5, 20]
assignee: "@amirhossein"
tags: [p1, l2, AC-2, R3]
---

# GATE AC-2: featuriser parity with CBFV to 1e-9

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** Proof that the reimplementation is faithful.

## Why this exists

This is the gate that makes the CBFV replacement trustworthy. If the reimplemented
featuriser does not reproduce CBFV's numbers on the training set, every downstream model
would be trained on subtly different features than `REPORT.md` describes.

**If this fails, the reimplementation is wrong — not CBFV.**

## Done when

- [ ] All 1279 training formulae featurised by both CBFV (in the `Project` env) and `hydms.descriptors`
- [ ] Every one of the 22 columns agrees to within 1e-9 absolute
- [ ] Failure output names the column and the worst-offending formula, not just a boolean
- [ ] Registered in the gate harness as `AC-2` and run by CI

- [ ] **Parity cannot be a claim about the numbers, only about this code (from #16).** The
      published Oliynyk table is a *revised* edition of the one CBFV ships: of the thirteen
      properties the selected features need, five agree exactly and eight do not -- up to 10 in
      `valence_d` (Ga, Ge), 2.0 in `gilman_no_of_valence_electrons` (Lu), 0.54 in
      `covalent_radius` (Th, U). Comparing our featuriser's output against CBFV's while the
      tables differ measures the tables, not the code. This gate must read: **the featuriser
      reproduces CBFV to 1e-9 given the same table**, with
      `tests/descriptors/data/cbfv_oliynyk_reference.csv` supplied as that table. It is test
      input for this gate and must never become package data -- CBFV carries no licence, which
      is the whole reason the descriptor layer exists

- [ ] **Parity through this project's parser cannot be bit-exact, and the reason is the element
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

- [ ] **This gate cannot detect a wrong-axis reduction, and #17 found one that would matter.**
      AC-2 compares 22 columns. Reducing the composition batch over its fast axis instead of its
      leading one costs up to 2.274e-12 on those 22 — which passes — while costing **2.794e-09
      on `bp_mult_mp`**, over tolerance, on a property no selected feature uses. So a featuriser
      with a real numerical defect passes this gate today and fails it the moment #25 re-runs
      selection onto a different property. `tests/descriptors/test_stats.py` guards the axis
      directly (padding a batch must change nothing *exactly*); this box exists so that guard is
      not deleted as redundant when this gate goes green

- [ ] **No europium-containing formula may be compared at all.** CBFV drops Eu from its JARVIS
      index and answers anyway, substituting an all-zero property vector; `element_data.py`
      raises. A refusal and a number are not comparable, so `Eu1Ni5` must be excluded from the
      parity set **explicitly and with the reason recorded**, not filtered out quietly

- [ ] **This gate also cannot see the seven features that are not computable everywhere
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

- [ ] **The seam this gate needs exists, and it is a parameter (from #20).**
      `featurize(formulas, temperatures, *, contract=None, tables=None)`. Pass
      `tables={"oliynyk": <CBFV's copy>}` and both the numbers **and the computability verdict**
      come from that table — which is what makes the 266 Gordy rows comparable here even though
      the shipped featuriser refuses them. Build the table with
      `PropertyTable.of(name, citation, values)` and **spell its properties the way the contract
      does** (`gordy_en`, not `Gordy_electonegativity`): `PUBLISHED_SPELLING` inverted is the map,
      and `tests/descriptors/test_featurize.py`'s `cbfv_oliynyk` fixture is the eleven lines that
      do it. The jarvis half needs no override — CBFV's `jarvis.csv` *is* NIST's file

- [ ] **Compare in one batch, not row by row (from #20).** A lone composition and a batched one
      agreed only up to arity 7 before this card fixed `statistics()`; they now agree at every
      arity, and the fix is one `np.repeat` that a later "simplification" could remove without
      any gate noticing. Featurising all 1,279 formulae in a single call is both the faster route
      and the one that cannot be affected by it. Excluding `Eu1Ni5` stays a deliberate,
      recorded exclusion (box above), not a filter

- [ ] **A 16-formula version of this gate already passes (from #20).** All 22 columns against
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
