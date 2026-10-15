---
id: 80
status: done
priority: Normal
blocked_by: [79]
assignee: "@amirhossein"
tags: [ph, l6, S10]
---

# API reference documentation

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What a caller needs to know to use a prediction correctly — including what the service will not tell them.

## Why this exists

An API reference that lists endpoints and field types is generated for free by OpenAPI.
What cannot be generated is the part that stops misuse: what the interval means, why the model refuses,
what the trained ranges are, and why comparing a material wt% to a DOE system target is an overstatement.

Written with the `grill-with-docs` skill. Its interview must answer one question before a word of the
document is written: **how does a caller tell a refusal from a genuinely low prediction?** If that
cannot be answered crisply, the contract is wrong and the document should not paper over it.

## Done when

- [x] `docs/API.md` covers every endpoint with a real request and a real response
- [x] It states what the interval is (conformal, at a named level) and what it is not
- [x] It lists every refusal reason code and what a caller should do about each
- [x] It states the trained ranges — temperature, elements, alloy families — and the applicability domain
- [x] It carries the material-versus-system caveat for capacity comparisons
- [x] It names the artifact version the examples were produced against
- [x] The ADRs the interview produced are filed under `docs/adr/`

## Runnable check

```bash
python scripts/check_board.py --root .
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6; `docs/PRD-inverse-design.md` — S10, S7

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)

- 2026-09-12: **Landed. `docs/API.md` is generated, and the interview's one required question had
  a crisp answer, which is what let the document be written at all.** (by @assistant)

  **How a caller tells a refusal from a genuinely low prediction: three ways, and the third is
  structural.** HTTP `200` versus `422`; `refused` false versus true; and `capacity` present
  versus *the key not existing at all*. `refused` is a property on both answer types rather than
  a field on either, and a `Refusal` has no field a number could occupy — so there is no way for
  this service to spell a bare estimate and no way for a low answer to arrive looking like a
  decline. The card said that if the question could not be answered crisply the contract was
  wrong; it could, because #75 made it structural rather than conventional.

  The worked case the page leads with is **`Mg2Ni` at 573 K**, which is refused `high-uncertainty`
  — not because the estimate is small but because the calibrated band came back 1.36 wt% wide
  against the 1.12 this project will report. That is the one a caller will misread, so it is the
  example rather than a sentence.

  **The page is generated, and the split is the design.** `hydms/delivery/apidoc.py` holds the
  prose beside the facts, the same arrangement `refusals.py` uses. Three sources, kept apart
  because they fail differently: the code read live (the vocabulary, the batch limit, the schema
  strings, the element coverage), the **committed OpenAPI document** for the route table — so the
  page and the machine-readable contract cannot disagree, and HG-3 already guards that file — and
  a **committed fixture of real exchanges** for everything needing a fit.

  **`--probe` is split from `--emit` because `artifacts/` is gitignored.** A generator that talked
  to a model would be a check that silently never runs — the trap already found on
  `artifacts/current.json` (#34) and `reports/loco/` (#30). `--probe` needs the fit and is the
  maintainer's; `--emit` and the nine tests need only the fixture. **Verified rather than asserted:**
  with `artifacts/` renamed away, `python -m hydms.delivery.apidoc` still reports the page current
  and all nine tests still pass.

  **Reachability was measured, not hedged.** "The fit decides" is what a small probe set can
  honestly say and it is useless to a caller asking which refusals they can actually receive. A
  50 x 10 sweep through the request door against `v3` reaches **8 of the 9** declared codes;
  `untrusted-family` is the one it cannot, which is what `docs/REFUSALS.md` claims and what HG-2
  goes red on. The page carries a paragraph saying why this *disagrees* with the gate reports
  without either being wrong: HG-2 and HG-3 run a dozen probes and record
  `above-physical-ceiling` and `out-of-domain` as unreached on this fit, which is the honest
  statement for a small set; the sweep asks the different question of whether any typed request
  reaches them at all.

  **One box was nearly ticked falsely.** "It states the trained ranges — temperature, **elements**,
  alloy families" — the first draft had temperature, capacity, feature spans and the LOACO table,
  and no elements anywhere. They turned out to be derivable with no artifact from the novelty
  screen's committed reference: **50 elements over 780 canonical compositions, 9 of them appearing
  in two compositions or fewer**. The page states it is *not* a bound — no screen checks membership,
  the novelty screen measures distance instead — because a reader would otherwise take a list on
  an API page as a rule that refuses.

  `pyproject.toml` gained `delivery/*.json` to package data, because the module's docstring
  claimed the fixture shipped in a wheel and it did not.

  **19 tests** in `tests/delivery/test_apidoc.py`, and the second half of them were added after
  measuring: the module came in at **75 %** covered in isolation, and the gap was the error paths
  — the sentences that tell a maintainer *what to run*. `--probe` when the fixture is absent,
  `--emit` when the page is stale, `openapi --emit` when the contract is missing. This repository
  has already been bitten by a guard that learned a new failure mode and kept its old reason (#90),
  so each is probed for its wording rather than assumed to follow the code. **84 %** now; what
  remains uncovered is `probe()` and `_reachable()`, which is the artifact-requiring half and is
  the design rather than an omission.

  `tests/delivery` **179 passed** (from 160); `tests/delivery` + `tests/screens` **334 passed**.
  Fast lane `pytest -m "not slow" --cov`: **1461 passed, 4 deselected, 1038 s**, coverage
  **87.89 %** against the 80 % floor. ruff, ruff format and mypy clean. Gates: 7 passed / 0 failed
  / 2 skipped — AC-5 (frozen) and HG-4, whose coverage data predates this change and says so.
