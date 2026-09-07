---
id: 90
status: done
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

- [x] A committed probe set — inputs chosen to reach every rejection path, not sampled — runs
      through the real screens and the real `#75` contract, never a parallel copy of either
- [x] `docs/REFUSALS.md` is **generated** from that run: a Markdown table of
      `input → code → reason`, one row per probe. Markdown rather than JSON on purpose — the whole
      value of the file is that a wrong sentence lands on a diff line somebody reads
- [x] An `--emit` flag regenerates it, and a fast-lane test asserts the committed file is
      byte-identical to what the code produces. Same shape as `loco.md` (#30) and
      `novelty-reference.json` (#49), and it inherits their lesson: the byte-identity test is what
      catches upstream nondeterminism nobody was testing for
- [x] **The emitted code set equals `reason_codes()` exactly** — a declared code nothing reaches is
      named as dead vocabulary, an emitted code nothing declared is a contract violation. This is
      the card's red condition and it does not depend on a reader
- [x] It lives in `docs/`, not `reports/`. `.gitignore` excludes `/reports/*` with per-directory
      negations, so a new `reports/refusals/` would be invisible on a fresh clone and the CI check
      would read nothing — the trap already found on `artifacts/current.json` (#34) and
      `reports/loco/` (#30). The file is cheap to regenerate, so it has no claim on `reports/`
      anyway, and `docs/**` is an allowed path under the freeze
- [x] `docs/QA-PROTOCOL.md` §4 gains one reviewer question: **does any function narrow a cause it
      knows to a boolean before the reason is written?** That is #49's root cause stated generally —
      `_vector` knew *why* and returned `False`, so the sentence had to be reconstructed downstream,
      wrongly. It is a code-shape judgement and cannot be automated; it belongs on a checklist, and
      writing it down is this card's job because this card is where the lesson was paid for
- [x] **Not a gate, deliberately.** `docs/FREEZE.md` names HG-1 … HG-4 as an unfreeze condition, and
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

- 2026-09-07: **Landed.** `hydms/delivery/refusals.py`, `tests/delivery/test_refusals.py` (28 tests,
  1.1 s), `docs/REFUSALS.md`. Twelve probes reaching all eight declared codes; suite 1308 passed / 4
  deselected, gates 5/0/4 with HG-1 13/13, ruff and mypy clean, board and freeze checks pass.

  **The QA-PROTOCOL box was already ticked before the card started.** §4 question 8 went in with
  #49, referencing #90 by number. This card only re-aimed the last sentence at the file, now that
  the file exists.

  **What decided the shape: the resolution rule, and where it lives.** A catalogue with "one row per
  probe" needs one code per probe, and two screens can both reject. `resolve()` takes the first
  rejecting screen's code — run order is the only precedence declared *across* screens — and carries
  every rejecting screen's sentence. That is the single judgement this module adds, and it is the
  one thing #76 could plausibly duplicate, so it is public and boxed there as *call it, do not
  re-derive it*.

  **The screens are `delivery_screens()`, not the screens that exist.** Running #49's ElMD novelty
  screen here would emit `beyond-known-chemistry`, which `reason_codes()` does not declare and the
  contract refuses — correctly. That refusal is now a test rather than a comment, and it is the
  mechanism by which #76's decision to admit the novelty screen will force a probe and a
  regeneration rather than passing silently.

  **A finding, and it is the contract's doing.** `PredictionRequest` runs `temperature_k` through
  `_finite()`, so a caller cannot express "no temperature" — which means the temperature window's
  declared `INDETERMINATE` and the sentence it writes for it are **unreachable from a real request**.
  The vocabulary is still complete (the domain screen reaches `indeterminate` two other ways, and
  both have probes), so the card's red condition still holds; what is lost is that one sentence can
  never land on a diff. Boxed on #77, stated on the page itself under "One sentence this page cannot
  show", rather than papered over with a probe that bypasses the contract to reach it.

  **The `LaNi5Xx2` row is worth reading.** The sentence it now collects is *"could not be given a
  physical capacity ceiling — it does not parse, **or** it names an element the 'oliynyk' table has
  no mass for"*. That disjunction is the correct shape for a cause the screen genuinely does not
  narrow, and it is what #49's false sentence should have been: the failure mode was not vagueness,
  it was a confident specific claim reconstructed downstream by code that no longer knew which of
  the two had happened.

  **The probes carry stated inputs, and the page says so.** Nothing is trained, so the prediction,
  the band width, the alloy class and the one feature value are inputs the screens read, not model
  output; every answer carries `model_version = 'unfitted-probe'`. A catalogue that let a stated
  6.0 wt% read as a prediction would be committing the error it exists to catch. `temperature(K)`
  could not serve as the feature column even though it is in the reference's spans — its span *is*
  the window's interval, so the window rejects first and `outside-feature-range` would be
  unreachable; `range_Mendeleev_Number` is carried instead, and `candidates()` refuses a `FEATURE`
  the committed reference does not range-check rather than letting the code go quietly dead. (by @assistant)
