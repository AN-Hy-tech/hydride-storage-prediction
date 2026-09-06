---
id: 49
status: backlog
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

- [ ] ElMD distance computed from each candidate to its nearest training composition
- [ ] Nearest neighbour's formula reported alongside the distance, so novelty is inspectable
- [ ] Distances computed batched; a per-candidate loop over the training set would be too slow
- [ ] GPL-3.0 dependency noted in `pyproject.toml` and in ADR 2
- [ ] **The distance and the nearest formula ride on the verdict frame, not a second return
      value.** `hydms.screens.apply_screens` (#44) carries any extra column a screen returns into
      the verdict table as `<screen>.<column>`, so "reported alongside the distance" is satisfied by
      returning them beside `passed`/`code`/`reason` — a parallel API would put the number and the
      verdict on two paths that can disagree. Declare the rejection code in `reasons`.

- [ ] **This screen's threshold cannot be derived from the leave-one-class-out curve, and #48
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
