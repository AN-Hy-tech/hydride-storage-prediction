# Environment

**Use the conda environment `Project`. Do not use the machine's default Python.**

Every number in `REPORT.md` was produced under `Project`. Running the pipeline under anything
else does not reproduce them, and in the case of the default interpreter does not run at all.

| | `Project` (correct) | Machine default (wrong) |
|---|---|---|
| Python | 3.10.13 | 3.13 |
| NumPy | 1.26.4 | 2.x |

## Why 3.13 is excluded

NumPy 2.0 removed a batch of long-deprecated aliases (`np.float_`, `np.unicode_`, `np.NaN`, the
`np.object`/`np.bool`/`np.int` spellings) and changed scalar promotion rules. The scientific stack
this pipeline pins to — CBFV 1.1.0 in particular, unmaintained since 2022 — predates that break.

This is not a preference. CBFV computes **every descriptor in the model**, and PRD §7.2 records
that it "will break under NumPy 2.x" as one of the reasons the featuriser is being reimplemented.
Until that reimplementation lands and passes AC-2, the 1.26.x pin is load-bearing.

## Verified contents

Confirmed by direct query on 2026-08-30, not copied from documentation:

| Package | Version |
|---|---|
| python | 3.10.13 |
| numpy | 1.26.4 |
| pandas | 2.3.1 |
| scipy | 1.15.2 |
| scikit-learn | 1.6.1 |
| catboost | 1.2.8 |
| CBFV | 1.1.0 |
| cleanlab | 2.7.1 |
| optuna | 4.1.0 |
| shap | 0.46.0 |
| matminer | 0.9.3 |
| pymatgen | 2024.11.13 |
| Boruta | 0.4.3 |

## Files

Recreation is **two stages**: conda first, then pip. This is not a stylistic choice — a
single-file `conda env create` provably cannot rebuild this environment, for the reason in
*Why two stages* below.

| File | What it is | Stage |
|---|---|---|
| `environment.yml` | 248 conda packages, exact versions, no build strings | 1 — different OS or architecture |
| `environment.lock.yml` | 248 conda packages with build strings — the resolved solve | 1 — same platform |
| `requirements-lock.txt` | 212 pip packages, exact versions | 2 — both cases |

All have the machine-local `prefix:` line stripped; it records wherever the exporting machine
happened to keep its envs, and conda ignores it on create.

```bash
# Stage 1 — conda
conda env create -f environment.lock.yml -n Project

# Stage 2 — pip, WITHOUT dependency resolution (see below; --no-deps is required)
conda run -n Project python -m pip install --no-deps -r requirements-lock.txt

# Stage 3 — the project itself, editable
conda run -n Project python -m pip install -e .

# Verify the parts that matter
conda run -n Project python -c "import CBFV, catboost, sklearn, numpy; print(numpy.__version__)"

# Run anything in it
conda run -n Project python scripts/spike_feature_provenance.py --check-all-22
```

The whole rebuild takes about 7 minutes with a warm package cache and appreciably longer cold;
`scripts/verify_environment.py` runs stages 1-2 and the import check in one command.

> **It does not currently complete on this machine, and the reason is not fixable by retrying.**
> Stage 1 dies after ~26 s with `UnavailableInvalidChannel: HTTP 403 FORBIDDEN for channel
> pkgs/main` — Anaconda refusing `defaults`, re-confirmed 2026-09-12 (`pkgs/main` 403,
> `conda-forge` 200). This is not an incidental tail: **95 of the 248 conda packages come from
> `defaults`, including `python` itself (`3.10.13=h966fe2a_0`), `numpy`
> (`1.26.4=py310h055cbcc_0`) and the whole MKL stack.** So the lock describes the environment
> that produced the published results and **cannot presently be rebuilt from scratch** by
> anyone here. Every pinned version — MKL included — does exist on `conda-forge`, so a re-solve
> against `conda-forge` + `nodefaults` with `blas=*=mkl` is viable, but ~95 builds would change
> and `mkl_fft`/`mkl_random` have no equivalent there. Because the manifest records versions
> rather than builds or BLAS, a re-solved env would claim identical provenance while possibly
> computing differently — which is why the remedy is gated on running AC-1 and AC-2 in a
> throwaway env first. The options and their costs are the open box on card #1.

**`hydms` itself must never enter the lock files.** Once `pip install -e .` has been run,
`pip freeze` reports it as `-e git+https://…#egg=hydms`. A regenerated `requirements-lock.txt`
would carry that line and make the environment depend on cloning itself. Delete it after any
regeneration.

## Why two stages

Exporting the pip packages inside the conda file's `pip:` block — which is what
`conda env export` does by default — produces a file that **fails every time**:

```
ERROR: Cannot install ... because these package versions have conflicting dependencies.
ERROR: ResolutionImpossible
CondaEnvException: Pip failed
```

The 209 pip packages accreted incrementally over the life of the project. The environment works,
but its pins were never simultaneously solvable, and pip's modern resolver refuses to install a
set it cannot prove consistent. Re-exporting will not help; the conflict is in the environment
itself, not in how it was written down.

The fix is to stop asking pip to resolve. **A lockfile is already the complete resolved closure**,
so re-deriving it is both unnecessary and, here, impossible — `--no-deps` installs exactly the
pinned set and nothing else. That flag is not a valid directive inside a requirements *file*, so it
cannot live in the conda `pip:` block; it has to be a separate command, which is what forces the
split.

Consequences:

- **Both stages are mandatory.** Stage 1 alone yields an environment with no CBFV, no CatBoost and
  no scikit-learn — they are all pip packages here.
- Because nothing is resolved at install time, `requirements-lock.txt` must stay complete. Adding a
  package by hand means adding its dependencies by hand too. Prefer regenerating both files from a
  working environment over editing them.

`environment.lock.yml` pins build strings, so it is platform-specific by design. On a different
OS the solve will fail and `environment.yml` is the file to use — accepting that a different
build of the same version is not bit-identical.

## Known export defect — read this before re-exporting

**`requirements-lock.txt` carries a hand-applied fix. Regenerating it will silently undo it.**

The raw export writes `python-graphviz==0.20.3` among the pip packages. That name only exists on
conda-forge; the PyPI distribution is called `graphviz`. Pip cannot resolve it, so the conda stage
succeeds, the pip stage dies at the very end, and the install fails with:

```
ERROR: Could not find a version that satisfies the requirement python-graphviz==0.20.3
       (from versions: none)
CondaEnvException: Pip failed
```

The cause is a package that was conda-installed and later pip-overwritten. `conda list` still shows
conda's name while marking the channel `pypi_0`, and the export trusts the name over the channel:

```
python-graphviz   0.20.3   pypi_0   pypi      <- conda's view, wrong name
Name: graphviz                                 <- pip's view, correct name
```

The line now reads `graphviz==0.20.3` in both files. **After any re-export, re-apply it**, and check
whether the same class of error has appeared elsewhere — one mis-filed name is enough to fail the
whole create, and each attempt costs a full re-solve to discover. To find them all in one pass,
compare every pip-section name against what pip actually has installed:

```bash
conda run -n Project python -c "import re,importlib.metadata as md; \
n=lambda s:re.sub(r'[-_.]+','-',s).lower(); \
have={n(d.metadata['Name']) for d in md.distributions() if d.metadata['Name']}; \
L=[l.split('==')[0] for l in open('requirements-lock.txt',encoding='utf-8').read().splitlines() \
   if l and not l.startswith('#')]; \
print('misfiled:', [p for p in L if n(p) not in have] or 'none')"
```

Against the corrected file it reports `none`. Run before the fix, it found exactly one entry out
of 208 — a useful reminder that a single bad name is the difference between a lockfile that
recreates and one that does not.

## Known problem: this environment is polluted

`Project` carries **462 dependency lines**, roughly 8.2 GB on disk. A large fraction has nothing
to do with the ML pipeline: `fastapi`, `uvicorn`, `asyncpg`, `aiosmtplib`, `boto3`, `bcrypt`,
`argon2-cffi` and `dash` are all still installed. They are leftovers from the N8N prediction
service that was removed from the repository in commit `63127e5`.

**This is pinned deliberately and should not be cleaned up yet.** The lockfile's job is to record
what actually produced the published results, not what a tidy environment would have looked like.
Removing packages now would mean the pin no longer reproduces the numbers it exists to reproduce.

The right place to fix it is the package scaffold (card #2): `pyproject.toml` declares what
`hydms` actually *needs*, which will be a small fraction of this. Once the pipeline runs from that
declaration and reproduces the metrics, this environment becomes the historical record rather than
the working one, and a narrow runtime environment replaces it.

Consequences to be aware of until then:

- The CI slow lane (card #7) pays this recreation cost on every retrain. That is a reason to keep
  the fast lane free of conda entirely, which is what card #68 does.
- More packages means more solve conflicts. If `conda env create` fails on a fresh machine, try
  `environment.yml` before assuming the pin is broken.
