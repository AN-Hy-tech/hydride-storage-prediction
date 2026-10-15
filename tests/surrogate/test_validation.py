"""L3 -- the folds group on the material, and nothing scores on what it was chosen with. Card #88.

Four properties, and each one is a defect that produced a published hydride number:

  - **A material is in one fold.** Not its spelling -- the material.
    ``benchmark_model_selection.py:895`` folded rows with no ``groups=``, and 141 of 896
    training rows had their exact formula in another fold.
  - **The reported score comes from a fold the search never saw.** ``:1156`` tuned and
    ``:1168`` scored through one ``splits`` object.
  - **The record can be checked afterwards.** ``tuned_on`` is *measured* -- the inner folds the
    search actually read -- and the ids are issued for content, so the detector that compares
    them has something to detect. ``test_the_guard_is_not_vacuous`` is the test that matters
    most in this file: it shows the nesting assertion could still fail.
  - **One protocol, two outer partitions.** Leave-one-alloy-class-out (#30, AC-6) is the same
    call with the outer cut swapped, not a second way of scoring a model.

The fixtures use small bin counts so that a 132-row frame can be stratified at all; the real
1,279-row dataset is exercised directly by the tests that carry `real` in their names.
"""

from __future__ import annotations

import itertools
import re
from functools import partial
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")

import pandas as pd  # noqa: E402
from hydms.config import Split as SplitSettings  # noqa: E402
from hydms.data.canonical import CanonicalisationError, group_keys  # noqa: E402
from hydms.qa import LeakDetected, SelectionRecord, assert_selection_is_nested  # noqa: E402
from hydms.surrogate.validation import (  # noqa: E402
    HELD_OUT_SPLITS,
    Contender,
    FoldSpace,
    ScoringTask,
    TuningTask,
    ValidationError,
    grouped_folds,
    leave_one_class_out,
    nested_scores,
)

#: Small bins, because a 132-row fixture cannot fill five quantile bins of two variables and
#: still leave five compositions in every stratum. The real data is stratified by
#: `pipeline.yaml`'s numbers in the tests that read it.
SMALL = SplitSettings(
    test_fraction=0.2,
    val_fraction=0.1,
    target_bins=2,
    temperature_bins=2,
    min_stratum_size=2,
)

ELEMENTS = ("La", "Ni", "Ti", "Fe", "Mg", "Zr", "V", "Cr", "Co", "Mn", "Al", "Ca")
CLASSES = ("AB", "AB2", "AB5", "Mg")

# The one collision measured on the real file, in miniature: one material, two spellings, two
# rows. Every fold test in this file has it in the frame, because a fold set that keeps them
# together for the wrong reason -- an accident of ordering -- is the failure being guarded.
TWO_SPELLINGS = ("Ce1Mg12", "Mg12Ce1")


def _rows() -> list[dict[str, Any]]:
    """Two measurements of each of 66 compositions, plus the collision pair."""
    rows: list[dict[str, Any]] = []
    for n, (first, second) in enumerate(itertools.combinations(ELEMENTS, 2)):
        for step in (0, 1):
            rows.append(
                {
                    "Composition": f"{first}1{second}{n % 5 + 2}",
                    "Alloy_class": CLASSES[n % len(CLASSES)],
                    "temperature(K)": 273.0 + 7.0 * n + 40.0 * step,
                    "H2_W% (max)": 0.5 + (n % 9) * 0.4 + 0.1 * step,
                }
            )
    for spelling in TWO_SPELLINGS:
        rows.append(
            {
                "Composition": spelling,
                "Alloy_class": "Mg",
                "temperature(K)": 598.0,
                "H2_W% (max)": 6.0,
            }
        )
    return rows


@pytest.fixture()
def alloys() -> pd.DataFrame:
    """134 rows over 67 compositions, one of them spelled two ways."""
    rows = _rows()
    return pd.DataFrame(rows, index=[f"r{n}" for n in range(len(rows))])


@pytest.fixture()
def training(alloys: pd.DataFrame) -> pd.Series:
    """A split assignment that holds the last twenty rows out, so `nested_scores` will run."""
    names = ["train"] * (len(alloys) - 20) + ["val"] * 10 + ["test"] * 10
    return pd.Series(names, index=alloys.index, name="split")


@pytest.fixture(scope="session")
def real_training() -> tuple[pd.DataFrame, pd.Series]:
    """The real 1,279 rows and card #13's split assignment, computed once."""
    from hydms.data.load import load_hydride_data
    from hydms.data.splits import assign_splits

    frame = load_hydride_data()
    return frame, assign_splits(frame)


def _folds(frame: pd.DataFrame, space: FoldSpace | None = None, **kwargs: Any) -> Any:
    """`grouped_folds` with the fixture's bin counts, so a test says only what it varies."""
    return grouped_folds(frame, space, settings=SMALL, **kwargs)


def _counting_contender(name: str = "counter", *, reads_folds: bool = True) -> Contender:
    """A stand-in model: it reads its inner folds and scores the fold size.

    It fits nothing. What every nested test below is about is the protocol's bookkeeping, and
    a contender that reads its folds and returns a number exercises all of it.
    """

    def tune(task: TuningTask) -> int:
        return len(list(task.folds)) if reads_folds else 0

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        return {"outer": float(len(task.test))}

    return Contender(name=name, tune=tune, score=score)


# --------------------------------------------------------------------------------------
# L7 -- a material is in one fold
# --------------------------------------------------------------------------------------


def test_no_canonical_composition_appears_in_two_folds_of_the_real_training_split(
    real_training: tuple[pd.DataFrame, pd.Series],
) -> None:
    """The card's assertion, on the data the leak was measured on.

    `grouped_folds` runs the detector itself before returning, so this re-derives the keys
    from the frame rather than reading the fold set's own: a generator that had quietly
    grouped on something else would agree with itself and still leak.
    """
    frame, split = real_training
    train = frame.loc[split == "train"]
    keys = group_keys(train)

    folds = grouped_folds(train, name="outer")

    seen: dict[str, str] = {}
    for fold in folds:
        for key in keys.loc[list(fold.test)]:
            assert key not in seen or seen[key] == fold.name, (
                f"{key!r} is in both {seen.get(key)} and {fold.name}; every selected feature "
                f"is a composition statistic or the temperature, so those rows carry the "
                f"same descriptor vector on both sides of the line (leak L7)"
            )
            seen[key] = fold.name
    assert len(seen) == keys.nunique()


def test_two_spellings_of_one_material_land_in_one_fold(alloys: pd.DataFrame) -> None:
    """`Ce1Mg12` and `Mg12Ce1`: 6.0 wt% at 598 K, written two ways, one fold."""
    folds = _folds(alloys, name="outer")
    where = {
        spelling: [
            fold.name
            for fold in folds
            for label in fold.test
            if alloys.loc[label, "Composition"] == spelling
        ]
        for spelling in TWO_SPELLINGS
    }
    assert where[TWO_SPELLINGS[0]] == where[TWO_SPELLINGS[1]], where


def test_every_row_is_held_out_exactly_once(alloys: pd.DataFrame) -> None:
    held = [label for fold in _folds(alloys) for label in fold.test]
    assert sorted(held) == sorted(alloys.index)


def test_a_fold_trains_on_everything_it_does_not_hold_out(alloys: pd.DataFrame) -> None:
    for fold in _folds(alloys):
        assert set(fold.train) | set(fold.test) == set(alloys.index)
        assert not set(fold.train) & set(fold.test)


def test_the_same_seed_reproduces_the_folds(alloys: pd.DataFrame) -> None:
    """AC-1's requirement, at the level of the folds rather than the metrics."""
    first = _folds(alloys, seed=42)
    again = _folds(alloys, seed=42)
    assert [(f.name, f.test) for f in first] == [(f.name, f.test) for f in again]


def test_another_seed_cuts_different_folds(alloys: pd.DataFrame) -> None:
    """Otherwise the seed is decoration and `test_the_same_seed_...` proves nothing."""
    first = _folds(alloys, seed=42)
    other = _folds(alloys, seed=7)
    assert [f.test for f in first] != [f.test for f in other]


def test_one_fold_is_not_a_partition(alloys: pd.DataFrame) -> None:
    with pytest.raises(ValidationError, match="at least two folds"):
        _folds(alloys, splits=1)


def test_more_folds_than_compositions_is_refused(alloys: pd.DataFrame) -> None:
    """The unit is the material: 67 compositions cannot fill 200 group-disjoint folds."""
    with pytest.raises(ValidationError, match="distinct composition"):
        _folds(alloys, splits=200)


def test_a_frame_with_no_formula_column_is_refused(alloys: pd.DataFrame) -> None:
    with pytest.raises(CanonicalisationError, match="no column"):
        _folds(alloys.drop(columns=["Composition"]))


# --------------------------------------------------------------------------------------
# The fold space -- an id is issued for content
# --------------------------------------------------------------------------------------


def test_two_folds_over_the_same_materials_share_an_id() -> None:
    space = FoldSpace()
    assert space.identify(["lani5", "tife"]) == space.identify(["tife", "lani5"])
    assert space.identify(["lani5", "tife"]) != space.identify(["lani5", "mg2ni"])


def test_an_unseen_fold_has_no_id_and_asking_does_not_issue_one() -> None:
    space = FoldSpace()
    space.identify(["lani5"])
    assert space.known(["tife"]) is None
    assert len(space) == 1


def test_the_same_cut_in_one_space_gets_the_same_ids_back(alloys: pd.DataFrame) -> None:
    """Content, not call order: cutting the same folds twice does not issue ten more ids."""
    space = FoldSpace()
    first = _folds(alloys, space, seed=42)
    again = _folds(alloys, space, seed=42)
    assert [f.id for f in first] == [f.id for f in again]
    assert len(space) == len(first)


def test_the_guard_is_not_vacuous(alloys: pd.DataFrame, training: pd.Series) -> None:
    """`assert_selection_is_nested` could still fire on a run of this protocol.

    The nesting check is an intersection of two id sets. If inner and outer ids came from
    independent counters the intersection would be empty whatever the protocol did, and every
    green result in this file would mean nothing. So: an outer fold's held-out compositions
    still resolve, in the run's own space, to that outer fold's id -- which is what an inner
    fold holding the same materials would have collided with -- and a record built with that
    id in both places is red.
    """
    evaluation = nested_scores(
        alloys,
        training,
        [_counting_contender()],
        outer=partial(grouped_folds, name="outer", settings=SMALL),
        settings=SMALL,
    )
    outer = evaluation.outer[0]
    assert evaluation.space.known(outer.held_out) == outer.id

    leaking = SelectionRecord(
        model="counter",
        tuned_on=evaluation.records[0].tuned_on | {outer.id},
        scored_on=evaluation.records[0].scored_on,
        metrics=evaluation.records[0].metrics,
    )
    with pytest.raises(LeakDetected, match="the tuner also saw"):
        assert_selection_is_nested([leaking])


# --------------------------------------------------------------------------------------
# L4, L2 -- the nested protocol
# --------------------------------------------------------------------------------------


@pytest.fixture()
def nested(alloys: pd.DataFrame, training: pd.Series) -> Any:
    return nested_scores(
        alloys,
        training,
        [_counting_contender("first"), _counting_contender("second")],
        outer=partial(grouped_folds, name="outer", settings=SMALL),
        settings=SMALL,
    )


def test_the_reported_score_comes_from_folds_the_tuner_never_saw(nested: Any) -> None:
    for record in nested.records:
        assert record.tuned_on, "a search that read no fold must not reach a record at all"
        assert record.scored_on == nested.outer.ids()
        assert not record.tuned_on & record.scored_on


def test_the_tuner_is_handed_the_outer_folds_training_rows_and_nothing_else(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    """Structural, not conventional: the frame it receives does not contain the test rows."""
    seen: dict[str, set[Any]] = {}

    def tune(task: TuningTask) -> int:
        seen[task.outer] = set(task.frame.index)
        return len(list(task.folds))

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        return {"outer": float(len(task.test))}

    evaluation = nested_scores(
        alloys,
        training,
        [Contender("watched", tune, score)],
        outer=partial(grouped_folds, name="outer", settings=SMALL),
        settings=SMALL,
    )
    for fold in evaluation.outer:
        assert seen[fold.name] == set(fold.train)
        assert not seen[fold.name] & set(fold.test)


def test_the_inner_folds_are_cut_from_the_outer_folds_training_rows(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    inner: dict[str, list[Any]] = {}

    def tune(task: TuningTask) -> int:
        inner[task.outer] = [label for fold in task.folds for label in fold.test]
        return 0

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        return {"outer": 1.0}

    evaluation = nested_scores(
        alloys,
        training,
        [Contender("watched", tune, score)],
        outer=partial(grouped_folds, name="outer", settings=SMALL),
        settings=SMALL,
    )
    for fold in evaluation.outer:
        assert sorted(inner[fold.name]) == sorted(fold.train)


def test_a_search_that_reads_no_fold_is_refused(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    """It tuned on something the protocol cannot record, which is the L4 shape."""
    with pytest.raises(ValidationError, match="read none of the"):
        nested_scores(
            alloys,
            training,
            [_counting_contender(reads_folds=False)],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )


@pytest.mark.parametrize("split_name", HELD_OUT_SPLITS)
def test_a_metric_named_after_a_held_out_split_is_red(
    alloys: pd.DataFrame, training: pd.Series, split_name: str
) -> None:
    """L2: the published Val R2 came from the set that ranked the members."""

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        return {split_name: 0.94}

    contender = Contender("catboost", _counting_contender().tune, score)
    with pytest.raises(LeakDetected, match="carries a metric"):
        nested_scores(
            alloys,
            training,
            [contender],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )


def test_the_record_is_the_mean_of_the_per_fold_table(nested: Any) -> None:
    for record in nested.records:
        rows = nested.per_fold.loc[nested.per_fold["model"] == record.model, "outer"]
        assert len(rows) == len(nested.outer)
        assert record.metrics["outer"] == pytest.approx(rows.mean())


def test_every_contender_is_compared_on_the_same_folds(nested: Any) -> None:
    first, second = nested.records
    assert first.tuned_on == second.tuned_on
    assert first.scored_on == second.scored_on


def test_the_chosen_configuration_is_recorded_per_model_and_fold(nested: Any) -> None:
    """A nested result nobody can trace back to hyperparameters is not a result."""
    for record in nested.records:
        for fold in nested.outer:
            assert (record.model, fold.name) in nested.chosen


def test_an_unknown_model_is_a_loud_lookup(nested: Any) -> None:
    with pytest.raises(KeyError, match="no record for"):
        nested.record("catboost")
    assert nested.record("first").model == "first"


def test_a_fold_that_scores_nothing_is_refused(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        return {}

    with pytest.raises(ValidationError, match="returned no metric"):
        nested_scores(
            alloys,
            training,
            [Contender("silent", _counting_contender().tune, score)],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )


def test_a_metric_that_is_not_a_number_is_refused(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    """`"0.94"` is not a score. `float()` would take it, which is why the check is a type."""

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        return {"outer": "0.94"}  # type: ignore[dict-item]

    with pytest.raises(ValidationError, match="not a number"):
        nested_scores(
            alloys,
            training,
            [Contender("stringly", _counting_contender().tune, score)],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )


def test_a_split_that_holds_nothing_out_is_refused(alloys: pd.DataFrame) -> None:
    """The same guard `fit_scaler` makes: cross-validation is not a substitute for a test set."""
    everything = pd.Series(["train"] * len(alloys), index=alloys.index, name="split")
    with pytest.raises(ValidationError, match="holds nothing out"):
        nested_scores(
            alloys,
            everything,
            [_counting_contender()],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )


def test_a_split_indexed_differently_from_the_matrix_is_refused(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    with pytest.raises(ValidationError, match="indexed differently"):
        nested_scores(alloys, training.iloc[:-5], [_counting_contender()])


def test_an_empty_comparison_is_refused(alloys: pd.DataFrame, training: pd.Series) -> None:
    with pytest.raises(ValidationError, match="no contenders"):
        nested_scores(alloys, training, [])


def test_two_contenders_under_one_name_are_refused(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    with pytest.raises(ValidationError, match="share a name"):
        nested_scores(
            alloys,
            training,
            [_counting_contender("twin"), _counting_contender("twin")],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )


# --------------------------------------------------------------------------------------
# AC-6 -- the same protocol, one alloy class at a time
# --------------------------------------------------------------------------------------


def test_leave_one_class_out_holds_out_one_class_and_all_of_it(alloys: pd.DataFrame) -> None:
    from hydms.data.canonical import alloy_classes

    labels = alloy_classes(alloys)
    folds = leave_one_class_out(alloys)
    assert len(folds) == labels.nunique()
    for fold in folds:
        held = set(labels.loc[list(fold.test)])
        assert len(held) == 1
        assert fold.name.endswith(held.pop())
        assert not set(labels.loc[list(fold.train)]) & set(labels.loc[list(fold.test)])


def test_leave_one_class_out_is_the_same_interface(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    """AC-6 runs through `nested_scores` with the outer cut swapped, and nothing else."""
    evaluation = nested_scores(
        alloys,
        training,
        [_counting_contender()],
        outer=leave_one_class_out,
        settings=SMALL,
    )
    assert {fold.name for fold in evaluation.outer} == {
        f"class:{label}" for label in CLASSES
    }
    record = evaluation.record("counter")
    assert not record.tuned_on & record.scored_on


def test_a_single_class_cannot_be_left_out(alloys: pd.DataFrame) -> None:
    one = alloys.assign(Alloy_class="AB5")
    with pytest.raises(ValidationError, match="at least two classes"):
        leave_one_class_out(one)


# --------------------------------------------------------------------------------------
# The project's only fold generator
# --------------------------------------------------------------------------------------


def test_nothing_else_in_the_package_generates_folds() -> None:
    """The card's first line, asserted rather than left to review.

    A second `KFold` anywhere under `hydms/` is a second answer to "which rows may this model
    see", and the one in `hydms/data/splits.py` -- `StratifiedShuffleSplit`, which cuts the
    train/val/test split rather than folds -- is deliberately not one.
    """
    package = Path(__file__).resolve().parents[2] / "hydms"
    imported = re.compile(r"^\s*from sklearn\.model_selection import (?P<names>.+)$", re.M)
    offenders = [
        path.relative_to(package).as_posix()
        for path in package.rglob("*.py")
        if path.name != "validation.py"
        and any(
            "KFold" in name
            for match in imported.finditer(path.read_text(encoding="utf-8"))
            for name in match.group("names").split(",")
        )
    ]
    assert not offenders, (
        f"{offenders} generate cross-validation folds outside "
        f"hydms/surrogate/validation.py, which is the project's only fold generator"
    )


# --------------------------------------------------------------------------------------
# The out-of-fold table -- card #29
# --------------------------------------------------------------------------------------


def test_a_contender_that_keeps_nothing_leaves_the_table_empty(nested: Any) -> None:
    """The default, and why it is one. Every contender written before card #29 keeps nothing.

    Including the constant baseline the L2 and L4 sentinels run, which has no row-level
    prediction to offer at all. A required sink would have made those sentinels carry a frame
    they do not have.
    """
    assert nested.out_of_fold.empty


def test_kept_predictions_are_stamped_with_the_model_and_the_fold(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    """The protocol stamps them, not the contender: it knows which fold it is running."""

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        task.keep(pd.DataFrame({"predicted": 1.0}, index=task.test.index))
        return {"outer": float(len(task.test))}

    evaluation = nested_scores(
        alloys,
        training,
        [Contender("keeper", _counting_contender().tune, score)],
        outer=partial(grouped_folds, name="outer", settings=SMALL),
        settings=SMALL,
    )
    kept = evaluation.out_of_fold
    assert not kept.empty
    assert set(kept.columns) == {"model", "fold", "predicted"}
    assert set(kept["model"]) == {"keeper"}
    assert set(kept["fold"]) == {fold.name for fold in evaluation.outer}
    # Every held-out row of every outer fold, exactly once: the folds partition the training
    # split, so the table is the training split with one prediction each.
    assert len(kept) == sum(len(fold.test) for fold in evaluation.outer)


def test_predictions_for_rows_the_model_was_fitted_on_are_refused(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    """The catastrophic case, and the reason the sink checks rather than accepts.

    Training-row predictions handed back as out-of-fold predictions would score beautifully
    and nothing downstream could tell -- the interval, the subgroup breakdown and the chapter
    would all be about a model scored on its own training data.
    """

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        task.keep(pd.DataFrame({"predicted": 1.0}, index=task.train.index))
        return {"outer": float(len(task.test))}

    with pytest.raises(ValidationError, match="fitted on would score like a prediction"):
        nested_scores(
            alloys,
            training,
            [Contender("leaking", _counting_contender().tune, score)],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )


def test_a_short_table_is_refused_too(
    alloys: pd.DataFrame, training: pd.Series
) -> None:
    """A fold that quietly returns half its rows gives an interval over a subset nobody chose."""

    def score(configuration: int, task: ScoringTask) -> dict[str, float]:
        half = task.test.index[: len(task.test) // 2]
        task.keep(pd.DataFrame({"predicted": 1.0}, index=half))
        return {"outer": float(len(task.test))}

    with pytest.raises(ValidationError, match="handed back predictions for"):
        nested_scores(
            alloys,
            training,
            [Contender("partial", _counting_contender().tune, score)],
            outer=partial(grouped_folds, name="outer", settings=SMALL),
            settings=SMALL,
        )
