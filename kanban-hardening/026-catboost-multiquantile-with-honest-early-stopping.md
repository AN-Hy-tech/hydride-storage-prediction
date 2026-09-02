---
id: 26
status: backlog
priority: High
blocked_by: [23, 25, 88]
assignee: "@amirhossein"
tags: [p1, l3, S2, R4]
---

# CatBoost MultiQuantile with honest early stopping

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** The capacity model and its quantile heads.

## Why this exists

Two changes from the archived model.

First, **the leak**: `Catboostmodel.py:605` calls `fit(combined_pool, eval_set=test_pool,
early_stopping_rounds=5000)` — early stopping on the **test** set. Here early stopping uses
validation, and test is touched once, at the end.

Second, **quantiles**: `MultiQuantile` with alpha 0.1 / 0.5 / 0.9 so the model emits an
interval, not a point. This is what makes LCB ranking possible.

## Done when

- [ ] `loss_function='MultiQuantile:alpha=0.1,0.5,0.9'`
- [ ] **`use_best_model=True`** — CatBoost validates at fit time that `eval_set` is non-empty, which
      makes the guard mechanical rather than a convention
- [ ] Early stopping on the validation split; the test split is not passed to `fit`
- [ ] A test asserting the test split is never referenced during training
- [ ] The quantile **column order** is asserted in a test — position is the only thing identifying
      P10 / P50 / P90
- [ ] Folds come from ticket 88's protocol; no fold is both tuned on and scored on
- [ ] Optuna search space ported from the archived script, selection on validation score only
- [ ] Training is CPU-only (`MultiQuantile` has no GPU support) and the runtime is recorded for the
      slow lane's budget
- [ ] The **L1 sentinel** and the **L5 sentinel** (ticket 71) are wired to this module — `live`
      checks in `hydms/qa/sentinels.py` calling `hydms.qa.assert_early_stopping_is_honest` with the
      real `eval_set` and scored-row identities, once for the final fit and once per fold. Gate HG-1
      goes red once `hydms/surrogate/model.py` exists without them
- [ ] **L12 has no sentinel and this card owes one.** `Catboostmodel.py:516-518` set
      `weights = np.where(np.expm1(y) > 3, 2.0, 1.0)` — sample weights conditioned on the target,
      with a hand-tuned threshold. Whatever weighting scheme this card chooses, add the
      **L12 sentinel** to `hydms/qa/sentinels.py`: weights must be a function of the training rows'
      own features and of nothing else. Until it exists, HG-1 cannot report green

## Runnable check

```bash
python -m hydms.surrogate.train --target capacity && python -m pytest tests/surrogate/test_no_test_leak.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S2, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-08-30: **API check before implementation.** `loss_function="MultiQuantile:alpha=0.1,0.5,0.9"`
  returns one column per alpha, **in the order given in the string** — position is the only thing
  identifying P10/P50/P90, so that order deserves an explicit assertion in a test rather than a
  comment. `use_best_model=True` is validated at fit time to require a non-empty `eval_set`, which
  is the mechanical guard this card wants against the audit's early-stopping-on-test leak: the
  honest `eval_set` is the validation split. Note `MultiQuantile` is one of the few regression
  losses with **no GPU support**, so this trains CPU-only — relevant to the slow lane's runtime
  budget. Details in `docs/LIBRARY-APIS.md`. (by @assistant)

- 2026-09-02: Amended for Phase H. Blocked on 88 as well: fixing the early-stopping-on-test leak (L1) without
  fixing fold reuse (L4) and row-level folds (L7) would still report a tuning optimum as a held-out
  score. The `use_best_model=True` requirement is what turns the guard from a convention into a
  fit-time error (by @assistant)
