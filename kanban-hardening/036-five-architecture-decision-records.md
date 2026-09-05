---
id: 36
status: backlog
priority: High
blocked_by: [34]
assignee: "@amirhossein"
tags: [p1, l7, S7]
---

# Five architecture decision records

**Phase 1 — Hardening Chapter 1** · **L7 Evidence** · Estimate: 1 d

> **Owns (hidden behind this module):** Why the hardest-to-reverse choices were made, so they are not silently re-litigated.

## Why this exists

Five decisions that are hard to reverse, surprising without context, and the result of a
real trade-off:

1. Optimise in composition space; never invert descriptors
2. Reimplement the featuriser rather than depend on unlicensed CBFV
3. Rank by conformalised LCB, not predicted mean
4. New `hydms/` package; `Machine_Model/src/` archived rather than rewritten
5. pymoo with the element subset fixed per run, over mixed-integer encoding

## Done when

- [ ] `docs/adr/0001..0005-*.md` exist, one per decision
- [ ] Each states context, the alternatives genuinely considered, the decision and its consequences
- [ ] Each links to the PRD section and the research memo section that informed it
- [ ] ADR 2 records the CBFV licence finding explicitly, since a future reader will otherwise re-suggest depending on it

- [ ] **A sixth candidate arrived from #29 (2026-09-05): how the reported interval is
      constructed.** It meets all three tests. *Hard to reverse:* Chapter 1 quotes the number, and
      changing the estimator after publication changes every score in the thesis. *Surprising
      without context:* the bootstrap resamples **canonical groups rather than rows**, which costs
      only 13 % of the independent units (780 groups over 893 rows, 692 of them singletons) and
      looks like pedantry until you know `group_keys` is the seam #13, #87 and #88 all share.
      *A real trade-off:* the out-of-fold predictions come from five models with overlapping
      training sets, so no bootstrap over them is unbiased (Bengio & Grandvalet 2004) — the
      interval is knowingly too narrow, and the alternatives were either more compute than this
      phase has or a research project. The mitigation chosen was to state the caveat in the emitted
      table and carry the per-fold spread beside it as a second, cruder interval. Decide whether
      this displaces one of the five above or becomes a sixth

## Runnable check

```bash
ls docs/adr/*.md | wc -l
```

## Traces to

`docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
