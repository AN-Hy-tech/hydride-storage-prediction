"""L12 -- a row may not be weighted by its own answer.

``Catboostmodel.py:516-518``::

    combined_y_original = np.expm1(combined_y)
    # Modified weights: double weight for capacities > 3
    weights_combined = np.where(combined_y_original > 3, 2.0, 1.0)

and the same three lines again at ``:570-572``, inside every cross-validation fold. Every
metric the archival pipeline reports afterwards is a metric of a model that was told which
examples matter *because of what they measure*.

**The defect is not the number 3.** Raising it to 4, or tuning it, or deriving it from a
quantile, changes nothing about the leak: the weighting is a function of ``y``. So the
property this file asserts is a blindness rather than a bound, and the detector measures it by
perturbing the target and requiring the weights to stay exactly where they were.

This is the sentinel card #26 owed. Until it existed, `hydms.qa.sentinels.DEFERRED` recorded
the gap -- "the weighting scheme is #26's decision to make" -- and gate HG-1 could not report
green. The decision was **unweighted**, and the value of that decision is entirely in the
blindness: a constant is a function of the features, and this is what says so.

Card #71, closed by card #26.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the detector runs over a frame")

import pandas as pd  # noqa: E402
from hydms.qa import LeakDetected, assert_weights_ignore_target, for_leak  # noqa: E402

TARGET = "H2_W% (max)"
ROWS = ("a", "b", "c", "d", "e", "f")


def _frame() -> pd.DataFrame:
    """Six rows straddling 3 wt%, so the archival threshold actually separates them."""
    return pd.DataFrame(
        {
            "avg_atomic_mass": [58.7, 47.9, 24.3, 91.2, 88.9, 140.1],
            "temperature(K)": [298.0, 303.0, 573.0, 323.0, 298.0, 598.0],
            TARGET: [1.5, 2.0, 2.5, 3.5, 4.0, 5.0],
        },
        index=list(ROWS),
    )


# --------------------------------------------------------------------------------------
# The defect
# --------------------------------------------------------------------------------------


def test_the_archival_weighting_is_red() -> None:
    """The three lines above, reintroduced. This is the demonstration QA-PROTOCOL §5 requires."""
    with pytest.raises(LeakDetected) as exc:
        assert_weights_ignore_target(
            lambda frame: [2.0 if value > 3.0 else 1.0 for value in frame[TARGET]],
            _frame(),
            target_column=TARGET,
        )
    message = str(exc.value)
    assert "leak L12" in message
    assert "of 6 row(s) changed" in message, "the message must say how much of the weighting moved"
    assert "'a'" in message, "and name the rows, or the next person re-derives them"


def test_the_same_expression_over_a_feature_is_green() -> None:
    """The minimal difference: same shape, same weights, one column to the left."""
    assert_weights_ignore_target(
        lambda frame: [2.0 if value > 300.0 else 1.0 for value in frame["temperature(K)"]],
        _frame(),
        target_column=TARGET,
    )


def test_a_threshold_moved_out_of_the_way_is_still_red() -> None:
    """Retuning the threshold is the fix that is not one, and the ramp is what says so.

    9.0 is above every capacity in the frame, so this weighting is *constant* on the rows as
    given -- and it stays constant under a shuffle and a 1.5x rescale too, whose image tops
    out at 8.5. The first pass of the detector passes it. The second, which replaces the
    column with a ramp over a millionfold range, does not. This test is why that pass exists:
    it was written expecting one perturbation to be enough and it was not.
    """
    with pytest.raises(LeakDetected, match="leak L12"):
        assert_weights_ignore_target(
            lambda frame: [2.0 if value > 9.0 else 1.0 for value in frame[TARGET]],
            _frame(),
            target_column=TARGET,
        )


def test_a_weighting_keyed_on_a_quantile_of_the_batch_is_red() -> None:
    """Weighting the upper half of the target: the plausible version of the archival rule."""
    with pytest.raises(LeakDetected, match="leak L12"):
        assert_weights_ignore_target(
            lambda frame: [
                2.0 if value > frame[TARGET].median() else 1.0 for value in frame[TARGET]
            ],
            _frame(),
            target_column=TARGET,
        )


def test_a_weighting_that_reads_only_the_target_s_spread_is_red() -> None:
    """The case the rescale exists for, and the one a shuffle alone cannot see.

    Every row gets the same weight, so the weighting is invariant to which row holds which
    label -- a shuffle changes nothing. What it is not invariant to is the *scale* of the
    target, and that is the half of the first perturbation that is not the shuffle.
    """
    with pytest.raises(LeakDetected, match="leak L12"):
        assert_weights_ignore_target(
            lambda frame: [float(frame[TARGET].std())] * len(frame),
            _frame(),
            target_column=TARGET,
        )


# --------------------------------------------------------------------------------------
# Misuse is not a finding
# --------------------------------------------------------------------------------------


def test_a_missing_target_column_is_a_caller_error_not_a_pass() -> None:
    """A check against a column that is not there passes vacuously, which is the leak's shape."""
    with pytest.raises(ValueError, match="passing vacuously|pass vacuously"):
        assert_weights_ignore_target(
            lambda frame: [1.0] * len(frame),
            _frame().drop(columns=[TARGET]),
            target_column=TARGET,
        )


def test_a_non_numeric_target_is_refused() -> None:
    frame = _frame()
    frame[TARGET] = frame[TARGET].astype(str)
    with pytest.raises(ValueError, match="cannot be perturbed numerically"):
        assert_weights_ignore_target(
            lambda f: [1.0] * len(f), frame, target_column=TARGET
        )


def test_an_empty_frame_is_refused() -> None:
    with pytest.raises(ValueError, match="no rows"):
        assert_weights_ignore_target(
            lambda f: [], _frame().iloc[:0], target_column=TARGET
        )


def test_a_weighting_that_returns_the_wrong_shape_is_a_caller_error() -> None:
    """Not a leak: a detector that cries L12 when it was misused is one nobody will believe."""
    with pytest.raises(ValueError, match="not the length of the batch|weight\\(s\\) for"):
        assert_weights_ignore_target(
            lambda f: [1.0, 1.0], _frame(), target_column=TARGET
        )
    with pytest.raises(ValueError, match="not a number"):
        assert_weights_ignore_target(
            lambda f: ["heavy"] * len(f), _frame(), target_column=TARGET
        )


# --------------------------------------------------------------------------------------
# The real weighting
# --------------------------------------------------------------------------------------


@pytest.mark.leak
def test_the_project_weighting_cannot_see_the_target() -> None:
    """`hydms.surrogate.model.sample_weights`, run rather than read.

    The function slices the frame to the declared features in its first statement, so the
    target is unreachable from anything below it -- the same guard `select_features` uses for
    leak L6. This asserts the consequence rather than the statement.
    """
    from dataclasses import replace
    from functools import partial

    from hydms.surrogate.model import ModelSettings, sample_weights

    # The real settings with `features` pointed at this frame's two columns, and nothing else
    # changed. The subject is the function, not the feature list it happens to be given.
    settings = replace(
        ModelSettings.from_config(), features=("avg_atomic_mass", "temperature(K)")
    )
    assert_weights_ignore_target(
        partial(sample_weights, settings=settings), _frame(), target_column=TARGET
    )


@pytest.mark.leak
def test_l12_is_registered_and_no_longer_deferred() -> None:
    """The gap card #26 closed. HG-1 counts deferrals as honest incompleteness, not coverage."""
    from hydms.qa.sentinels import DEFERRED

    sentinel = for_leak("L12")
    assert sentinel is not None, "L12 has a sentinel now; #26 is the card that owed it"
    assert sentinel.subject == "hydms.surrogate.model"
    assert sentinel.detector == "hydms.qa.detectors.assert_weights_ignore_target"
    assert sentinel.live is not None, "a sentinel pointed at a miniature guards nothing"
    assert "L12" not in {entry.leak for entry in DEFERRED}
