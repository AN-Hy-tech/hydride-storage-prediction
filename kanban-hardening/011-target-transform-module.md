---
id: 11
status: backlog
priority: Normal
blocked_by: [9]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# Target transform module

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the modelled target is log1p(wt%) and how to get back to wt%.

## Why this exists

The target is `log1p(H2_W% (max))`, inverse `expm1`. That pairing is currently spread
across the pipeline, and `REPORT.md` 7.3 already flags that SHAP values were reported in log
space by mistake. One module owning both directions makes that error structurally hard to
repeat.

## Done when

- [ ] `to_model_space(wt_pct)` and `to_wt_pct(model_value)` are the only transform entry points
- [ ] Round-trip property test holds to floating tolerance across the data range
- [ ] Docstring states which `REPORT.md` metrics are in which space
- [ ] **The transform is `log1p`, and it is measured, not inferred.** `hydride_prefeaturizing.csv`'s
      `log_H2_W% (max)` equals `numpy.log1p` of `H2_W% (max)` elementwise on all 1279 rows, and
      `Machine_Model/src/log_transform_target.py:35` is where it was applied. It is **not**
      `log(10y)` and **not** `log1p(10y)`; both were checked and both are wrong. So the inverse is
      `expm1`, and the round-trip test has a known answer to hold it to (found by #9)
- [ ] **Compute the log target, never join it from `hydride_prefeaturizing.csv`.** That file is
      row-for-row aligned with `hydride_data.csv` — verified elementwise on formula and temperature
      for all 1279 rows — but *only* positionally: there is no key to join it on, because
      `(Composition, temperature(K))` is not unique on either file (1279 rows, 1272 distinct pairs;
      see #10). Reading the column across would be leak L9 in a new place. Since #9 measured the
      transform to be exactly `log1p`, `to_model_space` recomputes it and the file becomes a
      fixture to check against, not a source (found by #10)

## Runnable check

```bash
python -m pytest tests/data/test_target.py -q
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
