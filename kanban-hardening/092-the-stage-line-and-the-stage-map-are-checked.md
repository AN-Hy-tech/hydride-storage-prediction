---
id: 92
status: backlog
priority: P4
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l0]
---

# The stage line and the stage map are checked, not remembered

**No stage — slots in where its blockers allow** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Whether a card's stated stage is the stage the board assigns it.

## Why this exists

On 2026-09-11 a session found **thirty-nine of sixty-four** cards stating the wrong stage. Thirty-six
still carried the *frozen* board's `Phase 0 / Phase 1 / Phase A` heading, preserved verbatim by #72's
`git mv`; #73 and #74 claimed `Stage S1` when the runbook says in so many words that both landed
after S4 closed; #91 claimed `S6` when `README.md` says it is in no stage at all. The
[README.md](README.md) stage → card map had never named #1, #2, #4, #6, #7, #8, #68, #90 or #91, so
nine cards had no assignment to disagree with.

**None of it could go red.** `scripts/check_board.py` reads `id`, `status`, `blocked_by` and links —
it has never read the bold line under the title, and no test, gate or `--emit` does either. This is
the same shape as [../CONTEXT.md](../CONTEXT.md), which `CLAUDE.md` already names as an anti-pattern:
a document that only a reader can falsify drifts silently and takes a reader's trust with it.

**The `blocked_by` half drifted too, and that half *is* machine-readable** — it was simply not
checked against the prose. #34 sat in `doing` with all four declared blockers `done` while the
runbook said three times that it waits on HG-2, HG-3 and HG-4; #89 carried an edge to #34 that its
own *Done when* does not support, and that edge was holding #83 (S7) shut. Both are corrected by
hand. The point of this card is that the next one should not need a hand.

## Done when

- [ ] `scripts/check_board.py` parses each card's stage line and asserts it equals the stage the
      `README.md` map assigns that card — including `No stage`, which must be an assignment rather
      than an absence
- [ ] The map is **parsed from `README.md`**, not restated in Python. A second list is a second
      thing to drift; the table is the owner
- [ ] Every card on the board appears in exactly one stage row. A card in none is a failure, which
      is what would have caught the nine
- [ ] The tag vocabulary is asserted disjoint from the stage vocabulary: an `S`-number in `tags:`
      is a PRD user story (§5) and must never be read as a stage. There is no Stage S9–S12
- [ ] Negative-tested: flipping one card's stage line produces a non-zero exit that names the card,
      its claim and the map's answer
- [ ] Stdlib-only, like the rest of `check_board.py` — it must run on a bare `setup-python` with no
      conda environment

## Not an unfreeze condition

Stated explicitly, because the temptation is real. [../docs/FREEZE.md](../docs/FREEZE.md) fixed four
conditions "before results are seen, so it cannot be softened later", and widening that list is the
one thing the charter exists to resist — in either direction. This card is a durability improvement
on work already done; **the freeze lifts without it.** It may land before the lift or after.

## Runnable check

```bash
python scripts/check_board.py --root .
```

## Traces to

[README.md](README.md) § Stage → card map — the table this would make load-bearing.
[../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §2 — the execution order it encodes.
Card #68, which seeded exactly this kind of check and deliberately checked only what it could
honestly check at the time.

## Narrative

- 2026-09-26: Moved verbatim from `CONTEXT.md`, entry **User story**, where it stood as a *State of the term* block. The glossary now holds definitions only; card state lives here. (by @assistant)

  > *State of the term, not part of the definition:* on 2026-09-11 **thirty-nine of sixty-four cards
  > stated the wrong stage** — thirty-six still carrying the frozen board's `Phase` heading after
  > #72's `git mv`, two claiming an `S1` the runbook contradicts, one an `S6` the README does. Nothing
  > reads that line: not `check_board.py`, not a test, not an `--emit`. All are corrected and **#92**
  > is the card for making the map load-bearing. Until it lands, this pair is checked by a reader or
  > not at all.
