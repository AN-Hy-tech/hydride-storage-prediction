"""Card #20 — the descriptor layer's public interface, and the four ways it can lie.

The arithmetic is already defended: #17 pins the five statistics against CBFV's own output,
#18 pins the six JARVIS composites against hand-computed decimals, #19 pins the names, the
order and the dtype. What is left for this file is everything that only appears once the
pieces are assembled into one call.

1. **The assembly.** A featuriser that puts the right numbers in the wrong columns passes
   every test those three cards wrote. So every one of the 22 columns is checked against
   CBFV's own output for sixteen formulae, with CBFV's own table supplied — which is what
   makes it a statement about this code rather than about the two editions of the Oliynyk
   table (#16).
2. **The refusal.** Seven features are not computable for every composition, and the failure
   this module exists to prevent is a NaN that a median-fill downstream turns back into
   something that looks like a measurement. 266 of the 1,279 curated rows are refused, by
   name, with the blocking element said out loud.
3. **The batch.** Architectures A and B evaluate candidates in batches, and #17 measured that
   the reduction's axis is worth 2.794e-09 — over AC-2's tolerance. So a composition's
   features must not depend on what it was batched with, and that is asserted with ``==``
   rather than a tolerance.
4. **The labels.** The metadata that AC-6 needs is re-attached to this matrix afterwards, and
   the way that goes wrong is a positional join after a row went missing (leak L9,
   ``merge_datasets.py:46``). Labels are carried through; nothing is ever dropped.
"""

from __future__ import annotations

import csv
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hydms.data.load import load_hydride_data, parse_formula
from hydms.data.metadata import refuse_non_features
from hydms.descriptors.composites import CompositeError
from hydms.descriptors.contract import (
    CONTRACT,
    DTYPE,
    PASSTHROUGH,
    PUBLISHED_SPELLING,
    FeatureContract,
    assert_contract,
)
from hydms.descriptors.element_data import PropertyTable
from hydms.descriptors.featurize import FeaturisationError, featurize

DATA = Path(__file__).parent / "data"
CBFV_OLIYNYK = DATA / "cbfv_oliynyk_reference.csv"
FIXTURE = DATA / "cbfv_statistics_reference.csv"

#: The feature the citable Oliynyk edition cannot always supply, and the row that loses all
#: six JARVIS features. Both measured on card #19 and re-measured here through `featurize`,
#: because the count that matters to a caller is *rows the call refuses*, not columns.
GORDY = "dev_Gordy_electonegativity"
EUROPIUM_ROW = "Eu1Ni5"

#: Measured over `Machine_Model/data/raw/hydride_data.csv`. 265 rows lose Gordy alone and
#: `Eu1Ni5` loses seven features at once, so the batch refuses 266. Drop Gordy and the
#: remaining 21 features cover all but the europium row — that number is the trade #24 and
#: #25 make, so it is pinned rather than described.
REFUSED_ROWS = 266
GORDY_ONLY_ROWS = 265
ROWS_WITHOUT_GORDY = 1278
CURATED_ROWS = 1279

#: The verdict is per element *set*, so it is memoised. Pinned because the module docstring
#: quotes it as the reason the memo is worth having.
DISTINCT_ELEMENT_SETS = 464

#: Against CBFV's own output, given CBFV's own table: worst 4.547e-13 absolute and 6.828e-15
#: relative over all 22 columns and all sixteen fixture formulae. The tolerance is the
#: project's usual 1e-12 — three orders inside it, and three orders inside AC-2's 1e-9. The
#: residue is element order (#17): `parse_formula` sorts by symbol and CBFV does not, so the
#: sums accumulate differently. This is not gate AC-2; #21 owns that, over all 1,279 formulae,
#: with an output that names the offending column and row.
PARITY_RTOL = 1e-12
PARITY_ATOL = 1e-12

#: The card asks for 10,000 formulae in one call rather than 10,000 calls.
BIG_BATCH = 10_000

#: One of the eleven JARVIS columns that are not the arithmetic their names claim (#18). No
#: selected feature uses it; #25's re-selection could land on one, which is why the guard
#: exists and why this test does not wait for that to happen.
INCONSISTENT_COMPOSITE = "avg_atom_mass_mult_voro_coord"


# ---------------------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------------------


def _ours() -> dict[str, str]:
    """CBFV's spelling of an Oliynyk property -> ours. The inverse of the published map."""
    return {published: ours for ours, published in PUBLISHED_SPELLING.items()}


@pytest.fixture(scope="module")
def cbfv_oliynyk() -> PropertyTable:
    """CBFV's copy of the Oliynyk table, spelled the way the contract spells its properties.

    Test input, never package data: CBFV carries no licence, which is the whole reason this
    layer exists. Card #16 committed it so parity can be a claim about the code — eight of the
    thirteen properties the selected features need differ between the two editions.
    """
    ours = _ours()
    with CBFV_OLIYNYK.open(encoding="utf-8", newline="") as handle:
        values = {
            row["element"]: {
                ours.get(key, key): float(cell)
                for key, cell in row.items()
                if key != "element" and cell != ""
            }
            for row in csv.DictReader(handle)
        }
    return PropertyTable.of("oliynyk", "CBFV 1.1.0's copy of Oliynyk et al.", values)


@pytest.fixture(scope="module")
def cbfv_statistics() -> list[dict[str, str]]:
    """CBFV 1.1.0's own output: five statistics of nineteen properties over sixteen formulae."""
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def fixture_formulae(cbfv_statistics: list[dict[str, str]]) -> list[str]:
    return sorted({row["formula"] for row in cbfv_statistics})


@pytest.fixture(scope="module")
def curated() -> pd.DataFrame:
    """The 1,279 curated rows, formula and temperature as the raw file has them."""
    return load_hydride_data()


@pytest.fixture(scope="module")
def without_gordy() -> FeatureContract:
    """The 22 less the one feature the citable table cannot always supply."""
    return FeatureContract.from_names([n for n in CONTRACT.names if n != GORDY])


# ---------------------------------------------------------------------------------------
# The matrix is the contract
# ---------------------------------------------------------------------------------------


def test_one_call_returns_the_twenty_two_columns_in_contract_order() -> None:
    features = featurize(["LaNi5", "TiFe", "Mg2Ni"], 298.0)

    assert list(features.columns) == list(CONTRACT.names)
    assert features.shape == (3, len(CONTRACT))
    assert set(map(str, features.dtypes)) == {DTYPE}
    assert_contract(features)


def test_nothing_in_the_matrix_is_a_hole() -> None:
    """No NaN, ever. A refusal is the only other outcome, and it is an exception."""
    features = featurize(["LaNi5", "TiFe", "Ti0.8Zr0.2Mn1.4V0.2Cr0.4"], 298.0)
    assert np.isfinite(features.to_numpy()).all()


def test_the_matrix_carries_no_metadata_and_no_target() -> None:
    """`refuse_non_features` is #12's guard; passing it is a property of what this returns."""
    refuse_non_features(featurize(["LaNi5", "TiFe"], 298.0))


def test_an_empty_batch_returns_the_columns_with_no_rows() -> None:
    """A generation whose every candidate was screened out is not an error."""
    features = featurize([], 298.0)
    assert features.shape == (0, len(CONTRACT))
    assert_contract(features)


def test_a_narrower_contract_returns_exactly_its_columns(without_gordy: FeatureContract) -> None:
    features = featurize(["LaNi5"], 298.0, contract=without_gordy)
    assert list(features.columns) == list(without_gordy.names)
    assert GORDY not in features.columns


# ---------------------------------------------------------------------------------------
# The assembly: every column against CBFV's own numbers, given CBFV's own table
# ---------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def against_cbfv(fixture_formulae: list[str], cbfv_oliynyk: PropertyTable) -> pd.DataFrame:
    return featurize(fixture_formulae, 298.0, tables={"oliynyk": cbfv_oliynyk})


@pytest.mark.parametrize("feature", [spec.name for spec in CONTRACT if not spec.is_passthrough])
def test_every_column_reproduces_cbfv(
    feature: str,
    against_cbfv: pd.DataFrame,
    cbfv_statistics: list[dict[str, str]],
    fixture_formulae: list[str],
) -> None:
    """The column, not the arithmetic — a right number in a wrong column is the failure here.

    Parametrised by feature so a break names the column. The fixture is CBFV's own output and
    is looked up by (formula, table, property) so a mis-assembled column cannot find its own
    expectation by accident.
    """
    spec = CONTRACT[feature]
    assert spec.statistic is not None and spec.prop is not None
    published = PUBLISHED_SPELLING.get(spec.prop, spec.prop)
    expected = {
        row["formula"]: float(row[spec.statistic])
        for row in cbfv_statistics
        if row["table"] == spec.table and row["property"] == published
    }
    assert set(expected) == set(fixture_formulae), f"{feature}: fixture does not cover it"

    got = against_cbfv[feature].to_numpy()
    want = np.array([expected[formula] for formula in fixture_formulae])
    np.testing.assert_allclose(got, want, rtol=PARITY_RTOL, atol=PARITY_ATOL)


def test_the_fixture_would_notice_a_swapped_column(
    against_cbfv: pd.DataFrame, cbfv_statistics: list[dict[str, str]], fixture_formulae: list[str]
) -> None:
    """The check above is only worth having if two columns are never interchangeable."""
    columns = [name for name in against_cbfv.columns if name != PASSTHROUGH]
    for left, right in pairwise(columns):
        assert not np.allclose(
            against_cbfv[left], against_cbfv[right], rtol=PARITY_RTOL, atol=PARITY_ATOL
        ), f"{left} and {right} are indistinguishable over the fixture formulae"


# ---------------------------------------------------------------------------------------
# The batch
# ---------------------------------------------------------------------------------------


def test_ten_thousand_formulae_in_one_call(without_gordy: FeatureContract) -> None:
    """The card's box, stated as the call it forbids: one call, not ten thousand."""
    formulae = ["LaNi5", "TiFe", "Mg2Ni", "Ti0.8Zr0.2Mn1.4V0.2Cr0.4"] * (BIG_BATCH // 4)
    features = featurize(formulae, 298.0, contract=without_gordy)
    assert features.shape == (BIG_BATCH, len(without_gordy))


def test_a_composition_does_not_depend_on_its_batch(without_gordy: FeatureContract) -> None:
    """Exactly, not to a tolerance.

    #17 measured that reducing the batch over its fast axis costs up to 2.794e-09 — above gate
    AC-2's 1e-9 — on a property no selected feature uses today. This is that property restated
    where a caller can see it: padding a batch with wider compositions must change nothing at
    all, so `==` is the right operator and a tolerance here would hide the defect.
    """
    formulae = ["LaNi5", "Ti0.12Zr0.215V0.10Cr0.075Mn0.081Fe0.01Co0.07Ni0.322Sn0.003Al0.004"]
    batched = featurize(formulae, [298.0, 350.0], contract=without_gordy)
    for position, formula in enumerate(formulae):
        alone = featurize([formula], [batched[PASSTHROUGH].iloc[position]], contract=without_gordy)
        assert (alone.to_numpy() == batched.iloc[[position]].to_numpy()).all(), formula


def test_the_rows_come_back_in_the_order_they_went_in(without_gordy: FeatureContract) -> None:
    formulae = ["LaNi5", "TiFe", "Mg2Ni", "ZrV2"]
    kelvin = [200.0, 300.0, 400.0, 500.0]
    forward = featurize(formulae, kelvin, contract=without_gordy)
    reverse = featurize(formulae[::-1], kelvin[::-1], contract=without_gordy)
    assert (forward.to_numpy() == reverse.to_numpy()[::-1]).all()


# ---------------------------------------------------------------------------------------
# Refusal: formulae
# ---------------------------------------------------------------------------------------


def test_every_unparseable_formula_is_named_with_its_label() -> None:
    """All of them, at once. Finding them one exception at a time is how a session is spent."""
    with pytest.raises(FeaturisationError) as caught:
        featurize(["LaNi5", "Xx2", "TiFe", "La0Ni5"], 298.0)

    message = str(caught.value)
    assert "2 of 4" in message
    assert "'Xx'" in message and "not a chemical element" in message
    assert "amounts must be positive" in message
    assert "[1]" in message and "[3]" in message


def test_a_bad_formula_is_never_silently_dropped() -> None:
    """The failure this refusal exists to prevent is a shorter frame, not a bad number."""
    with pytest.raises(FeaturisationError):
        featurize(["LaNi5", ""], 298.0)


def test_a_bare_string_is_not_a_batch() -> None:
    with pytest.raises(FeaturisationError) as caught:
        featurize("LaNi5", 298.0)  # type: ignore[arg-type]
    assert "character by character" in str(caught.value)


def test_a_repeated_label_is_refused_because_metadata_re_attaches_by_label() -> None:
    formulae = pd.Series(["LaNi5", "TiFe"], index=["a", "a"])
    with pytest.raises(FeaturisationError) as caught:
        featurize(formulae, 298.0)
    assert "repeats 1 label" in str(caught.value)


# ---------------------------------------------------------------------------------------
# Refusal: a hole is not a number
# ---------------------------------------------------------------------------------------


def test_a_composition_with_a_hole_names_the_feature_and_the_blocking_element() -> None:
    with pytest.raises(FeaturisationError) as caught:
        featurize(["LaNi5", "CeNi5"], 298.0)

    message = str(caught.value)
    assert "1 of 2 composition(s)" in message
    assert GORDY in message
    assert "Ce" in message
    assert "the published table leaves the cell empty" in message
    assert "FeatureContract.from_names()" in message


def test_the_europium_row_loses_seven_features_at_once() -> None:
    with pytest.raises(FeaturisationError) as caught:
        featurize([EUROPIUM_ROW], 298.0)
    assert "7 of 22 features cannot be computed" in str(caught.value)


def test_a_narrower_contract_featurises_what_the_twenty_two_cannot(
    without_gordy: FeatureContract,
) -> None:
    """The refusal is about the contract, not about the composition."""
    with pytest.raises(FeaturisationError):
        featurize(["CeNi5"], 298.0)
    features = featurize(["CeNi5"], 298.0, contract=without_gordy)
    assert features.shape == (1, len(without_gordy))
    assert np.isfinite(features.to_numpy()).all()


def test_the_shipped_tables_refuse_266_of_the_curated_rows(curated: pd.DataFrame) -> None:
    """The number a caller feels, as opposed to #19's per-column count.

    Also the reason the batch refuses rather than returning what it can: 266 rows would go
    missing from a 1,279-row matrix, and the join that re-attaches the target would not
    notice.
    """
    with pytest.raises(FeaturisationError) as caught:
        featurize(curated["Composition"], curated["temperature(K)"])
    assert f"{REFUSED_ROWS} of {CURATED_ROWS} composition(s)" in str(caught.value)

    verdicts = [CONTRACT.computability(parse_formula(f)) for f in curated["Composition"]]
    gordy_only = [v for v in verdicts if v.unavailable == (GORDY,)]
    assert len(gordy_only) == GORDY_ONLY_ROWS
    assert len({tuple(sorted(parse_formula(f))) for f in curated["Composition"]}) == (
        DISTINCT_ELEMENT_SETS
    )


def test_without_gordy_the_curated_set_featurises_but_for_europium(
    curated: pd.DataFrame, without_gordy: FeatureContract
) -> None:
    """The trade #24 and #25 own, measured rather than described."""
    keep = [
        label
        for label, formula in curated["Composition"].items()
        if without_gordy.computability(parse_formula(formula)).complete
    ]
    assert len(keep) == ROWS_WITHOUT_GORDY
    assert curated["Composition"].loc[list(set(curated.index) - set(keep))].tolist() == [
        EUROPIUM_ROW
    ]

    features = featurize(
        curated["Composition"].loc[keep], curated["temperature(K)"].loc[keep], contract=without_gordy
    )
    assert features.shape == (ROWS_WITHOUT_GORDY, len(without_gordy))
    assert np.isfinite(features.to_numpy()).all()


# ---------------------------------------------------------------------------------------
# Temperatures
# ---------------------------------------------------------------------------------------


def test_the_integer_temperature_is_cast_and_a_fractional_one_survives() -> None:
    """`assert_contract` refuses an int64 column by name; 313.5 K must not become 313."""
    integral = featurize(["LaNi5"], np.array([313], dtype=np.int64))
    assert str(integral[PASSTHROUGH].dtype) == DTYPE
    assert integral[PASSTHROUGH].iloc[0] == 313.0

    fractional = featurize(["LaNi5"], [313.5])
    assert fractional[PASSTHROUGH].iloc[0] == 313.5


def test_a_scalar_temperature_is_broadcast_over_the_batch() -> None:
    features = featurize(["LaNi5", "TiFe", "Mg2Ni"], 298.0)
    assert features[PASSTHROUGH].tolist() == [298.0, 298.0, 298.0]


def test_a_temperature_series_on_a_different_index_is_refused() -> None:
    """Leak L9's shape: pairing two columns by position after one of them moved."""
    formulae = pd.Series(["LaNi5", "TiFe"], index=[7, 8])
    kelvin = pd.Series([298.0, 350.0], index=[0, 1])
    with pytest.raises(FeaturisationError) as caught:
        featurize(formulae, kelvin)
    assert "leak L9" in str(caught.value)

    # Saying "positional is what I meant" is allowed, but it has to be said.
    features = featurize(formulae, np.asarray(kelvin))
    assert features[PASSTHROUGH].tolist() == [298.0, 350.0]


def test_a_non_finite_temperature_is_refused_with_its_label() -> None:
    with pytest.raises(FeaturisationError) as caught:
        featurize(pd.Series(["LaNi5", "TiFe"], index=["a", "b"]), [298.0, np.nan])
    assert "not finite" in str(caught.value)
    assert "'b'" in str(caught.value)


def test_a_temperature_per_row_is_required() -> None:
    with pytest.raises(FeaturisationError) as caught:
        featurize(["LaNi5", "TiFe"], [298.0])
    assert "2 formula(e) and 1 temperature(s)" in str(caught.value)


# ---------------------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------------------


def test_the_callers_labels_come_back_so_metadata_re_attaches_by_label() -> None:
    """What #12's L13 hook needs: a matrix that can be joined back on the row's own label.

    The index here is deliberately neither sorted nor a range, because a positional join and
    a label join agree on a RangeIndex and a test that cannot tell them apart is describing.
    """
    formulae = pd.Series(["LaNi5", "TiFe", "Mg2Ni"], index=["r-9", "r-1", "r-5"])
    kelvin = pd.Series([298.0, 350.0, 400.0], index=formulae.index)

    features = featurize(formulae, kelvin)
    assert list(features.index) == ["r-9", "r-1", "r-5"]

    beside = pd.DataFrame({"Alloy_class": ["AB5", "AB", "A2B"]}, index=["r-1", "r-5", "r-9"])
    joined = pd.concat([beside, features], axis=1)
    assert len(joined) == 3
    for label in formulae.index:
        alone = featurize([formulae[label]], [kelvin[label]])
        assert (joined.loc[label, list(CONTRACT.names)].to_numpy() == alone.to_numpy()[0]).all()


def test_a_list_gets_a_range_index_rather_than_invented_labels() -> None:
    features = featurize(["LaNi5", "TiFe"], 298.0)
    assert list(features.index) == [0, 1]


# ---------------------------------------------------------------------------------------
# The tables are an argument (gate AC-2's requirement, and nobody else's)
# ---------------------------------------------------------------------------------------


def test_the_verdict_is_about_the_table_actually_used(cbfv_oliynyk: PropertyTable) -> None:
    """The reason the parity gate can run at all.

    CBFV's copy supplies `gordy_en` for all 21 elements the citable 2024 edition leaves blank,
    so the same composition is refused against the shipped table and featurised against
    CBFV's. A verdict computed against the shipped table regardless would refuse 266 of the
    rows AC-2 exists to compare.
    """
    with pytest.raises(FeaturisationError):
        featurize(["CeNi5"], 298.0)

    features = featurize(["CeNi5"], 298.0, tables={"oliynyk": cbfv_oliynyk})
    assert np.isfinite(features[GORDY].to_numpy()).all()


def test_a_supplied_table_changes_the_numbers(cbfv_oliynyk: PropertyTable) -> None:
    """The two editions differ on eight of the thirteen properties (#16), so this must move."""
    # Aluminium is one of the 23 elements whose `zunger_radii_sum` was revised for the 2024
    # edition; lanthanum and nickel are not, which is why the formula is not LaNi5.
    shipped = featurize(["La1Ni4Al1"], 298.0)
    reference = featurize(["La1Ni4Al1"], 298.0, tables={"oliynyk": cbfv_oliynyk})
    assert shipped["dev_Zunger_radii_sum"].iloc[0] != reference["dev_Zunger_radii_sum"].iloc[0]
    assert shipped["avg_polzbl_divi_atom_mass"].iloc[0] == (
        reference["avg_polzbl_divi_atom_mass"].iloc[0]
    ), "the jarvis half was not supplied and must not move"


def test_a_table_this_project_does_not_have_is_refused(cbfv_oliynyk: PropertyTable) -> None:
    with pytest.raises(FeaturisationError) as caught:
        featurize(["LaNi5"], 298.0, tables={"magpie": cbfv_oliynyk})
    assert "no such element property table: magpie" in str(caught.value)


# ---------------------------------------------------------------------------------------
# The composite guard (#18)
# ---------------------------------------------------------------------------------------


def test_a_composite_column_that_is_not_its_own_arithmetic_is_refused() -> None:
    """Eleven of JARVIS's 156 composites are wrong on Cs and Gd. #25 can select one."""
    contract = FeatureContract.from_names([INCONSISTENT_COMPOSITE, PASSTHROUGH])
    with pytest.raises(CompositeError) as caught:
        featurize(["LaNi5"], 298.0, contract=contract)

    message = str(caught.value)
    assert "atom_mass_mult_voro_coord" in message
    assert "Cs" in message and "Gd" in message


def test_the_composite_guard_runs_before_any_row_is_built() -> None:
    """An empty batch still refuses: the defect is in the table, not in the candidates."""
    contract = FeatureContract.from_names([INCONSISTENT_COMPOSITE, PASSTHROUGH])
    with pytest.raises(CompositeError):
        featurize([], 298.0, contract=contract)


def test_the_selected_composites_pass_the_guard() -> None:
    """The rule costs nothing today; the eleven are what make it a rule (#18)."""
    features = featurize(["LaNi5"], 298.0)
    assert np.isfinite(features["avg_polzbl_divi_atom_mass"].to_numpy()).all()
