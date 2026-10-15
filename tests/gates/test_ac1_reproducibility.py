"""Card #32 — the reproducibility gate, and the decision it is built on.

The decision first, because the gate is shaped by it. ``model.FIXED`` pins no ``thread_count``,
and card #32 asked whether that left AC-1 unanswerable on a machine with a different core count
from the maintainer's. It was measured rather than argued: the deployed configuration fitted at
1, 4 and 20 threads produced the same 2,584 trees, the same best iteration, the same conformal
correction and a bit-identical head matrix over all 1,279 rows. So ``thread_count`` stays out of
``FIXED`` — pinning it would change nothing while capping a 1 h 41 m run's parallelism — and the
gate **varies** it instead, which makes the claim stronger for free.

What is tested here, and where
-------------------------------

The comparison logic is tested directly: it decides what "identical" means, it has to treat a
moved tree count as seriously as a moved R², and none of that needs a booster. The gate itself
fits two real models and is marked ``slow`` for the same reason it is declared ``Speed.SLOW`` —
it belongs to the lane that can afford three minutes, and a fast-lane test of it would be a
three-minute fast lane.
"""

from __future__ import annotations

import math

import pytest
from hydms.gates import Speed, Status
from hydms.gates.ac1_seed_reproducibility import (
    GATE,
    THREAD_COUNTS,
    TOLERANCE,
    _differences,
)

pytestmark = pytest.mark.gate


def _run(**overrides):
    run = {
        "threads": 20,
        "metrics": {"r2": 0.7070641667962626, "interval_coverage": 0.7795275590551181},
        "correction": 0.03735492530223672,
        "trees": 2584,
        "best_iteration": 2583,
        "grown_on": 701,
        "calibration": 172,
    }
    run.update(overrides)
    return run


# --------------------------------------------------------------------------------------
# What the gate declares
# --------------------------------------------------------------------------------------


def test_it_is_a_slow_lane_gate_owned_by_card_32() -> None:
    assert GATE.speed is Speed.SLOW
    assert GATE.card == 32
    assert GATE.name == "AC-1"


def test_the_two_runs_differ_in_thread_count() -> None:
    """The decision, pinned. If someone re-pins the thread count, this goes red and says why."""
    assert 1 in THREAD_COUNTS
    assert None in THREAD_COUNTS, "one run must take every core the machine has"
    assert len(set(THREAD_COUNTS)) == 2


def test_thread_count_is_not_in_the_fixed_parameters() -> None:
    """The other half of card #32's decision, asserted where a future edit would trip on it.

    Adding ``thread_count`` to ``FIXED`` would change the fitted model and silently override
    what this gate varies, leaving it comparing a run against itself.
    """
    from hydms.surrogate.model import FIXED

    assert "thread_count" not in FIXED


def test_identical_means_identical() -> None:
    assert TOLERANCE == 0.0


# --------------------------------------------------------------------------------------
# What counts as a difference
# --------------------------------------------------------------------------------------


def test_two_runs_that_agree_have_no_differences() -> None:
    assert _differences(_run(), _run()) == []


def test_a_moved_metric_is_named_with_both_values_and_the_gap() -> None:
    moved = _differences(_run(), _run(metrics={"r2": 0.70, "interval_coverage": 0.7795275590551181}))
    assert [name for name, *_ in moved] == ["r2"]
    _name, first, second, gap = moved[0]
    assert (first, second) == (0.7070641667962626, 0.70)
    assert gap == pytest.approx(0.0070641667962626, abs=1e-15)


@pytest.mark.parametrize(
    "field", ["correction", "trees", "best_iteration", "grown_on", "calibration"]
)
def test_the_fits_own_record_is_compared_not_only_its_score(field: str) -> None:
    """A fit that stopped elsewhere and scored the same is reproducible by accident.

    AC-1 is not a claim about luck, so the tree count, the stopping iteration and the row
    accounting are compared beside the metrics.
    """
    original = _run()[field]
    moved = _differences(_run(), _run(**{field: original + 1}))
    assert [name for name, *_ in moved] == [field]


def test_two_nan_metrics_are_the_same_number_here() -> None:
    """``r2`` is NaN when the truth has no variance, and NaN != NaN would report that as drift."""
    nan = {"r2": float("nan")}
    assert _differences(_run(metrics=nan), _run(metrics=nan)) == []


def test_a_metric_that_became_nan_is_a_difference() -> None:
    moved = _differences(_run(metrics={"r2": 0.7}), _run(metrics={"r2": float("nan")}))
    assert [name for name, *_ in moved] == ["r2"]
    assert math.isnan(moved[0][3])


# --------------------------------------------------------------------------------------
# The gate itself
# --------------------------------------------------------------------------------------


@pytest.mark.slow
def test_the_deployed_fit_reproduces_itself_across_thread_counts() -> None:
    """Two real fits, about three minutes. The lane this gate is declared for.

    Not a duplicate of the measurement in the module docstring: that one established the
    property once, this one is what keeps establishing it after every change to the fitting
    path.
    """
    pytest.importorskip("catboost", reason="the deployed fit is CatBoost's")
    pytest.importorskip("mapie", reason="the band is MAPIE-calibrated; `pip install -e .[uq]`")
    from hydms.config import load

    result = GATE.check(load())
    assert result.status is Status.PASSED, result.message
    assert result.measured == 0.0
    assert "thread-invariant" in result.message
