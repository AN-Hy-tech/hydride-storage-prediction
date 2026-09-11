---
id: 22
status: done
priority: High
blocked_by: [20]
assignee: "@amirhossein"
tags: [p1, l2, R6]
---

# Featurisation throughput benchmark

**Stage S3 — Descriptor layer** · **L2 Descriptors** · Estimate: 0.5 d

> **Owns (hidden behind this module):** How many candidates per second the system can evaluate.

## Why this exists

Risk R6: NSGA-II makes far more surrogate calls than enumeration. Memo section 7 says to
measure this on day one because **it decides whether enumeration or evolution is the right
paradigm**, and it bounds how large Architecture A's grid can be.

Not a nice-to-have measurement — an input to the design of tickets 53 and 59.

## Done when

- [x] Throughput measured for batch sizes 1, 100, 10k, 100k formulae — **242 / 14,291 / 40,848
      / 44,831 formulae per second**, over *distinct* candidates, plus the curated set as its own row
- [x] Result recorded in `docs/BENCHMARKS.md` with the machine spec, the parse/arithmetic split,
      and the 13x regression it found
- [x] A candidate-budget estimate for Architecture A written from it — **a 1e6-point grid
      featurises in ~24 s and 1e7 in ~4 min, so featurisation does not bound the grid below 1e7**;
      NSGA-II's whole 100k-evaluation budget is 2.2 s. **What this does not license:** one candidate
      evaluation is featurisation *plus* the scaler, the surrogate, the conformal interval and two
      screens, none of which exists. The surrogate is almost certainly the bottleneck; re-measure at #28
- [x] If throughput is under ~1k/s at batch 10k, a note is filed against ticket 59 on feasibility
      — **not met, so no note is owed** (40,848/s, 40x above). It could not have been filed as written
      in any case: #59 is on the frozen board and `check_freeze.py` denies edits under `kanban/`, so the
      condition is carried as a **test** instead. `tests/descriptors/test_benchmark.py` fails the build
      below 1,000/s at batch 10,000, and its message says where the note goes if it ever fires

- [x] **The starting numbers, measured on the development machine while landing #20.** 10,000
      formulae in one call: **0.31 s**. The 1,278 featurisable curated rows: **0.21 s**. The
      shape of the cost is one Python pass to parse and intern the symbols, then 19 fancy-indexes
      and 19 batched reductions — so per-row cost is dominated by `parse_formula`, and a
      benchmark that does not separate parsing from arithmetic will report the parser.
      One caveat for the singleton case: a batch of **one** is deliberately computed as a
      duplicated pair (see #20's finding about arity 8), so it does twice the arithmetic of the
      smallest possible call. That is bounded and intentional; it is not a regression to optimise.
      **Amended: the starting numbers were measured over four distinct formulae repeated 2,500
      times, and they are wrong by 13x.** Ten thousand *distinct* candidates took **3.34 s**, not
      0.31 s, because the computability memo is keyed by element set and a batch of four repeats
      answered it four times instead of ten thousand. The card's own instruction is what caught it:
      "a benchmark that does not separate parsing from arithmetic will report the parser" is right
      about the principle and wrong about the culprit -- the parser is 22%, and 97% of the wall
      clock was `PropertyTable.has`, called 13.8 million times to answer nineteen questions.
      Fixed by moving the servable-element memo onto the table (`PropertyTable.servable`), which
      is where it belongs; 10k distinct now takes **0.245 s**. The singleton caveat stands and a
      second per-call cost joined it: `require_self_consistent` is **5 ms of every call**, 57% of a
      batch of one, boxed on #44

## Runnable check

```bash
python -m hydms.descriptors.benchmark --sizes 1,100,10000,100000
```

## Traces to

`docs/PRD-inverse-design.md` — R6

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: **Landed, and S3 is closed.** `hydms/descriptors/benchmark.py`,
  `tests/descriptors/test_benchmark.py`, `docs/BENCHMARKS.md`. Suite **593**, ruff 0.8.4
  and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, AC-2 still green. The card was
  budgeted at half a day for a printout and returned a **13× defect in the layer it measures**.

  **The number the project has been quoting since #20 was measured on four formulae.** `0.31 s for
  10,000` — in `featurize`'s module docstring, in #20's narrative and in three board handoffs — came
  from `["LaNi5", "TiFe", "Mg2Ni", "Ti0.8Zr0.2Mn1.4V0.2Cr0.4"] * 2500`. Ten thousand rows, **four**
  distinct compositions. Featurisation memoises the computability verdict per element *set*, so that
  batch answered it four times rather than ten thousand. Ten thousand genuinely distinct candidates
  took **3.34 s** — 2,996 formulae/s, three times the card's own feasibility floor rather than forty.

  **`cProfile` put 97% of the wall clock in one place**: `FeatureContract.computability` →
  `_servable_in` → `PropertyTable.has`, **13,767,231 calls** to answer nineteen questions. The
  servable-element set for a property was cached only for the *shipped* tables, keyed by table name —
  and `featurize._sources` always hands `computability` a resolved `tables=` mapping, so the cached
  branch was unreachable from the featuriser and the set was rebuilt for every feature of every
  candidate. The comment on the uncached branch said "that path recomputes, which is affordable
  because the only caller is a gate that runs once." Every caller was on that path.

  **Fixed where the fact lives.** `PropertyTable.servable(prop)` over a `cached_property`, and the
  two-function `_servable` pair in `contract.py` collapses to a one-line forward — one path, not a
  fast twin and a slow twin that nothing distinguished from the call site. Same batches, same
  machine: 10,000 distinct **3.3375 s → 0.2448 s (13.6×)**, 100,000 **21.03 s → 2.23 s (9.4×)**, the
  curated rows **0.1602 s → 0.0221 s (7.2×)**. The suite went 24.9 s → 17.9 s and AC-2 1.54 s → 1.28 s
  as side effects. No test changed its expected value: the verdicts are identical, they are computed
  once instead of per candidate.

  **The card's own instruction is what caught it, and it was right about the principle and wrong
  about the culprit.** "A benchmark that does not separate parsing from arithmetic will report the
  parser" — so the benchmark times `parse_formula` separately, and the parser turned out to be **22%**
  while the thing hiding behind "arithmetic" was a cache miss. The split stays in the output for the
  same reason it was asked for: it is what makes the remaining 78% a claim about numpy rather than an
  unexamined total.

  **Distinctness is now a property of the benchmark, asserted twice.** The candidates are distinct
  strings *and* distinct element sets — the second matters because the memo is keyed by the set, so
  distinct strings alone would let the workload quietly become a cache again. They are drawn from the
  curated set's own arity distribution (2–10) over the 34 elements the shipped tables can serve all 22
  features for, seeded from `pipeline.yaml`, which is what a candidate generator on the simplex
  actually produces. The curated 1,013 rows are reported as their own row because the training-matrix
  workload and the search workload are different questions.

  **The feasibility condition is carried as a test, not as a note.** The card says to file against
  ticket #59 if throughput falls under ~1k/s at batch 10k. It does not — 40,848/s — and the note could
  not have been filed as written anyway, because #59 is on the frozen board and `check_freeze.py`
  denies edits under `kanban/`. So the condition became
  `test_ten_thousand_distinct_candidates_stay_above_the_cards_floor`, whose failure message says
  where the note goes and what the cause was last time. A condition that lives in a card is checked
  when someone remembers; one that lives in the suite is checked every push.

  **What R6 now knows, and what it still does not.** A 1e6-point grid featurises in ~24 s and 1e7 in
  ~4 min, so Architecture A is not bounded by featurisation below 1e7 points, and NSGA-II's whole
  100,000-evaluation budget is 2.2 s. **Featurisation is therefore not what decides between the two
  architectures.** What decides it is unmeasured: one evaluation is featurisation *plus* the scaler,
  the surrogate, the conformal interval and two screens — #23, #26, #27, #44, #48, #49, none of which
  exists. At 22 µs per candidate, featurisation is very unlikely to be the bottleneck. That sentence
  is in `docs/BENCHMARKS.md` in bold, because the failure mode of this card's deliverable is somebody
  quoting 44,000 candidates/s as an end-to-end rate.

  **A second per-call cost, measured and boxed rather than fixed.** `require_self_consistent` re-audits
  both tables' composite columns on every call — **5 ms**, 2% of a ten-thousand batch and 57% of a
  batch of one. It does not move any number this card publishes, so it was not optimised; it is boxed
  on **#44**, where a per-candidate screen loop would make it a 200× cost, with the note that the
  audit is a pure function of (table, properties) and can be memoised the way this card memoised
  `servable`. `featurize`'s docstring no longer calls it "cheap". (by @assistant)
