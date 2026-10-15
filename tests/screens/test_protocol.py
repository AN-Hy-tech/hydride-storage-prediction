"""L4 -- the screen contract: a verdict with a reason, never a silent drop. Card #44.

The module under test has one job and it is negative: make it impossible for a candidate to
disappear without a sentence saying which rule removed it. So most of what is here is the
refusal path -- a screen that drops a row, adds one, reorders them, writes into the batch it
was handed, or invents a reason code it never declared, and in each case the error naming
what happened.

Three properties are load-bearing rather than incidental:

  - **Every screen runs.** There is no short-circuit on the first rejection, because
    "rejected by one rule of five" and "rejected by all five" are different findings and the
    shortlist review needs to tell them apart.
  - **Each screen is called once, whatever the batch size.** That is the batch rule made
    structural. ``featurize`` has a 5 ms per-call floor, 57% of a batch of one
    (``docs/BENCHMARKS.md``), so a runner that called a screen per candidate would cost
    ~200x before screening anything.
  - **Nothing is filtered here.** ``select()`` is a separate, explicit call by a caller who
    asked for the shortlist.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

pytest.importorskip("pandas", reason="the screen layer is pandas frames end to end")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from hydms.screens.protocol import (  # noqa: E402
    ADMITTED,
    ADMITTED_COLUMN,
    INDETERMINATE,
    Screen,
    ScreenError,
    Verdicts,
    apply_screens,
    verdict_table,
)

REJECTED = "rejected-for-testing"


class FakeScreen:
    """A well-formed screen whose answer the test dictates, and which counts its own calls.

    Not a mock: it goes through :func:`verdict_table` exactly as a real screen does, so a
    change to the verdict shape breaks it the same way it would break #48 and #49.
    """

    def __init__(
        self,
        name: str = "fake",
        *,
        rejects: tuple[Any, ...] = (),
        reasons: tuple[str, ...] = (REJECTED,),
        evidence: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.reasons = reasons
        self.rejects = rejects
        self.evidence = evidence
        self.calls = 0
        self.batches: list[int] = []

    def verdict(self, candidates: pd.DataFrame) -> pd.DataFrame:
        self.calls += 1
        self.batches.append(len(candidates))
        rejected = candidates.index.isin(self.rejects)
        frame = verdict_table(
            ~rejected,
            np.where(rejected, REJECTED, ADMITTED),
            np.where(rejected, f"{self.name} rejected it", f"{self.name} admitted it"),
            index=candidates.index,
        )
        for column, value in (self.evidence or {}).items():
            frame[column] = value
        return frame


class Custom:
    """A screen that returns whatever the test's callable returns, however malformed."""

    def __init__(
        self,
        build: Callable[[pd.DataFrame], Any],
        *,
        name: str = "custom",
        reasons: tuple[str, ...] = (REJECTED,),
    ) -> None:
        self.name = name
        self.reasons = reasons
        self._build = build

    def verdict(self, candidates: pd.DataFrame) -> Any:
        return self._build(candidates)


@pytest.fixture()
def candidates() -> pd.DataFrame:
    """Four candidates, labelled, so a dropped or reordered row is visible by name."""
    return pd.DataFrame(
        {
            "Composition": ["LaNi5", "TiFe", "Mg2Ni", "ZrMn2"],
            "temperature(K)": [300, 400, 500, 600],
        },
        index=["a", "b", "c", "d"],
    )


def batch(rows: int) -> pd.DataFrame:
    return pd.DataFrame({"temperature(K)": np.linspace(200, 700, rows)})


# --------------------------------------------------------------------------------------
# The shape of a verdict
# --------------------------------------------------------------------------------------


def test_a_well_formed_screen_satisfies_the_protocol() -> None:
    assert isinstance(FakeScreen(), Screen)


def test_every_candidate_gets_a_row_even_when_all_of_them_are_rejected(candidates) -> None:
    verdicts = apply_screens(candidates, [FakeScreen(rejects=tuple(candidates.index))])

    assert len(verdicts.table) == len(candidates)
    assert verdicts.table.index.equals(candidates.index)
    assert not verdicts.admitted.any()


def test_the_table_carries_one_block_per_screen_in_the_order_they_ran(candidates) -> None:
    verdicts = apply_screens(candidates, [FakeScreen("first"), FakeScreen("second")])

    assert list(verdicts.table.columns) == [
        ADMITTED_COLUMN,
        "first.passed",
        "first.code",
        "first.reason",
        "second.passed",
        "second.code",
        "second.reason",
    ]
    assert verdicts.screens == ("first", "second")


def test_every_verdict_carries_a_reason_including_the_ones_that_passed(candidates) -> None:
    verdicts = apply_screens(candidates, [FakeScreen(rejects=("b",))])
    reasons = verdicts.table["fake.reason"]

    assert reasons.loc["b"] == "fake rejected it"
    assert (reasons.drop("b") == "fake admitted it").all()
    assert reasons.str.strip().ne("").all()


def test_evidence_columns_are_carried_through_prefixed(candidates) -> None:
    """#49 reports the ElMD distance and the nearest formula beside its verdict."""
    screen = FakeScreen(evidence={"distance": 0.25, "nearest": "LaNi5"})

    verdicts = apply_screens(candidates, [screen])

    assert verdicts.table["fake.distance"].eq(0.25).all()
    assert verdicts.table["fake.nearest"].eq("LaNi5").all()


def test_the_verdict_of_one_screen_comes_back_unprefixed(candidates) -> None:
    verdicts = apply_screens(candidates, [FakeScreen("a"), FakeScreen("b", rejects=("c",))])

    one = verdicts.verdict("b")

    assert list(one.columns) == ["passed", "code", "reason"]
    assert one.loc["c", "code"] == REJECTED
    with pytest.raises(ScreenError, match="no screen named 'nope'"):
        verdicts.verdict("nope")


# --------------------------------------------------------------------------------------
# No silent drop: what the runner refuses
# --------------------------------------------------------------------------------------


def test_a_screen_that_drops_a_row_is_refused_and_the_row_is_named(candidates) -> None:
    dropper = Custom(lambda frame: FakeScreen().verdict(frame).drop(index="c"))

    with pytest.raises(ScreenError, match=r"'c'") as raised:
        apply_screens(candidates, [dropper])
    assert "have no verdict" in str(raised.value)
    assert "filtering happens afterwards" in str(raised.value)


def test_a_screen_that_invents_a_row_is_refused(candidates) -> None:
    def invent(frame: pd.DataFrame) -> pd.DataFrame:
        verdicts = FakeScreen().verdict(frame)
        return pd.concat([verdicts, verdicts.iloc[[0]].rename(index={"a": "z"})])

    with pytest.raises(ScreenError, match=r"invented 1 row\(s\): 'z'"):
        apply_screens(candidates, [Custom(invent)])


def test_a_screen_that_reorders_the_batch_is_refused(candidates) -> None:
    shuffler = Custom(lambda frame: FakeScreen().verdict(frame).iloc[::-1])

    with pytest.raises(ScreenError, match="different order"):
        apply_screens(candidates, [shuffler])


def test_a_screen_that_adds_a_column_to_the_batch_is_named(candidates) -> None:
    def scribble(frame: pd.DataFrame) -> pd.DataFrame:
        frame["screened"] = True
        return FakeScreen().verdict(frame)

    with pytest.raises(ScreenError, match="modified the candidates"):
        apply_screens(candidates, [Custom(scribble)])


def test_a_screen_that_overwrites_a_value_in_place_is_caught(candidates) -> None:
    """The structural check cannot see this one; the content fingerprint can."""

    def rewrite(frame: pd.DataFrame) -> pd.DataFrame:
        frame.loc["a", "temperature(K)"] = 999
        return FakeScreen().verdict(frame)

    with pytest.raises(ScreenError, match="modified the candidates"):
        apply_screens(candidates, [Custom(rewrite)])


def test_a_screen_that_reorders_the_batch_in_place_is_caught(candidates) -> None:
    def resort(frame: pd.DataFrame) -> pd.DataFrame:
        frame.sort_index(ascending=False, inplace=True)  # noqa: PD002 -- the defect under test
        return FakeScreen().verdict(frame)

    with pytest.raises(ScreenError, match="modified the candidates"):
        apply_screens(candidates, [Custom(resort)])


def test_an_undeclared_code_is_refused_with_the_vocabulary_it_should_have_used(
    candidates,
) -> None:
    def improvise(frame: pd.DataFrame) -> pd.DataFrame:
        return verdict_table(False, "made-up-on-the-spot", "no", index=frame.index)

    with pytest.raises(ScreenError, match="'made-up-on-the-spot'") as raised:
        apply_screens(candidates, [Custom(improvise)])
    assert "does not declare" in str(raised.value)
    assert REJECTED in str(raised.value)


def test_passed_must_agree_with_the_code(candidates) -> None:
    def disagree(frame: pd.DataFrame) -> pd.DataFrame:
        return verdict_table(True, REJECTED, "passed, allegedly", index=frame.index)

    with pytest.raises(ScreenError, match="disagrees with itself"):
        apply_screens(candidates, [Custom(disagree)])


def test_a_blank_reason_is_refused(candidates) -> None:
    def mute(frame: pd.DataFrame) -> pd.DataFrame:
        verdicts = FakeScreen(rejects=("b",)).verdict(frame)
        verdicts.loc["b", "reason"] = "   "
        return verdicts

    with pytest.raises(ScreenError, match=r"without a reason: 'b'"):
        apply_screens(candidates, [Custom(mute)])


def test_a_missing_verdict_column_is_refused(candidates) -> None:
    def partial(frame: pd.DataFrame) -> pd.DataFrame:
        return FakeScreen().verdict(frame).drop(columns=["reason"])

    with pytest.raises(ScreenError, match="no 'reason' column"):
        apply_screens(candidates, [Custom(partial)])


def test_a_non_boolean_passed_column_is_refused(candidates) -> None:
    """A verdict of None is the silent drop wearing a different hat."""

    def maybe(frame: pd.DataFrame) -> pd.DataFrame:
        verdicts = FakeScreen().verdict(frame)
        verdicts["passed"] = pd.Series([True, None, True, True], index=frame.index)
        return verdicts

    with pytest.raises(ScreenError, match="not bool"):
        apply_screens(candidates, [Custom(maybe)])


def test_a_non_string_reason_is_refused(candidates) -> None:
    def numeric(frame: pd.DataFrame) -> pd.DataFrame:
        verdicts = FakeScreen().verdict(frame)
        verdicts["reason"] = 1.0
        return verdicts

    with pytest.raises(ScreenError, match="not strings"):
        apply_screens(candidates, [Custom(numeric)])


def test_something_that_is_not_a_frame_is_refused(candidates) -> None:
    with pytest.raises(ScreenError, match="not a DataFrame of verdicts"):
        apply_screens(candidates, [Custom(lambda frame: frame.index.tolist())])


# --------------------------------------------------------------------------------------
# What the runner refuses before any screen runs
# --------------------------------------------------------------------------------------


def test_no_screens_at_all_is_refused(candidates) -> None:
    """An empty screen list admits everything, which is the silent drop's mirror image."""
    with pytest.raises(ScreenError, match="No screens|no screens"):
        apply_screens(candidates, [])


def test_two_screens_with_the_same_name_are_refused(candidates) -> None:
    with pytest.raises(ScreenError, match="two screens are called 'fake'"):
        apply_screens(candidates, [FakeScreen(), FakeScreen()])


def test_a_screen_with_no_declared_vocabulary_is_refused(candidates) -> None:
    with pytest.raises(ScreenError, match="declares no reason vocabulary"):
        apply_screens(candidates, [FakeScreen(reasons=())])


def test_a_screen_may_not_declare_admitted_as_a_reason(candidates) -> None:
    with pytest.raises(ScreenError, match="That code means admitted"):
        apply_screens(candidates, [FakeScreen(reasons=(ADMITTED, REJECTED))])


def test_a_screen_name_may_not_contain_the_column_separator(candidates) -> None:
    with pytest.raises(ScreenError, match=r"contains '\.'"):
        apply_screens(candidates, [FakeScreen("too.clever")])


def test_a_repeated_candidate_label_is_refused(candidates) -> None:
    doubled = pd.concat([candidates, candidates.loc[["a"]]])

    with pytest.raises(ScreenError, match="repeats 'a'"):
        apply_screens(doubled, [FakeScreen()])


def test_something_that_is_not_a_frame_of_candidates_is_refused() -> None:
    with pytest.raises(ScreenError, match="must be a DataFrame"):
        apply_screens(["LaNi5", "TiFe"], [FakeScreen()])  # type: ignore[arg-type]


def test_a_screen_that_raises_is_left_to_raise(candidates) -> None:
    """A screen that cannot run is not a verdict, and must not be turned into one."""

    def broken(frame: pd.DataFrame) -> pd.DataFrame:
        raise RuntimeError("the property table is missing")

    with pytest.raises(RuntimeError, match="property table is missing"):
        apply_screens(candidates, [Custom(broken)])


# --------------------------------------------------------------------------------------
# One batch, one call -- and every screen runs
# --------------------------------------------------------------------------------------


def test_each_screen_is_called_once_whatever_the_batch_size() -> None:
    """The batch rule, made structural. A per-candidate loop is ~200x the work (#22)."""
    for rows in (1, 10, 1000):
        screen = FakeScreen()
        apply_screens(batch(rows), [screen])
        assert screen.calls == 1
        assert screen.batches == [rows]


def test_every_screen_runs_even_after_an_earlier_one_rejected_everything(
    candidates,
) -> None:
    first = FakeScreen("first", rejects=tuple(candidates.index))
    second = FakeScreen("second", rejects=("a",))

    verdicts = apply_screens(candidates, [first, second])

    assert second.calls == 1
    assert verdicts.table["second.passed"].tolist() == [False, True, True, True]


def test_a_duration_is_recorded_for_every_screen(candidates) -> None:
    verdicts = apply_screens(candidates, [FakeScreen("a"), FakeScreen("b")])

    assert set(verdicts.durations) == {"a", "b"}
    assert all(seconds >= 0.0 for seconds in verdicts.durations.values())


def test_an_empty_batch_produces_a_table_with_no_rows_and_all_its_columns() -> None:
    empty = pd.DataFrame({"temperature(K)": pd.Series(dtype="float64")})
    screen = FakeScreen()

    verdicts = apply_screens(empty, [screen])

    assert screen.calls == 1
    assert len(verdicts.table) == 0
    assert list(verdicts.table.columns) == [
        ADMITTED_COLUMN,
        "fake.passed",
        "fake.code",
        "fake.reason",
    ]
    assert list(verdicts.rejections().columns) == ["label", "screen", "code", "reason"]


# --------------------------------------------------------------------------------------
# Reading the result
# --------------------------------------------------------------------------------------


@pytest.fixture()
def screened(candidates) -> Verdicts:
    """Two screens: 'b' rejected by both, 'c' by one, 'a' and 'd' admitted."""
    return apply_screens(
        candidates,
        [FakeScreen("first", rejects=("b", "c")), FakeScreen("second", rejects=("b",))],
    )


def test_admitted_is_the_conjunction_of_every_screen(screened) -> None:
    assert screened.admitted.tolist() == [True, False, False, True]
    assert screened.table[ADMITTED_COLUMN].equals(screened.admitted)


def test_rejections_names_every_screen_that_rejected_a_candidate(screened) -> None:
    rejections = screened.rejections()

    assert list(rejections.columns) == ["label", "screen", "code", "reason"]
    assert rejections["label"].tolist() == ["b", "b", "c"]
    assert rejections["screen"].tolist() == ["first", "second", "first"]
    assert rejections["code"].eq(REJECTED).all()
    assert rejections["reason"].tolist() == [
        "first rejected it",
        "second rejected it",
        "first rejected it",
    ]


def test_rejections_is_empty_but_shaped_when_nothing_was_rejected(candidates) -> None:
    verdicts = apply_screens(candidates, [FakeScreen()])

    rejections = verdicts.rejections()

    assert rejections.empty
    assert list(rejections.columns) == ["label", "screen", "code", "reason"]


def test_summary_joins_the_screens_and_their_reasons_per_candidate(screened) -> None:
    summary = screened.summary()

    assert list(summary.columns) == [ADMITTED_COLUMN, "rejected_by", "reasons"]
    assert summary.index.equals(screened.table.index)
    assert summary.loc["b", "rejected_by"] == "first, second"
    assert summary.loc["b", "reasons"] == "first rejected it; second rejected it"
    assert summary.loc["c", "rejected_by"] == "first"
    assert summary.loc["a", "rejected_by"] == ""
    assert summary.loc["a", "reasons"] == ""


def test_summary_of_an_untouched_batch_has_empty_reasons(candidates) -> None:
    summary = apply_screens(candidates, [FakeScreen()]).summary()

    assert summary["rejected_by"].eq("").all()
    assert summary[ADMITTED_COLUMN].all()


def test_counts_report_each_screen_and_the_overall_result(screened) -> None:
    counts = screened.counts()

    assert list(counts.index) == ["first", "second", "overall"]
    assert counts.loc["first", "rejected"] == 2
    assert counts.loc["second", "rejected"] == 1
    assert counts.loc["overall", "admitted"] == 2
    assert (counts["seen"] == 4).all()
    assert (counts["admitted"] + counts["rejected"] == counts["seen"]).all()


# --------------------------------------------------------------------------------------
# The filtering, afterwards and explicitly
# --------------------------------------------------------------------------------------


def test_select_returns_the_admitted_rows_in_their_original_order(screened, candidates) -> None:
    shortlist = screened.select(candidates)

    assert shortlist.index.tolist() == ["a", "d"]
    assert shortlist["Composition"].tolist() == ["LaNi5", "ZrMn2"]


def test_select_returns_a_copy(screened, candidates) -> None:
    shortlist = screened.select(candidates)

    shortlist.loc["a", "Composition"] = "changed"

    assert candidates.loc["a", "Composition"] == "LaNi5"


def test_select_refuses_a_frame_that_is_not_the_one_that_was_screened(
    screened, candidates
) -> None:
    with pytest.raises(ScreenError, match="Select from the frame that was screened"):
        screened.select(candidates.drop(index="a"))


# --------------------------------------------------------------------------------------
# verdict_table
# --------------------------------------------------------------------------------------


def test_verdict_table_broadcasts_scalars_and_types_its_columns(candidates) -> None:
    frame = verdict_table(True, ADMITTED, "fine", index=candidates.index)

    assert list(frame.columns) == ["passed", "code", "reason"]
    assert frame["passed"].dtype == bool
    assert frame["passed"].all()
    assert frame["reason"].eq("fine").all()
    assert frame.index.equals(candidates.index)


def test_verdict_table_takes_the_index_from_a_series_when_it_is_not_given(candidates) -> None:
    passed = pd.Series([True, False, True, True], index=candidates.index)

    frame = verdict_table(passed, np.where(passed, ADMITTED, INDETERMINATE), "why")

    assert frame.index.equals(candidates.index)
    assert frame.loc["b", "code"] == INDETERMINATE


def test_verdict_table_refuses_a_series_on_a_different_index(candidates) -> None:
    stray = pd.Series([True, False], index=["x", "y"])

    with pytest.raises(ScreenError, match="not on the candidates' index"):
        verdict_table(stray, ADMITTED, "why", index=candidates.index)


def test_verdict_table_refuses_a_sequence_of_the_wrong_length(candidates) -> None:
    with pytest.raises(ScreenError, match="2 entries for 4 candidate"):
        verdict_table([True, False], ADMITTED, "why", index=candidates.index)


def test_verdict_table_needs_an_index_from_somewhere() -> None:
    with pytest.raises(ScreenError, match="needs an index"):
        verdict_table(True, ADMITTED, "why")
