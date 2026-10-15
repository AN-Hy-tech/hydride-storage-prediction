"""L1 -- the screening stage and the contract it exists to enforce. Card #14.

The stage's whole value is what it *refuses* to do, so most of these tests are about rows it
leaves alone:

  - **Held-out rows are untouchable.** Targets and features byte-identical, in place, whatever
    the screening found about them. That is leaks L3 and L10, checked with the same detector
    gate HG-1 runs.
  - **No label is rewritten, on any split.** Stronger than the leak, and the reason is
    ``CleanLab.py:64,80``: the archival stage rewrote *training* labels too, with the model's
    own predictions.
  - **The two decided rows.** The byte-identical duplicate and the formula with a missing
    decimal point, both found structurally or by declaration rather than by row number.
  - **The CleanLab seam.** ``label_issues`` behaves like the boolean Series CleanLab returns,
    including for a row it never mentions.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the data layer is pandas frames end to end")
pytest.importorskip("sklearn", reason="the split protocol is scikit-learn's")

import pandas as pd  # noqa: E402  -- only importable once the skips above have passed
from hydms.data.load import load_hydride_data  # noqa: E402
from hydms.data.screening import (  # noqa: E402
    EXACT_DUPLICATE,
    LABEL_QUALITY,
    MALFORMED_FORMULA,
    MALFORMED_FORMULAE,
    ScreeningError,
    screen,
)
from hydms.data.splits import SPLIT_NAMES, assign_splits  # noqa: E402
from hydms.qa import LeakDetected  # noqa: E402

TARGET = "H2_W% (max)"
FORMULA = "Composition"


@pytest.fixture(scope="module")
def hydride() -> pd.DataFrame:
    return load_hydride_data()


@pytest.fixture(scope="module")
def split(hydride: pd.DataFrame) -> pd.Series:
    return assign_splits(hydride)


@pytest.fixture(scope="module")
def screened(hydride: pd.DataFrame, split: pd.Series):
    return screen(hydride, split)


def toy() -> tuple[pd.DataFrame, pd.Series]:
    """Four rows, one per split plus a training row, small enough to reason about."""
    frame = pd.DataFrame(
        {
            FORMULA: ["LaNi5", "TiFe", "Mg2Ni", "ZrV2"],
            TARGET: [1.4, 1.9, 3.6, 2.0],
            "temperature(K)": [298, 300, 573, 310],
        },
        index=["a", "b", "c", "d"],
    )
    assignment = pd.Series(["train", "train", "val", "test"], index=frame.index, name="split")
    return frame, assignment


# --------------------------------------------------------------------------------------
# Held-out rows are untouchable
# --------------------------------------------------------------------------------------


def test_held_out_targets_and_features_survive_byte_identical(hydride, split, screened) -> None:
    held_out = split[split != "train"].index
    assert list(screened.frame.loc[held_out, TARGET]) == list(hydride.loc[held_out, TARGET])
    assert screened.frame.loc[held_out].equals(hydride.loc[held_out])


def test_a_finding_on_a_held_out_row_is_reported_and_not_acted_on() -> None:
    """Improving a held-out set by removing rows from it is the mirror image of L3."""
    frame, assignment = toy()
    issues = pd.Series([False, False, True, True], index=frame.index)
    result = screen(frame, assignment, label_issues=issues)

    assert set(result.removed) == set()
    assert len(result.frame) == len(frame)
    report = result.report()
    assert set(report["split"]) == {"val", "test"}
    assert not report["removed"].any()


def test_no_label_is_rewritten_on_any_split(hydride, screened) -> None:
    """`CleanLab.py:64,80` rewrote training labels with `predicted_label`. Nothing here does,
    and the check covers every surviving row rather than only the held-out ones."""
    kept = screened.frame.index
    assert list(screened.frame[TARGET]) == list(hydride.loc[kept, TARGET])


def test_the_row_order_of_the_survivors_is_unchanged(hydride, screened) -> None:
    kept = [label for label in hydride.index if label in set(screened.frame.index)]
    assert list(screened.frame.index) == kept


# --------------------------------------------------------------------------------------
# The two decided rows
# --------------------------------------------------------------------------------------


def test_the_byte_identical_duplicate_is_found_and_dropped(hydride, screened) -> None:
    """Rows 687 and 694: one `La0.9Ce0.1Ni5` measurement at 373 K entered twice, same
    citation. Both land in train, so the later copy goes."""
    report = screened.report()
    duplicates = report[report["kind"] == EXACT_DUPLICATE]
    assert len(duplicates) == 1
    assert bool(duplicates["removed"].iloc[0])
    label = duplicates["label"].iloc[0]
    assert label not in set(screened.frame.index)
    assert hydride.loc[label, FORMULA] == "La0.9Ce0.1Ni5"


def test_the_duplicate_is_found_structurally_not_by_row_number() -> None:
    frame, assignment = toy()
    frame = pd.concat([frame, frame.loc[["a"]].rename(index={"a": "e"})])
    assignment = pd.concat([assignment, pd.Series(["train"], index=["e"])])
    result = screen(frame, assignment)
    assert result.removed == ("e",)
    assert result.report()["kind"].tolist() == [EXACT_DUPLICATE]


def test_the_malformed_formula_is_declared_and_dropped(hydride, screened) -> None:
    report = screened.report()
    malformed = report[report["kind"] == MALFORMED_FORMULA]
    assert len(malformed) == 1
    assert bool(malformed["removed"].iloc[0])
    assert "missing decimal point" in malformed["reason"].iloc[0]


def test_every_declared_malformed_formula_is_still_in_the_file(hydride) -> None:
    """A declaration about a row that no longer exists is a decision nothing enforces."""
    present = set(hydride[FORMULA])
    assert set(MALFORMED_FORMULAE) <= present


def test_exactly_two_rows_are_removed_and_only_from_train(hydride, split, screened) -> None:
    assert len(screened.removed) == 2
    assert all(split.loc[label] == "train" for label in screened.removed)
    assert len(screened.frame) == len(hydride) - 2


def test_the_counts_show_removals_only_in_train(screened) -> None:
    table = screened.counts()
    assert list(table.index) == list(SPLIT_NAMES)
    assert int(table.loc["train", "removed"]) == 2
    assert int(table.loc["val", "removed"]) == 0
    assert int(table.loc["test", "removed"]) == 0
    assert int(table["rows_in"].sum()) == 1279
    assert int(table["rows_out"].sum()) == 1277


# --------------------------------------------------------------------------------------
# The CleanLab seam
# --------------------------------------------------------------------------------------


def test_a_flagged_training_row_is_dropped_with_its_score() -> None:
    frame, assignment = toy()
    issues = pd.Series([True, False, False, False], index=frame.index)
    quality = pd.Series([0.02, 0.9, 0.8, 0.7], index=frame.index)
    result = screen(frame, assignment, label_issues=issues, label_quality=quality)

    assert result.removed == ("a",)
    row = result.report().iloc[0]
    assert row["kind"] == LABEL_QUALITY
    assert row["quality"] == pytest.approx(0.02)
    assert "measurement pressure" in row["reason"]


def test_rows_the_issue_series_never_mentions_are_treated_as_clean() -> None:
    """CleanLab is fitted on the training rows, so what it returns covers those alone."""
    frame, assignment = toy()
    issues = pd.Series([True], index=["a"])
    result = screen(frame, assignment, label_issues=issues)
    assert result.removed == ("a",)
    assert len(result.frame) == 3


def test_without_a_label_issue_series_only_the_structural_findings_fire() -> None:
    frame, assignment = toy()
    result = screen(frame, assignment)
    assert result.removed == ()
    assert result.report().empty
    assert list(result.report().columns) == [
        "label", "kind", "split", "removed", "quality", "reason",
    ]


def test_a_row_is_reported_once_even_when_two_kinds_apply() -> None:
    """A duplicate that CleanLab also flags is one finding, not two -- the report is a list of
    rows with a reason, not a list of reasons."""
    frame, assignment = toy()
    frame = pd.concat([frame, frame.loc[["a"]].rename(index={"a": "e"})])
    assignment = pd.concat([assignment, pd.Series(["train"], index=["e"])])
    issues = pd.Series(True, index=frame.index)
    result = screen(frame, assignment, label_issues=issues)
    assert len(result.report()) == len(result.report()["label"].drop_duplicates())
    assert result.report().set_index("label").loc["e", "kind"] == EXACT_DUPLICATE


# --------------------------------------------------------------------------------------
# The failure path
# --------------------------------------------------------------------------------------


def test_a_misaligned_split_assignment_refuses() -> None:
    frame, assignment = toy()
    with pytest.raises(ScreeningError, match="not aligned"):
        screen(frame, assignment.iloc[:2])


def test_an_unrecognised_split_name_refuses() -> None:
    frame, assignment = toy()
    assignment = assignment.replace("val", "holdout")
    with pytest.raises(ScreeningError, match="holdout"):
        screen(frame, assignment)


def test_a_row_with_no_split_refuses() -> None:
    frame, assignment = toy()
    assignment.loc["c"] = None
    with pytest.raises(ScreeningError, match="no split"):
        screen(frame, assignment)


def test_the_contract_is_enforced_at_runtime_not_only_by_construction(monkeypatch) -> None:
    """Delete the guard in your head and something must go red: a stage that rewrote a
    held-out label would be caught by the same detector HG-1 runs, from inside `screen`."""
    frame, assignment = toy()
    original = pd.DataFrame.drop

    def rewrite(self, *args, **kwargs):
        out = original(self, *args, **kwargs)
        if TARGET in out.columns and "c" in out.index:
            out = out.copy()
            out.loc["c", TARGET] = 99.0
        return out

    monkeypatch.setattr(pd.DataFrame, "drop", rewrite)
    issues = pd.Series([True, False, False, False], index=frame.index)
    with pytest.raises(LeakDetected):
        screen(frame, assignment, label_issues=issues)


# --------------------------------------------------------------------------------------
# The CleanLab seam gives the same verdict every time (card #104)
# --------------------------------------------------------------------------------------


def noisy(rows: int = 120) -> tuple[pd.DataFrame, pd.Series]:
    """A smooth target over three columns, with a few labels pushed far off it."""
    import numpy as np

    rng = np.random.default_rng(7)
    features = pd.DataFrame(rng.uniform(size=(rows, 3)), columns=["p", "q", "r"])
    target = features["p"] * 2 + features["q"] ** 2 + rng.normal(scale=0.05, size=rows)
    target.iloc[::17] += 1.5
    return features, target.rename("y")


def test_the_default_forest_predicts_on_one_thread(monkeypatch) -> None:
    # The step #104's probes localised: a forest on n_jobs=-1 sums its trees in the order the
    # threads finish, and CleanLab's ranking turns that last-digit drift into a new verdict.
    # Caught here structurally, because the drift itself is intermittent.
    import cleanlab.regression.learn as learn
    from hydms.data.screening import label_issues

    handed: list[object] = []

    class Spy:
        def __init__(self, model, **kwargs) -> None:
            handed.append(model)

        def find_label_issues(self, X, y):
            return pd.DataFrame({"is_label_issue": [False] * len(y), "label_quality": 1.0})

    monkeypatch.setattr(learn, "CleanLearning", Spy)
    label_issues(*noisy(), seed=42)
    assert [model.get_params()["n_jobs"] for model in handed] == [1]


def test_a_parallel_estimator_is_refused_before_it_is_fitted() -> None:
    from hydms.data.screening import label_issues
    from sklearn.ensemble import RandomForestRegressor

    with pytest.raises(ScreeningError, match=r"n_jobs=-1.*#104"):
        label_issues(*noisy(), estimator=RandomForestRegressor(n_jobs=-1), seed=42)


def test_the_same_rows_and_seed_give_the_same_scores_bit_for_bit() -> None:
    # Equality, not a tolerance: the claim is reproduction, and #104's drift was 5e-4 at worst
    # but began at the last digit, which any tolerance here would have passed. A ten-tree
    # forest keeps this in the fast lane (the default's hundred trees cost about 12 s a call); the
    # thread count, which is what #104 was about, is the default's.
    from hydms.data.screening import label_issues
    from sklearn.ensemble import RandomForestRegressor

    def forest() -> RandomForestRegressor:
        return RandomForestRegressor(n_estimators=10, max_depth=4, n_jobs=1, random_state=0)

    first, second = (label_issues(*noisy(), estimator=forest(), seed=42) for _ in range(2))
    assert first.issues.equals(second.issues)
    assert first.quality.equals(second.quality)
    assert first.flagged > 0
