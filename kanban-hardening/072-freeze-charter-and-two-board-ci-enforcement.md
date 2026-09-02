---
id: 72
status: done
priority: High
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l0]
---

# Freeze charter and two-board CI enforcement

**Stage S0 — Freeze and tooling** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** The boundary between the hardening phase and the frozen inverse-design programme, and the machinery that keeps it.

## Why this exists

The phase's premise is that everything not on the path to an honest forward prediction is
suspended. A freeze that lives only in a document is a freeze the next session forgets. This card makes
it executable in two halves that do not subsume each other:

- **The diff half** (`scripts/check_freeze.py`) rejects a change that touches a denied path. It must
  exempt a card *migrating* out of the frozen board, or the freeze cannot establish itself.
- **The board half** (`scripts/check_board.py`) rejects a card on the frozen board that has left
  `backlog`. A card can be moved off backlog in a commit that touches nothing the diff check notices.

The two board directories share one id space. Ids were preserved on migration because renumbering
would break every `blocked_by` edge, every `Traces to` link, and the `## Narrative` notes that the ADRs
and card #37 are written from.

## Done when

- [x] Cards 1-37, 44, 48, 49, 68 migrated to `kanban-hardening/` with ids unchanged
- [x] `docs/FREEZE.md` declares the freeze, the denied paths, and the unfreeze condition
- [x] `docs/PHASE-H-RUNBOOK.md` holds the stage order and the leak inventory
- [x] `scripts/check_board.py` validates both boards as one id space and enforces the frozen-board
      status rule
- [x] `scripts/check_freeze.py` rejects denied paths and exempts card migration
- [x] `kanban-hardening/README.md` is the board charter
- [x] Cards #69-#89 created; #12, #13, #14, #24, #26 amended
- [x] `.github/workflows/integrity.yml` runs the freeze check
- [x] `CLAUDE.md` and `kanban/README.md` point at the new board

## Runnable check

```bash
python scripts/check_board.py --root . && python scripts/check_freeze.py --base origin/main
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S0

## Narrative

- 2026-09-02: Created and largely executed in one session. The freeze check needed a rename
  exemption: without it the migration commit that establishes the freeze would be rejected by the
  freeze it establishes. `kanban/README.md` is exempt too — board metadata, not a card, and the freeze
  has to be able to announce itself on the board it freezes (by @assistant)

- 2026-09-02: **S0 closed.** Both halves of the freeze were shown to go red before being trusted: a
  card status change on the frozen board is caught by `check_board.py`, and an edit to `research/` or
  to a frozen card is caught by `check_freeze.py`, each with its own message. The migration exemption
  needed one fix found by the check itself — it matched on filename, so card #24, which was renamed
  after moving boards, read as a deletion from the frozen board. It now matches on the id prefix,
  because a migrated card is free to be renamed. (by @assistant)
