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

The L13 sentinel's ``live`` hook is **not** here: its subject is
``hydms.descriptors.featurize``, which does not exist until S3. These tests cover the half of
the card the data layer owns.
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
