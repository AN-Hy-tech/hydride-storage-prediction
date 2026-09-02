---
id: 14
status: backlog
priority: High
blocked_by: [13]
assignee: "@amirhossein"
tags: [p1, l1, S1]
---

# CleanLab screening as a data-layer stage

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** Which **training** rows are label-suspect, and the record of
> what was removed. Held-out labels are not this module's to touch.

## Why this exists

The audit's fourth broken link: `Boruta_FeatEng.py:23-25` reads `data/splits/` — the
**pre-CleanLab** splits — while its own comment claims it reads managed data. The effective
pipeline bypassed CleanLab entirely, contradicting `README.md` step 4 and `REPORT.md` 3.2.

The domain memo supplies the physics: sloping plateaus make measured capacity depend on
measurement pressure, and pressure is absent from the dataset. That is a better account of
what CleanLab detects than 'some experiments are wrong'.

**Amended for Phase H — scope narrowed, and this is the important part of the ticket.** The archival
`CleanLab.py` does not remove rows. At `:90`, reached for validation and test at `:96-97`, it does this:

```python
managed_df['target'] = np.where(outliers_mask, y_pred, y)
```

**Every held-out label whose residual exceeds the threshold is replaced by the model's own
prediction.** Points so replaced have residual exactly zero by construction, so any R² or RMSE computed
downstream is measured partly against synthetic targets. That is leak **L3**, and it is more severe
than any of the three the PRD names. It is inert today only because nothing reads `CleanLab.py`'s
output — and this ticket, as originally written, is the one that would have wired it in.

So: this stage may **drop or reweight training rows only**. Validation and test targets are immutable
as they pass through it. Porting the `manage_outliers` behaviour is not in scope and would be a defect.

## Done when

- [ ] Feature selection (24) consumes CleanLab's output, closing the bypass
- [ ] **The stage drops or reweights training rows only** — no label is ever rewritten, on any split
- [ ] **Validation and test targets are byte-identical before and after this stage** — asserted, and
      covered by the L3 sentinel in ticket 71
- [ ] Held-out **feature** values are byte-identical too. The recovered `Outliers_Management.py:60-72`
      clipped val/test features using their own residuals — leak L10, the same defect on the other
      side of the table. If this stage grows any outlier handling, that is where it comes back
- [ ] The **L3 sentinel** and the **L10 sentinel** (ticket 71) are wired to this module — `live`
      checks in `hydms/qa/sentinels.py` calling `hydms.qa.assert_holdout_unchanged` on the real
      stage, once for `y` and once for `X`. Gate HG-1 goes red once `hydms/data/screening.py` exists
      without them
- [ ] Removed rows written to a report with their residuals, not silently dropped
- [ ] Counts recorded per split for the Chapter 1 revision (37)
- [ ] Module docstring records the counter-caution: removing real measurements in underrepresented regimes flatters metrics

## Runnable check

```bash
python -m pytest tests/data/test_clean.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Amended for Phase H. The audit found `CleanLab.py:90` overwrites validation and test ground-truth
  labels with the model's own predictions (leak L3) — worse than any leak the PRD names, and inert only
  because its output is an orphan. This ticket was the one that would have connected it. Scope is now
  explicitly drop-or-reweight, training rows only (by @assistant)
