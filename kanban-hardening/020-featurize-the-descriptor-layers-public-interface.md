---
id: 20
status: backlog
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

- [ ] Single public function; everything else in the layer is private
- [ ] Batched: 10k formulae in one call, not 10k calls
- [ ] Invalid formulae are reported with their index, never silently dropped
- [ ] Output passes `assert_contract` (19) by construction
- [ ] **The parser is `hydms.data.load.parse_formula`, not `pymatgen.core.Composition`.** The line
      above naming pymatgen predates #9, which built the validated grammar this project uses —
      periodic-table membership, strictly positive amounts, non-empty result — and asserted it at
      parity with CBFV over all 1279 + 772 formulae. #87 then built the canonical key on that same
      function. Adding pymatgen here would make three parsers with three ideas of what a formula is,
      and the differences would show up as compositions that featurise but cannot be keyed. Check
      whether pymatgen is even in `environment.lock.yml` before assuming it is available
- [ ] **Creating `hydms/descriptors/featurize.py` turns gate HG-1 red until #12 wires L13.** The L13
      sentinel (written by #87) names that module as its subject and has no `live` hook yet, so the
      moment the module exists the audit reports `L13 [unwired] #12`. That is the mechanism working;
      coordinate with #12 rather than deleting the sentinel

## Runnable check

```bash
python -m pytest tests/descriptors/test_featurize.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, S12

## Narrative

- 2026-09-03: Two boxes added by #87. The card's "formula parsing via `pymatgen.core.Composition`"
  line is now the odd one out — #9 owns the grammar and #87's key is built on it — and creating this
  module is what makes the L13 sentinel demand its live hook (by @assistant)

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
