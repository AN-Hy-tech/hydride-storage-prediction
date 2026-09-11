---
id: 77
status: backlog
priority: High
blocked_by: [76]
assignee: "@amirhossein"
tags: [ph, l6, HG-2, R1]
---

# GATE HG-2: the refusal path — never a bare number

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** What the system does when it does not know — and the guarantee that it never answers as though it did.

## Why this exists

This is the card the whole phase exists for. A model that returns 2.1 wt% for a
composition it has never seen anything like is not merely inaccurate — it is *confidently* inaccurate,
and a user has no way to tell that apart from a good prediction.

Tree ensembles extrapolate as constants, which is risk R1 in the PRD: outside the training hull the
model produces a plausible flat number rather than an obvious failure. The interval and the domain
verdict are what make that visible, and a refusal is what makes it unmissable.

A refusal must carry a **reason**. "Cannot predict" sends the user away; "contains Tc, which appears in
no training alloy" tells them what to do next.

## Done when

- [ ] Unparseable formula → refusal, with the parse failure named
- [ ] Element absent from the training set → refusal, naming the element
- [ ] Temperature outside the trained range (195-773 K) → refusal, naming the range
- [ ] Outside the applicability-domain ceiling (#48) → refusal, reporting the distance and the ceiling
- [ ] Every refusal carries a machine-readable code **and** a human-readable reason
- [ ] **No path through `predict_capacity()` can return a point estimate without an interval and a
      domain verdict** — asserted exhaustively, not sampled
- [ ] Registered in the gate harness as HG-2
- [ ] **The unparseable-formula and unknown-element refusals carry `INDETERMINATE` (from #75).**
      Neither is a threshold any screen declares a code for, and the delivery vocabulary is derived
      from the screens rather than written down — so there is no `unparseable-formula` code to reach
      for, and inventing one here is precisely the second source of truth #75 exists to prevent.
      `INDETERMINATE` is the declared code for "this rule could not be evaluated on this candidate",
      it is a **rejection**, and #48's screen already emits it for a formula it cannot give a
      physical ceiling to. The distinguishing detail goes in the human-readable `explanation`. This
      gate must assert both refusals are reachable and that neither returns a number

- [ ] **A non-finite temperature raises instead of refusing, and that leaves one declared sentence
      unreachable** (added 2026-09-07 by #90). `PredictionRequest.__post_init__` runs `temperature_k`
      through `_finite()`, so `float('nan')` is a `ContractError` and can never become a `Refusal`.
      `hydms.screens.window.Window` nonetheless declares `INDETERMINATE` for "there was no number to
      compare" and writes a sentence for it — a sentence no caller can reach and no diff can show
      (`docs/REFUSALS.md`, § "One sentence this page cannot show"). Decide it rather than inherit it:
      either a malformed request is a caller error and raising is right, in which case say so where
      the window declares the code; or a caller who omitted a temperature deserves a refusal like any
      other, in which case this gate owns making it one. An unreachable branch that writes prose is
      exactly where a stale sentence hides

- [ ] **`untrusted-family` is declared, published and unreachable through `predict_capacity()`**
      (added 2026-09-11 by #76). The applicability screen judges it from an alloy-class label and
      the leave-one-class-out transfer measured for that family (#30). A user types a formula and a
      temperature; there is no label, and nothing in the package maps a novel composition to a
      family. Supplying the column with an unknown value is **worse** than omitting it — the screen
      answers `indeterminate` for a class it has no transfer estimate for, so every novel candidate,
      which is the entire point of the exercise, would be refused for the wrong reason. So #76
      omits it, and `docs/REFUSALS.md` documents a code the delivery path cannot produce. This gate
      owns saying which codes are reachable **through which entry point**: reachable from the batch
      CSV path (#84) and from screening a curated frame, not from a single prediction. A bare
      "every code is reachable" assertion here would be false or would have to quietly widen what
      "reachable" means

- [ ] **The null-check obligation is discharged by measurement, and this gate inherits the pin**
      (added 2026-09-11 by #76). Every object null is refused at three independent guards and every
      stringified null but one is refused by the grammar;
      `test_every_spelling_of_a_missing_value_is_refused_except_the_one_that_is_chemistry` pins it.
      **`"NaN"` is sodium and nitrogen to both parsers and must keep being answered** — if this gate
      adds a null blocklist, it refuses a real material. #84 owns the boundary where a missing value
      becomes text

- [ ] **A formula that is not a string is reported as "the formula is empty", which is false about
      the input** (added 2026-09-11 by #76's QA pass). `PredictionRequest.__post_init__` runs
      `if not isinstance(self.formula, str) or not self.formula.strip()` and raises **one** sentence
      for both arms, so `predict_capacity(5, 298.0)` and `predict_capacity(["La1Ni5"], 298.0)` are
      both told "a request needs a composition; the formula is empty. An empty string is a caller
      error rather than an unparseable material" — a sentence whose every clause is about a case
      that did not happen. The temperature field one line below does **not** make this conflation:
      it distinguishes `temperature_k must be a number, not bool` from `temperature_k is nan, which
      is not a finite number`, so the asymmetry is within one `__post_init__` and is visible by
      reading it.

      It is reachable and it crosses a real boundary. `PredictionRequest.from_dict` checks only that
      the two keys are *present*, so `{"formula": 5, "temperature_k": 298}` — which JSON delivers
      without complaint and a CSV column of part numbers produces by accident — arrives here, and
      #78's API and #84's uploader will both hand a user the wrong explanation of what they did
      wrong. This gate owns every sentence the refusal path can produce; a `ContractError` is not a
      `Refusal`, but #77 already owns the question of whether a malformed request should *become*
      one (the non-finite-temperature box above), and the two decisions are the same decision. Fix
      the wording where it is raised, or fold both arms into a refusal — but do not leave a guard
      whose message names a cause it did not observe

- [ ] **`docs/REFUSALS.md` catalogues a sentence for `unreadable-formula` that `predict_capacity()`
      cannot produce** (added 2026-09-11 by #76's QA pass). This is the *same* entry-point question
      the `untrusted-family` box above asks, found on a second row, and it is the more visible of
      the two because an unreadable formula is the refusal a user is most likely to trigger by
      typing.

      The page's probe hands the screens a frame whose feature columns are already filled and whose
      formula column is unreadable, so the screens run and the row carries **their** sentence:
      *"'LaNi5Xx2' could not be given a physical capacity ceiling -- it does not parse, or it names
      an element the 'oliynyk' table has no mass for; …ElMD does not raise on it…"*. The delivery
      path never reaches a screen for that input — `featurize` raises first, by the ordering #76
      settled and could not avoid — so `predict_capacity("LaNi5Xx2", 298.0)` returns the same code
      with the **featuriser's** sentence (*"1 of 1 formula(e) could not be parsed: ['candidate']
      'Xx1' names 'Xx', which is not a chemical element…"*) and, correctly, zero screen verdicts.
      Two true sentences; the catalogue shows the one the API will not send.

      Neither sentence is wrong and nothing is mis-refused — this is a *wrong words* finding, which
      is the class this page was built to catch, landing on the page itself. The page's own framing
      is what makes it one: it says it holds "every sentence the delivery path can produce", and the
      predict module's docstring says the catalogue "documents this function rather than something
      adjacent to it". For eleven of thirteen rows that is true. This gate owns the qualifier, and
      it already owns a section for it (*"One sentence this page cannot show"*). Either add a probe
      that goes through `predict_capacity()` so the typed-formula sentence is on a diff line too, or
      say per row which entry point reaches it — but do not let the page keep claiming both

## Runnable check

```bash
conda run -n Project python -m hydms.gates run HG-2
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6, HG-2; `docs/PRD-inverse-design.md` — S2, R1

## Narrative

- 2026-09-02: Created for Phase H. The distinction that matters to a user, and that the API
  documentation (#80) must answer: how do you tell a refusal from a genuinely low prediction? (by @assistant)
