"""The element property tables, and the refusals that keep a hole from becoming a number.

Card #16. Two things are being tested here that look like bookkeeping and are not.

The first is **coverage against the right number of elements**. The card was written asking
for 54, which is what ``REPORT.md`` §2.3 and the PRD's dataset table both say. Counted from
the parsed compositions of all 1279 rows the answer is 55, seven of them appearing exactly
once (N, Eu, Lu, Pb, Au, Os, Re). A table checked against 54 would pass while one element
silently had no properties, so these tests derive the set from the loader rather than writing
a number down, and the disagreement is recorded on card #89.

The second is that **the tables disagree with CBFV in ways SOURCES.md claims precisely**. A
prose table of deltas rots. These tests assert it, so the claim either stays true or the build
goes red.
"""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import pytest
from hydms.data.load import load_hydride_data, parse_formula
from hydms.descriptors.element_data import (
    TABLES,
    ElementDataError,
    load_table,
    require_coverage,
)

REFERENCE = Path(__file__).parent / "data" / "cbfv_oliynyk_reference.csv"

#: The thirteen Oliynyk properties behind 15 of the 22 selected features, and the nine JARVIS
#: base properties plus five composites behind another 6. Card #8 resolved the mapping;
#: card #19 owns the contract that names them feature by feature.
OLIYNYK_NEEDED = (
    "zunger_radii_sum",
    "pauling_en",
    "valence_d",
    "specific_heat_j_g_k",
    "gilman_no_of_valence_electrons",
    "covalent_radius",
    "mulliken_en",
    "heat_of_vaporization_kj_mol",
    "gordy_en",
    "mendeleev_number",
    "density_g_ml",
    "atomic_weight",
    "unfilled_s",
)

JARVIS_NEEDED = (
    "polzbl",
    "atom_mass",
    "therm_cond",
    "bp",
    "first_ion_en",
    "X",
    "voro_coord",
    "mol_vol",
    "is_alkaline",
)

JARVIS_COMPOSITES = {
    "polzbl_divi_atom_mass": ("polzbl", "/", "atom_mass"),
    "atom_mass_mult_therm_cond": ("atom_mass", "*", "therm_cond"),
    "bp_divi_atom_mass": ("bp", "/", "atom_mass"),
    "first_ion_en_mult_X": ("first_ion_en", "*", "X"),
    "voro_coord_divi_mol_vol": ("voro_coord", "/", "mol_vol"),
}


@pytest.fixture(scope="module")
def dataset_elements() -> frozenset[str]:
    """Every element the curated dataset actually uses, counted rather than remembered."""
    frame = load_hydride_data()
    parsed = [parse_formula(formula) for formula in frame["Composition"]]
    return frozenset(symbol for composition in parsed for symbol in composition)


# --------------------------------------------------------------------------------------
# The tables load and are what SOURCES.md says they are
# --------------------------------------------------------------------------------------


def test_both_tables_load_and_are_cached() -> None:
    for name in TABLES:
        table = load_table(name)
        assert table.name == name
        assert table.properties
        assert table.elements
    assert load_table("oliynyk") is load_table("oliynyk")


def test_the_tables_have_the_documented_shape() -> None:
    """The shapes in SOURCES.md, asserted so the document cannot drift from the data."""
    oliynyk = load_table("oliynyk")
    assert (len(oliynyk.elements), len(oliynyk.properties)) == (85, 99)
    jarvis = load_table("jarvis")
    assert (len(jarvis.elements), len(jarvis.properties)) == (103, 438)


def test_an_unknown_table_names_the_two_that_exist() -> None:
    with pytest.raises(ElementDataError, match="unknown element property table"):
        load_table("magpie")


# --------------------------------------------------------------------------------------
# Coverage: 55, not 54
# --------------------------------------------------------------------------------------


def test_the_dataset_uses_fifty_five_elements_not_fifty_four(
    dataset_elements: frozenset[str],
) -> None:
    """The card asked for 54. Measured from the data it is 55; card #89 holds the mismatch."""
    assert len(dataset_elements) == 55
    once = {"N", "Eu", "Lu", "Pb", "Au", "Os", "Re"}
    assert once <= dataset_elements


def test_every_dataset_element_is_in_both_tables(dataset_elements: frozenset[str]) -> None:
    for name in TABLES:
        absent = sorted(dataset_elements - load_table(name).elements)
        assert absent == [], f"{name} is missing {absent}"


#: JARVIS carries a europium row and marks almost all of its properties -9999. These are the
#: two of the nine needed base properties that are real measurements.
EU_REAL = ("atom_mass", "X")


def test_europium_is_a_hole_here_and_a_silent_zero_in_cbfv(
    dataset_elements: frozenset[str],
) -> None:
    """`Eu1Ni5` cannot be featurised from JARVIS. The point is that it is *said*, not hidden.

    CBFV's `jarvis.csv` drops europium from the index entirely; NIST's file keeps the row and
    writes -9999 across it. Neither can produce a JARVIS descriptor for `Eu1Ni5` (row 516).
    CBFV answers anyway -- substituting an all-zero property vector, emitting a full row of
    plausible numbers, and naming the formula only in a `skipped` list that
    `extract_features_cbfv.py` never read, so the published feature matrix contains that row.
    This layer refuses instead, which is the entire difference and the reason the card asks
    for a raise rather than a NaN.
    """
    assert "Eu" in dataset_elements
    table = load_table("jarvis")
    assert "Eu" in table.elements, "NIST lists Eu even though its values are sentinels"
    for prop in EU_REAL:
        assert table.value("Eu", prop) > 0.0
    for prop in (p for p in JARVIS_NEEDED if p not in EU_REAL):
        assert not table.has("Eu", prop)
        with pytest.raises(ElementDataError, match="hole in the published table"):
            table.value("Eu", prop)


def test_the_sentinel_never_survives_as_a_number() -> None:
    """-9999 is 9130 of JARVIS's 45114 cells. Not one may reach a caller as a value."""
    table = load_table("jarvis")
    for element in sorted(table.elements):
        for prop in (*JARVIS_NEEDED, *JARVIS_COMPOSITES):
            if table.has(element, prop):
                assert table.value(element, prop) != -9999.0


def test_neither_table_covers_all_fifty_five_and_the_gaps_are_named(
    dataset_elements: frozenset[str],
) -> None:
    """The honest result of this card: both published sources have gaps, in different places.

    JARVIS is complete except for europium; Oliynyk is complete except for `gordy_en`. Neither
    gap is this loader's doing and neither may be papered over -- what the loader owes is that
    they are impossible to miss.
    """
    with pytest.raises(ElementDataError, match=r"Eu\]"):
        require_coverage("jarvis", dataset_elements, [*JARVIS_NEEDED, *JARVIS_COMPOSITES])

    without_europium = dataset_elements - {"Eu"}
    require_coverage("jarvis", without_europium, [*JARVIS_NEEDED, *JARVIS_COMPOSITES])


# --------------------------------------------------------------------------------------
# A hole raises. This is the card.
# --------------------------------------------------------------------------------------


def test_gordy_electronegativity_is_a_hole_and_coverage_says_so(
    dataset_elements: frozenset[str],
) -> None:
    """`dev_Gordy_electonegativity` is one of the 22 and the publication does not supply it.

    Not a hypothetical. The published table carries a `Gordy EN` column and leaves it empty
    for every element this dataset uses, so the feature cannot be computed from the citable
    source. #19 and #24/#25 own what to do about it; this test's job is to make sure it can
    never be discovered as a NaN halfway down the pipeline.
    """
    with pytest.raises(ElementDataError) as caught:
        require_coverage("oliynyk", dataset_elements, OLIYNYK_NEEDED)
    message = str(caught.value)
    assert "empty cell" in message
    assert "gordy_en" in message


def test_the_other_twelve_oliynyk_properties_are_complete(
    dataset_elements: frozenset[str],
) -> None:
    """Everything except `gordy_en` is there, so the failure above is specific, not general."""
    complete = tuple(p for p in OLIYNYK_NEEDED if p != "gordy_en")
    require_coverage("oliynyk", dataset_elements, complete)


def test_a_hole_raises_rather_than_yielding_nan() -> None:
    table = load_table("oliynyk")
    assert table.has("Ni", "gordy_en"), "nickel is one of the 34 the publication does supply"
    assert not table.has("Ce", "gordy_en")
    with pytest.raises(ElementDataError, match="hole in the published table"):
        table.value("Ce", "gordy_en")


def test_an_absent_element_raises_and_says_what_cbfv_would_have_done() -> None:
    table = load_table("oliynyk")
    assert "Og" not in table.elements
    with pytest.raises(ElementDataError, match="has no element"):
        table.value("Og", "atomic_weight")


def test_an_unknown_property_raises() -> None:
    with pytest.raises(ElementDataError, match="has no property"):
        load_table("jarvis").value("Ni", "enthusiasm")


def test_no_requested_value_is_ever_nan(dataset_elements: frozenset[str]) -> None:
    """The negative of the whole module: nothing that comes back is a NaN."""
    checks = [
        ("jarvis", (*JARVIS_NEEDED, *JARVIS_COMPOSITES), dataset_elements - {"Eu"}),
        ("oliynyk", tuple(p for p in OLIYNYK_NEEDED if p != "gordy_en"), dataset_elements),
    ]
    for name, properties, elements in checks:
        table = load_table(name)
        for prop in properties:
            for element in sorted(elements):
                assert not math.isnan(table.value(element, prop))


def test_vector_is_float64_and_refuses_a_partial_answer(
    dataset_elements: frozenset[str],
) -> None:
    table = load_table("oliynyk")
    elements = tuple(sorted(dataset_elements))
    values = table.vector("atomic_weight", elements)
    assert values.dtype.name == "float64"
    assert values.shape == (55,)
    # One hole anywhere in the request loses the whole array, deliberately: a partially
    # filled vector pushes the decision about holes onto whichever statistic sees it first.
    with pytest.raises(ElementDataError, match="hole in the published table"):
        table.vector("gordy_en", elements)


# --------------------------------------------------------------------------------------
# The claims SOURCES.md makes about CBFV, asserted
# --------------------------------------------------------------------------------------


def _reference() -> dict[str, dict[str, float]]:
    with REFERENCE.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)[1:]
        return {
            row[0]: {p: float(c) for p, c in zip(header, row[1:], strict=True) if c != ""}
            for row in reader
            if row
        }


#: SOURCES.md's delta table, as data. Left is the published column, right is CBFV's name.
AGREES_EXACTLY = {
    "pauling_en": "Pauling_Electronegativity",
    "specific_heat_j_g_k": "specific_heat_(J/g_K)_",
    "heat_of_vaporization_kj_mol": "heat_of_vaporization_(kJ/mol)_",
    "mendeleev_number": "Mendeleev_Number",
    "unfilled_s": "Number_of_unfilled_s_valence_electrons",
}

REVISED = {
    "zunger_radii_sum": ("Zunger_radii_sum", 5e-3),
    "density_g_ml": ("Density_(g/mL)", 8e-3),
    "atomic_weight": ("Atomic_Weight", 2e-2),
    "mulliken_en": ("Mulliken_EN", 3.216e-1),
    "covalent_radius": ("Covalent_Radius", 5.4e-1),
    "gilman_no_of_valence_electrons": ("gilmor_number_of_valence_electron", 2.0),
    "valence_d": ("valence_d", 10.0),
}


def test_five_oliynyk_properties_match_cbfv_exactly(dataset_elements: frozenset[str]) -> None:
    table = load_table("oliynyk")
    reference = _reference()
    for ours, theirs in AGREES_EXACTLY.items():
        for element in sorted(dataset_elements):
            assert table.value(element, ours) == reference[element][theirs], (
                f"{ours}[{element}] was documented as agreeing with CBFV exactly"
            )


def test_the_revised_properties_differ_by_exactly_what_was_documented(
    dataset_elements: frozenset[str],
) -> None:
    """The deltas are asserted, not described. AC-2 rests on knowing they are there."""
    table = load_table("oliynyk")
    reference = _reference()
    for ours, (theirs, documented) in REVISED.items():
        worst = max(
            abs(table.value(element, ours) - reference[element][theirs])
            for element in sorted(dataset_elements)
        )
        assert worst > 0.0, f"{ours} was documented as revised and now agrees with CBFV"
        assert worst == pytest.approx(documented, rel=1e-3), (
            f"{ours} differs from CBFV by {worst}, SOURCES.md says {documented}"
        )


#: The 21 dataset elements the published Oliynyk table has no Gordy electronegativity for.
#: Overwhelmingly the rare earths, which is what makes it expensive: they are most of the AB5
#: and AB2 chemistry this dataset is built on.
GORDY_MISSING = frozenset(
    "Ce Dy Er Eu Gd Hf Ho Ir Lu Nd Os Pr Pt Re Sm Ta Tb Th Tm U W".split()
)


def test_gordy_is_the_property_cbfv_has_and_the_publication_only_partly_does(
    dataset_elements: frozenset[str],
) -> None:
    """CBFV supplies Gordy EN for all 55; the citable table supplies it for 34.

    So `dev_Gordy_electonegativity` -- one of the 22 -- cannot be computed from the source
    this project stands on for any composition containing one of the other 21. Cards #19 and
    #24/#25 own the consequence: drop the feature and re-run selection, or find a second
    citable source. This test pins which elements, so that decision is made against a list.
    """
    reference = _reference()
    table = load_table("oliynyk")
    missing = {e for e in dataset_elements if not table.has(e, "gordy_en")}
    assert missing == GORDY_MISSING
    for element in sorted(dataset_elements):
        assert "Gordy_electonegativity" in reference[element], "CBFV has it for every element"


# --------------------------------------------------------------------------------------
# Risk R3, settled by the source data rather than by experiment
# --------------------------------------------------------------------------------------


def test_the_jarvis_composites_are_columns_and_are_the_arithmetic_of_their_parts(
    dataset_elements: frozenset[str],
) -> None:
    """Card #8 recorded that CBFV *synthesises* these. It does not; they are table columns.

    That settles PRD risk R3 and card #18's open question: a composite is a property of an
    element, so the statistic is taken over the composite. Statistic-of-composite, by
    construction. Verified here against the parts, so the claim is not merely a header
    sighting.
    """
    table = load_table("jarvis")
    for composite, (left, op, right) in JARVIS_COMPOSITES.items():
        assert composite in table.properties
        for element in sorted(dataset_elements):
            if not table.has(element, composite):
                continue  # europium, whose parts are sentinels; covered by its own test
            a = table.value(element, left)
            b = table.value(element, right)
            expected = a * b if op == "*" else (a / b if b != 0.0 else 0.0)
            assert table.value(element, composite) == pytest.approx(expected, rel=1e-9, abs=1e-9)


# --------------------------------------------------------------------------------------
# The licence boundary
# --------------------------------------------------------------------------------------


def test_nothing_in_the_descriptor_layer_imports_cbfv() -> None:
    """The card's fourth box, as a test rather than a habit.

    CBFV carries no licence, so it may not be a runtime dependency of a GPL-3.0 deliverable.
    It is allowed in exactly two places: `scripts/build_element_tables.py`, which writes the
    AC-2 reference fixture and is never run by CI, and the parity gate itself (card #21).
    """
    imports = re.compile(r"^\s*(?:import\s+CBFV|from\s+CBFV\b)", re.MULTILINE)
    root = Path(__file__).resolve().parents[2] / "hydms" / "descriptors"
    offenders = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if imports.search(path.read_text(encoding="utf-8"))
    )
    assert offenders == []
