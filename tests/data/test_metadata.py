"""L1 -- the metadata boundary, and the alloy class that has to cross it. Card #12.

Three questions:

  - **Does the class survive, correctly, for every row?** Reconciliation on the canonical key
    relabels 13 of 1279 rows and must lose none of them. The distribution is checked class by
    class, not as a total, because a total hides two classes trading rows.
  - **Can AC-6 be run on the result?** Leave-one-alloy-class-out needs ten non-empty folds
    counted in *compositions*, not rows. That is measured here rather than assumed, because
    it is the reason this card exists at all.
  - **Can a non-feature reach the model?** ``refuse_non_features`` is the last gate before a
    fit. The worst case it catches is not the alloy class -- it is the target.

The L13 sentinel's ``live`` hook is **not** here -- it lives in ``hydms/qa/sentinels.py`` and
runs the real featuriser, and the path it exercises end to end is asserted in
``tests/leaks/test_l13_class_survival.py``. What is here is the join it goes through:
``with_features``, tested on frames small enough to read, including every way it refuses.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the data layer is pandas frames end to end")

import pandas as pd  # noqa: E402  -- only importable once the skip above has passed
from hydms.config import load as load_config  # noqa: E402
from hydms.data.canonical import (  # noqa: E402
    ALLOY_CLASS_PRECEDENCE,
    CanonicalisationError,
)
from hydms.data.load import HYDRIDE_ALLOY_CLASSES, load_hydride_data  # noqa: E402
from hydms.data.metadata import (  # noqa: E402
    CANONICAL_KEY_COLUMN,
    MetadataError,
    class_distribution,
    metadata_columns,
    non_feature_columns,
    refuse_non_features,
    with_features,
    with_metadata,
)
from hydms.data.target import model_space_name  # noqa: E402

CLASS = "Alloy_class"


@pytest.fixture(scope="module")
def curated() -> pd.DataFrame:
    """The curated dataset, loaded once. Read-only: nothing here mutates it."""
    return load_hydride_data()


@pytest.fixture(scope="module")
def resolved(curated: pd.DataFrame) -> pd.DataFrame:
    return with_metadata(curated)


# --------------------------------------------------------------------------------------
# The class survives, for every row
# --------------------------------------------------------------------------------------


def test_every_row_survives_with_its_own_index_label(curated, resolved) -> None:
    assert len(resolved) == len(curated) == 1279
    assert resolved.index.equals(curated.index)


def test_the_input_frame_is_not_mutated(curated) -> None:
    before = curated[CLASS].tolist()
    with_metadata(curated)
    assert curated[CLASS].tolist() == before
    assert CANONICAL_KEY_COLUMN not in curated.columns


def test_the_ten_declared_classes_are_all_present_and_no_eleventh_appears(resolved) -> None:
    present = set(resolved[CLASS].unique())
    assert present == set(HYDRIDE_ALLOY_CLASSES)


def test_thirteen_rows_are_relabelled_and_the_totals_do_not_move(curated, resolved) -> None:
    changed = curated[CLASS] != resolved[CLASS]
    assert int(changed.sum()) == 13
    assert len(resolved) == len(curated)


def test_the_distribution_moves_into_the_structural_families(curated) -> None:
    """Class by class, not as a total. Measured during card #12; a change here is a change
    to every AC-6 fold, so it fails with the whole table rather than one number."""
    expected = {
        "AB5": (196, 196),
        "AB2": (368, 371),
        "AB": (90, 90),
        "A2B": (27, 32),
        "Mg": (148, 148),
        "HEA": (77, 77),
        "MEA": (110, 109),
        "LEA": (28, 26),
        "SS": (103, 103),
        "MIC": (132, 127),
    }
    table = class_distribution(curated)
    actual = {name: (int(row.raw), int(row.reconciled)) for name, row in table.iterrows()}
    assert actual == expected, f"\n{table}"
    assert int(table["raw"].sum()) == int(table["reconciled"].sum()) == 1279
    assert int(table["delta"].abs().sum()) == 16  # 8 rows out, 8 in, counted both ways


def test_the_distribution_is_reported_in_precedence_order(curated) -> None:
    table = class_distribution(curated)
    assert list(table.index) == list(ALLOY_CLASS_PRECEDENCE)


def test_two_spellings_of_one_material_receive_one_label(resolved) -> None:
    """``Ce1Mg12`` is ``MIC`` in the file and ``Mg12Ce1`` is ``Mg``. A fold that holds out a
    class must hold out every row of it, so the pair cannot keep two answers."""
    pair = resolved[resolved["Composition"].str.strip().isin(("Ce1Mg12", "Mg12Ce1"))]
    assert len(pair) >= 2
    assert set(pair[CANONICAL_KEY_COLUMN]) == {pair[CANONICAL_KEY_COLUMN].iloc[0]}
    assert set(pair[CLASS]) == {pair[CLASS].iloc[0]}


def test_every_composition_has_exactly_one_class(resolved) -> None:
    per_key = resolved.groupby(CANONICAL_KEY_COLUMN)[CLASS].nunique()
    assert len(per_key) == 1115
    assert per_key.max() == 1


# --------------------------------------------------------------------------------------
# AC-6 is feasible on the result
# --------------------------------------------------------------------------------------


def test_leave_one_class_out_has_ten_non_trivial_folds(curated) -> None:
    """Counted in compositions, because #88's folds group on the canonical key. The smallest
    fold is A2B with 24 materials; a class down to one material would make AC-6 a coin toss
    rather than a validation."""
    table = class_distribution(curated)
    assert len(table) == 10
    assert int(table["compositions"].min()) == 24
    assert int(table["compositions"].sum()) == 1115


# --------------------------------------------------------------------------------------
# No eleventh label
# --------------------------------------------------------------------------------------


def test_a_missing_class_refuses_rather_than_becoming_unknown(curated) -> None:
    """The card asked for ``UNKNOWN``. The curated file needs none -- the class is complete on
    all 1279 rows -- and an eleventh label changes the fold structure of AC-6, so a gap is a
    decision to make deliberately rather than a default to fall into."""
    holed = curated.copy()
    holed.loc[holed.index[3], CLASS] = None
    with pytest.raises(CanonicalisationError, match="no 'Alloy_class'"):
        with_metadata(holed)


def test_a_label_outside_the_vocabulary_refuses(curated) -> None:
    holed = curated.copy()
    holed.loc[holed.index[3], CLASS] = "UNKNOWN"
    with pytest.raises(CanonicalisationError, match="UNKNOWN"):
        with_metadata(holed)


# --------------------------------------------------------------------------------------
# Nothing that is not a feature reaches the model
# --------------------------------------------------------------------------------------


def test_the_two_column_lists_say_what_they_are_for() -> None:
    names = load_config().columns
    metadata = metadata_columns()
    assert set(metadata) == {
        names.formula,
        names.alloy_class,
        names.dataset,
        names.citation,
        CANONICAL_KEY_COLUMN,
    }
    assert names.target not in metadata, "a stage may drop the target; it may not drop the class"
    assert set(non_feature_columns()) == set(metadata) | {
        names.target,
        model_space_name(names.target),
    }


def test_a_clean_feature_matrix_passes() -> None:
    refuse_non_features(pd.DataFrame({"temperature(K)": [300.0], "avg_Density": [7.0]}))


@pytest.mark.parametrize("intruder", list(metadata_columns()))
def test_every_metadata_column_is_refused_in_a_feature_matrix(intruder) -> None:
    features = pd.DataFrame({"temperature(K)": [300.0], intruder: ["whatever"]})
    with pytest.raises(MetadataError, match="not features"):
        refuse_non_features(features)


@pytest.mark.parametrize("space", ["H2_W% (max)", "log_H2_W% (max)"])
def test_the_target_in_either_space_is_refused_and_named_as_the_target(space) -> None:
    """The one that would look like an excellent model rather than like a bug."""
    features = pd.DataFrame({"temperature(K)": [300.0], space: [1.4]})
    with pytest.raises(MetadataError, match="predicting its own input"):
        refuse_non_features(features)


def test_the_message_names_every_offender_not_the_first() -> None:
    features = pd.DataFrame(
        {"temperature(K)": [300.0], "Alloy_class": ["AB5"], "Citation": ["url"]}
    )
    with pytest.raises(MetadataError) as caught:
        refuse_non_features(features)
    message = str(caught.value)
    assert "2 column(s)" in message
    assert "Alloy_class" in message
    assert "Citation" in message


# --------------------------------------------------------------------------------------
# The join: the record and the matrix, side by side
# --------------------------------------------------------------------------------------


@pytest.fixture()
def record() -> pd.DataFrame:
    """Three rows shaped like `with_metadata`'s output, on a non-trivial index.

    The labels are deliberately neither sorted nor a range: a positional join and a label join
    agree on a `RangeIndex`, and a fixture that cannot tell them apart is describing rather
    than testing.
    """
    return pd.DataFrame(
        {
            "Composition": ["LaNi5", "TiFe", "Mg2Ni"],
            "Alloy_class": ["AB5", "AB", "A2B"],
            "Dataset": ["HydPark", "HydPark", "Extracted"],
            "Citation": ["a", "b", "c"],
            CANONICAL_KEY_COLUMN: ["La0.1667Ni0.8333", "Fe0.5Ti0.5", "Mg0.6667Ni0.3333"],
            "H2_W% (max)": [1.4, 1.9, 3.6],
            "temperature(K)": [298, 313, 573],
        },
        index=["r-9", "r-1", "r-5"],
    )


@pytest.fixture()
def matrix(record: pd.DataFrame) -> pd.DataFrame:
    """What a featuriser returns: float64 features on the caller's own labels."""
    return pd.DataFrame(
        {
            "avg_Density": [7.9, 6.5, 3.1],
            "temperature(K)": [298.0, 313.0, 573.0],
        },
        index=record.index,
    )


def test_the_record_and_the_matrix_come_back_as_one_frame(record, matrix) -> None:
    joined = with_features(record, matrix)

    assert list(joined.index) == list(record.index), "the record's rows, in the record's order"
    for name in metadata_columns():
        assert name in joined.columns
    assert list(joined["Alloy_class"]) == ["AB5", "AB", "A2B"]
    assert "avg_Density" in joined.columns
    assert list(joined.columns).count("temperature(K)") == 1


def test_the_input_frames_are_not_mutated(record, matrix) -> None:
    with_features(record, matrix)
    assert record["temperature(K)"].dtype == "int64"
    assert list(matrix.columns) == ["avg_Density", "temperature(K)"]


def test_the_matrix_may_not_carry_a_non_feature(record, matrix) -> None:
    """The first refusal, and the one that keeps the target out of a fit."""
    matrix["H2_W% (max)"] = [1.4, 1.9, 3.6]
    with pytest.raises(MetadataError, match="predicting its own input"):
        with_features(record, matrix)


def test_a_matrix_on_another_index_is_refused_rather_than_zipped(record, matrix) -> None:
    with pytest.raises(MetadataError, match="leak L9"):
        with_features(record, matrix.reset_index(drop=True))


def test_a_matrix_missing_a_row_is_refused(record, matrix) -> None:
    """The shape a featuriser that drops what it cannot parse would produce."""
    with pytest.raises(MetadataError) as caught:
        with_features(record, matrix.drop(index=["r-1"]))
    assert "3 record row(s) and 2 feature row(s)" in str(caught.value)


def test_the_same_rows_in_another_order_are_refused(record, matrix) -> None:
    """`concat` aligns on labels, so this one would be silently correct -- and still wrong.

    A matrix whose rows arrived in a different order than the record's was built from a
    differently ordered frame, and nothing else in the pipeline reorders. Refusing says so
    while the cause is still findable.
    """
    with pytest.raises(MetadataError, match="not on the record's index"):
        with_features(record, matrix.loc[["r-1", "r-5", "r-9"]])


def test_a_record_without_the_metadata_columns_is_refused(record, matrix) -> None:
    """A check for a column that was never there passes vacuously. That is the leak."""
    with pytest.raises(MetadataError, match="missing 1 of 5 metadata column"):
        with_features(record.drop(columns=["Alloy_class"]), matrix)


def test_temperature_arrives_from_the_matrix_and_carries_the_cast(record, matrix) -> None:
    """The one column both sides legitimately hold.

    `temperature(K)` is a column of the raw file *and* one of the 22 features. The matrix's
    copy wins because it is `float64` where the raw column is `int64` -- card #19's cast, so
    that a candidate at 313.5 K does not become 313.
    """
    joined = with_features(record, matrix)
    assert joined["temperature(K)"].dtype == "float64"
    assert list(joined["temperature(K)"]) == [298.0, 313.0, 573.0]


def test_a_matrix_featurised_at_other_temperatures_is_refused(record, matrix) -> None:
    """Agreement is what licences the matrix's copy to win, and it is checked, not assumed."""
    matrix.loc["r-1", "temperature(K)"] = 350.0

    with pytest.raises(MetadataError) as caught:
        with_features(record, matrix)
    message = str(caught.value)
    assert "'temperature(K)' arrives from both sides" in message
    assert "'r-1'" in message, "the message must name the row"
    assert "merge_datasets.py:49" in message


def test_a_shared_column_that_cannot_be_compared_is_refused(record, matrix) -> None:
    """A record column shadowed by a feature of the same name, where no comparison exists."""
    record["avg_Density"] = ["heavy", "middling", "light"]

    with pytest.raises(MetadataError, match="'avg_Density' arrives from both sides"):
        with_features(record, matrix)


def test_the_join_is_by_label_not_by_position(record, matrix) -> None:
    """The property `featurize` returns the caller's index for.

    Both frames hold the same labels; only the record's order is the answer. A positional
    concat would put `r-9`'s features on `r-1` and nothing downstream would notice.
    """
    joined = with_features(record, matrix)
    for label in record.index:
        assert joined.loc[label, "avg_Density"] == matrix.loc[label, "avg_Density"]
        assert joined.loc[label, "Alloy_class"] == record.loc[label, "Alloy_class"]
