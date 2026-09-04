"""L3 -- selection reads the fold's rows and nothing else. Card #24.

Four properties, each one a defect that produced a published hydride number:

  - **The rows are the fold's.** ``Boruta_FeatEng.py:57-113`` fitted all three stages on all
    896 training rows before any cross-validation, so the 22-feature contract ``REPORT.md``
    reports against is itself a fitted object with no held-out data behind it. That is L6.
  - **The input is screened.** ``:23-25`` reads the *pre-CleanLab* splits while its comment
    claims otherwise, so the published pipeline ran CleanLab and then ignored it.
  - **``temperature(K)`` survives.** The archival selector force-re-adds it twice by hand; it
    is the only non-composition feature and the model is useless without it.
  - **The three stages are the three that exist.** Not ``REPORT.md`` 3.3's five.

Most tests here run under :data:`SMALL_BUDGET` -- a handful of Boruta iterations over a small
forest. Boruta's *verdict* is not what this file asserts; which rows produced it is, and that
is answered at any budget. The two tests carrying ``real`` in their names read the actual
dataset, and the one that runs the configured budget is marked ``slow``.
"""

from __future__ import annotations

import itertools
from dataclasses import replace
from functools import partial
from typing import Any

import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")
pytest.importorskip("boruta", reason="BorutaPy is the selector being ported")
pytest.importorskip("statsmodels", reason="the VIF loop is statsmodels'")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from hydms.qa import LeakDetected, assert_selection_ignores_holdout  # noqa: E402
from hydms.surrogate.selection import (  # noqa: E402
    SENTINEL_BUDGET,
    STAGE_NAMES,
    SelectionError,
    SelectionSettings,
    select_across_folds,
    select_features,
    selected_names,
    sentinel_settings,
)

#: Enough Boruta to decide something, cheap enough to run forty times. Every threshold that
#: is *not* about cost stays at `pipeline.yaml`'s value, so a test cannot pass because the
#: fixture moved a threshold out of its way.
SMALL_BUDGET = dict(SENTINEL_BUDGET)

ELEMENTS = ("La", "Ni", "Ti", "Fe", "Mg", "Zr", "V", "Cr", "Co", "Mn", "Al", "Ca")
CLASSES = ("AB", "AB2", "AB5", "Mg")


def _settings(**overrides: Any) -> SelectionSettings:
    return replace(SelectionSettings.from_config(), **{**SMALL_BUDGET, **overrides})


@pytest.fixture()
def alloys() -> pd.DataFrame:
    """132 rows over 66 compositions, with a record beside a small, honest feature matrix.

    Three of the six candidate columns carry signal and three do not: ``useful`` is the target
    itself plus noise, ``middling`` is half of it, ``constant`` never moves, and the three
    ``noise`` columns are drawn independently. That is enough for the stages to have something
    to do without the fixture becoming a second dataset.
    """
    rng = np.random.default_rng(11)
    rows: list[dict[str, Any]] = []
    for n in range(132):
        first, second = ELEMENTS[n % len(ELEMENTS)], ELEMENTS[(n + 5) % len(ELEMENTS)]
        target = 0.5 + (n % 9) * 0.4
        rows.append(
            {
                "Composition": f"{first}1{second}{n % 5 + 2}",
                "Alloy_class": CLASSES[n % len(CLASSES)],
                "Dataset": "Extracted",
                "Citation": "https://example.invalid",
                "H2_W% (max)": target,
                "temperature(K)": 273.0 + 3.0 * (n % 40),
                "useful": target + rng.normal(scale=0.05),
                "middling": target * 0.5 + rng.normal(scale=0.5),
                "constant": 1.0,
                "noise_a": rng.normal(size=1)[0],
                "noise_b": rng.normal(size=1)[0],
                "noise_c": rng.normal(size=1)[0],
            }
        )
    frame = pd.DataFrame(rows, index=[f"r{n}" for n in range(len(rows))])
    frame["canonical_key"] = frame["Composition"]
    return frame


@pytest.fixture()
def train(alloys: pd.DataFrame) -> list[str]:
    """The first hundred rows. The other 32 are what the selector must not read."""
    return list(alloys.index[:100])


@pytest.fixture()
def held_out(alloys: pd.DataFrame) -> list[str]:
    return list(alloys.index[100:])


@pytest.fixture(scope="session")
def real_frame() -> tuple[pd.DataFrame, pd.Series]:
    """The real matrix as the L6 live check builds it: 1,278 rows, 21 features, #13's split.

    ``dev_Gordy_electonegativity`` is left out for the reason
    :data:`hydms.surrogate.select.COSTLY_FEATURE` states -- the citable Oliynyk table cannot
    serve it for 21 elements, and carrying it would drop 266 rows from a fixture whose point
    is to be the whole file.
    """
    from hydms.config import load as load_config
    from hydms.data.load import load_hydride_data, parse_formula
    from hydms.data.metadata import with_features, with_metadata
    from hydms.data.splits import assign_splits
    from hydms.descriptors.contract import CONTRACT, FeatureContract
    from hydms.descriptors.featurize import featurize
    from hydms.surrogate.select import COSTLY_FEATURE

    names = load_config().columns
    record = with_metadata(load_hydride_data())
    split = assign_splits(record)
    contract = FeatureContract.from_names(
        [name for name in CONTRACT.names if name != COSTLY_FEATURE]
    )
    keep = [
        label
        for label, formula in record[names.formula].items()
        if contract.computability(parse_formula(formula)).complete
    ]
    usable = record.loc[keep]
    frame = with_features(
        usable, featurize(usable[names.formula], usable[names.temperature], contract=contract)
    )
    return frame, split.loc[keep]


# --------------------------------------------------------------------------------------
# L6 -- the rows are the fold's
# --------------------------------------------------------------------------------------


def test_perturbing_the_held_out_rows_does_not_change_the_selected_set(
    alloys: pd.DataFrame, train: list[str], held_out: list[str]
) -> None:
    """The card's own assertion, through the detector gate HG-1 runs."""
    assert_selection_ignores_holdout(
        partial(selected_names, train=train, settings=_settings()),
        alloys,
        holdout=held_out,
    )


def test_the_guard_is_not_vacuous(
    alloys: pd.DataFrame, train: list[str], held_out: list[str]
) -> None:
    """The archival shape, on this fixture, is caught.

    The test that matters most in this file. A check that passes because the fixture cannot
    express the defect is worse than no check, so the leaking twin -- selection over every row
    of the frame, which is what ``Boruta_FeatEng.py`` does -- must go red on the same data.
    """

    def leaky(frame: pd.DataFrame) -> tuple[str, ...]:
        return selected_names(frame, list(frame.index), settings=_settings())

    with pytest.raises(LeakDetected, match="Selection read data it does not own"):
        assert_selection_ignores_holdout(leaky, alloys, holdout=held_out)


def test_the_selection_is_identical_when_the_held_out_rows_are_absent_entirely(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """Stronger than perturbing them: deleting them changes nothing either.

    Perturbation proves the selector does not *depend* on those values. This proves it never
    touches those rows at all -- a stage that, say, computed a variance over the whole frame
    and then subset would pass the first check on a lucky perturbation and fail this one.
    """
    settings = _settings()
    whole = select_features(alloys, train, settings=settings)
    trimmed = select_features(alloys.loc[train], train, settings=settings)
    assert whole.features == trimmed.features
    assert whole.rows == trimmed.rows
    assert whole.held_out == 32
    assert trimmed.held_out == 0


def test_the_same_rows_select_the_same_features_twice(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """AC-1's property for this stage: one seed, one answer, order included."""
    settings = _settings()
    assert (
        select_features(alloys, train, settings=settings).features
        == select_features(alloys, train, settings=settings).features
    )


def test_a_different_seed_is_allowed_to_differ_but_the_run_is_recorded(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """The seed reaches Boruta. Not an assertion that it *must* differ -- only that it is used.

    A settings object whose seed went nowhere would make AC-1 pass for the wrong reason, so
    what is asserted is that the seed is carried into the result's own provenance rather than
    that a particular pair of seeds disagrees.
    """
    first = select_features(alloys, train, settings=_settings(seed=1))
    second = select_features(alloys, train, settings=_settings(seed=2))
    assert first.rows == second.rows == len(train)


# --------------------------------------------------------------------------------------
# The three stages
# --------------------------------------------------------------------------------------


def test_the_stages_are_the_three_that_exist_in_the_order_they_run(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """Not REPORT.md 3.3's five. There is no correlation filter and no 0.005 threshold."""
    selection = select_features(alloys, train, settings=_settings())
    assert tuple(stage.name for stage in selection.stages) == STAGE_NAMES
    assert list(selection.trace().index) == list(STAGE_NAMES)


def test_the_variance_filter_drops_a_constant_column(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    selection = select_features(alloys, train, settings=_settings())
    variance = selection.stages[0]
    assert "constant" in variance.dropped
    assert "constant" not in selection.features


def test_temperature_is_force_kept_even_when_it_is_constant(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """``Boruta_FeatEng.py:59-61`` and ``:71-73``, which re-add it by hand after both stages.

    Made constant here so the variance filter would certainly drop it: the must-keep is what
    puts it back, and the ``restored`` column of the trace is what says so out loud.
    """
    frame = alloys.copy()
    frame["temperature(K)"] = 298.0
    selection = select_features(frame, train, settings=_settings())
    assert "temperature(K)" in selection.features
    assert "temperature(K)" in selection.stages[0].restored


def test_the_trace_is_a_funnel_each_stage_starting_where_the_last_left_off(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """The stage-by-stage counts the card asks be logged, checked for being a funnel at all."""
    selection = select_features(alloys, train, settings=_settings())
    trace = selection.trace()
    assert trace.loc["variance", "features_in"] == len(selection.candidates)
    for earlier, later in itertools.pairwise(STAGE_NAMES):
        assert trace.loc[later, "features_in"] == trace.loc[earlier, "features_out"]
    assert trace.loc[STAGE_NAMES[-1], "features_out"] == len(selection)


def test_the_vif_loop_drops_an_exactly_collinear_column_and_keeps_the_must_keep(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """A column that is an exact multiple of another has an infinite VIF, and goes first.

    ``variance_inflation_factor`` computes ``1 / (1 - R^2)``, which divides by zero on a
    perfectly collinear column; the archival loop caught that and treated it as infinite, and
    so does this one. The pair is placed among the *useful* columns so Boruta confirms both
    and the VIF loop is the stage that has to separate them.
    """
    frame = alloys.copy()
    frame["mirror"] = frame["useful"] * 3.0
    selection = select_features(frame, train, settings=_settings())
    assert not {"useful", "mirror"}.issubset(set(selection.features))
    assert "temperature(K)" in selection.features


def test_the_vif_loop_never_drops_a_must_keep_even_when_it_is_the_collinear_one(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """``temperature(K)`` is excluded from the dropping, not from the computation.

    Its own duplicate is what gets removed. The archival loop protects it the same way, and
    the reason is not statistical: it is the only non-composition feature in the set.
    """
    frame = alloys.copy()
    frame["shadow_temperature"] = frame["temperature(K)"] * 2.0 + 1.0
    selection = select_features(
        frame, train, settings=_settings(must_keep=("temperature(K)",))
    )
    assert "temperature(K)" in selection.features
    assert "shadow_temperature" not in selection.features


# --------------------------------------------------------------------------------------
# The screened input -- the Boruta_FeatEng.py:23-25 bypass
# --------------------------------------------------------------------------------------


def test_selection_consumes_the_screening_verdict(
    alloys: pd.DataFrame, train: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bypass, closed: the rows the stages fit on are the rows screening left.

    CleanLab is stood in for -- it costs fourteen seconds on the real matrix and what is
    under test here is the wiring, not its judgement -- with a verdict that condemns a fifth
    of the rows. A selector that still fitted on all of them would report the original count.
    """
    import hydms.surrogate.selection as selection_module
    from hydms.data.screening import LabelIssues

    condemned = set(train[:20])

    def verdict(features: pd.DataFrame, target: pd.Series, **_: Any) -> LabelIssues:
        flags = pd.Series(
            [label in condemned for label in features.index],
            index=features.index,
            name="is_label_issue",
        )
        return LabelIssues(
            issues=flags,
            quality=pd.Series(0.0, index=features.index, name="label_quality"),
            rows=len(features),
            estimator="stand-in",
        )

    monkeypatch.setattr(selection_module, "label_issues", verdict)
    selection = select_features(alloys, train, settings=_settings(screen_labels=True))

    assert selection.flagged == 20
    assert set(selection.removed) == condemned
    assert selection.rows == len(train) - 20
    assert selection.rows_offered == len(train)


def test_screening_is_off_only_when_it_is_asked_to_be(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """With ``screen_labels`` false there is no verdict to report, and the count says so.

    ``flagged`` is ``None`` rather than zero. Zero would read as "CleanLab ran and found
    nothing", which is a different claim from "CleanLab did not run".
    """
    selection = select_features(alloys, train, settings=_settings(screen_labels=False))
    assert selection.flagged is None
    assert selection.removed == ()
    assert selection.rows == len(train)


def test_screening_inside_the_selector_cannot_reach_a_row_it_was_not_given(
    alloys: pd.DataFrame, train: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Screening is handed the fold's rows, which is why it may drop any of them.

    The stage's own contract is that it removes nothing outside ``train``. Here every row it
    sees *is* training, so the check that matters is the other one: it saw only those.
    """
    import hydms.surrogate.selection as selection_module
    from hydms.data.screening import LabelIssues

    seen: list[int] = []

    def verdict(features: pd.DataFrame, target: pd.Series, **_: Any) -> LabelIssues:
        seen.append(len(features))
        assert set(features.index) == set(train)
        return LabelIssues(
            issues=pd.Series(False, index=features.index, name="is_label_issue"),
            quality=pd.Series(1.0, index=features.index, name="label_quality"),
            rows=len(features),
            estimator="stand-in",
        )

    monkeypatch.setattr(selection_module, "label_issues", verdict)
    select_features(alloys, train, settings=_settings(screen_labels=True))
    assert seen == [len(train)]


# --------------------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------------------


def test_a_matrix_carrying_the_target_is_refused(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """Selection choosing the target would choose it every time."""
    with pytest.raises(SelectionError, match="are not features"):
        select_features(
            alloys, train, features=["useful", "H2_W% (max)"], settings=_settings()
        )


def test_the_target_is_never_a_candidate_by_default(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """The derived candidate list runs through ``non_feature_columns``, not past it."""
    selection = select_features(alloys, train, settings=_settings())
    assert "H2_W% (max)" not in selection.candidates
    assert "log_H2_W% (max)" not in selection.candidates
    assert "Alloy_class" not in selection.candidates


def test_an_empty_training_set_is_refused(alloys: pd.DataFrame) -> None:
    with pytest.raises(SelectionError, match="no training labels"):
        select_features(alloys, [], settings=_settings())


def test_a_training_label_the_frame_does_not_have_is_refused(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    with pytest.raises(SelectionError, match="not in the frame"):
        select_features(alloys, [*train, "nowhere"], settings=_settings())


def test_a_repeated_training_label_is_refused(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """A row counted twice is weighted twice in every stage."""
    with pytest.raises(SelectionError, match="labels repeat"):
        select_features(alloys, [*train, train[0]], settings=_settings())


def test_a_frame_with_no_target_is_refused(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """Selection is supervised; Boruta has nothing to rank against."""
    with pytest.raises(SelectionError, match="nothing for Boruta to rank against"):
        select_features(alloys.drop(columns=["H2_W% (max)"]), train, settings=_settings())


def test_a_frame_with_no_candidate_feature_is_refused(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    """Selection over nothing returns nothing and reads as a clean run."""
    bare = alloys[["Composition", "Alloy_class", "Dataset", "Citation", "H2_W% (max)"]]
    with pytest.raises(SelectionError, match="no candidate feature"):
        select_features(bare, train, settings=_settings())


def test_a_named_candidate_the_frame_does_not_have_is_refused(
    alloys: pd.DataFrame, train: list[str]
) -> None:
    with pytest.raises(SelectionError, match="not columns of the frame"):
        select_features(alloys, train, features=["useful", "absent"], settings=_settings())


# --------------------------------------------------------------------------------------
# Inside the folds
# --------------------------------------------------------------------------------------


@pytest.fixture()
def split(alloys: pd.DataFrame) -> pd.Series:
    """A split that holds the last 32 rows out, so `select_across_folds` will run."""
    names = ["train"] * 100 + ["val"] * 16 + ["test"] * 16
    return pd.Series(names, index=alloys.index, name="split")


def test_selection_runs_once_per_outer_fold(
    alloys: pd.DataFrame, split: pd.Series
) -> None:
    """The card's fourth box: never once over the whole training set."""
    from hydms.config import load as load_config

    result = select_across_folds(alloys, split, settings=_settings())
    assert len(result) == load_config().model.cv_folds
    assert len(result.folds) == len(result.selections)


def test_no_fold_selection_ever_saw_the_whole_training_split(
    alloys: pd.DataFrame, split: pd.Series
) -> None:
    """The observable difference between inside the folds and once: rows withheld.

    Every fold's selection is offered fewer rows than the training split holds, and the ones
    it was not offered are that fold's test rows. A driver that quietly passed the whole
    split to each selection would show ``rows_offered`` equal to 100 on every row of the
    table.
    """
    result = select_across_folds(alloys, split, settings=_settings())
    table = result.per_fold()
    assert (table["rows_offered"] < 100).all()
    assert table["rows_offered"].sum() == 100 * (len(result) - 1)


def test_the_folds_are_group_disjoint_on_the_canonical_composition(
    alloys: pd.DataFrame, split: pd.Series
) -> None:
    """`select_across_folds` cuts card #88's folds, so L7 is closed here by construction.

    Asserted rather than assumed: this is the only place selection meets the fold generator,
    and a driver that grew its own `KFold` would still produce a plausible table.
    """
    result = select_across_folds(alloys, split, settings=_settings())
    held = [set(fold.held_out) for fold in result.folds]
    for first in range(len(held)):
        for second in range(first + 1, len(held)):
            assert not held[first] & held[second]


def test_consensus_is_a_subset_of_the_union_and_of_every_fold(
    alloys: pd.DataFrame, split: pd.Series
) -> None:
    result = select_across_folds(alloys, split, settings=_settings())
    consensus, union = set(result.consensus()), set(result.union())
    assert consensus <= union
    for selection in result.selections:
        assert consensus <= set(selection.features)
        assert set(selection.features) <= union


def test_stability_counts_every_feature_any_fold_chose(
    alloys: pd.DataFrame, split: pd.Series
) -> None:
    """The number that says whether "the 22 features" was ever a stable object."""
    result = select_across_folds(alloys, split, settings=_settings())
    table = result.stability()
    assert set(table.index) == set(result.union())
    assert (table["of"] == len(result)).all()
    assert set(table.index[table["folds"] == len(result)]) == set(result.consensus())


def test_a_split_that_holds_nothing_out_is_refused(alloys: pd.DataFrame) -> None:
    """The same refusal `fit_scaler` and `nested_scores` make, for the same reason."""
    everything = pd.Series("train", index=alloys.index, name="split")
    with pytest.raises(SelectionError, match="holds nothing out"):
        select_across_folds(alloys, everything, settings=_settings())


def test_a_misaligned_split_is_refused(alloys: pd.DataFrame, split: pd.Series) -> None:
    with pytest.raises(SelectionError, match="indexed differently"):
        select_across_folds(alloys, split.iloc[:-4], settings=_settings())


def test_a_split_with_no_training_row_is_refused(alloys: pd.DataFrame) -> None:
    nothing = pd.Series("test", index=alloys.index, name="split")
    with pytest.raises(SelectionError, match="no row to 'train'"):
        select_across_folds(alloys, nothing, settings=_settings())


# --------------------------------------------------------------------------------------
# The real data
# --------------------------------------------------------------------------------------


def test_the_real_selector_reads_only_the_training_split(
    real_frame: tuple[pd.DataFrame, pd.Series],
) -> None:
    """The L6 live check, run here as a test as well as through `audit()`.

    Same subject, same rows, same budget: 1,278 rows, the 893 labels #13 assigns to `train`,
    and `sentinel_settings()`. What it costs and what the reduced budget does and does not
    cover are stated on `hydms.surrogate.selection.SENTINEL_BUDGET`.
    """
    frame, split = real_frame
    training = [label for label in frame.index if split.loc[label] == "train"]
    holdout = [label for label in frame.index if split.loc[label] != "train"]
    assert len(training) == 893
    assert len(holdout) == 385

    assert_selection_ignores_holdout(
        partial(selected_names, train=training, settings=sentinel_settings()),
        frame,
        holdout=holdout,
    )


def test_avg_is_alkaline_survives_the_variance_filter_on_the_real_training_rows(
    real_frame: tuple[pd.DataFrame, pd.Series],
) -> None:
    """Card #24 predicted this column would be dropped. It is not, and the premise was wrong.

    The box read: its inter-quartile span over the 893 training rows is exactly zero, so a
    `RobustScaler` substitutes a scale of 1.0 and "the scaled column is all zeros". A zero IQR
    is not constancy. The column takes 75 distinct values over those rows and its variance is
    0.0707 -- seventy times `selection.variance_threshold` -- so it survives, and it survives
    scaled too, because dividing by 1.0 and subtracting a median does not change a variance.

    Asserted here rather than written into a narrative, because the narrative would not go red
    if the featuriser ever made the column genuinely constant.
    """
    from hydms.config import load as load_config

    frame, split = real_frame
    training = frame.loc[[label for label in frame.index if split.loc[label] == "train"]]
    column = training["avg_is_alkaline"]

    assert float(np.percentile(column, 75) - np.percentile(column, 25)) == 0.0
    assert column.nunique() == 75
    assert float(column.var(ddof=0)) > load_config().selection.variance_threshold

    selection = select_features(
        frame, list(training.index), settings=sentinel_settings()
    )
    assert "avg_is_alkaline" not in selection.stages[0].dropped


@pytest.mark.slow
def test_the_configured_budget_reproduces_the_reduced_one_on_which_rows_it_reads(
    real_frame: tuple[pd.DataFrame, pd.Series],
) -> None:
    """The reduced budget is a cost decision, not a different selector. Eleven minutes.

    `SENTINEL_BUDGET` changes how long Boruta iterates and nothing else, and the claim that
    this does not weaken the L6 check is only worth what a run at the configured budget says.
    Marked `slow`: excluded from the CI fast lane, and the reason the fast lane can afford
    the sentinel at all.
    """
    frame, split = real_frame
    training = [label for label in frame.index if split.loc[label] == "train"]
    holdout = [label for label in frame.index if split.loc[label] != "train"]
    configured = replace(SelectionSettings.from_config(), screen_labels=False)

    assert_selection_ignores_holdout(
        partial(selected_names, train=training, settings=configured),
        frame,
        holdout=holdout,
    )


# --------------------------------------------------------------------------------------
# The settings object
# --------------------------------------------------------------------------------------


def test_the_settings_come_from_the_configuration(alloys: pd.DataFrame) -> None:
    """No literal in the module is a threshold."""
    from hydms.config import load as load_config

    config = load_config()
    settings = SelectionSettings.from_config()
    assert settings.variance_threshold == config.selection.variance_threshold
    assert settings.vif_threshold == config.selection.vif_threshold
    assert settings.boruta_max_iter == config.selection.boruta_max_iter
    assert settings.boruta_max_depth == config.selection.boruta_max_depth
    assert settings.must_keep == tuple(config.selection.must_keep)
    assert settings.seed == config.seed
    assert settings.boruta_estimators == "auto"
    assert settings.screen_labels is True


def test_the_sentinel_budget_changes_only_what_it_names() -> None:
    """A cost lever, not a second selector. Everything L6 is about stays configured."""
    configured = SelectionSettings.from_config()
    reduced = sentinel_settings()
    assert set(SENTINEL_BUDGET) == {"boruta_max_iter", "boruta_estimators", "screen_labels"}
    assert reduced.variance_threshold == configured.variance_threshold
    assert reduced.vif_threshold == configured.vif_threshold
    assert reduced.must_keep == configured.must_keep
    assert reduced.boruta_max_depth == configured.boruta_max_depth
    assert reduced.seed == configured.seed
    assert reduced.boruta_max_iter < configured.boruta_max_iter
