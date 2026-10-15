"""L3 -- the scaler is fitted once, on train, and can never be fitted again. Card #23.

Four properties, and each is a defect that has happened in a published hydride pipeline:

  - **The fit sees the training rows and nothing else.** Not by convention: :func:`fit_scaler`
    is handed the whole matrix with the split assignment and selects the rows itself, and it
    refuses a split that holds nothing out.
  - **The loaded object has no ``fit``.** ``fit``, ``fit_transform`` and ``partial_fit`` raise
    and say why. The property survives a round trip through the artifact store, which is what
    "versioned with the model" means in practice.
  - **The batch is scaled by name.** A permuted matrix comes back correct rather than
    plausible-and-wrong, and the output order is always the fitting order, which is what the
    model downstream needs.
  - **Twice is the same.** The scaler holds no state a transform can move, so the same batch
    scales identically however many other batches went through in between.

The parity test at the bottom measures the module docstring's claim -- that
``(x - centre) / scale`` is bit-identical to ``RobustScaler.transform`` -- against the real
1,278 x 21 training matrix rather than trusting the sentence.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from hydms.data.metadata import MetadataError  # noqa: E402
from hydms.surrogate.scaler import (  # noqa: E402
    QUANTILE_RANGE,
    SCALER_PAYLOAD,
    FittedScaler,
    ScalerError,
    fit_scaler,
    scaler_from,
)

FEATURES = ["avg_atom_mass", "dev_atom_mass", "temperature(K)"]


# --------------------------------------------------------------------------------------
# Fixtures -- a small matrix whose held-out rows are nothing like its training rows
# --------------------------------------------------------------------------------------


@pytest.fixture()
def matrix() -> pd.DataFrame:
    """Eight rows. The last two are off the scale of the first six, deliberately.

    If a fit ever reaches them the median and the span both move, which is what the
    fit-on-train tests read.
    """
    return pd.DataFrame(
        {
            "avg_atom_mass": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 5000.0, 6000.0],
            "dev_atom_mass": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 700.0, 800.0],
            "temperature(K)": [298.0, 303.0, 313.0, 323.0, 333.0, 343.0, 900.0, 950.0],
        },
        index=[f"r{n}" for n in range(8)],
    )


@pytest.fixture()
def split(matrix: pd.DataFrame) -> pd.Series:
    """Six training rows, one validation row, one test row -- on the matrix's own index."""
    return pd.Series(
        ["train"] * 6 + ["val", "test"], index=matrix.index, name="split"
    )


@pytest.fixture()
def scaler(matrix: pd.DataFrame, split: pd.Series) -> FittedScaler:
    return fit_scaler(matrix, split)


# --------------------------------------------------------------------------------------
# The fit sees the training rows and nothing else
# --------------------------------------------------------------------------------------


def test_the_fit_uses_only_the_training_rows(
    matrix: pd.DataFrame, split: pd.Series, scaler: FittedScaler
) -> None:
    """Centre and scale are the training rows' statistics, not the whole matrix's."""
    train = matrix.loc[split == "train"]
    expected_centre = train.median()
    low, high = train.quantile([0.25, 0.75]).to_numpy()

    assert scaler.feature_names == tuple(FEATURES)
    assert scaler.centre == pytest.approx(tuple(expected_centre[FEATURES]))
    assert scaler.scale == pytest.approx(tuple(high - low))

    # And they are nothing like the whole matrix's, so the test can tell the two apart.
    assert scaler.centre[0] != pytest.approx(float(matrix["avg_atom_mass"].median()))


def test_the_fit_records_what_it_saw_and_what_it_did_not(scaler: FittedScaler) -> None:
    assert scaler.fitted_on == "train"
    assert scaler.fitted_rows == 6
    assert scaler.held_out_rows == 2
    assert scaler.quantile_range == QUANTILE_RANGE
    assert len(scaler) == 3
    assert "temperature(K)" in scaler


def test_a_split_that_holds_nothing_out_is_refused(matrix: pd.DataFrame) -> None:
    """The guard that stops "fit on train" from being satisfied by relabelling."""
    everything = pd.Series("train", index=matrix.index, name="split")
    with pytest.raises(ScalerError) as exc:
        fit_scaler(matrix, everything)
    assert "every one of 8 row(s)" in str(exc.value)
    assert "pre-filtered training subset" in str(exc.value)


def test_a_split_with_no_rows_for_the_named_one_is_refused(matrix: pd.DataFrame) -> None:
    split = pd.Series(["val"] * 4 + ["test"] * 4, index=matrix.index, name="split")
    with pytest.raises(ScalerError, match="no row is assigned to 'train'"):
        fit_scaler(matrix, split)


def test_a_split_that_is_not_a_split_name_is_refused(
    matrix: pd.DataFrame, split: pd.Series
) -> None:
    with pytest.raises(ScalerError, match="'training' is not a split"):
        fit_scaler(matrix, split, on="training")


def test_a_split_on_a_different_index_is_refused(matrix: pd.DataFrame) -> None:
    """Paired by label, never by position -- leak L9 in a new place."""
    positional = pd.Series(["train"] * 6 + ["val", "test"], name="split")
    with pytest.raises(ScalerError) as exc:
        fit_scaler(matrix, positional)
    assert "does not line up" in str(exc.value)
    assert "leak L9" in str(exc.value)


def test_a_split_in_a_different_order_is_refused(
    matrix: pd.DataFrame, split: pd.Series
) -> None:
    with pytest.raises(ScalerError, match="in a different order"):
        fit_scaler(matrix, split.iloc[::-1])


def test_a_matrix_carrying_the_target_is_refused(
    matrix: pd.DataFrame, split: pd.Series
) -> None:
    """`refuse_non_features` runs at fit time, where the feature set is established."""
    contaminated = matrix.assign(**{"H2_W% (max)": 1.0})
    with pytest.raises(MetadataError, match="predicting its own input"):
        fit_scaler(contaminated, split)


def test_a_repeated_column_is_refused(matrix: pd.DataFrame, split: pd.Series) -> None:
    """`temperature(K)` is a raw column and a feature; a positional concat returns it twice."""
    doubled = pd.concat([matrix, matrix[["temperature(K)"]]], axis=1)
    with pytest.raises(ScalerError, match="repeats column"):
        fit_scaler(doubled, split)


def test_a_non_numeric_column_is_refused(matrix: pd.DataFrame, split: pd.Series) -> None:
    with pytest.raises(ScalerError, match="are not numeric"):
        fit_scaler(matrix.assign(shape="cubic"), split)


def test_a_non_finite_value_in_the_training_rows_is_refused(
    matrix: pd.DataFrame, split: pd.Series
) -> None:
    holed = matrix.copy()
    holed.loc["r2", "dev_atom_mass"] = np.nan
    with pytest.raises(ScalerError) as exc:
        fit_scaler(holed, split)
    assert "'dev_atom_mass'" in str(exc.value)
    assert "would then scale to NaN" in str(exc.value)


def test_a_non_finite_value_outside_the_training_rows_is_not_this_functions_business(
    matrix: pd.DataFrame, split: pd.Series
) -> None:
    """The fit only reads the training rows, so only those can stop it."""
    holed = matrix.copy()
    holed.loc["r7", "dev_atom_mass"] = np.inf
    assert fit_scaler(holed, split).fitted_rows == 6


def test_fitting_on_something_that_is_not_a_frame_is_refused(split: pd.Series) -> None:
    with pytest.raises(ScalerError, match="not a ndarray"):
        fit_scaler(np.zeros((8, 3)), split)  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# The batch is scaled by name, in fitting order
# --------------------------------------------------------------------------------------


def test_transform_centres_and_scales(scaler: FittedScaler, matrix: pd.DataFrame) -> None:
    scaled = scaler.transform(matrix)
    centre = np.asarray(scaler.centre)
    scale = np.asarray(scaler.scale)
    expected = (matrix[FEATURES].to_numpy() - centre) / scale
    assert np.array_equal(scaled.to_numpy(), expected)
    assert list(scaled.columns) == FEATURES
    assert scaled.index.equals(matrix.index)
    assert (scaled.dtypes == "float64").all()


def test_a_permuted_batch_comes_back_in_fitting_order_and_correct(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    """The AC-4 failure mode, closed: the caller's order does not reach the model."""
    permuted = matrix[["temperature(K)", "avg_atom_mass", "dev_atom_mass"]]
    assert list(scaler.transform(permuted).columns) == FEATURES
    pd.testing.assert_frame_equal(scaler.transform(permuted), scaler.transform(matrix))


def test_an_array_is_refused_because_it_carries_no_names(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    """scikit-learn accepts one with a UserWarning; that is the door this closes."""
    with pytest.raises(ScalerError) as exc:
        scaler.transform(matrix.to_numpy())  # type: ignore[arg-type]
    assert "AC-4" in str(exc.value)


def test_a_missing_or_unexpected_column_is_named(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    with pytest.raises(ScalerError) as exc:
        scaler.transform(matrix.drop(columns=["dev_atom_mass"]).assign(avg_radius=1.0))
    message = str(exc.value)
    assert "1 missing: 'dev_atom_mass'" in message
    assert "1 unexpected: 'avg_radius'" in message


def test_a_batch_repeating_a_column_is_refused(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    doubled = matrix[[*FEATURES, "temperature(K)"]]
    with pytest.raises(ScalerError, match="repeats column"):
        scaler.transform(doubled)


def test_a_non_finite_candidate_is_refused_with_its_row_named(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    holed = matrix.copy()
    holed.loc["r3", "avg_atom_mass"] = np.nan
    with pytest.raises(ScalerError) as exc:
        scaler.transform(holed)
    message = str(exc.value)
    assert "1 of 8 row(s)" in message
    assert "'avg_atom_mass'" in message
    assert "'r3'" in message


def test_transform_does_not_touch_the_batch_it_was_given(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    before = matrix.copy(deep=True)
    scaler.transform(matrix)
    pd.testing.assert_frame_equal(matrix, before)


# --------------------------------------------------------------------------------------
# Twice is the same -- the card's fourth box
# --------------------------------------------------------------------------------------


def test_scaling_a_candidate_batch_twice_is_identical(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    candidates = matrix.iloc[:3]
    first = scaler.transform(candidates)
    second = scaler.transform(candidates)
    pd.testing.assert_frame_equal(first, second, check_exact=True)


def test_another_batch_in_between_changes_nothing(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    """The defect memo 4.3 names: a candidate scored differently for its company."""
    candidates = matrix.iloc[:3]
    alone = scaler.transform(candidates)
    scaler.transform(matrix)
    scaler.transform(matrix.iloc[6:] * 1000)
    pd.testing.assert_frame_equal(scaler.transform(candidates), alone, check_exact=True)


def test_a_candidate_scales_the_same_alone_as_in_a_crowd(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    crowd = scaler.transform(matrix)
    alone = scaler.transform(matrix.loc[["r7"]])
    assert np.array_equal(alone.to_numpy(), crowd.loc[["r7"]].to_numpy())


def test_the_statistics_are_unchanged_by_transforming(
    scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    before = (scaler.centre, scaler.scale, scaler.fitted_rows)
    scaler.transform(matrix * 1e6)
    assert (scaler.centre, scaler.scale, scaler.fitted_rows) == before


# --------------------------------------------------------------------------------------
# There is no fit on it
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("method", ["fit", "fit_transform", "partial_fit"])
def test_the_fitting_methods_raise_and_say_why(
    scaler: FittedScaler, matrix: pd.DataFrame, method: str
) -> None:
    with pytest.raises(ScalerError) as exc:
        getattr(scaler, method)(matrix)
    message = str(exc.value)
    assert f"{method}() does not exist" in message
    assert "centres them on themselves" in message


def test_the_object_is_immutable(scaler: FittedScaler) -> None:
    with pytest.raises(FrozenInstanceError, match="cannot assign to field"):
        scaler.centre = (0.0, 0.0, 0.0)  # type: ignore[misc]


# --------------------------------------------------------------------------------------
# A zero span, which is invisible after the fit
# --------------------------------------------------------------------------------------


def test_a_constant_feature_is_recorded_rather_than_left_as_a_scale_of_one(
    matrix: pd.DataFrame, split: pd.Series
) -> None:
    """`RobustScaler` substitutes 1.0 for a zero span, so 1.0 alone cannot be read back."""
    flat = matrix.assign(avg_is_alkaline=0.0)
    scaler = fit_scaler(flat, split)
    position = scaler.feature_names.index("avg_is_alkaline")
    assert scaler.scale[position] == 1.0
    assert scaler.degenerate == ("avg_is_alkaline",)
    assert (scaler.transform(flat)["avg_is_alkaline"] == 0.0).all()


def test_a_span_of_exactly_one_is_not_called_degenerate(
    matrix: pd.DataFrame, split: pd.Series
) -> None:
    """The ambiguity the `degenerate` field exists to remove, from the other side."""
    # Six evenly spaced training values with step 0.4: the linear-interpolation quartiles
    # sit at 0.4 and 1.4, so the span is exactly 1.0 -- the same number a zero span is
    # substituted with.
    unit = matrix.assign(avg_unit=[0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 9.0, 9.0])
    scaler = fit_scaler(unit, split)
    position = scaler.feature_names.index("avg_unit")
    assert scaler.scale[position] == 1.0
    assert scaler.degenerate == ()


def test_describe_is_one_row_per_feature(scaler: FittedScaler) -> None:
    table = scaler.describe()
    assert list(table.index) == FEATURES
    assert list(table.columns) == ["centre", "scale", "degenerate"]
    assert not table["degenerate"].any()


# --------------------------------------------------------------------------------------
# The type refuses to be built wrong by hand
# --------------------------------------------------------------------------------------


def _fitted(**overrides: Any) -> FittedScaler:
    fields: dict[str, Any] = {
        "feature_names": ("a", "b"),
        "centre": (0.0, 0.0),
        "scale": (1.0, 1.0),
        "fitted_on": "train",
        "fitted_rows": 6,
        "held_out_rows": 2,
        "quantile_range": QUANTILE_RANGE,
    }
    fields.update(overrides)
    return FittedScaler(**fields)


def test_a_scaler_over_no_features_is_refused() -> None:
    with pytest.raises(ScalerError, match="scales nothing"):
        _fitted(feature_names=(), centre=(), scale=())


def test_a_repeated_feature_name_is_refused() -> None:
    with pytest.raises(ScalerError, match="more than once"):
        _fitted(feature_names=("a", "a"))


def test_mismatched_widths_are_refused() -> None:
    with pytest.raises(ScalerError, match="one centre and one scale per feature"):
        _fitted(scale=(1.0, 1.0, 1.0))


def test_a_zero_scale_is_refused_because_it_divides_by_zero() -> None:
    with pytest.raises(ScalerError, match="scale of zero"):
        _fitted(scale=(1.0, 0.0))


def test_a_non_finite_statistic_is_refused() -> None:
    with pytest.raises(ScalerError, match="not a finite number"):
        _fitted(centre=(0.0, np.nan))


def test_a_degenerate_name_that_is_not_a_feature_is_refused() -> None:
    with pytest.raises(ScalerError, match="are not features of this scaler"):
        _fitted(degenerate=("c",))


# --------------------------------------------------------------------------------------
# Versioned with the model: the round trip through the artifact store
# --------------------------------------------------------------------------------------


CONTRACT_PAYLOAD = {
    "features": [
        {"name": name, "statistic": "avg", "table": "oliynyk",
         "property": "atom_mass", "dtype": "float64"}
        for name in FEATURES
    ]
}


@pytest.fixture()
def saved(tmp_path: Path, scaler: FittedScaler) -> Any:
    """A v1 holding the fitted scaler, loaded back with gates deliberately unchecked.

    `require_gates=False` is the window card #4 opened for exactly this: a version saved
    before #31/#32/#33 exist records no passing gate run and therefore cannot load without
    it. It closes at #34, and the delivery path never passes it.
    """
    pytest.importorskip("joblib", reason="the artifact store persists through joblib")
    from hydms.artifacts import load, save

    save(
        {SCALER_PAYLOAD: scaler},
        contract=CONTRACT_PAYLOAD,
        seeds={"pipeline": 42},
        store=tmp_path,
    )
    return load("v1", store=tmp_path, require_gates=False)


def test_a_scaler_survives_the_round_trip_and_scales_identically(
    saved: Any, scaler: FittedScaler, matrix: pd.DataFrame
) -> None:
    restored = scaler_from(saved)
    assert restored == scaler
    pd.testing.assert_frame_equal(
        restored.transform(matrix), scaler.transform(matrix), check_exact=True
    )


def test_the_restored_scaler_still_has_no_fit(saved: Any, matrix: pd.DataFrame) -> None:
    """The card's structural guard, asserted on the object that came off disk."""
    with pytest.raises(ScalerError, match="does not exist on a fitted scaler"):
        scaler_from(saved).fit(matrix)


def test_a_version_holding_a_raw_estimator_is_refused(
    tmp_path: Path, matrix: pd.DataFrame
) -> None:
    """What a version written before this card holds: something with a `fit` on it."""
    pytest.importorskip("joblib", reason="the artifact store persists through joblib")
    preprocessing = pytest.importorskip(
        "sklearn.preprocessing", reason="scikit-learn is core"
    )
    from hydms.artifacts import load, save

    save(
        {SCALER_PAYLOAD: preprocessing.RobustScaler().fit(matrix)},
        contract=CONTRACT_PAYLOAD,
        seeds={"pipeline": 42},
        store=tmp_path,
    )
    bundle = load("v1", store=tmp_path, require_gates=False)
    with pytest.raises(ScalerError) as exc:
        scaler_from(bundle)
    assert "RobustScaler, not a FittedScaler" in str(exc.value)


def test_a_scaler_scaling_a_feature_the_contract_never_declared_is_refused(
    tmp_path: Path, matrix: pd.DataFrame, split: pd.Series
) -> None:
    """Two runs assembled into one version: the featuriser cannot build that column."""
    pytest.importorskip("joblib", reason="the artifact store persists through joblib")
    from hydms.artifacts import load, save

    wider = fit_scaler(matrix.assign(avg_radius=[1.0, 2, 3, 4, 5, 6, 70, 80]), split)
    save(
        {SCALER_PAYLOAD: wider},
        contract=CONTRACT_PAYLOAD,
        seeds={"pipeline": 42},
        store=tmp_path,
    )
    bundle = load("v1", store=tmp_path, require_gates=False)
    with pytest.raises(ScalerError) as exc:
        scaler_from(bundle)
    assert "'avg_radius'" in str(exc.value)


def test_a_narrower_scaler_is_accepted_because_selection_is_expected_to_narrow_it(
    tmp_path: Path, matrix: pd.DataFrame, split: pd.Series
) -> None:
    """#24 selects a subset; the check is a subset check, not an equality one."""
    pytest.importorskip("joblib", reason="the artifact store persists through joblib")
    from hydms.artifacts import load, save

    narrow = fit_scaler(matrix[["avg_atom_mass", "temperature(K)"]], split)
    save(
        {SCALER_PAYLOAD: narrow},
        contract=CONTRACT_PAYLOAD,
        seeds={"pipeline": 42},
        store=tmp_path,
    )
    bundle = load("v1", store=tmp_path, require_gates=False)
    assert scaler_from(bundle).feature_names == ("avg_atom_mass", "temperature(K)")


def test_a_bundle_without_a_scaler_names_what_it_does_hold(
    tmp_path: Path,
) -> None:
    pytest.importorskip("joblib", reason="the artifact store persists through joblib")
    from hydms.artifacts import load, save

    save({"model": {"trees": 1}}, contract=CONTRACT_PAYLOAD, seeds={"pipeline": 42},
         store=tmp_path)
    bundle = load("v1", store=tmp_path, require_gates=False)
    with pytest.raises(KeyError, match="model"):
        scaler_from(bundle)


# --------------------------------------------------------------------------------------
# Parity with scikit-learn, on the real training matrix
# --------------------------------------------------------------------------------------


@pytest.fixture()
def real_training_matrix(hydride_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """The real feature matrix and its split assignment, built the way the pipeline will.

    Twenty-one features, not twenty-two: ``dev_Gordy_electonegativity`` refuses 266 of the
    1,279 rows because the citable 2024 Oliynyk edition leaves ``gordy_en`` blank for 21
    elements. Without it the remaining 21 cover every row but one -- ``Eu1Ni5``, whose jarvis
    cells are empty for six features. That trade is cards #24 and #25', and it is taken here
    only so the parity check runs on the real thing rather than on a fixture.

    The refused rows are found by asking the contract per *element* rather than per row: a
    hole is a (feature, element) pair, so an element that blocks any feature blocks every
    composition containing it. Fifty-odd verdicts instead of 1,279.
    """
    pytest.importorskip("sklearn", reason="the split protocol and the fit are scikit-learn's")
    from hydms.data.load import parse_formula
    from hydms.data.splits import assign_splits
    from hydms.descriptors.contract import CONTRACT, FeatureContract
    from hydms.descriptors.featurize import featurize

    contract = FeatureContract.from_names(
        [name for name in CONTRACT.names if name != "dev_Gordy_electonegativity"]
    )
    split = assign_splits(hydride_raw)
    parsed = {label: parse_formula(text) for label, text in hydride_raw["Composition"].items()}
    universe = sorted({element for amounts in parsed.values() for element in amounts})
    blocking = {
        element for element in universe if not contract.computability([element]).complete
    }
    keep = [
        label for label, amounts in parsed.items() if not blocking & set(amounts)
    ]
    rows = hydride_raw.loc[keep]
    features = featurize(rows["Composition"], rows["temperature(K)"], contract=contract)
    return features, split.loc[keep]


def test_the_real_matrix_is_1278_rows_of_21_features(
    real_training_matrix: tuple[pd.DataFrame, pd.Series],
) -> None:
    features, split = real_training_matrix
    assert features.shape == (1278, 21)
    assert int((split == "train").sum()) == 893


def test_the_transform_is_bit_identical_to_robustscalers(
    real_training_matrix: tuple[pd.DataFrame, pd.Series],
) -> None:
    """The module docstring's claim, measured rather than trusted.

    Bit-identical, not within a tolerance: both are an elementwise float64 subtract followed
    by an elementwise float64 divide, and there is no reduction to reassociate. If this ever
    goes red, `hydms.surrogate.scaler` has stopped doing `RobustScaler`'s arithmetic and the
    published fit is no longer reproducible.
    """
    from sklearn.preprocessing import RobustScaler

    features, split = real_training_matrix
    ours = fit_scaler(features, split)
    theirs = RobustScaler(quantile_range=QUANTILE_RANGE).fit(features.loc[split == "train"])

    assert np.array_equal(np.asarray(ours.centre), theirs.center_)
    assert np.array_equal(np.asarray(ours.scale), theirs.scale_)
    assert np.array_equal(ours.transform(features).to_numpy(), theirs.transform(features))


def test_one_published_feature_is_constant_over_the_training_split(
    real_training_matrix: tuple[pd.DataFrame, pd.Series],
) -> None:
    """`avg_is_alkaline`. Not this card's to remove -- #24's variance filter is 0.001 -- but
    a scale of 1.0 stops being readable as "the span was zero" the moment the fit is over."""
    features, split = real_training_matrix
    scaler = fit_scaler(features, split)
    assert scaler.degenerate == ("avg_is_alkaline",)
    assert scaler.fitted_rows == 893
    assert scaler.held_out_rows == 385
