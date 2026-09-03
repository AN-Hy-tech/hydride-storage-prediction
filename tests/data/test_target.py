"""L1 -- the target transform and the two spaces it moves between. Card #11.

Four questions, and they are different:

  - **Which transform is it?** The card says ``log1p``. That is checked against the
    published ``log_H2_W% (max)`` column over all 1279 rows, together with the three
    candidates that were ruled out -- ``log(y)``, ``log1p(10y)`` and ``log(10y)`` -- so the
    answer is demonstrated rather than asserted.
  - **How exact is it?** Not bit-exact, in three independent ways, and each one is measured
    here rather than trusted from the module docstring. This is the test that would notice
    if :data:`~hydms.data.target.ROUND_TRIP_TOLERANCE` were tightened past what the data
    supports.
  - **Does the name carry the space?** A ``Series`` that goes into model space comes back
    with ``log_`` on its heading, and a second transform refuses. That renaming is the
    structural half of what this module is for.
  - **The failure path.** Every unusable value raises and the message names every offending
    row, not the first. ``docs/QA-PROTOCOL.md`` section 4.1.
"""

from __future__ import annotations

import math

import pytest

pytest.importorskip("pandas", reason="the data layer is pandas frames end to end")

import pandas as pd  # noqa: E402  -- only importable once the skip above has passed
from hydms.config import load as load_config  # noqa: E402
from hydms.data.load import (  # noqa: E402
    load_hydride_data,
    load_prefeaturized,
    prefeaturized_schema,
)
from hydms.data.target import (  # noqa: E402
    MODEL_SPACE_PREFIX,
    MODEL_SPACE_RANGE,
    ROUND_TRIP_TOLERANCE,
    WT_PCT_RANGE,
    TargetError,
    model_space_name,
    to_model_space,
    to_wt_pct,
)

TARGET = "H2_W% (max)"


@pytest.fixture(scope="module")
def published() -> tuple[pd.Series, pd.Series]:
    """The raw target and the published log column, in file order.

    Positional alignment is the only alignment these two files have -- there is no key to
    join them on (card #10) -- which is precisely why the transform is recomputed and this
    column is a fixture rather than a source.
    """
    names = load_config().columns
    raw = load_hydride_data()[names.target]
    log = load_prefeaturized()[model_space_name(names.target)]
    assert len(raw) == len(log) == 1279
    return raw, log


# --------------------------------------------------------------------------------------
# Which transform is it
# --------------------------------------------------------------------------------------


def test_the_transform_is_log1p_measured_against_the_published_column(published) -> None:
    raw, log = published
    difference = (to_model_space(raw).to_numpy() - log.to_numpy())
    assert abs(difference).max() < ROUND_TRIP_TOLERANCE


@pytest.mark.parametrize(
    ("name", "candidate"),
    [
        ("log(y)", lambda y: math.log(y)),
        ("log1p(10y)", lambda y: math.log1p(10 * y)),
        ("log(10y)", lambda y: math.log(10 * y)),
    ],
)
def test_the_three_transforms_that_were_ruled_out_are_wrong_by_more_than_two(
    published, name, candidate
) -> None:
    """Each is off by over 2.0 in absolute terms -- not a near miss, and not a tolerance
    question. Without this, "the transform is log1p" is a claim with nothing behind it."""
    raw, log = published
    worst = max(abs(candidate(value) - reference) for value, reference in zip(raw, log, strict=True))
    assert worst > 2.0, f"{name} is closer to the published column than it should be"


# --------------------------------------------------------------------------------------
# How exact is it
# --------------------------------------------------------------------------------------


def test_the_round_trip_holds_across_the_published_range(published) -> None:
    raw, _ = published
    back = to_wt_pct(to_model_space(raw))
    assert (back - raw).abs().max() < ROUND_TRIP_TOLERANCE
    assert back.name == raw.name


def test_the_round_trip_holds_on_a_sweep_of_the_whole_range() -> None:
    """The data covers its range unevenly; a sweep covers it evenly, including the ends."""
    low, high = WT_PCT_RANGE
    sweep = pd.Series([low + (high - low) * i / 500 for i in range(501)], name=TARGET)
    assert (to_wt_pct(to_model_space(sweep)) - sweep).abs().max() < ROUND_TRIP_TOLERANCE


def test_the_round_trip_is_not_bit_exact_which_is_why_a_tolerance_exists(published) -> None:
    """Measured: 794 of 1279 rows return exactly, the rest within 2.7e-15.

    If this ever goes red the arithmetic has become exact, and the docstring's counts and
    :data:`~hydms.data.target.ROUND_TRIP_TOLERANCE` should be re-measured rather than the
    assertion relaxed. Nothing may compare two target vectors with ``==``.
    """
    raw, _ = published
    back = to_wt_pct(to_model_space(raw))
    assert not back.equals(raw)
    assert (back - raw).abs().max() < 1e-14


def test_the_published_column_is_decimal_text_not_the_transform_itself(published) -> None:
    """``log_transform_target.py:59`` wrote it with ``to_csv``, so it round-tripped through
    decimal. It agrees to a ulp and no further, which is why the golden test above uses a
    tolerance and why nothing joins this column across."""
    raw, log = published
    recomputed = to_model_space(raw)
    assert recomputed.to_numpy().tolist() != log.to_numpy().tolist()
    assert (recomputed.to_numpy() - log.to_numpy()).max() < 1e-15


# --------------------------------------------------------------------------------------
# Does the name carry the space
# --------------------------------------------------------------------------------------


def test_a_named_series_carries_its_space_in_its_name() -> None:
    series = pd.Series([0.1, 1.0, 7.19], name=TARGET)
    moved = to_model_space(series)
    assert moved.name == f"{MODEL_SPACE_PREFIX}{TARGET}"
    assert to_wt_pct(moved).name == TARGET


def test_an_unnamed_series_stays_unnamed() -> None:
    moved = to_model_space(pd.Series([0.1, 1.0]))
    assert moved.name is None
    assert to_wt_pct(moved).name is None


def test_a_prediction_named_after_nothing_in_particular_keeps_its_name() -> None:
    """``to_wt_pct`` never refuses a name: a surrogate's output did not come from a column."""
    assert to_wt_pct(pd.Series([0.5], name="P50")).name == "P50"


def test_transforming_twice_refuses_rather_than_producing_log_log() -> None:
    moved = to_model_space(pd.Series([0.1], name=TARGET))
    with pytest.raises(TargetError, match="already a model-space column name"):
        to_model_space(moved)


def test_the_prefeaturized_schema_declares_the_same_name() -> None:
    """The one contract, spelled once: the loader's schema and this module must agree."""
    names = load_config().columns
    assert model_space_name(names.target) in prefeaturized_schema().column_names


# --------------------------------------------------------------------------------------
# Scalars
# --------------------------------------------------------------------------------------


def test_scalars_go_through_the_same_two_functions() -> None:
    """The two ends of the published range, and back.

    These read ``abs=ROUND_TRIP_TOLERANCE`` and not ``abs=0.0``, which is what they said
    until the CI fast lane first ran on Linux (card #6). ``math.log1p`` delegates to the
    platform's libm, and the two disagree in the last bit: ``math.log1p(7.19)`` is
    ``2.1029138978649784`` under MSVC, which is where the literal in
    :data:`~hydms.data.target.MODEL_SPACE_RANGE` was measured, and ``2.102913897864978``
    under glibc -- one ulp, about 4.4e-16, four orders inside the tolerance. Asserting
    bit-equality against a hardcoded libm result is a claim about the C library, not about
    this module, and it is the only assertion in the suite that made one.
    """
    low, high = WT_PCT_RANGE
    assert to_model_space(low) == pytest.approx(MODEL_SPACE_RANGE[0], abs=ROUND_TRIP_TOLERANCE)
    assert to_model_space(high) == pytest.approx(MODEL_SPACE_RANGE[1], abs=ROUND_TRIP_TOLERANCE)
    assert to_wt_pct(to_model_space(high)) == pytest.approx(high, abs=ROUND_TRIP_TOLERANCE)


def test_zero_weight_percent_is_a_legitimate_target() -> None:
    """An alloy that stores nothing is a measurement, not a violation. ``log1p(0) == 0``."""
    assert to_model_space(0.0) == 0.0
    assert to_wt_pct(0.0) == 0.0


def test_a_negative_model_value_comes_back_negative_rather_than_clipped() -> None:
    """A quantile head's lower band can go under zero. Clipping here would erase the only
    signal that the model has left the region it can defend -- that judgement is the refusal
    path's (card #77), which sees the interval and the domain verdict as well."""
    assert to_wt_pct(-0.5) == pytest.approx(math.expm1(-0.5))
    assert to_wt_pct(-0.5) < 0.0


# --------------------------------------------------------------------------------------
# The failure path
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [-0.01, -1.0, float("nan"), float("inf"), "3.2 wt%"])
def test_an_unusable_weight_percent_raises(bad) -> None:
    with pytest.raises(TargetError):
        to_model_space(pd.Series([1.0, bad], name=TARGET))


@pytest.mark.parametrize("bad", [float("nan"), float("-inf"), None])
def test_an_unusable_model_value_raises(bad) -> None:
    with pytest.raises(TargetError):
        to_wt_pct(pd.Series([1.0, bad]))


def test_the_message_names_every_offending_row_not_the_first() -> None:
    series = pd.Series([1.0, -1.0, 2.0, -2.0], index=["a", "b", "c", "d"], name=TARGET)
    with pytest.raises(TargetError) as caught:
        to_model_space(series)
    message = str(caught.value)
    assert "2 of 4" in message
    assert "row b" in message
    assert "row d" in message


def test_a_model_value_that_overflows_is_named_rather_than_crashing() -> None:
    with pytest.raises(TargetError, match="overflows"):
        to_wt_pct(1000.0)


def test_a_scalar_failure_names_the_value() -> None:
    with pytest.raises(TargetError, match="-3.0"):
        to_model_space(-3.0)
