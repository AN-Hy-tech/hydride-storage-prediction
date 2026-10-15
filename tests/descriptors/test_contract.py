"""The 22-feature contract, and the four things about it that are not bookkeeping.

Card #19.

**The count in the card was wrong and these tests carry the measured one.** The card says two
of the 22 cannot be computed from the citable sources. Counted per column over all 1,279
curated rows it is **seven**: ``dev_Gordy_electonegativity``, blocked on 266 rows by 21
elements, and all six JARVIS features, blocked on the single europium row. The card named
both causes and counted the six as one; a caller asking "can I build this matrix?" needs six
answers, so ``test_seven_of_the_twenty_two_are_not_computable_everywhere`` pins seven.

**The order is declared, not recovered.** The order the published model was trained in --
``selected_cols_final`` in ``Boruta_FeatEng.py`` -- was never committed, so
``test_the_order_is_report_md_s`` asserts against
``reports/feature_selection/feature_selection_report.csv``, the SHAP-descending order
REPORT.md 3.2 prints. What protects AC-4 is that exactly one place declares an order, not
that the order matches a history nobody kept.

**The naming rule has to be injective or the contract cannot be regenerated.**
``test_the_naming_rule_never_collides`` builds every name either table could ever produce --
5 statistics x 537 properties -- and checks all 2,685 are distinct. Card #25 rebuilds the
contract from names alone; if two (statistic, property) pairs could share a name, that
rebuild would silently pick one.

**The Gordy hole is the citable edition's, not CBFV's.**
``test_cbfv_supplies_every_gordy_value_the_publication_omits`` measures it: CBFV's copy of
the Oliynyk table has a value for all 21 elements Lee et al. 2024 leave blank. So gate AC-2,
which runs against CBFV's table, cannot see this hole at all, and the 266 rows are something
the reimplementation acquires by citing its sources properly. Cards #21, #24 and #25 carry
the consequences.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
from hydms.data.load import load_hydride_data, parse_formula
from hydms.data.metadata import with_metadata
from hydms.descriptors.contract import (
    CONTRACT,
    DTYPE,
    PASSTHROUGH,
    PUBLISHED_SPELLING,
    ContractError,
    FeatureContract,
    FeatureSpec,
    assert_contract,
)
from hydms.descriptors.element_data import TABLES, load_table
from hydms.descriptors.stats import STATISTICS

CBFV_OLIYNYK = Path(__file__).parent / "data" / "cbfv_oliynyk_reference.csv"
#: The archival pipeline's feature-selection report, kept as a fixture when that pipeline was
#: deleted (card #107): an independent witness that the 22 are the ones it selected.
SELECTION_REPORT = Path(__file__).parent / "data" / "feature_selection_report.csv"

#: REPORT.md 3.2, the 22 in the order the thesis prints them. Written out rather than read
#: from the module under test: a contract that agrees with itself proves nothing.
PUBLISHED = (
    "avg_polzbl_divi_atom_mass",
    "dev_Zunger_radii_sum",
    "dev_Pauling_Electronegativity",
    "avg_valence_d",
    "dev_atom_mass_mult_therm_cond",
    "avg_is_alkaline",
    "dev_bp_divi_atom_mass",
    "dev_specific_heat_(J/g_K)_",
    "dev_gilmor_number_of_valence_electron",
    "dev_Covalent_Radius",
    "range_Mulliken_EN",
    "range_specific_heat_(J/g_K)_",
    "range_heat_of_vaporization_(kJ/mol)_",
    "dev_Gordy_electonegativity",
    "range_first_ion_en_mult_X",
    "range_Mendeleev_Number",
    "range_Density_(g/mL)",
    "dev_voro_coord_divi_mol_vol",
    "dev_heat_of_vaporization_(kJ/mol)_",
    "range_Atomic_Weight",
    "temperature(K)",
    "avg_Number_of_unfilled_s_valence_electrons",
)

#: The six JARVIS features, every one of them blocked by europium alone.
JARVIS_FEATURES = (
    "avg_polzbl_divi_atom_mass",
    "dev_atom_mass_mult_therm_cond",
    "avg_is_alkaline",
    "dev_bp_divi_atom_mass",
    "range_first_ion_en_mult_X",
    "dev_voro_coord_divi_mol_vol",
)

#: The 21 dataset elements Lee et al. 2024 leave blank for ``gordy_en``. Pinned identically
#: in ``test_element_data.py``; repeated here because this is where the *consequence* for the
#: feature set is measured.
GORDY_MISSING = frozenset(
    "Ce Dy Er Eu Gd Hf Ho Ir Lu Nd Os Pr Pt Re Sm Ta Tb Th Tm U W".split()
)

#: Reading a decimal string out of a committed CSV and comparing it to a literal of the same
#: digits is exact in IEEE 754, but nothing in this project compares a published number with
#: ``==`` -- see ``hydms/data/target.py`` and ``tests/descriptors/test_stats.py``.
CSV_TOLERANCE = 1e-12


# ---------------------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def compositions() -> list[dict[str, float]]:
    """The parsed composition of every curated row, in file order."""
    frame = load_hydride_data()
    return [parse_formula(formula) for formula in frame["Composition"]]


@pytest.fixture(scope="module")
def cbfv_oliynyk() -> dict[str, dict[str, str]]:
    """CBFV 1.1.0's own Oliynyk table, as raw text -- the AC-2 reference #16 committed."""
    with CBFV_OLIYNYK.open(encoding="utf-8", newline="") as handle:
        return {row["element"]: row for row in csv.DictReader(handle)}


def frame_matching_contract() -> pd.DataFrame:
    """A one-row matrix that satisfies the contract, for the guard tests to damage."""
    return pd.DataFrame({name: [0.0] for name in CONTRACT.names}, dtype=DTYPE)


# ---------------------------------------------------------------------------------------
# The names, the order and the provenance
# ---------------------------------------------------------------------------------------


def test_the_contract_is_the_published_twenty_two() -> None:
    assert len(CONTRACT) == 22
    assert CONTRACT.names == PUBLISHED


def test_the_order_is_report_md_s() -> None:
    """Asserted against the published artifact, not against a list retyped here.

    ``feature_selection_report.csv`` is SHAP-descending and is what REPORT.md 3.2 prints.
    The order the model was *trained* in is not recoverable -- see this module's docstring.
    """
    with SELECTION_REPORT.open(encoding="utf-8", newline="") as handle:
        published = tuple(row["Feature"] for row in csv.DictReader(handle))
    assert CONTRACT.names == published


def test_fifteen_oliynyk_six_jarvis_and_one_passthrough() -> None:
    """Card #8's split. A single-table featuriser cannot reach AC-2 regardless of care."""
    by_table = Counter(spec.table for spec in CONTRACT)
    assert by_table == {"oliynyk": 15, "jarvis": 6, None: 1}
    passthrough = [spec for spec in CONTRACT if spec.is_passthrough]
    assert [spec.name for spec in passthrough] == [PASSTHROUGH]


def test_nineteen_distinct_properties_behind_twenty_one_descriptors() -> None:
    """Two properties are used twice, by different statistics -- the count is not 21."""
    used = {(spec.table, spec.prop) for spec in CONTRACT if spec.table is not None}
    assert len(used) == 19
    repeated = Counter(spec.prop for spec in CONTRACT if spec.table is not None)
    assert {p for p, n in repeated.items() if n > 1} == {
        "specific_heat_j_g_k",
        "heat_of_vaporization_kj_mol",
    }


def test_every_declared_property_exists_in_its_table() -> None:
    for spec in CONTRACT:
        if spec.table is None:
            continue
        assert spec.prop in load_table(spec.table).properties, spec.name


def test_the_alias_map_is_cbfvs_own_header(cbfv_oliynyk: dict[str, dict[str, str]]) -> None:
    """The 13 Oliynyk spellings, checked against CBFV's table rather than remembered.

    Including ``Gordy_electonegativity``: the misspelling is the source table's and the
    published feature name carries it, so the map must too.
    """
    header = set(next(iter(cbfv_oliynyk.values()))) - {"element"}
    assert set(PUBLISHED_SPELLING.values()) == header
    assert PUBLISHED_SPELLING["gordy_en"] == "Gordy_electonegativity"


def test_the_jarvis_half_needs_no_alias() -> None:
    """CBFV's ``jarvis.csv`` is NIST's own file, so its column names are already published."""
    for spec in CONTRACT:
        if spec.table == "jarvis":
            assert spec.name == f"{spec.statistic}_{spec.prop}"


# ---------------------------------------------------------------------------------------
# Regeneration: the contract must be rebuildable from names alone (card #25)
# ---------------------------------------------------------------------------------------


def test_from_names_reproduces_the_contract_exactly() -> None:
    """What card #25 calls after re-running selection. Regenerated, never hand-edited."""
    assert FeatureContract.from_names(CONTRACT.names) == CONTRACT


def test_the_two_tables_share_no_property_name() -> None:
    """Why a name can resolve to a table on its own."""
    oliynyk = set(load_table("oliynyk").properties)
    jarvis = set(load_table("jarvis").properties)
    assert oliynyk & jarvis == set()


def test_the_naming_rule_never_collides() -> None:
    """Every name either table could ever produce, and all of them distinct.

    5 statistics x 537 properties = 2,685 names. If two (statistic, property) pairs could
    share a name, ``from_names`` would silently resolve to whichever it found first.
    """
    built = Counter(
        f"{statistic}_{PUBLISHED_SPELLING.get(prop, prop)}"
        for statistic in STATISTICS
        for table in TABLES
        for prop in load_table(table).properties
    )
    assert sum(built.values()) == 2685
    assert [name for name, count in built.items() if count > 1] == []


def test_a_property_whose_name_starts_with_a_statistic_still_resolves() -> None:
    """JARVIS has three: ``avg_ion_rad``, ``max_oxid_s``, ``min_oxid_s``.

    The split is on the *first* underscore, so ``dev_avg_ion_rad`` is the deviation of
    ``avg_ion_rad`` and not something ambiguous.
    """
    leading = [
        prop
        for prop in load_table("jarvis").properties
        if prop.split("_", 1)[0] in STATISTICS
    ]
    assert sorted(leading) == ["avg_ion_rad", "max_oxid_s", "min_oxid_s"]

    rebuilt = FeatureContract.from_names(["dev_avg_ion_rad", "min_max_oxid_s"])
    assert [(s.statistic, s.table, s.prop) for s in rebuilt] == [
        ("dev", "jarvis", "avg_ion_rad"),
        ("min", "jarvis", "max_oxid_s"),
    ]


def test_from_names_reports_every_unresolvable_name_at_once() -> None:
    with pytest.raises(ContractError) as caught:
        FeatureContract.from_names(["avg_valence_d", "median_valence_d", "dev_not_a_property"])
    message = str(caught.value)
    assert "2 of 3" in message
    assert "median_valence_d" in message
    assert "dev_not_a_property" in message
    assert "in neither table" in message


# ---------------------------------------------------------------------------------------
# Computability: the question the card exists to answer
# ---------------------------------------------------------------------------------------


def test_seven_of_the_twenty_two_are_not_computable_everywhere(
    compositions: list[dict[str, float]],
) -> None:
    """The card said two. Measured over all 1,279 curated rows it is seven columns."""
    blocked: Counter[str] = Counter()
    for composition in compositions:
        for name in CONTRACT.computability(composition).unavailable:
            blocked[name] += 1

    assert set(blocked) == {"dev_Gordy_electonegativity", *JARVIS_FEATURES}
    assert blocked["dev_Gordy_electonegativity"] == 266
    for name in JARVIS_FEATURES:
        assert blocked[name] == 1, name


def test_the_gordy_hole_costs_266_rows_and_236_compositions(
    compositions: list[dict[str, float]],
) -> None:
    """Rows are not the unit AC-6 and the folds care about; compositions are (card #88)."""
    frame = with_metadata(load_hydride_data())
    incomplete = [
        index
        for index, composition in enumerate(compositions)
        if not CONTRACT.computability(composition).complete
    ]
    assert len(incomplete) == 266
    assert len(compositions) == 1279
    assert frame.iloc[incomplete]["canonical_key"].nunique() == 236
    assert frame["canonical_key"].nunique() == 1115


def test_the_loss_falls_on_ab5_and_mic_not_on_ab2(
    compositions: list[dict[str, float]],
) -> None:
    """The card expected "most of the AB5 and AB2 chemistry". AB2 is the second least hit.

    Measured shares of rows losing at least one feature: AB5 46.4%, MIC 42.5%, AB2 9.2%.
    """
    frame = with_metadata(load_hydride_data())
    incomplete = [
        index
        for index, composition in enumerate(compositions)
        if not CONTRACT.computability(composition).complete
    ]
    affected = frame.iloc[incomplete]["Alloy_class"].value_counts()
    whole = frame["Alloy_class"].value_counts()

    assert (int(affected["AB5"]), int(whole["AB5"])) == (91, 196)
    assert (int(affected["MIC"]), int(whole["MIC"])) == (54, 127)
    assert (int(affected["AB2"]), int(whole["AB2"])) == (34, 371)
    assert int(affected.get("LEA", 0)) == 0
    assert affected["AB2"] / whole["AB2"] < affected["AB5"] / whole["AB5"]


def test_europium_blocks_exactly_the_six_jarvis_features() -> None:
    """``Eu1Ni5``, row 516 -- the only europium-bearing row in the curated data.

    NIST marks 434 of europium's 438 JARVIS properties -9999; the four real ones are ``X``,
    ``Z``, ``atom_mass`` and ``atom_rad``, and no selected feature can be built from those.
    """
    verdict = CONTRACT.computability(parse_formula("Eu1Ni5"))
    assert not verdict.complete
    # Gordy too: europium is one of the 21 the publication leaves blank.
    assert set(verdict.unavailable) == {"dev_Gordy_electonegativity", *JARVIS_FEATURES}
    assert {hole.element for hole in verdict.holes} == {"Eu"}
    assert all(hole.table in TABLES for hole in verdict.holes)
    assert PASSTHROUGH in verdict.available


def test_a_verdict_names_the_blocking_element_and_the_reason() -> None:
    """A screen returns a verdict with a reason, never a silent drop (card #44)."""
    verdict = CONTRACT.computability(parse_formula("Ce1Ni5"))
    assert verdict.unavailable == ("dev_Gordy_electonegativity",)
    hole = verdict.holes[0]
    assert (hole.element, hole.table, hole.prop) == ("Ce", "oliynyk", "gordy_en")
    assert "leaves the cell empty" in hole.reason
    assert "Ce" in verdict.reason
    assert "gordy_en" in verdict.reason


def test_an_element_no_table_has_is_a_different_reason_from_an_empty_cell() -> None:
    """Both make a feature uncomputable; only one is a hole in a real publication."""
    verdict = CONTRACT.computability(["Ni", "Xx"])
    reasons = {hole.reason for hole in verdict.holes if hole.element == "Xx"}
    assert reasons == {"the table has no such element"}
    assert len(verdict.unavailable) == 21


def test_a_composition_of_well_covered_elements_computes_everything() -> None:
    verdict = CONTRACT.computability(parse_formula("La1Ni5"))
    assert verdict.complete
    assert verdict.holes == ()
    assert verdict.available == CONTRACT.names
    assert "all 22 features are computable" in verdict.reason


def test_an_empty_composition_has_no_verdict() -> None:
    with pytest.raises(ContractError, match="empty composition"):
        CONTRACT.computability([])


def test_amounts_are_irrelevant_to_computability() -> None:
    """A hole is per element per property; how much of the element there is cannot matter."""
    assert CONTRACT.computability({"Ce": 0.001, "Ni": 5.0}).unavailable == (
        CONTRACT.computability({"Ce": 99.0, "Ni": 1.0}).unavailable
    )


def test_cbfv_supplies_every_gordy_value_the_publication_omits(
    cbfv_oliynyk: dict[str, dict[str, str]],
) -> None:
    """The hole belongs to the 2024 revision, not to CBFV -- so gate AC-2 cannot see it.

    #21 runs the parity comparison against this very table, where nothing is missing. The 266
    rows are a cost the reimplementation acquires by citing its source properly, and the
    trade is #24's and #25's to make.
    """
    oliynyk = load_table("oliynyk")
    for element in sorted(GORDY_MISSING):
        assert not oliynyk.has(element, "gordy_en"), element
        cell = cbfv_oliynyk[element]["Gordy_electonegativity"]
        assert cell not in ("", "nan"), element
        assert float(cell) > 0.0
    assert float(cbfv_oliynyk["Ce"]["Gordy_electonegativity"]) == pytest.approx(
        4.5734, abs=CSV_TOLERANCE
    )
    assert float(cbfv_oliynyk["Hf"]["Gordy_electonegativity"]) == pytest.approx(
        6.3704, abs=CSV_TOLERANCE
    )


# ---------------------------------------------------------------------------------------
# assert_contract: the four ways a matrix goes wrong
# ---------------------------------------------------------------------------------------


def test_a_matching_matrix_passes() -> None:
    assert_contract(frame_matching_contract())


def test_a_missing_column_is_named() -> None:
    frame = frame_matching_contract().drop(columns=["avg_valence_d"])
    with pytest.raises(ContractError, match="1 missing: avg_valence_d"):
        assert_contract(frame)


def test_an_extra_column_is_named_and_points_at_the_guard_that_owns_it() -> None:
    frame = frame_matching_contract()
    frame["H2_W% (max)"] = 1.0
    with pytest.raises(ContractError) as caught:
        assert_contract(frame)
    assert "not in the contract: H2_W% (max)" in str(caught.value)
    assert "refuse_non_features" in str(caught.value)


def test_the_right_columns_in_the_wrong_order_are_refused() -> None:
    """The failure this function exists for: it is the one that returns numbers, not errors."""
    frame = frame_matching_contract()
    swapped = list(CONTRACT.names)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    with pytest.raises(ContractError) as caught:
        assert_contract(frame[swapped])
    assert "wrong order" in str(caught.value)
    assert "position 0" in str(caught.value)
    assert repr(CONTRACT.names[0]) in str(caught.value)


def test_an_integer_temperature_column_is_refused() -> None:
    """The raw file stores ``temperature(K)`` as an integer, so this is the realistic slip.

    A candidate evaluated at 313.5 K truncates to 313 in an int64 column, silently.
    """
    frame = frame_matching_contract()
    frame[PASSTHROUGH] = frame[PASSTHROUGH].astype("int64")
    with pytest.raises(ContractError) as caught:
        assert_contract(frame)
    assert f"not {DTYPE}" in str(caught.value)
    assert "temperature(K) is int64" in str(caught.value)


def test_duplicated_column_names_are_refused_before_anything_else() -> None:
    frame = frame_matching_contract()
    frame = pd.concat([frame, frame[["avg_valence_d"]]], axis=1)
    with pytest.raises(ContractError, match="duplicated column name"):
        assert_contract(frame)


def test_every_problem_is_reported_at_once() -> None:
    frame = frame_matching_contract().drop(columns=["avg_valence_d"])
    frame["not_a_feature"] = 0.0
    frame[PASSTHROUGH] = frame[PASSTHROUGH].astype("int64")
    with pytest.raises(ContractError) as caught:
        assert_contract(frame)
    message = str(caught.value)
    assert "missing" in message
    assert "not in the contract" in message
    assert f"not {DTYPE}" in message


def test_assert_contract_accepts_a_regenerated_contract() -> None:
    """What #25 will do: a different N, checked the same way."""
    smaller = FeatureContract.from_names(["avg_valence_d", "dev_Covalent_Radius"])
    frame = pd.DataFrame({name: [0.0] for name in smaller.names}, dtype=DTYPE)
    assert_contract(frame, smaller)
    with pytest.raises(ContractError, match="2-feature contract"):
        assert_contract(frame[list(reversed(smaller.names))], smaller)


# ---------------------------------------------------------------------------------------
# The manifest (card #4 stores it; this module decides what it says)
# ---------------------------------------------------------------------------------------


def test_the_manifest_round_trips_through_json() -> None:
    payload = json.loads(json.dumps(CONTRACT.as_manifest()))
    assert FeatureContract.from_manifest(payload) == CONTRACT


def test_the_manifest_records_provenance_per_feature() -> None:
    entries = {entry["name"]: entry for entry in CONTRACT.as_manifest()["features"]}
    assert entries["dev_Gordy_electonegativity"] == {
        "name": "dev_Gordy_electonegativity",
        "statistic": "dev",
        "table": "oliynyk",
        "property": "gordy_en",
        "dtype": DTYPE,
    }
    assert entries[PASSTHROUGH]["table"] is None


def test_the_digest_is_order_sensitive() -> None:
    """Two contracts over the same names in different orders are different contracts."""
    reordered = FeatureContract.from_names(list(reversed(CONTRACT.names)))
    assert set(reordered.names) == set(CONTRACT.names)
    assert reordered.digest != CONTRACT.digest


def test_a_tampered_manifest_is_refused() -> None:
    payload = CONTRACT.as_manifest()
    payload["features"] = list(reversed(payload["features"]))
    with pytest.raises(ContractError, match="does not match the contract"):
        FeatureContract.from_manifest(payload)


def test_a_malformed_manifest_says_what_is_missing() -> None:
    with pytest.raises(ContractError, match="'features' list"):
        FeatureContract.from_manifest({"digest": "0" * 64})
    with pytest.raises(ContractError, match="missing"):
        FeatureContract.from_manifest({"features": [{"name": "avg_valence_d"}]})


# ---------------------------------------------------------------------------------------
# The types themselves
# ---------------------------------------------------------------------------------------


def test_a_spec_is_either_a_descriptor_or_a_passthrough() -> None:
    with pytest.raises(ContractError, match="half a descriptor"):
        FeatureSpec(name="avg_valence_d", statistic="avg", table="oliynyk", prop=None)


def test_a_spec_refuses_a_statistic_stats_does_not_implement() -> None:
    with pytest.raises(ContractError, match="mode"):
        FeatureSpec(name="mode_valence_d", statistic="mode", table="oliynyk", prop="valence_d")


def test_a_spec_refuses_a_third_table() -> None:
    with pytest.raises(ContractError, match="magpie"):
        FeatureSpec(name="avg_x", statistic="avg", table="magpie", prop="x")


def test_a_contract_refuses_duplicate_names() -> None:
    spec = CONTRACT.features[0]
    with pytest.raises(ContractError, match="more than once"):
        FeatureContract(features=(spec, spec))


def test_an_empty_contract_is_not_a_contract() -> None:
    with pytest.raises(ContractError, match="no features"):
        FeatureContract(features=())


def test_lookup_by_name() -> None:
    assert CONTRACT["avg_valence_d"].prop == "valence_d"
    assert "avg_valence_d" in CONTRACT
    assert "avg_not_a_feature" not in CONTRACT
    with pytest.raises(KeyError, match="22 feature"):
        CONTRACT["avg_not_a_feature"]


def test_the_contract_and_its_specs_are_frozen() -> None:
    import dataclasses

    with pytest.raises(dataclasses.FrozenInstanceError):
        CONTRACT.features[0].name = "something else"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        CONTRACT.features = ()  # type: ignore[misc]
