---
id: 94
status: done
priority: P2
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l6]
---

# A crossed band raises where it should refuse

**Stage S8 — Evidence and close** · **L6 Delivery** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What a caller is told when the surrogate's own heads come back out of order.

**This card is NOT an unfreeze condition.** It was found by #93 and is filed so it has an owner,
not to widen `docs/FREEZE.md`. The unfreeze condition is fixed and stays fixed.

## Why this exists

Quantile crossing is a measured property of this surrogate, not a hypothetical.
`hydms.surrogate.model.quantile_metrics` returns a `crossings` field because "MultiQuantile fits
the heads jointly but does not constrain them to be monotone … **measured at 23 % of rows on a
small fit**, so this is a real number to report rather than a defensive zero"
(`hydms/surrogate/model.py:1291`), and `hydms/surrogate/conformal.py`'s header records that
**CQR's widening cannot repair a crossing** — the correction is one constant added to both outer
heads, so it shifts a band it cannot re-order.

Card #93 then watched it happen on a real prediction. On the versions CI resolves, two of three
candidates — `Ti1Fe1` and `Mg2Ni1`, both outside the fixture's La–Ni training family — came back
from `hydms.surrogate.predict.predict` with widths of **−0.094422** and **−0.029760** wt%.

The surrogate is right to hand that on unclipped: repairing it would turn a defect a screen can
see into a plausible narrow band, and
`tests/surrogate/test_predict.py::test_a_crossed_band_reaches_the_caller_unclipped` now pins that.
**The question this card owns is what happens next**, and today the answer is:

- `hydms.delivery.contract.Interval.__post_init__` raises `ContractError` on `upper < lower`, with
  a message that names quantile crossing explicitly. So the behaviour is *known* and *deliberate*
  at that boundary.
- `hydms/delivery/predict.py` never mentions crossing. Nothing between the surrogate and the
  contract looks at the sign of the width.

So a crossed candidate produces a **raised exception, not a refusal carrying a reason code** —
which is the one shape of answer this project has decided it does not give. #44's interface is "a
verdict with a reason, never a silent drop"; HG-2 (#77) makes a bare number unconstructible; #90
committed the catalogue of every reason the system can give. A `ContractError` escaping
`predict_capacity` is outside all three: a batch screen (#84) hits it on one bad row and loses the
batch, and the API (#78) turns it into a 500 rather than a refusal the client can read.

**It is not obvious that a new reason code is the right answer**, and this card should decide
rather than assume. A crossed band may belong under an existing domain verdict — the candidates
that crossed here are exactly the ones an applicability-domain screen (#48) or an ElMD novelty
screen (#49) should already be refusing, and a reason code that fires only for rows another screen
has already caught is a code no request can reach, which is the defect #90's own reachability
check exists to find. Measure before adding.

## Done when

- [x] **Measure it.** On a real fit, how many rows cross, and how many of those are *already*
      refused by the domain ceiling or the novelty screen? If the answer is "all of them", the fix
      is ordering — make sure the screens run before an `Interval` is constructed — and no new
      code is declared. If some cross while passing every screen, that is the case a reason has to
      cover
      — **Measured 2026-10-16, on a local fit at the deployed configuration** (`calibrate --save`
      from the committed `model-chosen.csv`; correction +0.038060, not `v3`'s +0.037355 — #104's
      thread nondeterminism): **zero rows cross**, in the 1,278 corpus pairs, in #93's `Ti1Fe1`
      / `Mg2Ni1` at 298 K, and in 9,422 random 2–4-element compositions over the corpus's
      elements at 195–773 K (two seeds). The narrowest band was 0.352 wt%; no median fell
      outside its band. So "all already refused" is vacuously true on this fit, and crossing is
      a property of a *weak* fit — the delivery fixture's 80-iteration one is where #93 saw it.
      Worse than vacuous: a crossed band that *did* arrive would pass the width rule, because
      `widths > max_interval_width` reads a negative width as the narrowest band of all. So the
      ordering already held (`Interval` is built only for admitted rows) and guarded nothing
- [x] **Decide and record**: a new reason code, an existing verdict, or an ordering guarantee.
      Whichever it is, `docs/REFUSALS.md` is **generated** (`hydms.delivery.refusals --emit`) —
      regenerate it, never edit it
      — **An existing verdict: `indeterminate`, from the domain screen's width rule.** A crossed
      band is a band that rule cannot judge, exactly as a missing width is, and it already
      answers a missing width with `indeterminate` — so `hydms/screens/domain.py` now treats
      `width < 0` the same way, with its own sentence ("the calibrated band is crossed — its
      upper head is … wt% below its lower one"). Not a new code: on the real fit nothing could
      reach it. Not `high-uncertainty`: its sentence would call a negative number "wide". Not
      at `Interval`: the contract keeps raising on an inverted band, because by then it is a
      bug. `docs/REFUSALS.md` regenerated with a `crossed-band` probe (frame door)
- [x] No declared-but-unreachable code is added. See
      [[enumerate-the-vocabulary-when-the-prose-cannot-go-red]]: a reason nothing can reach passes
      every shape check and means nothing
      — none added; the vocabulary is unchanged
- [x] A test drives a crossed band through the **delivery** path, not the surrogate path, and
      asserts what the caller is told. The surrogate half is already pinned by
      `test_a_crossed_band_reaches_the_caller_unclipped`
      — `tests/delivery/test_batch.py::test_one_crossed_band_refuses_its_own_row_and_not_the_batch`,
      over the fixture deployment with one formula's outer heads swapped (which candidates
      cross is machine-dependent, #93, so the crossing is stated). The screen half is
      `tests/screens/test_applicability.py::test_a_crossed_band_is_a_rejection_not_the_narrowest_band`.
      All four new tests fail on the old code
- [x] The batch page (#84) and the API (#78) are checked against the decision: one crossed row
      must not cost a batch, and must not become a 500
      — `/v1/predict/batch` answers 200 with the middle row refused; `/v1/predict` alone answers
      422 with a readable body (the runbook's refusal status). `screening()` renders
      answered / refused / answered. Both in `tests/delivery/test_batch.py`

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/ -k "cross or interval"
conda run -n Project python -m hydms.delivery.refusals --emit
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8; gate HG-2 (card #77) owns the refusal path this extends;
card #90 owns the catalogue any new reason lands in

## Narrative

- 2026-10-16: Closed. The card's framing assumed crossed rows would be the ones another screen
  already refuses; the measurement found no crossed rows at all on the real configuration, and
  found instead that the width rule would have *admitted* one. The fix is therefore in the screen
  that owns the band, not in the delivery path or the contract, and the existing code was the
  right one. The local fit and the script are throwaway (scratchpad); the numbers are in the
  first box. (by @assistant)
- 2026-09-26: #84 made the batch path one call, and that sharpens this card without deciding it.
  `predict_many` builds every answer from one screened frame, so a crossed band on any row raises
  `ContractError` out of the whole call. That means a `POST /v1/predict/batch` of up to 4,096 rows,
  or one chunk of the CSV page, fails whole. The route's old per-row loop failed the same way, so
  no behaviour regressed. But the blast radius is now a batch by construction, and the last box
  above is now concrete. The page catches the resulting `ServiceError` and says the batch failed,
  never showing the rows either side. `v3` answered all 1,279 corpus pairs in one call without
  raising, so no corpus row crosses on the deployed model. (by @assistant)
- 2026-09-12: Created by the #93 session. Filed rather than fixed for two reasons. The first is
  scope: #93 owns two tests and a diagnosis, and this is a question about what the delivery layer
  *says*. The second is that every card that would naturally own it — #77, #90, #48 — is already
  `done`, and an unticked box on a closed card is a finding nobody is going to see. The measured
  numbers that opened it are in #93's Done-when table. (by @assistant)
