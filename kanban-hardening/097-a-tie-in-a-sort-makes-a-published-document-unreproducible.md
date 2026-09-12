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

**It is `High` because it is one keyword away and it silently corrupts a published document.**

## Why this exists

`tests/surrogate/test_comparison.py::test_the_published_document_is_the_one_this_code_generates`
**failed once on CI and has passed since**, with no change to `comparison.py`, its inputs, or its
test in between. That makes it intermittent rather than environmental, and an intermittent
byte-identity failure on a *published* document is worse than a reproducible one: it means the
document committed in this repository may not be the document the code produces.

**The cause is identified exactly. The trigger is not.**

The cause is `hydms/surrogate/comparison.py:703`:

```python
charged = self.cost[self.cost["rows_blocked"] > 0].sort_values(
    "rows_blocked", ascending=False
)
```

`sort_values` defaults to `kind="quicksort"`, which pandas documents as **not stable**. The failing
diff is two adjacent rows swapping and nothing else:

```
+ | avg_polzbl_divi_atom_mass     | 1 | Eu |
- | dev_atom_mass_mult_therm_cond | 1 | Eu |
```

Both carry `rows_blocked == 1` and the same blocking element, so the sort key is a **tie** and an
unstable sort is free to return them in either order. Nothing downstream re-imposes an order.

**What was ruled out, so nobody repeats it:**

| Hypothesis | Checked | Result |
|---|---|---|
| Resolved versions differ (the usual cause) | `Successfully installed` on both runs | **identical** — numpy 1.26.4, pandas 2.3.3, scikit-learn 1.7.2, scipy 1.15.3 |
| Platform (Linux runner vs Windows) | the same test passes on both | **not platform** — it passed on the runner twice after failing once |
| `PYTHONHASHSEED` randomisation | 8 seeds locally | **all passed** |
| Random test ordering | `pytest-randomly` / `xdist` in the config | **neither is installed** |
| Something in #80/#85 | `git log c070988..HEAD -- reports/ hydms/surrogate/comparison.py` | **empty** — untouched |

So the tie is real and the sort is genuinely unstable; what decided it differently on one run is
still unknown. **Fix the tie anyway** — an unstable sort over a tied key is a defect whether or not
its trigger has been named, and naming the trigger is not worth a CI round trip per attempt when
the fix is one keyword.

**This is the generated-document pattern working, not failing.** The byte-identity test caught a
real nondeterminism nothing else was testing for, the same way #49's emit caught ElMD's
hash-ordered `_fuse`. Do not loosen the comparison and do not post-sort the rendered rows.

## Done when

- [ ] `comparison.py:703` sorts **stably** — `kind="stable"` preserves `declared.names` order for
      tied rows, which is already a deterministic order — or takes an explicit second key. Not by
      post-sorting the rendered rows
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

- 2026-09-12: Found by #80 while checking whether its own push had gone green. **The first filing
  of this card was wrong about the axis** and is corrected above: it said the test "fails on the
  runner and passes on the maintainer's machine", which read as a platform difference. The next two
  runs passed on that same runner with identical resolved versions, so it is **intermittent**, and
  the cause is an unstable `sort_values` over a tied key rather than anything about the
  environment. The evidence table records what was ruled out so the next session does not re-walk
  it. Filed rather than fixed in place: #25 owns
  `reports/feature_selection/` and is `done`, and #26 is `done` behind it, so reopening #25 would
  have made `check_board.py` fail on a blocker that is no longer done — the board is right to
  refuse that, and a `done` card carrying an unticked box would have been the same lie in a quieter
  form. (by @assistant)
