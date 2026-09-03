---
id: 11
status: done
priority: Normal
blocked_by: [9]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# Target transform module

**Stage S2 — Data layer** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the modelled target is log1p(wt%) and how to get back to wt%.

## Why this exists

The target is `log1p(H2_W% (max))`, inverse `expm1`. That pairing is currently spread
across the pipeline, and `REPORT.md` 7.3 already flags that SHAP values were reported in log
space by mistake. One module owning both directions makes that error structurally hard to
repeat.

## Done when

- [x] `to_model_space(wt_pct)` and `to_wt_pct(model_value)` are the only transform entry points
- [x] Round-trip property test holds to floating tolerance across the data range
- [x] Docstring states which `REPORT.md` metrics are in which space
- [x] **The transform is `log1p`, and it is measured, not inferred.** `hydride_prefeaturizing.csv`'s
      `log_H2_W% (max)` equals `numpy.log1p` of `H2_W% (max)` elementwise on all 1279 rows, and
      `Machine_Model/src/log_transform_target.py:35` is where it was applied. It is **not**
      `log(10y)` and **not** `log1p(10y)`; both were checked and both are wrong. So the inverse is
      `expm1`, and the round-trip test has a known answer to hold it to (found by #9)
- [x] **Compute the log target, never join it from `hydride_prefeaturizing.csv`.** That file is
      row-for-row aligned with `hydride_data.csv` — verified elementwise on formula and temperature
      for all 1279 rows — but *only* positionally: there is no key to join it on, because
      `(Composition, temperature(K))` is not unique on either file (1279 rows, 1272 distinct pairs;
      see #10). Reading the column across would be leak L9 in a new place. Since #9 measured the
      transform to be exactly `log1p`, `to_model_space` recomputes it and the file becomes a
      fixture to check against, not a source (found by #10)
- [x] **"Equals `numpy.log1p` elementwise" is true to one ulp, not bitwise, and the difference
      is the file rather than the transform.** Measured over all 1279 rows: the published column
      agrees with `log1p` of the target to at most **4.44e-16** but is bit-identical on only
      1005 rows against `numpy.log1p` and 866 against `math.log1p` — `log_transform_target.py:59`
      wrote it with `to_csv`, so it round-tripped through decimal text. Two further one-ulp
      effects compound: `math.log1p` and `numpy.log1p` differ by up to 1.11e-16, and
      `expm1(log1p(y))` returns `y` exactly on only 794 of 1279 rows. So `ROUND_TRIP_TOLERANCE`
      is 1e-12 and **nothing in this project may compare two target vectors with `==`** — the
      three candidates that were ruled out are wrong by more than 2.0, so no tolerance this
      loose can confuse them
- [x] **The module uses `math`, not `numpy`, and the cost is one ulp.** NumPy cannot be
      imported anywhere under `hydms/` while mypy runs outside the `Project` environment
      (`pyproject.toml`, `[tool.mypy]`); the descriptor layer owns the real fix. Since every
      caller comes through these two functions, one implementation is used everywhere and AC-1's
      bit-for-bit reproducibility is unaffected
- [x] **A named `Series` carries its space in its name.** `H2_W% (max)` in, `log_H2_W% (max)`
      out, and back again; transforming a `log_`-prefixed column refuses rather than producing
      `log_log_`. That is the structural half of "hard to repeat" — the REPORT §7.3 error is a
      column whose values are in log space and whose heading says weight percent, and this module
      cannot produce one. `hydms.data.load.prefeaturized_schema` now takes its heading from
      `model_space_name`, so the `log_` contract is spelled once

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/data/test_target.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-03: Box added by #10. `hydride_prefeaturizing.csv` can only be aligned to
  `hydride_data.csv` positionally — the two are row-for-row identical on formula and temperature,
  but `(Composition, temperature(K))` is not a unique key on either (1279 rows, 1272 distinct
  pairs), so there is nothing to join on. The transform is recomputed, and the file is a fixture
  to check against rather than a source. (by @assistant)

- 2026-09-03: Landed. `hydms/data/target.py` — `to_model_space`, `to_wt_pct`,
  `model_space_name` and the tolerance they imply; 27 tests in `tests/data/test_target.py`.
  Three things this card taught:

  **The card's own assertion needed loosening, and the reason is the file.** "Equals
  `numpy.log1p` elementwise on all 1279 rows" is true to 4.44e-16 and false bitwise on 274 of
  them. The published column was written by `to_csv` and read back through decimal text, so it
  is a *rendering* of the transform rather than the transform. That is a third, independent
  reason not to join the column across — #10 gave the first (no key) and #9 the second (the
  loader normalises nothing) — and it is why the golden test uses a tolerance. Written into the
  module docstring, because a tolerance with no measurement behind it is a number somebody will
  tighten.

  **A constant caught the same effect on itself.** `MODEL_SPACE_RANGE`'s lower bound was first
  written from a NumPy probe as `0.09531017980432493`; the scalar test went red against
  `math.log1p`'s `0.09531017980432487`. One ulp, in a literal, exactly the gap the docstring
  describes. Kept as a literal for that reason.

  **Which published metric is in which space is now written down, and one of them cannot be.**
  Read off the archival code: §4.2's CV R² column is log space (`cross_validate` on `y_train`,
  `benchmark_model_selection.py:1093`), every `*_Orig` column is weight percent
  (`evaluate_model(..., 'orig')` applies `expm1` first, `:946-949`), §4.3's bootstrap CI is
  weight percent (`:1194-1196`), §6.1's SHAP is log space. §4.2's footnote therefore defines
  its Overfitting column across two spaces — that is a ninth disagreement and went to #89.
  (by @assistant)
