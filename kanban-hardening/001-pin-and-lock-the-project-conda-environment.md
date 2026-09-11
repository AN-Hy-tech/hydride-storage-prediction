---
id: 1
status: done
priority: High
blocked_by: []
assignee: "@amirhossein"
tags: [p0, l0, S1, AC-1]
---

# Pin and lock the Project conda environment

**No stage — slots in where its blockers allow** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The exact interpreter and package versions every later result depends on.

## Why this exists

The audit found the default interpreter (`C:\Python313`, numpy 2.5.2) is **not** the
environment that produced the existing reports. That environment is conda `Project`
(Python 3.10.13, numpy 1.26.4, CBFV 1.1.0, catboost 1.2.8, sklearn 1.6.1, pandas 2.3.1).

Running the pipeline under 3.13 + numpy 2.x would very likely break on removed NumPy 2.0
aliases. Pin it before anyone writes code against the wrong interpreter.

## Done when

- [x] `environment.yml` exports the `Project` conda packages with exact versions (248)
- [x] `environment.lock.yml` records the resolved solve, build strings included
- [x] **`requirements-lock.txt` holds the 208 pip packages** — added to this card, see Narrative
- [x] `docs/ENVIRONMENT.md` states which interpreter to use and why 3.13 is excluded
- [x] A fresh rebuild from the lock files imports CBFV, catboost and sklearn without error
- [ ] **The rebuild no longer reaches stage 1 on this machine.** Run 2026-09-03 while working #10:
      `python scripts/verify_environment.py` fails after 26 s with
      `UnavailableInvalidChannel: HTTP 403 FORBIDDEN for channel pkgs/main`. That is Anaconda's
      `defaults` channel refusing the request, not a defect in the solve — but the lock lists
      `defaults` alongside `conda-forge`, so the rebuild claim above depends on a channel this
      machine cannot currently reach. Either re-verify from a host that can, or re-solve the lock
      against `conda-forge` with `nodefaults` so the guarantee is one the project can actually
      re-run. Until then the box above is history, not a check anybody can repeat (found by #10)

## Runnable check

```bash
python scripts/verify_environment.py
```

Rebuilds a throwaway env from both lock files and imports the packages the pipeline cannot run
without. Roughly 8 GB and 15-20 minutes, so it is a by-hand check after touching an environment
file — deliberately not in CI, where it belongs to the slow lane at best.

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-08-30: Every version the audit asserted was confirmed by direct query: Python 3.10.13,
  numpy 1.26.4, pandas 2.3.1, sklearn 1.6.1, catboost 1.2.8, CBFV 1.1.0. No corrections needed.

- 2026-08-30: **Deliverables amended — one lock file became two.** The card assumed a single
  `environment.lock.yml` could recreate the environment. It provably cannot, and the acceptance
  test is what caught it. Two separate defects, in order:

  1. `conda env export` writes `python-graphviz==0.20.3` into the `pip:` section. That name only
     exists on conda-forge; PyPI calls it `graphviz`. The package was conda-installed then
     pip-overwritten, so conda's metadata kept the conda name while flagging the channel `pypi_0`,
     and the export trusted the name over the channel. Hand-corrected. Since each attempt costs a
     full re-solve to discover, all 208 pip entries were then audited against what pip actually
     has installed rather than fixing one and hoping — exactly one was wrong.
  2. With that fixed, the rebuild failed again on `ResolutionImpossible`. The 208 pip pins
     accreted incrementally over the project's life; the environment works, but its pins were
     never simultaneously solvable and pip's resolver refuses a set it cannot prove consistent.
     Re-exporting cannot fix this — the conflict is in the environment, not in how it was
     written down.

  The fix is to stop asking pip to resolve at all: a lockfile is already the resolved closure, so
  `--no-deps` installs exactly the pinned set. `--no-deps` is not a valid directive inside a
  requirements *file*, so it cannot live in conda's `pip:` block. That constraint is what forces
  the split into `environment.lock.yml` (248 conda) + `requirements-lock.txt` (208 pip). Verified
  end to end: conda create exit 0, pip --no-deps exit 0, imports clean at numpy 1.26.4 /
  pandas 2.3.1 / sklearn 1.6.1.

- 2026-08-30: Finding for card #2 — this environment carries 462 packages and 8.2 GB, including
  the entire removed N8N web stack (`fastapi`, `uvicorn`, `asyncpg`, `boto3`, `bcrypt`, `dash`).
  It is pinned as-is deliberately: the lockfile's job is to reproduce the published numbers, not
  to be tidy. The narrow runtime dependency set belongs in card #2's `pyproject.toml`, and once
  the pipeline runs from that and reproduces the metrics, this becomes the historical record
  rather than the working environment. (by @assistant)

- 2026-09-03: Reopened box, not reopened card. `scripts/verify_environment.py` was run as part of
  #10's document pass — the runbook's section 5 lists it — and it now fails at stage 1 with an
  HTTP 403 from `repo.anaconda.com/pkgs/main`. Nothing in the repository changed; the channel did.
  Recorded here rather than fixed in passing because re-solving a lock file is this card's work and
  invalidates `environment.lock.yml`, which several other cards depend on. (by @assistant)
