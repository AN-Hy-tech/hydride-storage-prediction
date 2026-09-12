---
id: 97
status: backlog
priority: High
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l3]
---

# A tie in a sort makes a published document unreproducible

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 0.25 d

> **Owns (hidden behind this module):** Whether the same inputs produce the same published bytes on
> every machine.

**This card is NOT an unfreeze condition.** It was found on 2026-09-12 by #80, which was working
three layers away and read `gh run list` before claiming anything about CI. The unfreeze condition
is fixed and stays fixed.

**It is `High` because the branch is red in CI until it is fixed**, and a red branch is how the
next real failure gets ignored.

## Why this exists

`tests/surrogate/test_comparison.py::test_the_published_document_is_the_one_this_code_generates`
**fails on the CI runner and passes on the maintainer's machine.** The same inputs produce
different bytes in the two places, which means `reports/feature_selection/` is not reproducible and
the byte-identity test cannot mean what it says.

CI has been red on this since at least **run `34709161104`** (#34's push, 2026-09-12T17:45Z;
1 failed, 1442 passed, 9 skipped in 452 s). The local fast lane on the same tree is **1461 passed,
0 failed** — so this is not flakiness and not a timeout, it is a genuine platform difference.

**The whole difference is two adjacent rows swapping places:**

```
+ | avg_polzbl_divi_atom_mass     | 1 | Eu |
- | dev_atom_mass_mult_therm_cond | 1 | Eu |
```

Both rows carry **count `1` and element `Eu`**. The sort key is therefore a **tie**, and the order
falls through to whatever order the frame was already in — which is not guaranteed to be the same
under a different pandas version or platform.

**This is the generated-document pattern working, not failing.** The byte-identity test caught a
real nondeterminism that nothing else was testing for, exactly as #49's emit caught ElMD's
hash-ordered `_fuse` building its composition dict from `set(mol1) | set(mol2)`. The lesson is the
same one and it is worth restating here because the tempting fix is the wrong one: **do not loosen
the comparison, and do not sort the output after the fact.** Find the tie and break it.

## Done when

- [ ] The tie is broken **in the sort that produces the table**, not by post-sorting the rendered
      rows. The feature name is the obvious second key and is already the row's identity, so the
      order becomes a property of the data rather than of the reader
- [ ] Every other sort in `hydms/surrogate/comparison.py` is checked for the same defect. One tie
      found by accident usually means the others were never specified either — the question is
      "can two rows share this key?", not "has this one ever moved?"
- [ ] The document is regenerated and the new bytes committed, with the diff read rather than
      rubber-stamped: a row order that changes is fine, a *number* that changes is a different
      finding and belongs on its own card
- [ ] **Green on the runner**, confirmed by `gh run list` and not by a local run. A local pass is
      what this defect already had

## Runnable check

```bash
conda run -n Project python -m pytest tests/surrogate/test_comparison.py
gh run list --branch feat/phase-h-emergency-hardening --limit 3
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S4; `docs/QA-PROTOCOL.md` L7

## Narrative

- 2026-09-12: Found by #80 while checking whether its own push had gone green. It had not, and the
  red predated it by an hour. Filed rather than fixed in place: #25 owns
  `reports/feature_selection/` and is `done`, and #26 is `done` behind it, so reopening #25 would
  have made `check_board.py` fail on a blocker that is no longer done — the board is right to
  refuse that, and a `done` card carrying an unticked box would have been the same lie in a quieter
  form. (by @assistant)
