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
- [x] ~~A fresh rebuild from the lock files imports CBFV, catboost and sklearn without error~~
      — **true when run on 2026-08-30, and not repeatable on this machine since.** It is
      history, not a check. See the box below for what it now takes to make it one again
- [x] **The rebuild no longer reaches stage 1, the cause is permanent, and it is not a channel
      outage** (found 2026-09-03 by #10; measured 2026-09-12). `python scripts/verify_environment.py`
      fails after 26 s with `UnavailableInvalidChannel: HTTP 403 FORBIDDEN for channel pkgs/main`.
      Re-probed 2026-09-12:

      | endpoint | status |
      |---|---|
      | `repo.anaconda.com/pkgs/main/win-64/repodata.json` | **403** |
      | `repo.anaconda.com/pkgs/main/noarch/repodata.json` | **403** |
      | `conda.anaconda.org/conda-forge/win-64/repodata.json` | 200 |

      This is Anaconda refusing the request, not a transient failure and not a defect in the
      solve. Treat it as permanent for this host.

      **It is not a tail of incidental packages — the blocked channel supplies the interpreter.**
      `conda list --show-channel-urls -n Project` splits 459 packages as **211 pypi, 153
      conda-forge, 95 defaults**, and the 95 include the things nothing else can stand in for:

      | package | pinned build | from |
      |---|---|---|
      | `python` | `3.10.13=h966fe2a_0` | defaults |
      | `numpy` | `1.26.4=py310h055cbcc_0` | defaults |
      | `numpy-base` | `1.26.4=py310h65a83cf_0` | defaults |
      | `blas` | `1.0=mkl` | defaults |
      | `mkl` | `2023.1.0=h6b88ed4_46358` | defaults |
      | `mkl_fft`, `mkl_random`, `mkl-service`, `intel-openmp` | — | defaults |

      So the rebuild box above cannot be re-verified by anybody on this machine, at any effort,
      while the lock names `defaults`. **The guarantee is currently unbacked**, which matters
      more than it looks: this is the interpreter invariant, and every number the project
      reports rests on it.

      **A conda-forge re-solve is viable at the version level.** Checked against
      `conda-forge` with `--override-channels`, every critical pin exists there:

      | package | defaults build | conda-forge build |
      |---|---|---|
      | `python 3.10.13` | `h966fe2a_0` | `h4de0772_0_cpython` |
      | `numpy 1.26.4` | `py310h055cbcc_0` | `py310hf667824_0` |
      | `mkl 2023.1.0` | `h6b88ed4_46358` | `h6a75c08_46352` |

      MKL itself is on conda-forge, so the BLAS backend does **not** have to become OpenBLAS —
      it can be held with a `blas=*=mkl` / `libblas=*=*mkl` pin. What cannot be held is the rest:
      ~95 builds change, and `mkl_fft` and `mkl_random` have no conda-forge equivalent at all,
      because they are Anaconda's own numpy patches.

      **Why that is a decision and not a chore.** The manifest records package *versions*, not
      build strings and not the BLAS implementation — so a re-solved environment would report the
      same provenance as `artifacts/v2` while potentially computing differently. Changing BLAS
      reduction order is a larger perturbation than the one-ulp effects this project has already
      measured and set its `1e-12` tolerance against. That collides with two live gates: **AC-1**
      (seed reproducibility) and **AC-2** (featuriser parity to `1e-9`).

      **The project already owns the instrument to settle it empirically**, which is the reason
      not to guess: re-solve into a *throwaway* env, run AC-1, AC-2 and the suite there, and
      compare against the committed numbers. If they hold, the re-solve is free and the lock
      becomes re-runnable. If they move, that is a finding worth having explicitly rather than
      discovering later.

- [ ] **OPEN — which remedy, and who runs it.** Not a defect any more; a choice with a cost, and
      it is the maintainer's. Three options, in the order this card recommends them:

      1. **Re-solve against `conda-forge` + `nodefaults`, pinning `blas=*=mkl`, into a throwaway
         env; verify with AC-1, AC-2 and the suite before touching `environment.lock.yml`.**
         Makes the guarantee re-runnable and keeps MKL. Costs one ~8 GB / 15–20 min rebuild plus
         a gate run. Only rewrite the lock if the gates hold.
      2. **Re-verify from a host with a licensed `defaults` mirror.** Changes nothing and proves
         the existing lock. Needs a machine this project does not have.
      3. **Accept and say so.** Mark the rebuild box permanently historical and record in
         `docs/ENVIRONMENT.md` that the lock describes the env that produced the results but can
         no longer be rebuilt from scratch. Cheapest, and the least honest of the three, because
         the lock's whole purpose is to be re-runnable.

      `environment.lock.yml` **is editable** — #72 established 2026-09-12 that the freeze is a
      deny-list and that file was never on it, so option 1 is not blocked by the charter. Do not
      start the rebuild unasked: it is a long run, and option 1 is only worth it if the gate
      comparison is actually going to be read. Not an unfreeze condition.

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

- 2026-09-12: **Measured, and the finding grew.** The box read as "a channel is down, re-verify
  or re-solve". Two cheap commands changed its size: the 403 is permanent, and
  `conda list --show-channel-urls` shows **95 of 248 conda packages come from `defaults` —
  `python` and `numpy` among them**. So this was never a tail of incidental packages that could
  be swapped; the blocked channel supplies the interpreter, and the rebuild guarantee is
  unbacked rather than inconvenient.

  What kept it from being resolved on the spot is worth stating, because it is a real constraint
  and not caution: `conda-forge` has every pinned version including MKL, so a re-solve is
  genuinely viable — but the manifest records **versions**, not builds and not the BLAS
  implementation. A re-solved environment would therefore report the same provenance as
  `artifacts/v2` while possibly computing differently, and this project has already measured
  one-ulp sensitivities and set a `1e-12` tolerance against them. That is precisely the silent
  divergence the phase exists to remove, so the re-solve is gated on running AC-1 and AC-2 in a
  throwaway env and reading the comparison — a real rebuild, and the maintainer's to start.
  Left OPEN with three costed options rather than half-done. (by @assistant)
