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

- [ ] **The charter's prose reads as an allow-list; the gate enforces a deny-list, and they do not
      agree** (added 2026-09-12 by the QA pass on #77). `docs/FREEZE.md` § "Allowed paths" names
      `hydms/** · tests/** · app/** · kanban-hardening/** · scripts/** · .github/** ·
      pyproject.toml · CLAUDE.md · README.md · docs/** except the PRD`, which a reader takes as
      exhaustive. `scripts/check_freeze.py` denies only `DENIED = (kanban/,
      docs/PRD-inverse-design.md, research/, REPORT.md, Machine_Model/)` and passes everything
      else.

      So `environment.lock.yml`, `environment.yml`, `requirements-lock.txt`, `CONTEXT.md` and
      `.graphifyignore` are all editable, and none is named by the prose. This session edited
      `.graphifyignore` and `CONTEXT.md`-adjacent files and CI was green, which is the gate
      behaving as written.

      It matters for **card #1**, whose open box proposes re-solving `environment.lock.yml`
      against `conda-forge`: a session reading only FREEZE.md would conclude that work is
      forbidden and defer it forever, and a session reading only the script would conclude the
      charter means nothing. Decide which is authoritative and make the other say so — either
      widen the prose to describe a deny-list, or give the script the allow-list the prose
      already claims. Do **not** silently widen `DENIED`: the deny-list is deliberately short so
      that ordinary hardening work is not gated on editing this file. Not an unfreeze condition.

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
