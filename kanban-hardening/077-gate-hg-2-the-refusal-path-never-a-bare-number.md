---
id: 77
status: done
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

- [x] Unparseable formula → refusal, with the parse failure named
- [x] ~~Element absent from the training set → refusal, naming the element~~ — **there is no such
      rule and there must not be one.** Measured against the deployed `v2`: `Tc2Ni` — technetium
      appears in no training alloy — is **answered**, at 4.17 on the ElMD scale against a ceiling
      of 11.73. That is #49's design, not an oversight: novelty is a distance between
      *compositions*, not a test of element membership, because the programme's purpose is
      proposing alloys nobody has made. An element-membership rule would refuse every genuinely
      new candidate and admit every re-proportioning of an old one. **Two real rules sit where
      this box expected one**, and the gate probes both: an element the *property tables* do not
      cover is `indeterminate` and the sentence names it (`Blocking element(s): Rn, Xe`); a
      composition far from the corpus is `beyond-known-chemistry` and the sentence names the
      distance, the ceiling and the nearest known alloy
- [x] Temperature outside the trained range (195-773 K) → refusal, naming the range. **Checked
      against the window's *own* verdict, not the composed explanation** — temperature is also a
      model input, so the applicability screen rejects the same candidate with a note that happens
      to name both bounds, and a check on the joined string passes while the window's own sentence
      has gone to "cannot predict". That is #49's defect exactly, and staging it is what found it
- [x] ~~Outside the applicability-domain ceiling (#48) → refusal, reporting the distance and the
      ceiling~~ — **the ceiling is a capacity, not a distance.** #48 established that the
      applicability domain is *not* a composition distance; the distance is #49's and is reported
      by `beyond-known-chemistry`. `out-of-domain` names the prediction and the 5.19 wt% level
      (`docs/REFUSALS.md`), which is the honest version of this box. It is reachable through the
      frame door and **contingent** at the request door: the model has to predict above that level,
      and neither `v2` nor the fixture fit does. A gate that demanded it would be red for the
      reason the model is well-behaved
- [x] Every refusal carries a machine-readable code **and** a human-readable reason
- [x] **No path through `predict_capacity()` can return a point estimate without an interval and a
      domain verdict** — asserted exhaustively, not sampled. **No probe set can deliver this**: a
      thousand formulas establish what a thousand formulas do. So the gate parses the *source* of
      `predict_capacity` and requires every `return` in it to be a call to `Refusal` or
      `PredictionResult`. A branch added later that returns a float, a dict or nothing is red the
      moment it is written, whatever it is given. Staged both ways in `tests/gates/`
- [x] Registered in the gate harness as HG-2
- [x] **The unparseable-formula and unknown-element refusals carry `INDETERMINATE` (from #75).**
      Neither is a threshold any screen declares a code for, and the delivery vocabulary is derived
      from the screens rather than written down — so there is no `unparseable-formula` code to reach
      for, and inventing one here is precisely the second source of truth #75 exists to prevent.
      `INDETERMINATE` is the declared code for "this rule could not be evaluated on this candidate",
      it is a **rejection**, and #48's screen already emits it for a formula it cannot give a
      physical ceiling to. The distinguishing detail goes in the human-readable `explanation`. This
      gate must assert both refusals are reachable and that neither returns a number

- [x] **A non-finite temperature raises instead of refusing, and that leaves one declared sentence
      unreachable** (added 2026-09-07 by #90). `PredictionRequest.__post_init__` runs `temperature_k`
      through `_finite()`, so `float('nan')` is a `ContractError` and can never become a `Refusal`.
      `hydms.screens.window.Window` nonetheless declares `INDETERMINATE` for "there was no number to
      compare" and writes a sentence for it — a sentence no caller can reach and no diff can show
      (`docs/REFUSALS.md`, § "One sentence this page cannot show"). Decide it rather than inherit it:
      either a malformed request is a caller error and raising is right, in which case say so where
      the window declares the code; or a caller who omitted a temperature deserves a refusal like any
      other, in which case this gate owns making it one. An unreachable branch that writes prose is
      exactly where a stale sentence hides

- [x] **`untrusted-family` is declared, published and unreachable through `predict_capacity()`**
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

- [x] **The null-check obligation is discharged by measurement, and this gate inherits the pin**
      (added 2026-09-11 by #76). Every object null is refused at three independent guards and every
      stringified null but one is refused by the grammar;
      `test_every_spelling_of_a_missing_value_is_refused_except_the_one_that_is_chemistry` pins it.
      **`"NaN"` is sodium and nitrogen to both parsers and must keep being answered** — if this gate
      adds a null blocklist, it refuses a real material. #84 owns the boundary where a missing value
      becomes text

- [x] **A formula that is not a string is reported as "the formula is empty", which is false about
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

- [x] **`docs/REFUSALS.md` catalogues a sentence for `unreadable-formula` that `predict_capacity()`
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

- 2026-09-11: **Closed. The delivery module ran against a real artifact for the first time, and
  two of the card's own four named causes turned out not to be rules this system has.**

  **`predict_capacity()` has now answered from `v2`.** Every session since #76 has said "not run
  against a real artifact — `v2` records no gate run, so `load_surrogate` refuses it", and this
  card is what unties that: it is the *same knot* #33 untied one layer down, and it takes the same
  resolution. `bundle_from(surrogate, ...)` is everything in `load_bundle` below the version
  lookup, so HG-2 loads its candidate through `gates/_artifact.candidate` — `require_gates=False`,
  the door the store documents — and assembles the bundle `load_bundle` would have. `load_bundle`
  grew no parameter and lost no guarantee: a test asserts it still raises `GatesIncomplete` on the
  very version the gate just scored. The gate runs in **2.5 s** against `v2` and is green.

  **Three claims, and only one of them needs an artifact — so this gate can go red where it
  cannot go green.** CI's fast lane has no `artifacts/` (gitignored), so AC-3, AC-4 and now HG-2
  all skip there. But the structural half — `PredictionResult` has no default for `interval` or
  `domain` and refuses `None` for both, `Refusal` has no field a number fits in — and the
  exhaustive half both run in an empty checkout, so a regression in either is red on every push
  and the behavioural half reports `SKIPPED` rather than a pass.

  **"Asserted exhaustively, not sampled" is not something a probe set can do.** A thousand
  formulas establish what a thousand formulas do. The gate therefore parses the *source* of
  `predict_capacity` and requires every `return` in it to be a call to `Refusal` or
  `PredictionResult`; a branch that returns a float, a dict or nothing is red the moment it is
  written. Three exits today. Staged red both ways.

  **"Element absent from the training set → refusal, naming the element" is not a rule, and must
  not become one.** Measured: `Tc2Ni` is **answered** — technetium is in no training alloy, is in
  the `oliynyk` table, and sits 4.17 from the corpus against an ElMD ceiling of 11.73. #49 built
  novelty as a distance between *compositions* precisely because the programme proposes alloys
  nobody has made; an element-membership rule would refuse every genuinely new candidate and admit
  every re-proportioning of an old one. Two real rules sit where the box expected one and the
  probe set names both. Same class of finding as #76's null-check box: the instruction was aimed
  at a symptom, and measuring the premise first is what the board keeps learning.

  **The AD box asked for "the distance and the ceiling", and #48 had already shown those are two
  different screens.** The applicability ceiling is a *capacity* (5.19 wt%); the distance is
  #49's, reported by `beyond-known-chemistry`. Corrected on the box rather than implemented.

  **Reachability is per door, and the three inherited findings were one question.** `untrusted-
  family` unreachable by typing, the catalogue's `unreadable-formula` sentence unreachable by
  typing, and the window's "no number to compare" sentence unreachable by typing — all the same
  fact: there are two doors into the screens and they can state different things. The *request*
  door takes a formula and a temperature and computes the rest; the *frame* door (`apply_screens`
  over a curated frame — the training data, #84's CSV, this page's probes) can state a prediction,
  a band, a class label and a feature value. So the gate measures **both** and requires their
  union to be the declared vocabulary exactly, and `docs/REFUSALS.md` now labels every row with
  its door. The label is **derived** from what a probe varies, not declared beside it, because a
  hand-maintained one is the half that goes stale.

  **`NOT_ALWAYS` is the only declared thing in the gate, and it distinguishes two kinds of
  "cannot".** `NEVER` — the input does not exist at that door, so no fit can reach it; the gate is
  **red** if it appears, which is #76's `untrusted-family` finding turned into an assertion.
  `SOMETIMES` — the fit decides; reported, never required, because demanding it would make the
  gate red for the reason the model is well-behaved. Four codes are `SOMETIMES` and one of them
  was a surprise: **`beyond-known-chemistry` is fit-dependent**, because the novelty screen runs
  *third* and `resolve` reports the first rejecting screen's code, so the applicability screen
  between it and the window can take the code first. Measured both ways — deployed `v2` answers
  `K1Rb1` with it, the cheap fixture fit answers with a domain code. A code in neither the
  measured set nor `NOT_ALWAYS` fails the gate: reachability moved and nothing says why.

  **Writing the red-demonstration found a defect in the gate itself.** The "names the range" check
  read the *composed* explanation, and temperature is also a model input — so the applicability
  screen rejects the same candidate with a note that happens to name both bounds, and the check
  stayed green with the window's own sentence blanked to "cannot predict". A true sentence from a
  different rule standing in for the one that was asked is #49's defect exactly. The check now
  reads the verdict of the screen that *owns* the code.

  **The non-string formula, and the decision behind it.** The guard raised one sentence for two
  arms, so `predict_capacity(5, 298.0)` was told "the formula is empty" — reachable across a real
  boundary, since `from_dict` checks only that the key is present. Two arms now, two sentences,
  mirroring the temperature field one line below. And the open question it shares with the
  non-finite temperature is **settled: a malformed request raises, it does not become a
  `Refusal`** — and the type had already settled it. A refusal carries the request it declines, so
  an input that cannot build a `PredictionRequest` cannot be carried by the `Refusal` describing
  it. Said where the window declares the code, as the box asked.

  19 tests in `tests/gates/test_hg2_refusal_path.py`, 9.0 s — every failing branch staged red.
  Fast lane (`pytest -m "not slow"`) **1370 passed, 4 deselected, 705 s** — up from 1337 at #76,
  which is these 19 plus 14 across `tests/delivery`. `hydms.gates run --fast`: **6 passed /
  3 skipped**, where it was 6/6 — HG-2 is in the passed set and only AC-5, HG-3 and HG-4 remain
  unchecked. `run HG-2` on its own exits 0 in **2.5 s**.
  `docs/REFUSALS.md` regenerated: a `Door` column, a two-doors section, and a new table showing
  what a caller typing each `request` row actually receives, including the featuriser's own
  sentence for `LaNi5Xx2` on its own diff line. A parse failure is refused before any feature is
  reached, which is why that sentence can be printed with no artifact on disk — pinned by a test
  that featurises it under two different contracts. ruff and mypy clean. (by @assistant)
