---
id: 1
status: backlog
priority: High
blocked_by: []
assignee: "@amirhossein"
tags: [p0, l0, S1, AC-1]
---

# Pin and lock the Project conda environment

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The exact interpreter and package versions every later result depends on.

## Why this exists

The audit found the default interpreter (`C:\Python313`, numpy 2.5.2) is **not** the
environment that produced the existing reports. That environment is conda `Project`
(Python 3.10.13, numpy 1.26.4, CBFV 1.1.0, catboost 1.2.8, sklearn 1.6.1, pandas 2.3.1).

Running the pipeline under 3.13 + numpy 2.x would very likely break on removed NumPy 2.0
aliases. Pin it before anyone writes code against the wrong interpreter.

## Done when

- [ ] `environment.yml` exports the full `Project` env with exact versions
- [ ] `environment.lock.yml` records the resolved solve for byte-identical recreation
- [ ] `docs/ENVIRONMENT.md` states which interpreter to use and why 3.13 is excluded
- [ ] A fresh `conda env create` from the lockfile imports CBFV, catboost and sklearn without error

## Runnable check

```bash
conda env create -f environment.lock.yml -n hydms-verify && conda run -n hydms-verify python -c "import CBFV, catboost, sklearn, numpy; print(numpy.__version__)"
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
