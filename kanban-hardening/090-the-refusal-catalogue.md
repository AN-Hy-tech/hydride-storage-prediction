---
id: 90
status: backlog
priority: Normal
blocked_by: [44, 48, 49, 75]
assignee: "@amirhossein"
tags: [ph, l4, l6]
---

# The refusal catalogue: every reason the system can give, on one committed page

**No stage — slots in where its blockers allow** · **L4 Screens / L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** The complete set of things this system can say when it
> declines to answer — and the guarantee that the set on the page is the set the code produces.

## Why this exists

Card #49's QA pass found a defect no test could see: the screen refused `LaNi5Xx2` correctly, with
the correct code and no number, and explained itself with a sentence written for a *different*
defect — "it parses to an empty formula", which is true of `Xx2` and false of a string that parses
to `LaNi5`. The verdict was right and the reason was false. A green suite cannot tell those apart,
because a reason is prose and prose has no assertion that fits it.

Gate HG-2 (#77) already requires that a refusal **carry** a code and a reason. Nothing on either
board asks whether the reason is **true**. That gap is what this card owns, and the honest framing
matters: this card does not make stale prose go red. It makes stale prose appear **on a diff line**,
next to the input that produced it, where a human reads. That is the strongest mechanism available
for a defect whose only symptom is a false sentence.

**Tested against the real bug before being written.** The obvious rule — "a refusal must name the
offending input" — would **not** have caught #49: the false sentence named it (`ElMD could not read
'LaNi5Xx2'`) and then explained it wrongly. Every rule statable about a reason's *shape* passes on
that string. What survives is showing the pair.

**And the catalogue turns out to have real teeth as well.** `hydms.delivery.contract.reason_codes()`
*derives* the declared vocabulary from the screens rather than listing it, so the catalogue can
compare **declared** codes against **reachable** ones. A declared code no input can produce is dead
vocabulary; an emitted code that is not declared is a contract violation. Both are automatic red
conditions and neither depends on anybody reading anything.

## Done when

- [ ] A committed probe set — inputs chosen to reach every rejection path, not sampled — runs
      through the real screens and the real `#75` contract, never a parallel copy of either
- [ ] `docs/REFUSALS.md` is **generated** from that run: a Markdown table of
      `input → code → reason`, one row per probe. Markdown rather than JSON on purpose — the whole
      value of the file is that a wrong sentence lands on a diff line somebody reads
- [ ] An `--emit` flag regenerates it, and a fast-lane test asserts the committed file is
      byte-identical to what the code produces. Same shape as `loco.md` (#30) and
      `novelty-reference.json` (#49), and it inherits their lesson: the byte-identity test is what
      catches upstream nondeterminism nobody was testing for
- [ ] **The emitted code set equals `reason_codes()` exactly** — a declared code nothing reaches is
      named as dead vocabulary, an emitted code nothing declared is a contract violation. This is
      the card's red condition and it does not depend on a reader
- [ ] It lives in `docs/`, not `reports/`. `.gitignore` excludes `/reports/*` with per-directory
      negations, so a new `reports/refusals/` would be invisible on a fresh clone and the CI check
      would read nothing — the trap already found on `artifacts/current.json` (#34) and
      `reports/loco/` (#30). The file is cheap to regenerate, so it has no claim on `reports/`
      anyway, and `docs/**` is an allowed path under the freeze
- [ ] `docs/QA-PROTOCOL.md` §4 gains one reviewer question: **does any function narrow a cause it
      knows to a boolean before the reason is written?** That is #49's root cause stated generally —
      `_vector` knew *why* and returned `False`, so the sentence had to be reconstructed downstream,
      wrongly. It is a code-shape judgement and cannot be automated; it belongs on a checklist, and
      writing it down is this card's job because this card is where the lesson was paid for
- [ ] **Not a gate, deliberately.** `docs/FREEZE.md` names HG-1 … HG-4 as an unfreeze condition, and
      a fifth gate would either edit that list or need a footnote explaining its absence from it.
      This card asserts in `tests/` and runs in the fast lane like everything else. Registration as
      **HG-5 is boxed on #91**, after the freeze lifts

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_refusals.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6, HG-2; `docs/PRD-inverse-design.md` — S2, R1

## Narrative

- 2026-09-07: Created from a `/grill-with-docs` session that began as "add a logging system to catch
  bugs during the model's working cycle". Four things the grilling settled, recorded so the card is
  not re-argued from its title.

  **Logging was the wrong instrument for the bug that prompted it.** #49's defect raised nothing,
  returned the right code, and would have written the same false sentence to any log just as
  confidently. Three classes of bug were separated: loud failure (already handled — `ScreenError`,
  `ContractError`, `FormulaError` and `LeakDetected` all raise with offenders named), silent wrong
  *number* (the 13 named leaks are guarded by `hydms/qa/detectors.py` and HG-1; an unnamed
  fourteenth is not), and silent wrong *words* (this card). Only the last two were taken.

  **This project's existing answer to "catch bugs automatically" is not logs.** `hydms/qa/detectors.py`
  is eight assertions wired into the pipeline's own code path — explicitly not test helpers, so the
  sentinel tests the real guard rather than a copy that can drift. The mechanism chosen here is
  continuous with that: refuse first, record second. There is, for the record, **no logging in this
  repository at all** — zero `getLogger` across `hydms/`, `app/` and `scripts/`, and 126 `print()`
  calls across 15 modules. Converting those to a logger is tidiness, not bug-catching, and is
  deliberately not in this card.

  **The record half was split off** into #91, because it needs #76 and #78 and this half needs
  nothing that is not already `done`. A single card would have sat untouched until S6.

  **This card is not an unfreeze condition and must not become one.** `docs/FREEZE.md` fixed four
  conditions "before results are seen, so it cannot be softened later", and widening that list is
  the one thing that document exists to resist. It may sit open across the lift. (by @assistant)
