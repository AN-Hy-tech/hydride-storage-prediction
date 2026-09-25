---
id: 84
status: backlog
priority: Normal
blocked_by: [82]
assignee: "@amirhossein"
tags: [ph, l6, S10]
---

# Batch CSV screening page

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The many-candidates journey, and the guarantee that a batch cannot launder a refusal into a number.

## Why this exists

A researcher with a list of candidate compositions should not paste them one at a time.
The risk a batch path introduces is that refusals become invisible: a spreadsheet of numbers with a few
blank cells reads as a spreadsheet of numbers.

Every row carries its own verdict out, and the download carries the same columns the single-prediction
path shows on screen. A downloaded result with no interval column would be the exact failure this phase
was built to prevent, one export away.

## Done when

- [ ] Upload a CSV of compositions and temperatures; a documented row limit; a schema error names
      the offending row
- [ ] **An empty formula cell is refused before it is parsed, and `NaN` in that column is the
      trap** (added 2026-09-07 by #49's QA pass). A CSV is exactly where a blank cell becomes a
      string: pandas gives `np.nan` or `pd.NA` depending on dtype, `str(pd.NA)` is `<NA>` — which
      ElMD read as nitrogen until #49 cross-checked it — and **`"NaN"` written literally is a
      valid formula to every parser here**, sodium and nitrogen. Such a row would be answered
      with a capacity, an interval and a novelty distance and would look like a result. Refuse
      null and blank cells on read, name the row, and count them in the refusal summary. #76
      carries the same box for the single-prediction path
- [ ] Every output row carries the estimate, the interval, the domain verdict and the ElMD distance
- [ ] Refused rows are present in the output, marked as refused with their reason — never dropped and
      never blank
- [ ] A summary states how many rows were refused and why, before the user downloads anything
- [ ] The download includes the artifact version
- [ ] Results are sortable by interval width, so the least certain rows can be found

- [ ] **A missing cell must not reach the formula column as text, and `"NaN"` is why**
      (added 2026-09-11 by #76). #76 measured every spelling of a missing value at the prediction
      path: each object null (`None`, `nan`, `pd.NA`, `pd.NaT`) is refused before a parser sees it,
      and each stringified null (`"nan"`, `"<NA>"`, `"None"`, `"NaT"`, `"N/A"`) is refused by the
      grammar. **One survives and cannot be guarded downstream: `"NaN"` parses to sodium and
      nitrogen in both parsers**, featurises to real numbers, and would be answered with a confident
      capacity, an interval and a novelty distance. It is indistinguishable from chemistry *once it
      is a string*, so the only place it can be caught is here — this card chooses how the CSV is
      read. State the `na_values` decision explicitly and test it with a file whose missing-value
      token is `NaN`: `df.to_csv(na_rep="NaN")` is a real export and this is the file it produces.
      Do **not** solve it by refusing the string; that refuses a real material

- [ ] **A CSV of thousands cannot go through `POST /v1/predict/batch`, and the fix is not a
      cleverer page** (added 2026-09-12 by #78). Measured on the deployed `v2`: one served
      prediction costs **66–78 ms** and splits 13 ms featurise / 22 ms surrogate / 34 ms screens.
      There is no hot spot, and none of it is *work* — it is per-call pandas overhead on a one-row
      frame, paid three times per candidate — so the cost is **linear in the rows with nothing
      amortised**, and #78's limit of 256 rows (~19 s) is what that arithmetic permits at the
      transport. A 2,000-row upload is ~2.5 minutes of HTTP request. Decide here how this page
      screens a real file, and the honest options are a batched call in the **library** (one
      featurise, one surrogate call, one `apply_screens` pass over N rows, which is what the
      screens were built for — see `hydms.screens.protocol`'s "called once per batch") or chunked
      requests with visible progress. **Not** a bigger `max_batch_rows`: the limit is a timeout
      budget, not a preference

      **2026-09-26, decided (architecture grilling): the batched call in the library.**
      `predict_many(requests, bundle)` in `hydms.delivery.predict` becomes the evaluator's
      primary path, named to match `ServiceClient.predict_many` and the batch route. Then
      `predict_capacity` is its one-row case. `FeaturisationError` gains the offending row labels
      **as data**, so a bad formula refuses only its own row with the featuriser's sentence: no
      pre-parse, which would duplicate the grammar, and no per-row fallback, which would bring
      back the cost. The route calls `predict_many` once. The limit stays **256** until this card
      re-measures, then it is set from that number. Acceptance: for every row, `predict_many(xs)[i]`
      equals `predict_capacity(xs[i])` to 1e-12, and the test includes duplicate formulas in one
      batch

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_batch.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S10

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
