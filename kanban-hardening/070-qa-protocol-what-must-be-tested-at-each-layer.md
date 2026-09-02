---
id: 70
status: backlog
priority: Normal
blocked_by: [69]
assignee: "@amirhossein"
tags: [ph, l0]
---

# QA protocol: what must be tested at each layer

**Stage S1 — QA foundation** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The testing contract — what a card must prove before it may be called done, per layer.

## Why this exists

The board's cards each carry a `## Runnable check`, but nothing says what a check has to
*cover* for the card to be honest. Without that, a check degenerates into `import hydms` and the phase
ships a green build over untested code.

This is where the phase's standard is written down once: which layers need golden tests, which need
property or metamorphic tests, which need a gate, and what a reviewer looks for before approving.

## Done when

- [ ] `docs/QA-PROTOCOL.md` exists and states, per layer L0-L7, what a card must prove
- [ ] It names the four test kinds in use — golden, metamorphic, contract, sentinel — and when each applies
- [ ] It gives the reviewer checklist and the definition of done
- [ ] It states the rule that a gate card's check must be able to **fail** — a gate that cannot go red
      is not a gate
- [ ] It is linked from `kanban-hardening/README.md`

## Runnable check

```bash
python scripts/check_board.py --root .
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
