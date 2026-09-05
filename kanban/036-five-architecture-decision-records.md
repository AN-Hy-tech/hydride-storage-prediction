---
id: 36
status: backlog
priority: High
blocked_by: [34]
assignee: "@amirhossein"
tags: [p1, l7, S7]
---

# Six architecture decision records

**Phase 1 — Hardening Chapter 1** · **L7 Evidence** · Estimate: 1 d

> **Owns (hidden behind this module):** Why the hardest-to-reverse choices were made, so they are not silently re-litigated.

## Why this exists

Six decisions that are hard to reverse, surprising without context, and the result of a
real trade-off:

1. Optimise in composition space; never invert descriptors
2. Reimplement the featuriser rather than depend on unlicensed CBFV
3. Rank by conformalised LCB, not predicted mean
4. New `hydms/` package; `Machine_Model/src/` archived rather than rewritten
5. pymoo with the element subset fixed per run, over mixed-integer encoding
6. Persist a promoted artifact and load it everywhere; never refit — AC-1 the single sanctioned refit

## Done when

- [ ] `docs/adr/0001..0006-*.md` exist, one per decision
- [ ] Each states context, the alternatives genuinely considered, the decision and its consequences
- [ ] Each links to the PRD section and the research memo section that informed it
- [ ] ADR 2 records the CBFV licence finding explicitly, since a future reader will otherwise re-suggest depending on it

## Runnable check

```bash
ls docs/adr/*.md | wc -l
```

## Traces to

`docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-05: **Sixth ADR added — persist-vs-refit.** Widened this card from five decisions to six: ADR 6 is
  `0006-persist-artifacts-never-refit.md`, records the decision resolved on #34 (persist by default; AC-1 on #32
  the single sanctioned refit). Rationale: as hard to reverse and as re-litigable as the five already listed — a
  future reader will otherwise re-suggest "just retrain each run." The Narrative on #34/#32 carries the context,
  alternatives and consequences the ADR is written from. Card title, the decision list and the `0001..0006` glob
  updated to match; the card filename keeps its `five` slug so its id and history are stable. (by @amirhossein)
