"""L4 -- the window screen, and both sides of every boundary. Card #44.

``docs/QA-PROTOCOL.md`` names the obligation for this layer: *boundary cases on each window
are covered, both sides*. So the interesting rows here are 195 and 773 exactly (admitted --
they are measured training temperatures, not theoretical limits), and the values either side
of them.

The other half is the fail-closed rule. A candidate whose value cannot be read is refused
with :data:`~hydms.screens.protocol.INDETERMINATE`, never admitted, because a guard rail
that could not run must not pass anything; and a *missing column* raises instead, because
that is the wrong frame rather than a fact about any candidate in it.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the screen layer is pandas frames end to end")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from hydms.config import load as load_config  # noqa: E402
from hydms.screens.protocol import (  # noqa: E402
    ADMITTED,
    INDETERMINATE,
    Screen,
    ScreenError,
    apply_screens,
)
from hydms.screens.window import OUTSIDE_WINDOW, Window, temperature_window  # noqa: E402

COLUMN = "temperature(K)"


@pytest.fixture()
def window() -> Window:
    return Window(
        name="temperature",
        column=COLUMN,
        low=195.0,
        high=773.0,
        units="K",
        quantity="the trained temperature range",
    )


def frame_of(values: list[float | None]) -> pd.DataFrame:
    return pd.DataFrame({COLUMN: pd.Series(values, dtype="float64")})


# --------------------------------------------------------------------------------------
# Both sides of both boundaries
# --------------------------------------------------------------------------------------


def test_a_window_is_a_screen(window) -> None:
    assert isinstance(window, Screen)
    assert window.reasons == (OUTSIDE_WINDOW, INDETERMINATE)


def test_both_boundaries_are_inside_the_window(window) -> None:
    """195 K and 773 K are measured rows of the dataset, not theoretical limits."""
    verdicts = window.verdict(frame_of([195.0, 773.0]))

    assert verdicts["passed"].all()
    assert verdicts["code"].eq(ADMITTED).all()


def test_just_outside_either_boundary_is_rejected(window) -> None:
    verdicts = window.verdict(frame_of([194.9, 773.1]))

    assert not verdicts["passed"].any()
    assert verdicts["code"].eq(OUTSIDE_WINDOW).all()


def test_a_value_in_the_middle_is_admitted_with_a_reason(window) -> None:
    verdicts = window.verdict(frame_of([300.0]))

    assert verdicts.loc[0, "passed"]
    assert verdicts.loc[0, "reason"] == "inside the trained temperature range 195-773 K"


def test_the_reason_says_which_side_the_candidate_fell_off(window) -> None:
    verdicts = window.verdict(frame_of([100.0, 900.0]))

    assert verdicts.loc[0, "reason"] == (
        "temperature(K) = 100 K is below the trained temperature range 195-773 K"
    )
    assert verdicts.loc[1, "reason"] == (
        "temperature(K) = 900 K is above the trained temperature range 195-773 K"
    )


def test_a_missing_value_is_indeterminate_and_is_not_admitted(window) -> None:
    verdicts = window.verdict(frame_of([np.nan, 300.0, np.inf]))

    assert verdicts["passed"].tolist() == [False, True, False]
    assert verdicts["code"].tolist() == [INDETERMINATE, ADMITTED, INDETERMINATE]
    assert "could not be applied" in verdicts.loc[0, "reason"]


def test_an_integer_column_is_read_as_written(window) -> None:
    """`temperature(K)` arrives as int64 from the raw file; 773 must still be inside."""
    verdicts = window.verdict(pd.DataFrame({COLUMN: pd.Series([195, 773, 774], dtype="int64")}))

    assert verdicts["passed"].tolist() == [True, True, False]


def test_an_empty_batch_is_judged_without_incident(window) -> None:
    verdicts = window.verdict(frame_of([]))

    assert len(verdicts) == 0
    assert list(verdicts.columns) == ["passed", "code", "reason"]


# --------------------------------------------------------------------------------------
# What the window refuses to guess about
# --------------------------------------------------------------------------------------


def test_a_missing_column_raises_rather_than_rejecting_every_row(window) -> None:
    with pytest.raises(ScreenError, match="which the candidates do not have"):
        window.verdict(pd.DataFrame({"Composition": ["LaNi5"]}))


def test_a_non_numeric_column_raises(window) -> None:
    with pytest.raises(ScreenError, match="A window compares numbers"):
        window.verdict(pd.DataFrame({COLUMN: ["300 K"]}))


def test_a_boolean_column_raises(window) -> None:
    with pytest.raises(ScreenError, match="A window compares numbers"):
        window.verdict(pd.DataFrame({COLUMN: [True, False]}))


def test_an_empty_interval_is_refused_at_construction() -> None:
    with pytest.raises(ScreenError, match="is empty"):
        Window(name="backwards", column=COLUMN, low=773.0, high=195.0)


def test_a_non_finite_bound_is_refused_at_construction() -> None:
    with pytest.raises(ScreenError, match="non-finite bounds"):
        Window(name="unbounded", column=COLUMN, low=195.0, high=float("nan"))


def test_a_window_needs_a_name_and_a_column() -> None:
    with pytest.raises(ScreenError, match="needs a name and a column"):
        Window(name="  ", column=COLUMN, low=1.0, high=2.0)


# --------------------------------------------------------------------------------------
# The trained temperature range comes from config
# --------------------------------------------------------------------------------------


def test_the_temperature_window_reads_its_bounds_and_its_column_from_config() -> None:
    cfg = load_config()

    screen = temperature_window()

    assert screen.column == cfg.columns.temperature
    assert (screen.low, screen.high) == (
        cfg.domain.temperature_min_k,
        cfg.domain.temperature_max_k,
    )
    assert (screen.low, screen.high) == (195.0, 773.0)


def test_tightening_the_window_is_a_config_change(window) -> None:
    """#48's ceiling must have the same property: a threshold nobody has to edit code for."""
    cfg = load_config()
    tightened = temperature_window(cfg)
    assert tightened.high == 773.0

    narrower = Window(
        name=tightened.name,
        column=tightened.column,
        low=tightened.low,
        high=500.0,
        units=tightened.units,
        quantity=tightened.quantity,
    )

    assert narrower.verdict(frame_of([600.0])).loc[0, "code"] == OUTSIDE_WINDOW


def test_the_whole_curated_dataset_falls_inside_the_trained_window(hydride_raw) -> None:
    """The bounds are the measured span, so every real row must be admitted by them."""
    verdicts = apply_screens(hydride_raw, [temperature_window()])

    assert verdicts.admitted.all()
    assert verdicts.counts().loc["temperature", "seen"] == 1279
    assert verdicts.rejections().empty


def test_a_candidate_outside_the_window_is_carried_through_the_runner_not_dropped() -> None:
    candidates = pd.DataFrame(
        {"Composition": ["LaNi5", "TiFe"], COLUMN: [300.0, 1200.0]},
        index=["known", "too-hot"],
    )

    verdicts = apply_screens(candidates, [temperature_window()])

    assert len(verdicts.table) == 2
    assert verdicts.admitted.tolist() == [True, False]
    assert verdicts.summary().loc["too-hot", "rejected_by"] == "temperature"
    assert "above the trained temperature range" in verdicts.summary().loc["too-hot", "reasons"]
    assert verdicts.select(candidates).index.tolist() == ["known"]
