---
id: 17
status: done
priority: High
blocked_by: [16]
assignee: "@amirhossein"
tags: [p1, l2, S12]
---

# Weighted composition statistics

**Stage S3 — Descriptor layer** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** How a per-element property becomes a per-composition number.

## Why this exists

The `avg_` / `dev_` / `range_` / `max_` / `min_` statistics over a fraction vector. This
is the whole of what CBFV does mathematically; the rest is table lookup.

Keep this module pure and total: fractions in, scalar out, no I/O.

## Done when

- [x] `avg`, `dev`, `range`, `max`, `min` implemented over (fractions, property vector) —
      `hydms/descriptors/stats.py`, `statistics(weights, values) -> Statistics`. It takes
      **weights**, not fractions, and normalises them itself; that is what makes the
      rescaling box below true at all, and it is how CBFV does it (`_fractional_composition`
      divides by the sum of amounts). `range`, `max` and `min` are **unweighted** — over the
      distinct elements present, with no reference to how much of each there is
- [x] Property tests: statistics are invariant to element ordering and to fraction rescaling
      — **amended: neither invariance is exact, in this module or in CBFV, and the card was
      written assuming they were.** A sequential accumulation in a different element order
      rounds differently; rescaling re-rounds the division that normalises the weights.
      Measured over both committed tables and the fixture's formulae, with `atol=1e-12`:
      permutation needs `rtol >= 4.313e-16`, rescaling needs `rtol >= 5.283e-15`. Both tests
      assert `|a - b| <= atol + rtol*|b|` with `rtol = atol = 1e-12`, three orders of
      headroom. CBFV itself moves by up to 1.364e-12 (oliynyk) and 2.794e-09 (jarvis) when a
      formula string is merely reversed — 293 of 400 real formulae — so an equality test here
      would have been asserting something CBFV does not do either. `docs/QA-PROTOCOL.md` §L2
      asks for these two invariances and is right to; it just cannot have them to the bit
- [x] `dev` matches CBFV's definition exactly (fraction-weighted mean absolute deviation) —
      **confirmed, and the confirmation is stronger than the box asked for.** It is
      `sum_i f_i * |p_i - avg|` about the fraction-weighted mean, and transcribing that
      reproduces CBFV's `dev` column to **0.0** — exactly, not to a tolerance — over all
      1,279 × 44 oliynyk cells and 1,278 × 438 jarvis cells. The three plausible misreadings
      are nowhere near: a fraction-weighted population standard deviation differs by up to
      **328.8**, an unweighted standard deviation by **1172.2**, an unweighted mean absolute
      deviation by **1094.9**. **The source was wrong, though:** ticket #8's spike output
      resolves *provenance* — which table each feature comes from — and says nothing about
      arithmetic. Confirmed against CBFV 1.1.0 itself instead, and the result is committed as
      `tests/descriptors/data/cbfv_statistics_reference.csv` so it stays checked without CBFV
- [x] Vectorised over a batch of compositions, not looped per composition — and the *shape*
      it vectorises in turned out to be the whole of the card. See below

- [x] **The reduction must run down the leading axis, and that is worth 2.794e-09.** NumPy
      sums pairwise when it reduces the fast axis, which reorders the additions; reducing the
      leading axis accumulates sequentially, and adding an exactly-zero padded term to a
      finite float is exact. So the caller-natural `(n_compositions, arity)` shape reduced
      over axis 1 — the obvious way to write this — differs from CBFV by up to 1.364e-12 on
      oliynyk and **2.794e-09 on jarvis, over gate AC-2's 1e-9 tolerance**, on `bp_mult_mp`.
      Transposed to `(arity, n_compositions)` and reduced over axis 0 it is **bit-identical
      to CBFV on both tables, all five statistics, every cell**. `statistics()` transposes
      internally, so no caller can get this wrong. Two tests state it as arithmetic rather
      than as a shape, so they survive a rewrite: padding a batch with all-zero columns must
      change nothing *exactly*, and a row's statistics must not depend on what else shared
      its batch

- [x] **One property at a time, deliberately.** `statistics()` carries no trailing property
      axis. A hole in a published table is per property *per element* — `gordy_en` is empty
      for 21 of the 55 elements, every jarvis property of europium is a sentinel — so a
      property axis inside this module would force the caller to drop a whole composition
      because one of nineteen properties has a hole, or a whole property because one
      composition needs it. Keeping the axis outside leaves that with #19, where it belongs

- [x] **CBFV's median-fill did not fire on this dataset, and it was worth checking.**
      `generate_features` ends with `X[cols].fillna(median_values)` — a NaN feature cell
      becomes the *dataset median of its column*. Over the 55 elements this dataset uses,
      CBFV's own oliynyk table has no holes at all (its four hole-carrying properties are
      empty only for elements the dataset never mentions), so **zero cells** of the published
      matrix are median substitutions from the oliynyk side. The mechanism is real and the
      europium row (#89) is the jarvis-side version of it; the oliynyk side is clean

## Runnable check

```bash
python -m pytest tests/descriptors/test_stats.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-03: Landed. `hydms/descriptors/stats.py` and 28 tests in
  `tests/descriptors/test_stats.py`; 439 tests green, ruff and mypy clean, `audit()` unchanged
  at 4/13 (no sentinel names this module — L13's subject is `hydms.descriptors.featurize`,
  which is #20). Four things this card taught.

  **The card said "measure `dev` rather than assume", and measuring it confirmed the card.**
  That is worth saying plainly because the previous two cards both found their instructions
  wrong: `dev` really is the fraction-weighted mean absolute deviation the card named, exact
  to 0.0 against CBFV. What was wrong was only the *provenance* of the confirmation — ticket
  #8's spike resolved which table each feature comes from and never touched arithmetic — so
  the check had to be built rather than cited. It now exists as a committed fixture.

  **The real finding was not `dev` but the axis.** Writing the obvious vectorisation —
  a `(n_compositions, arity)` batch reduced over its fast axis — reproduces CBFV to 1.4e-12
  on oliynyk and **2.794e-09 on jarvis, above AC-2's tolerance**. NumPy uses pairwise
  summation on the contiguous axis and sequential accumulation on the leading one, and a
  padded exact zero is invisible to the second and not to the first. Transposing costs
  nothing and buys bit-identity. It was found by probing before implementing, which is the
  only reason it is a design note here rather than a mystery in #21 three cards from now.

  **Nothing about a float here was assumed twice.** Six separate one-ulp effects were
  measured on the way: normalising weights with `np.sum` versus CBFV's sequential `natoms +=`
  (10 of 1279 rows, 1.11e-16 — and 0 rows once the sum also runs down the leading axis);
  reversing a formula string in CBFV (293 of 400 rows); scaling every amount by 3 or 0.1;
  permuting elements; and the fact that `parse_formula` sorts elements by symbol while CBFV
  keeps parse order, which alone moves a statistic by up to 3.638e-12 on the jarvis
  properties the features need. That last one means **parity with CBFV can never be bit-exact
  through this project's parser**, which #21 now carries. Card #11 reached the same place
  from the target transform; this is the descriptor layer's version of it.

  **A fix in passing, because it blocked the deliverable.**
  `scripts/build_element_tables.py` required `--oliynyk` and `--jarvis` even to write a CBFV
  fixture that needs neither — and both are one-off downloads the repository does not keep.
  The AC-2 reference fixture #16 committed was therefore already unregenerable on a clean
  machine. They are now optional, must be passed together, and the script refuses a run that
  would build nothing. #15's lesson, applied to a tool rather than to a record: a golden that
  cannot be rebuilt stops being a check the moment its inputs move. (by @assistant)
