"""AC-1 -- the same seed reproduces identical metrics.

PRD section 10.1: the pipeline runs end to end from the raw data with one command, with no
absolute paths, and re-running with the same seed reproduces identical metrics.

What is re-run, and what is not
-------------------------------

**The deployed fit, twice.** :func:`~hydms.surrogate.deploy.deployed_fit` is the whole sequence
a shipped model is made by -- screen, carve, fit, calibrate -- and every stochastic step in this
project lives inside it or upstream of it: card #13's split, CleanLab's screen, the group-aware
carve, the early-stopping slice and CatBoost's own sampling. Running it twice and demanding the
same numbers is what this criterion asks.

**Not the hyperparameter search.** The nested run that *chooses* the configuration costs about
1 h 41 m, and running it twice would put three and a half hours in a lane nobody would then
run. This gate fits at the configuration ``reports/model/model-chosen.csv`` already records --
:func:`~hydms.surrogate.deploy.deployed_params`, the same reading ``calibrate --save`` makes --
so what it establishes is that *the model this project ships* is reproducible, and it says so
rather than implying more. Optuna's sampler is seeded from the same ``seed``; that half of the
claim is guarded by ``tests/surrogate/test_model.py`` and not here.

The thread count, which was an open question and is now a measurement
----------------------------------------------------------------------

``model.FIXED`` pins ``grow_policy``, ``bootstrap_type``, ``task_type``, ``verbose`` and
``allow_writing_files`` -- **not** ``thread_count``, so CatBoost takes every core it finds.
Card #32 asked whether that made this criterion unanswerable across machines, since the slow
lane runs on ``windows-latest`` and the maintainer's machine has twenty cores.

**Measured on 2026-09-06, on the real deployed configuration over the real matrix.** Fitting at
``thread_count`` 1, 4 and 20 gave the same 2,584 trees, the same best iteration 2583, the same
conformal correction ``+0.037355`` and a bit-identical head matrix over all 1,279 rows -- so
every metric agreed to the last digit. Under ``Lossguide`` with a Bayesian bootstrap, this
fit *is* thread-invariant.

Two consequences, and they are the whole of card #32's decision:

  - **``thread_count`` does not join ``FIXED``.** Pinning it would change nothing measurable
    while capping the parallelism of a 1 h 41 m run, and it would not buy cross-machine
    determinism anyway -- the instruction set is not something a parameter pins.
  - **This gate varies it rather than holding it constant**, because the stronger claim is now
    free: the two runs below differ in thread count *and* must still agree exactly. A gate that
    held it constant would pass on a machine where the property had quietly stopped holding.

Why the tolerance is zero
--------------------------

Everywhere else this project compares floats with a tolerance, because it has measured one-ulp
effects it will not pretend are absent. Here the criterion **is** bit-identity: "reproduces
identical metrics" is not a claim about being close. The measurement above says the bar is
reachable, so a nonzero gap is a finding about a newly-introduced nondeterminism, not a
rounding residue -- and the result names the metric and both values so it can be chased.

Owned by card #32.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Final

from hydms.config import Config

from ._core import Gate, GateResult, Speed

__all__ = ["GATE", "THREAD_COUNTS", "TOLERANCE"]

#: Identical means identical. See the module docstring.
TOLERANCE: Final = 0.0

#: The two fits this gate compares, by thread count. One thread and every core, because the
#: measurement that licensed varying it at all spanned exactly that range -- and because a
#: single-threaded CatBoost is the one configuration that cannot be accused of getting the same
#: answer by scheduling luck.
THREAD_COUNTS: Final = (1, None)

#: The split the metrics are computed on. The same one AC-3 scores, for the same reason: it is
#: the only split neither fit was shaped by.
HELD_OUT: Final = "test"


@dataclass(frozen=True)
class SeedReproducibility:
    """The gate. It fits two models and compares what they are worth, never their bytes."""

    name: str = "AC-1"
    title: str = "Same seed reproduces identical metrics"
    card: int = 32
    speed: Speed = Speed.SLOW

    def check(self, cfg: Config) -> GateResult:
        try:
            import catboost  # noqa: F401
        except ImportError as error:
            return GateResult.skip(
                self.name,
                f"CatBoost is not installed in this interpreter ({error}), so there is no fit "
                f"to repeat. This gate belongs to the slow lane, where the training extra is "
                f"installed: `conda run -n Project python -m hydms.gates run AC-1`.",
            )

        from hydms.surrogate.conformal import calibrated_heads
        from hydms.surrogate.deploy import deployed_fit, deployed_params
        from hydms.surrogate.model import ModelSettings, capacity_matrix, quantile_metrics
        from hydms.surrogate.train import REPORTS

        settings = ModelSettings.from_config(cfg)
        params, provenance = deployed_params(cfg.paths.reports / REPORTS)
        frame, split = capacity_matrix(cfg, settings=settings)
        rows = list(frame.index[split == HELD_OUT])
        if not rows:
            return GateResult.fail(
                self.name,
                f"the split assigns no row to {HELD_OUT!r}, so there is no metrics table to "
                f"compare. It holds {sorted(split.unique())}.",
                measured="0 rows",
                threshold=TOLERANCE,
            )

        truth = frame.loc[rows, cfg.columns.target]
        runs: list[dict[str, Any]] = []
        for threads in THREAD_COUNTS:
            chosen = dict(params or {})
            if threads is not None:
                chosen["thread_count"] = threads
            fit = deployed_fit(frame, split, params=chosen, settings=settings, config=cfg)
            heads = calibrated_heads(fit.model, frame.loc[rows], conformal=fit.conformal)
            runs.append(
                {
                    "threads": threads if threads is not None else os.cpu_count(),
                    "metrics": quantile_metrics(truth, heads, fit.model.quantiles),
                    "correction": float(fit.conformal.correction),
                    "trees": int(fit.model.record.trees),
                    "best_iteration": int(fit.model.record.best_iteration),
                    "grown_on": len(fit.model.record.fitted),
                    "calibration": len(fit.calibration),
                }
            )

        first, second = runs
        differences = _differences(first, second)
        scope = (
            f"Two runs of hydms.surrogate.deploy.deployed_fit at seed {settings.seed}, "
            f"configuration from {provenance}, scored on {len(rows)} row(s) of "
            f"{HELD_OUT!r}. The runs differ in thread count -- "
            f"{first['threads']} against {second['threads']} -- which card #32 measured to be "
            f"a free strengthening: this fit is thread-invariant, so `thread_count` stays out "
            f"of model.FIXED and this gate varies it instead of pinning it. "
            f"Seeded: card #13's split, the CleanLab screen, the calibration carve, the "
            f"early-stopping slice and CatBoost's own sampling. Not established here: the "
            f"hyperparameter search that chose the configuration, which costs 1 h 41 m and is "
            f"read from disk rather than repeated."
        )

        if differences:
            worst = max(gap for _, _, _, gap in differences)
            return GateResult.fail(
                self.name,
                f"{len(differences)} number(s) moved between two runs at the same seed:\n"
                + "\n".join(
                    f"  {name}: {a!r} then {b!r} (gap {gap:.6e})"
                    for name, a, b, gap in sorted(differences, key=lambda d: -d[3])
                )
                + f"\nSomething in the fit is not seeded, or is not invariant to the thread "
                f"count. {scope}",
                measured=worst,
                threshold=TOLERANCE,
            )

        reported = first["metrics"]
        return GateResult.ok(
            self.name,
            "every metric is identical across the two runs: "
            + ", ".join(f"{name} {value:.6f}" for name, value in sorted(reported.items()))
            + f"; conformal correction {first['correction']:+.6f}; "
            f"{first['trees']} trees, best iteration {first['best_iteration']}, grown on "
            f"{first['grown_on']} row(s) with {first['calibration']} carved for calibration. "
            f"Compared on the metrics table and the fit's own record, never on model bytes, "
            f"which may legitimately differ. {scope}",
            measured=0.0,
            threshold=TOLERANCE,
        )


def _differences(
    first: dict[str, Any], second: dict[str, Any]
) -> list[tuple[str, Any, Any, float]]:
    """Every number that moved, as ``(name, first, second, gap)``.

    The metrics *and* the fit's own record -- tree count, best iteration, row counts -- because
    a fit that stopped at a different iteration and still scored the same is reproducible by
    accident, and AC-1 is not a claim about luck.
    """
    moved: list[tuple[str, Any, Any, float]] = []
    for name in sorted(first["metrics"]):
        a, b = float(first["metrics"][name]), float(second["metrics"][name])
        if a != b and not (a != a and b != b):  # NaN == NaN is the one legitimate 'same'
            moved.append((name, a, b, abs(a - b)))
    for name in ("correction", "trees", "best_iteration", "grown_on", "calibration"):
        a, b = first[name], second[name]
        if a != b:
            moved.append((name, a, b, abs(float(a) - float(b))))
    return moved


GATE: Gate = SeedReproducibility()
