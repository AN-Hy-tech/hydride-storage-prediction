---
id: 73
status: backlog
priority: Normal
blocked_by: [28, 69]
assignee: "@amirhossein"
tags: [ph, l0, S1, AC-1]
---

# End-to-end smoke pipeline on a sampled fixture

**Stage S1 — QA foundation** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** Proof that raw data reaches a prediction in one command, fast enough to run on every push.

## Why this exists

The audit's second finding was that the pipeline does not run end to end at all — four
broken links, including a featurisation input with no producer anywhere in the repository's history.
A full retrain is far too slow for the CI fast lane, so the guard against that regression is a smoke
run over a small sampled fixture: every stage executes, in order, on real data shaped like the real
thing, in under a minute.

This is not a performance test and not an accuracy test. It answers one question — *does the chain
still connect?* — which is exactly the question the repository could not answer before this phase.

## Done when

- [ ] A committed fixture sampled from `data/raw/`, small enough to run the whole chain in ≤ 60 s
- [ ] The fixture preserves the shapes that matter: multiple alloy classes, at least one repeated
      canonical composition, and at least one near-duplicate formula string
- [ ] One command runs load → merge → canonicalise → split → screen → featurise → select → fit →
      predict on the fixture
- [ ] No absolute path appears anywhere in the run
- [ ] The run is wired into the CI fast lane
- [ ] Running it twice with the same seed produces identical output

## Runnable check

```bash
conda run -n Project python -m pytest tests/test_smoke_pipeline.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1; `docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
