# Featurisation throughput

**Card #22 · PRD risk R6.** How many candidate compositions this project can turn into a feature
matrix per second, measured rather than assumed, because it is an input to a design decision and
not a vanity number: NSGA-II makes far more surrogate calls than enumeration, so the cost of one
evaluation is what decides whether Architecture A's grid or Architecture B's population is the
affordable shape. The inverse-design memo §7 says to measure it on day one.

Reproduce it:

```bash
conda run -n Project python -m hydms.descriptors.benchmark --sizes 1,100,10000,100000
```

The numbers below are a **dated measurement on one machine**, not a contract. What is enforced is
the floor: `tests/descriptors/test_benchmark.py` fails the build below **1,000 formulae/s at batch
10,000**, which is the card's own feasibility condition and ~40× under what this machine does. It
is a regression detector — a slow CI runner is allowed, a lost cache is not.

---

## 2026-09-04

```
Windows-10-10.0.26200-SP0 · Intel64 Family 6 Model 154 Stepping 3, GenuineIntel
Python 3.10.13 · numpy 1.26.4 · 22 feature columns · best of 3 runs
```

| batch | formulae/s | µs/formula | total (s) | parse (s) | arithmetic (s) | parse share |
|---|---:|---:|---:|---:|---:|---:|
| synthetic 1 | 242 | 4,138.3 | 0.0041 | 0.0000 | 0.0041 | 0% |
| synthetic 100 | 14,291 | 70.0 | 0.0070 | 0.0005 | 0.0065 | 7% |
| synthetic 10,000 | 40,848 | 24.5 | 0.2448 | 0.0531 | 0.1917 | 22% |
| synthetic 100,000 | 44,831 | 22.3 | 2.2306 | 0.5544 | 1.6762 | 25% |
| curated 1,013 | 45,926 | 21.8 | 0.0221 | 0.0062 | 0.0159 | 28% |

**What the rows are.** `synthetic N` is N **distinct** compositions drawn from the curated set's own
arity distribution (2–10 elements) over the 34 elements the shipped tables can serve every one of
the 22 features for — the workload a candidate generator on the composition simplex produces.
`curated` is the real 1,279 rows less the 266 the shipped tables refuse (`dev_Gordy_electonegativity`,
#19) — the training-matrix workload, which is a different question. Without that one feature the 21
that remain featurise all **1,278 rows in 0.026 s**.

**Why distinctness is the whole design of this benchmark.** Featurisation memoises the computability
verdict per element *set*, so tiling four formulae up to ten thousand rows measures the memo. That is
what the figure this file replaces was doing — see [The 13× that was hiding](#the-13-that-was-hiding).

**The batch of one is per-*call* overhead, not per-formula cost.** 4.1 ms, of which **5 ms of every
call**, at any size, is `require_self_consistent` re-auditing both tables' composite columns (#18's
guard, and it is what stops a descriptor being silently zero for caesium and gadolinium). It is 2% of
a ten-thousand-candidate batch and 57% of a batch of one. A second, smaller share is the pandas frame
construction. **Featurise in batches.** The consequence for a per-candidate screen was boxed on #44,
and #44 answered it structurally: `hydms.screens.Screen.verdict` takes a frame, there is no
single-candidate entry point, and `apply_screens` calls each screen **exactly once** per run
whatever the batch size (asserted at 1, 10 and 1,000 rows). What that still cannot see is a screen
that loops *internally*, which is why `Verdicts.durations` reports per-screen wall clock.

---

## What this means for R6

**Featurisation does not decide between Architecture A and Architecture B.** At ~41,000 candidates
per second:

| workload | candidates | featurisation |
|---|---:|---:|
| NSGA-II, population 200 × 500 generations | 100,000 | **2.2 s** |
| NSGA-II, population 500 × 1,000 generations | 500,000 | ~12 s |
| Architecture A, a 1e6-point grid | 1,000,000 | ~24 s |
| Architecture A, a 1e7-point grid | 10,000,000 | ~4 min |

So Architecture A's grid is not bounded by featurisation below ~1e7 points, and Architecture B's
whole evaluation budget is seconds. The card's condition — *under ~1k/s at batch 10k, file a note
against ticket 59 on feasibility* — **is not met, and no note is owed.** (It could not have been
filed as written in any case: #59 is on the frozen board and `scripts/check_freeze.py` denies edits
under `kanban/`. If this floor is ever breached, the note belongs here and in the runbook.)

**What is still unmeasured, and it is the half that matters.** These figures cover
`hydms.descriptors.featurize` only. One candidate evaluation is featurisation **plus** a scaler
transform, a CatBoost MultiQuantile prediction, a conformal interval and two screens — cards #23,
#26, #27, #44, #48 and #49. **Only #44 exists** (2026-09-04) — the screen contract and one window,
whose cost is a column comparison, so nothing here has moved. Featurisation at 22 µs/candidate is very
unlikely to be the bottleneck; the surrogate almost certainly is. **Nothing in this file licenses a
claim about candidates per second end to end.** Re-measure when #28's `predict()` lands, and put the
number here beside this one.

---

## The 13× that was hiding

This section is the finding, and it is the reason the card was worth its half-day.

The starting figures — **10,000 formulae in 0.31 s**, quoted by #20's narrative, `featurize`'s module
docstring and three board handoffs — were measured over
`["LaNi5", "TiFe", "Mg2Ni", "Ti0.8Zr0.2Mn1.4V0.2Cr0.4"] * 2500`: ten thousand rows carrying **four**
distinct compositions. Re-run over ten thousand distinct ones, the same call took **3.34 s**, or
2,996 formulae/s — three times the card's feasibility floor rather than forty.

`cProfile` put **97% of the wall clock** in one place: `FeatureContract.computability` →
`_servable_in` → `PropertyTable.has`, **13.8 million calls** to answer nineteen questions. The
servable-element set for a property was cached only when the *shipped* table was used, keyed by table
name, and `featurize` always passed a resolved `tables=` mapping — so the cached branch was
unreachable from the featuriser and the set was rebuilt from scratch for every feature of every
candidate. Four distinct compositions hid it perfectly: the verdict memo in `_require_computable` is
keyed by element set, so the cost was paid four times instead of ten thousand.

The fix moves the memo onto the table, where the set belongs
(`PropertyTable.servable`, a `cached_property` over a frozen dataclass), and deletes the two-branch
`_servable` pair in `contract.py`. One path, no fast twin and slow twin that nobody could tell apart.
Measured effect, same machine, same batches:

| batch | before | after | speed-up |
|---|---:|---:|---:|
| synthetic 10,000 | 3.3375 s | 0.2448 s | **13.6×** |
| synthetic 100,000 | 21.0275 s | 2.2306 s | 9.4× |
| curated 1,013 | 0.1602 s | 0.0221 s | 7.2× |

The whole test suite went from 24.9 s to 17.9 s as a side effect, and AC-2 from 1.54 s to 1.28 s.

**The lesson is about the benchmark, not the cache.** A hot spot that costs 97% of a call survived
cards #16, #19 and #20 — three cards with 208 tests over this layer between them — because every
measurement of it used a batch that was mostly repeats. `tests/descriptors/test_benchmark.py`
asserts the candidates are distinct *and* that their element sets are, so the workload cannot quietly
become a cache again.
