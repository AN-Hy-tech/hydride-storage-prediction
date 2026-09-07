---
id: 49
status: doing
priority: High
blocked_by: [44]
assignee: "@amirhossein"
tags: [pa, l4, S4, AC-7]
---

# Element Mover's Distance novelty screen

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** How chemically far a candidate is from everything already known.

## Why this exists

PRD 4.3 link 5: 'novel' must be a number, not an assertion. ElMD gives chemically
intuitive composition-to-composition distances along a modified Pettifor scale.

ElMD is **GPL-3.0**, which is compatible with the decided GPL-3.0 licence for this project —
recorded here so the choice is not revisited by mistake.

## Done when

- [x] ElMD distance computed from each candidate to its nearest training composition
- [x] Nearest neighbour's formula reported alongside the distance, so novelty is inspectable
- [x] Distances computed batched; a per-candidate loop over the training set would be too slow
- [x] GPL-3.0 dependency noted in `pyproject.toml` — ~~and in ADR 2~~. **ADR 2 does not exist
      yet**: `docs/adr/` is unwritten and card #36 owns it, so the ElMD half of that record is a
      box on #36 rather than a file this card can tick. `pyproject.toml`'s `novelty` extra
      carries the finding in full — GPL-3.0 by `LICENSE.txt` and `setup.py`, despite a trove
      classifier that says LGPLv3, and the licence file governs. Also recorded there because it
      is the sort of thing rediscovered the hard way: **`ElMD==0.5.0` is unsatisfiable**, since
      that sdist's metadata declares itself `0.4.25` and pip discards it as inconsistent. The
      `>=0.5` floor this project already had is correct and resolves to 0.5.15
- [x] **The distance and the nearest formula ride on the verdict frame, not a second return
      value.** `hydms.screens.apply_screens` (#44) carries any extra column a screen returns into
      the verdict table as `<screen>.<column>`, so "reported alongside the distance" is satisfied by
      returning them beside `passed`/`code`/`reason` — a parallel API would put the number and the
      verdict on two paths that can disagree. Declare the rejection code in `reasons`.

- [x] **This screen's threshold cannot be derived from the leave-one-class-out curve, and #48
      measured why** (added 2026-09-07). Per-class transfer R2 does not correlate with how
      isolated a family is: Spearman **-0.2727** in element-fraction space (p 0.446), **-0.0182**
      for the mean rather than the median, and **-0.2848** in the model's own 14-feature space
      (p 0.425), n = 10. The ordering is inverted at the ends — `A2B` and `LEA` are the two least
      isolated families and score 0.7264 and 0.4995, while the most isolated, `AB`, scores 0.4214.
      The feature-space row is the one that settles it for ElMD too: **the model reads fourteen
      numbers**, and if distance in the space it actually reads does not order its transfer
      failures, no metric over a space it never reads can be the mechanism behind them.

      **So this screen is novelty evidence, not the applicability domain.** #48's ceiling is a
      *capacity* level (5.19 wt%) and it already shipped without a distance. AC-7 asks that every
      published candidate carry an ElMD distance and an interval width, which is a reporting
      obligation and is what this card owes. Its rejection code — the card's fourth box requires
      one — has to be justified on its own terms (a distance beyond which "novel" stops meaning
      "a variation on something known" and starts meaning "a different problem"), and it must not
      be presented as a domain verdict. Note that the corpus is chemically homogeneous: only
      **3 of 385** held-out rows fall outside any training feature span, so a distance threshold
      fitted to look busy on this data will be fitted to noise

## Runnable check

```bash
python -m pytest tests/screens/test_novelty.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S4, AC-7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: #44 landed the contract this card implements, including the evidence-column seam this
  screen needs (a test pins that a screen returning `distance` and `nearest` gets them back as
  `<screen>.distance` and `<screen>.nearest`). The batched requirement in the third box is now the
  runner's own rule: `verdict()` takes a frame and is called once per run. (by @assistant)

- 2026-09-07: Landed. Four things this card learned that the next reader should not re-derive.

  **The metric has a closed form, and that is the entire batching answer.** ElMD's default
  `mod_petti` distance dispatches to `simple_emd`, which is `sum(abs(cumsum(a - b)))` over the
  103-slot Pettifor vector of atomic fractions. So the nearest-neighbour search over a whole
  batch is one `cdist(cumsum(C), cumsum(T), "cityblock")` — verified equal to ElMD's own answer
  to **3.6e-15** on the curated corpus. No `ElM2D`, no matrix API, no loop. Every *other* metric
  routes through the network simplex over a full cost matrix and does not reduce this way, which
  is why `MOD_PETTI` is asserted rather than assumed.

  **The card's third box is true, but not for the reason a cold timer says.** Measured: `cdist`
  runs at ~37 M pairs/s flat from 1e3 to 1e5 candidates; a **warm** `ElMD.elmd()` loop is 46x
  slower, and the broadcast form is 23x slower than `cdist` while allocating `n x m x 103`
  floats. The first measurement taken here said 3.5 ms/pair and therefore ~3,475 s for the
  corpus — that was numba compiling `simple_emd`, amortised over 200 calls, and it overstated the
  ratio by 2,500x. The cost that actually dominates is `ElMD(formula)` construction at **48.6 us**,
  which is why formulas are parsed once per *distinct string* per batch and not once per
  comparison. Warm the JIT before believing any ratio here.

  **ElMD has two defects and both are load-bearing.** It does not raise on an unparseable
  formula: `ElMD("")`, `ElMD("NotAnElement")` and `ElMD("Xx2")` return an object whose ratio
  vector sums to zero, and a zero vector has a finite, meaningless distance to everything — the
  exact silent failure #44 exists to prevent, so `vectors()` checks normalisation and an
  unreadable formula is `INDETERMINATE`, a rejection. And `ratio_vector` is **not reproducible
  across processes** for three or more elements: `_fuse` builds its dict from
  `set(mol1) | set(mol2)`, so insertion order follows the per-process randomised symbol hashes
  and `sum(composition.values())` differs by an ulp. **76 of 780 training compositions moved by
  2.2e-16 between two processes, every one multi-element.** Within one process it is perfectly
  stable, which is how it hides. It surfaced only because the `--emit` byte-identity test — the
  shape #30 used for `loco.md` — failed on the second emit. `vectors()` now sums the parsed
  counts in sorted symbol order, and a test pins the result against `ratio_vector` to 1e-12 so
  the deterministic path stays ElMD's metric rather than becoming a private one.

  **The threshold is 11.7320 and it rejects nothing on this corpus, which is the point.** #48
  removed the only calibration target this card was written to expect, so the ceiling is
  calibrated against the corpus's own internal spread: the largest distance from a training
  composition to its nearest *other* training composition. It is set by one composition,
  `Li0.94Pd1` against `Ce1Ni1`, and `NoveltyReference` names both so a bound held up by one row
  says so — drop that row and it falls to 5.1333. Against the held-out rows it fires **0 times
  in 385**; the most novel of them, `Ca1Al1.8B0.2`, is at 6.53 on a metric whose span is 102.0.
  That is a screen calibrated to a homogeneous corpus behaving correctly, not a screen that does
  not work, and the card's own last box predicted it: a threshold fitted to look busy on this
  data would be fitted to noise. The distance rides on every verdict either way, which is what
  AC-7 actually asks for.

  Left for #76: whether `delivery_screens()` gains this screen, which would make the optional
  `novelty` extra a hard requirement of every prediction. Boxed there with the trade-off stated,
  alongside the pin-or-digest question `novelty-reference.json` inherits from #48's reference.
  (by @assistant)
