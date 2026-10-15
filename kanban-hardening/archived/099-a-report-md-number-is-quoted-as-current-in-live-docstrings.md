---
id: 99
status: done
priority: P1
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l7]
---

# A REPORT.md number is quoted as current in live docstrings

**Stage S8 — Evidence and close** · **L7 Prose** · Estimate: 0.25 d

> **Owns (hidden behind this module):** That a number written into production prose describes the
> evidence this project has, not the evidence it replaced.

**This card is NOT an unfreeze condition.** It was found on 2026-09-12 by #81, which measured the
claim before implementing the chart that makes it.

## Why this exists

*"Only 39 test rows sit above 500 K"* appears in **three** production docstrings under `hydms/`,
in two test docstrings, and in two card paragraphs. (A fourth `hydms/` hit,
`hydms/figures/charts.py`, quotes the sentence in order to correct it and is not a site.) It traces to `REPORT.md:394` — *"where training samples are sparse
(n = 39)"* — which is a count over the **archival pipeline's 247-row test split**.

That split no longer exists. The group-aware nested protocol (#88) scores every row out of fold,
and the committed evidence is `reports/model/model-out-of-fold.csv`: **893 scored rows, 130 of them
above 500 K.** The counts were measured on 2026-09-12; `TemperatureSupport.above(500.0)` is what
measures them, and `tests/test_figures.py` asserts both.

**The claim is fine; the number is not.** 39/247 is 15.8% and 130/893 is 14.6%, so every sentence
these docstrings are making — coverage inside the trained range is badly uneven, the temperature
window is an outer bound, the learned applicability domain is what closes the gap — stays exactly
as true. What is wrong is that a reader checking the figure against the repository finds no 39
anywhere in it, and CLAUDE.md's own anti-pattern list names this shape: *"Quoting REPORT.md's
scores as current performance."*

**Where it stands.** Sites found by `grep -rn "39 test rows\|n = 39"`:

| File | What it is |
|---|---|
| `hydms/config/__init__.py:203` | production docstring |
| `hydms/data/screening.py:73` | production docstring |
| `hydms/screens/window.py:38` | production docstring |
| `tests/conftest.py:97` | fixture docstring |
| `tests/test_metamorphic.py:313` | test docstring |
| ~~`docs/PHASE-H-RUNBOOK.md:1152`~~ | S7's description of #81 — **corrected 2026-09-12 by #81**, which is the card that measured it |
| `kanban-hardening/044-*.md:104` | card prose — *"coverage inside is uneven (39 test rows above 500 K)"* |
| `kanban-hardening/README.md` (the #44 summary) | card prose, same sentence |

`REPORT.md` itself is **not** on this list and must not be edited: it is the archival record, the
freeze denies it, and it is corrected *beside* rather than in place — which is #89's job.

## Done when

- [x] Every site above states the measured figure and names what it was measured over. Not a bare
      number: "130 of 893 scored out-of-fold rows" says which evidence, and that is the property
      the old sentence lacked
- [x] Each site says where the number comes from, so the next session re-measures rather than
      re-types — `TemperatureSupport.above()` over `reports/model/model-out-of-fold.csv`
- [x] The card prose and the runbook are struck through rather than overwritten where the old
      number was load-bearing to an argument, the way #81's own *Done when* does it
- [x] `grep -rn "39 test rows" hydms/ tests/ docs/ kanban-hardening/` returns nothing that reads as
      a current fact
- [x] Nothing under `REPORT.md` or `Machine_Model/` is touched

## Runnable check

```bash
grep -rn "39 test rows" hydms/ tests/ docs/ kanban-hardening/
conda run -n Project python -m pytest tests/test_figures.py
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8; `CLAUDE.md` — Session anti-patterns

## Narrative

- 2026-10-15: Closed. Re-measured before writing, not copied from this card: `tests/test_figures.py`
  asserts `support.rows == 893` and `support.above(500.0) == 130` over the committed
  `reports/model/model-out-of-fold.csv`, and passes. The five code sites now say "130 of the 893
  scored out-of-fold rows" and name what measures it; the #44 card's sentence is struck through
  with the correction beside it. The README's #44 summary no longer carries the sentence, so it
  needed no edit. What `grep -rn "39 test rows"` still returns is the sentence *quoted in order to
  correct it* (`hydms/figures/charts.py`, #81, this card), which is not a site. (by @assistant)
- 2026-09-12: Filed by #81, which was told by its own card that "only 39 test rows sit above 500 K"
  and measured the premise before building the chart that reports it. The number was not wrong when
  it was written; it was inherited across a change of protocol that removed the thing it counted.
  That is the failure mode a constant in prose always has and a measurement never does, which is
  why `hydms.figures.charts.TemperatureSupport` takes counts rather than carrying one — the chart
  is now immune to this card, and the docstrings around it are not. (by @assistant)
