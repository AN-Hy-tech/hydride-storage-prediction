---
id: 84
status: done
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

- [x] Upload a CSV of compositions and temperatures; a documented row limit; a schema error names
      the offending row
- [x] **An empty formula cell is refused before it is parsed, and `NaN` in that column is the
      trap** (added 2026-09-07 by #49's QA pass). A CSV is exactly where a blank cell becomes a
      string: pandas gives `np.nan` or `pd.NA` depending on dtype, `str(pd.NA)` is `<NA>` — which
      ElMD read as nitrogen until #49 cross-checked it — and **`"NaN"` written literally is a
      valid formula to every parser here**, sodium and nitrogen. Such a row would be answered
      with a capacity, an interval and a novelty distance and would look like a result. Refuse
      null and blank cells on read, name the row, and count them in the refusal summary. #76
      carries the same box for the single-prediction path
- [x] Every output row carries the estimate, the interval, the domain verdict and the ElMD distance
- [x] Refused rows are present in the output, marked as refused with their reason — never dropped and
      never blank
- [x] A summary states how many rows were refused and why, before the user downloads anything
- [x] The download includes the artifact version
- [x] Results are sortable by interval width, so the least certain rows can be found

- [x] **A missing cell must not reach the formula column as text, and `"NaN"` is why**
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

- [x] **A CSV of thousands cannot go through `POST /v1/predict/batch`, and the fix is not a
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

**2026-09-26, where each box landed.** `tests/delivery/test_batch.py` (34 tests) plus four
AppTest runs of the page in `tests/delivery/test_app_script.py`.

| Box | Where | Pinned by |
|---|---|---|
| Upload, row limit, schema error | `hydms/delivery/batch.py` `read_upload`: `MAX_UPLOAD_ROWS = 10_000` (about 10 s in three requests). A file-level defect raises `UploadError` naming the column. A row-level one makes the row `unread`, and its sentence starts `row N:` | `test_a_schema_error_is_refused_whole_and_says_what`, `test_a_malformed_row_is_unread_and_named_while_the_rest_are_asked`, `test_the_row_limit_is_documented_and_enforced` |
| Empty cell before the parser | The standard-library `csv` reader turns nothing into anything. A cell in `MISSING_TOKENS` is `unread`, and the test proves every token fails `parse_formula` | `test_every_spelling_of_a_missing_formula_is_unread_before_any_parser_sees_it`, `test_no_missing_token_is_a_formula_so_reading_one_as_missing_refuses_no_material` |
| `NaN` | **Decision: ambiguous, and the caller decides.** `read_upload` lists the rows and `requests()` refuses until `nan_means` is `missing` or `formula`. The page asks with a radio button that has no default. The string is not refused, which would refuse sodium nitride, and it is not answered, which would answer a blank cell | `test_a_file_written_with_na_rep_nan_is_not_answered_as_sodium_nitride` (the file comes from `df.to_csv(na_rep="NaN")`), `test_nan_is_answered_as_chemistry_when_the_caller_says_so`, `test_the_batch_page_asks_what_nan_means_before_asking_the_model` |
| Estimate, interval, verdict, ElMD | `batch.COLUMNS`. An answered row carries capacity, lower, upper, width, level, domain code and reason, ElMD distance and nearest alloy | `test_an_answered_row_carries_estimate_interval_verdict_and_distance` |
| Refused rows present, never blank | One output row per input row, in order. A refused or unread row writes its status word into **every number column**, and an empty input cell echoes as `(empty)` | `test_every_uploaded_row_comes_back_in_order_and_none_is_blank`, `test_a_refused_row_says_refused_where_every_number_would_be` |
| Summary before download | `Screening.summary()`: refused by code, unread by cause with row numbers, and blank lines skipped. The page draws it above the table and the download | `test_the_summary_counts_refusals_by_reason_before_anything_is_downloaded`, `test_the_batch_page_screens_a_file_and_says_what_happened_first` |
| Artifact version | A `model_version` column on every row, and `hydms-screening-<version>.csv`. `screening()` refuses answers from another version | `test_the_download_carries_the_version_on_every_row_and_in_its_name` |
| Sortable by width | `Screening.ordered(by_width=True)`: widest first, and rows with no interval after all answered rows. The page has a toggle | `test_the_widest_interval_comes_first_and_rows_without_one_come_last` |
| `predict_many` | `hydms.delivery.predict.predict_many`. `predict_capacity` is its one-row case, and the route calls it once. `FeaturisationError.rows` carries each offender's own sentence, and parse failures and holes come in **one** raise, so the retry is one call and not a loop. `MAX_BATCH_ROWS` was re-measured and set to **4,096** (see below) | `test_every_row_of_a_batch_is_what_the_lone_call_says_about_it` (1e-12, duplicates included), `test_a_batch_is_featurised_and_predicted_once_not_once_a_row` (featurise calls `[10, 6]`, predict `[6]`), `test_the_batch_route_answers_each_row_as_the_single_route_does` |

**The re-measurement** (`v3`, the curated corpus's own pairs, best of three, the development
machine). Alone, `predict_capacity` costs **41 ms/row**. `predict_many` costs 0.91 ms/row at 256
rows and **0.83 ms/row at 1,279**. The route, end to end with JSON both ways, costs 0.27 s at 256
rows, 1.00 s at 1,024, **3.05 s at 4,096** and 5.64 s at 8,192. Time is no longer the binding
limit; the response is, at 1.1 KB a row. 4,096 rows is 3 s and a 4.5 MB body, a tenth of the
60 s budget. Recorded in `service.MAX_BATCH_ROWS`'s comment and `docs/BENCHMARKS.md`.

**Three consequences outside the card, handled.** (0) Gate HG-2 went red: it reads every `return` in `predict_capacity`, and the delegation was neither contract type. It now reads `predict_capacity`, `predict_many` and `_answer`, and checks what `predict_many` stores (#77's narrative). (1) The unreadable-formula refusal now carries
the row's own sentence ("the formula could not be parsed: 'LaNi5Xx2' names 'Xx', …"). Before, it
carried the batch's account ("1 of 1 formula(e) … ['candidate'] … a batch that silently returns
fewer rows …"). `docs/REFUSALS.md` was re-emitted, and `docs/API.md` re-probed against `v3`.
(2) At 4,096 rows the `batch-too-large` example would have committed 16,000 lines of identical
JSON. It is now stored shortened with `candidates_total` beside it, as the parity response
already was.

**What this card does not fix: #94.** One row whose band comes back crossed raises
`ContractError` from `Interval`. Since #84 that fails the whole `predict_many` call, so it fails
a batch request, as the route loop did before. The page catches the resulting `ServiceError` and
says the batch failed, never showing the rows either side. Whether a crossing should be a refusal
is #94's decision, and the finding is recorded there.

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_batch.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S10

## Narrative

- 2026-09-26: Done. The architecture grilling's decision held once it was built, with one
  refinement. The featuriser used to raise on parse failures *before* checking holes, so a batch
  holding both kinds would have needed two retries. It now reports both kinds in one raise, and
  `predict_many` featurises at most twice per batch, whatever is wrong with it. The measurement
  surprised in the other direction. The card expected the batch to amortise the cost; it took
  the cost out almost entirely, 41 ms to 0.83 ms a row. That moved the batch limit's binding
  constraint from time to response size. `NaN` was settled by refusing to guess: the reader
  surfaces it and the caller says which, because both readings are real. `AppTest` cannot drive
  an upload, so the page tests hand the script a file by patching `st.file_uploader`. The script
  itself ran against the fixture service. (by @assistant)
- 2026-09-02: Created for Phase H (by @assistant)
