"""Card #18 — the composite descriptors, the order they are formed in, and six hand pins.

Four claims, in the order the card makes them.

1. **The order is statistic-of-composite**, and the rejected order is not a near miss. It is
   pinned here as a negative test rather than deleted, because "both orders behind a flag, the
   loser deleted before merge" leaves nothing behind to stop a later simplification putting the
   loser back.
2. **The grammar is a spec, not a branch.** ``_divi_`` and ``_mult_`` decompose all 156 of
   JARVIS's composite columns, unambiguously, into columns of the same table.
3. **Eleven of those columns are not their own arithmetic**, and the audit that finds them is the
   guard a featuriser runs before trusting one.
4. **Each of the six JARVIS features is pinned to a hand-computed value** on ``Mg2Ni1``, where
   the fractions are 2/3 and 1/3 and the five statistics have closed forms a reader can check
   with a pencil.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest
from hydms.data.load import parse_formula
from hydms.descriptors.composites import (
    INFIXES,
    Composite,
    CompositeError,
    composite_properties,
    decompose,
    disagreements,
    require_self_consistent,
)
from hydms.descriptors.element_data import ElementDataError, load_table
from hydms.descriptors.stats import STATISTICS, statistics

FIXTURE = Path(__file__).parent / "data" / "cbfv_statistics_reference.csv"

#: The five composite properties behind five of the 22 selected features, and the plain column
#: behind the sixth. Card #8 resolved the mapping; `FEATURE_PROVENANCE.md` records it.
SELECTED_COMPOSITES = (
    "polzbl_divi_atom_mass",
    "atom_mass_mult_therm_cond",
    "bp_divi_atom_mass",
    "first_ion_en_mult_X",
    "voro_coord_divi_mol_vol",
)
SELECTED_PLAIN = "is_alkaline"

#: Measured on the committed table: 156 of JARVIS's 438 columns carry an infix, `oliynyk` has
#: none, and eleven of the 156 disagree with their own parts. Numbers rather than a shape,
#: because a golden that stops covering a case reports agreement it never checked (card #15).
JARVIS_COMPOSITE_COLUMNS = 156
INCONSISTENT_COLUMNS = 11
INCONSISTENT_ELEMENTS = {"Cs", "Gd"}

#: The hand pins agree with the float pipeline to 1.9e-16 relative, worst of the 30 values below.
#: The tolerance is the project's usual 1e-12 — four orders of headroom, and still twelve orders
#: tighter than the difference the rejected order would introduce.
PIN_RTOL = 1e-12
PIN_ATOL = 1e-12

#: How far composite-of-statistic lands from CBFV, per column, worst formula of the sixteen:
#: 1.8% at the very best (`avg_first_ion_en_mult_X`) and a factor of 65 at the worst
#: (`dev_bp_divi_atom_mass`). A floor of 1e-2 is therefore a measured statement about the
#: distance between the two orders, not a threshold chosen to make a test pass.
REJECTED_ORDER_FLOOR = 1e-2

#: ``Mg2Ni1``: fractions 2/3 magnesium and 1/3 nickel, so with ``a`` the magnesium value and
#: ``b`` the nickel one::
#:
#:     avg   = (2a + b) / 3
#:     dev   = (2/3)|a - avg| + (1/3)|b - avg|  =  (4/9)|a - b|
#:     range = |a - b|,  max = max(a, b),  min = min(a, b)
#:
#: Each expected value below is that arithmetic carried out in exact decimal — not by the code
#: under test, and not by numpy — from the two element values, which are themselves checked
#: against the table before use. `dev`'s closed form is worth reading twice: CBFV's `dev` is the
#: fraction-weighted mean absolute deviation, not a standard deviation of any kind (card #17).
HAND_PINS: dict[str, tuple[float, float, dict[str, str]]] = {
    "polzbl_divi_atom_mass": (
        0.44298155386545984,
        0.11585629730088903,
        {
            "avg": "0.333939801677269572829",
            "dev": "0.145389002917587026628",
            "range": "0.327125256564570809914",
            "max": "0.442981553865459842800",
            "min": "0.115856297300889032886",
        },
    ),
    "atom_mass_mult_therm_cond": (
        3888.8,
        5341.0994,
        {
            "avg": "4372.89980000000014115",
            "dev": "645.466399999999945673",
            "range": "1452.29939999999987776",
            "max": "5341.09940000000005966",
            "min": "3888.80000000000018190",
        },
    ),
    "bp_divi_atom_mass": (
        56.07899609133923,
        54.28208282362242,
        {
            "avg": "55.4800250021002909762",
            "dev": "0.798628118985249102479",
            "range": "1.79691326771681048058",
            "max": "56.0789960913392278030",
            "min": "54.2820828236224173224",
        },
    ),
    "first_ion_en_mult_X": (
        10.01656785,
        14.592018,
        {
            "avg": "11.5417178999999994934",
            "dev": "2.03353339999999999716",
            "range": "4.57545014999999999361",
            "max": "14.5920179999999994891",
            "min": "10.0165678499999994955",
        },
    ),
    "voro_coord_divi_mol_vol": (
        0.8571428571428571,
        1.8209408194233687,
        {
            "avg": "1.17840884456969430261",
            "dev": "0.428354649902449609774",
            "range": "0.963797962280511621991",
            "max": "1.82094081942336871727",
            "min": "0.857142857142857095276",
        },
    ),
    # Not a composite at all — a 0/1 flag, pinned with the five because the six JARVIS features
    # stand or fall together on europium, and because its statistics are exact thirds and ninths
    # that need no table at all to check: avg = 2/3, dev = 4/9, range = 1.
    "is_alkaline": (
        1.0,
        0.0,
        {
            "avg": "0.666666666666666666667",
            "dev": "0.444444444444444444444",
            "range": "1",
            "max": "1",
            "min": "0",
        },
    ),
}


@pytest.fixture(scope="module")
def jarvis():
    return load_table("jarvis")


def _fixture_rows(prop: str) -> list[dict[str, str]]:
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        return [r for r in csv.DictReader(handle) if r["table"] == "jarvis" and r["property"] == prop]


def _pack(formulae: list[str], value_of) -> tuple[np.ndarray, np.ndarray]:
    """Formulae to the ``(n_compositions, max_arity)`` pair :func:`statistics` takes."""
    parsed = [list(parse_formula(f).items()) for f in formulae]
    width = max(len(p) for p in parsed)
    weights = np.zeros((len(parsed), width))
    values = np.full((len(parsed), width), np.nan)
    for row, items in enumerate(parsed):
        for column, (element, amount) in enumerate(items):
            weights[row, column] = amount
            values[row, column] = value_of(element)
    return weights, values


# ---------------------------------------------------------------------------------------
# The grammar: a parse, not a guess
# ---------------------------------------------------------------------------------------


def test_the_grammar_decomposes_every_composite_column_of_both_tables(jarvis) -> None:
    """156 columns, each splitting exactly one way into two columns of the same table.

    This is what lets `INFIXES` be a two-entry specification rather than a table of special
    cases: if even one name were ambiguous or unresolvable, `decompose` would have to guess and
    the "declarative spec, not hard-coded branches" the card asks for would be a fiction.
    """
    found = composite_properties("jarvis")
    assert len(found) == JARVIS_COMPOSITE_COLUMNS
    assert composite_properties("oliynyk") == (), "oliynyk publishes no composites at all"

    for composite in found:
        assert composite.left in jarvis.properties
        assert composite.right in jarvis.properties
        infix = next(k for k, v in INFIXES.items() if v == composite.operator)
        assert composite.name == f"{composite.left}{infix}{composite.right}"

    assert {c.operator for c in found} == {"/", "*"}
    assert len({c.name for c in found}) == len(found)


def test_a_plain_column_is_not_a_composite(jarvis) -> None:
    for prop in ("polzbl", "atom_mass", SELECTED_PLAIN):
        assert decompose(prop, jarvis) is None


def test_a_feature_name_is_refused_rather_than_split_wrongly(jarvis) -> None:
    """`avg_polzbl_divi_atom_mass` splits into `avg_polzbl` and `atom_mass`, and the first is not
    a column. Guessing there would silently featurise from the wrong pair of properties."""
    with pytest.raises(CompositeError, match="statistic still attached"):
        decompose("avg_polzbl_divi_atom_mass", jarvis)


def test_an_ambiguous_name_is_refused(jarvis) -> None:
    """No column of either table decomposes two ways. One arriving from anywhere else is refused
    rather than resolved by position, because neither reading is more likely than the other."""
    with pytest.raises(CompositeError, match="decomposes 2 ways"):
        decompose("a_divi_b_divi_c")


# ---------------------------------------------------------------------------------------
# The audit: which columns are the arithmetic their names claim
# ---------------------------------------------------------------------------------------


def test_the_selected_composites_are_the_arithmetic_of_their_parts() -> None:
    """The five in the 22, on every element that carries them.

    Measured beyond what is asserted: on all 82 elements the published column and the quotient
    or product of its parts are the *same double*, bit for bit. That is asserted here through
    the tolerance rather than with `==`, because the published number is NIST's and ours is a
    division — an equality would be a claim about how a future revision of somebody else's file
    rounds its own columns.
    """
    assert disagreements("jarvis", SELECTED_COMPOSITES) == ()
    require_self_consistent("jarvis", SELECTED_COMPOSITES)


def test_a_plain_column_passed_to_the_audit_is_skipped_not_refused() -> None:
    """So a caller may hand over the whole property list it is about to featurise."""
    require_self_consistent("jarvis", [*SELECTED_COMPOSITES, SELECTED_PLAIN, "polzbl"])
    assert disagreements("jarvis", [SELECTED_PLAIN]) == ()


def test_eleven_jarvis_columns_are_not_the_arithmetic_of_their_parts(jarvis) -> None:
    """The published file contradicts itself about two elements, and this is the guard for it.

    Every `*_mult_voro_coord` column is 0.0 for caesium and gadolinium — formed as though
    `voro_coord` were 0 — while the `voro_coord` column itself stores 1.0 and
    `voro_coord_divi_mol_vol` uses that 1.0 (Gd: 1/19.9 = 0.05025125628140704, the stored value).
    """
    found = disagreements("jarvis")
    columns = sorted({d.composite.name for d in found})
    assert len(columns) == INCONSISTENT_COLUMNS
    assert all(name.endswith("_mult_voro_coord") for name in columns), columns
    assert {d.element for d in found} == INCONSISTENT_ELEMENTS
    assert {d.published for d in found} == {0.0}
    for element in INCONSISTENT_ELEMENTS:
        assert jarvis.value(element, "voro_coord") == 1.0

    with pytest.raises(CompositeError, match="not the arithmetic"):
        require_self_consistent("jarvis", ["X_mult_voro_coord"])


def test_the_audit_refuses_a_property_the_table_does_not_have() -> None:
    with pytest.raises(ElementDataError, match="no property"):
        require_self_consistent("jarvis", ["polzbl_divi_no_such_column"])


def test_a_hole_in_a_part_is_a_hole_in_the_column(jarvis) -> None:
    """156 columns out of 156. The table never carries a number for a composite whose operands it
    does not have — which is exactly what CBFV does do, substituting zeros for an element it
    lacks and emitting a full row of plausible descriptors."""
    for composite in composite_properties(jarvis):
        for element in sorted(jarvis.elements):
            if not jarvis.has(element, composite.name):
                continue
            assert jarvis.has(element, composite.left), f"{composite.name}[{element}]"
            assert jarvis.has(element, composite.right), f"{composite.name}[{element}]"

    # Europium, whose JARVIS row is all -9999: refused by the composite column exactly as by its
    # parts, which is why `Eu1Ni5` cannot be featurised rather than being featurised as zero.
    for prop in (*SELECTED_COMPOSITES, SELECTED_PLAIN):
        assert not jarvis.has("Eu", prop)


def test_a_division_by_zero_is_refused_rather_than_returned_as_zero() -> None:
    """Unreached on the committed table — no element has a zero denominator for any of the 156 —
    so this states the intent for a table that one day does."""
    composite = Composite(name="a_divi_b", left="a", operator="/", right="b")
    with pytest.raises(CompositeError, match="hole spelled"):
        composite.combine(1.0, 0.0)
    assert Composite(name="a_mult_b", left="a", operator="*", right="b").combine(3.0, 0.0) == 0.0


# ---------------------------------------------------------------------------------------
# The hand pins
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("prop", list(HAND_PINS))
def test_each_selected_jarvis_feature_matches_a_hand_computed_value(prop: str, jarvis) -> None:
    """One pin per feature, computed with a pencil rather than with the code under test.

    The pin's *inputs* are checked against the table first, so a table revision breaks this test
    at the value it changed instead of at the statistic three lines later.
    """
    magnesium, nickel, expected = HAND_PINS[prop]
    assert jarvis.value("Mg", prop) == magnesium
    assert jarvis.value("Ni", prop) == nickel

    parsed = parse_formula("Mg2Ni1")
    assert list(parsed) == ["Mg", "Ni"], "the closed forms below assume this element order"
    assert list(parsed.values()) == [2.0, 1.0]

    weights = np.array([list(parsed.values())])
    values = np.array([[magnesium, nickel]])
    got = statistics(weights, values)

    for statistic in STATISTICS:
        hand = float(Decimal(expected[statistic]))
        assert got[statistic][0] == pytest.approx(hand, rel=PIN_RTOL, abs=PIN_ATOL), (
            f"{statistic}_{prop} on Mg2Ni1: computed {got[statistic][0]!r}, hand-computed "
            f"{expected[statistic]}"
        )


# ---------------------------------------------------------------------------------------
# Risk R3: the rejected order, kept as a negative test
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("prop", SELECTED_COMPOSITES)
def test_the_statistic_is_taken_over_the_composite_and_not_the_other_way_round(
    prop: str, jarvis
) -> None:
    """Statistic-of-composite reproduces CBFV; composite-of-statistic misses it by 2% to 65x.

    R3 was settled by card #16 from the source data — a composite is a property of an element,
    so the statistic is taken over it — and this is the measurement that would have settled it
    the expensive way. It is kept because the two orders are one refactor apart in code and four
    orders apart in the answer.
    """
    rows = _fixture_rows(prop)
    assert rows, f"{prop} is not in the CBFV fixture"
    formulae = [row["formula"] for row in rows]
    composite = decompose(prop, jarvis)
    assert composite is not None

    weights, values = _pack(formulae, lambda e: jarvis.value(e, prop))
    right_way = statistics(weights, values)
    left = statistics(*_pack(formulae, lambda e: jarvis.value(e, composite.left)))
    right = statistics(*_pack(formulae, lambda e: jarvis.value(e, composite.right)))

    worst = 0.0
    for statistic in STATISTICS:
        cbfv = np.array([float(row[statistic]) for row in rows])
        assert np.allclose(right_way[statistic], cbfv, rtol=1e-12, atol=1e-12), (
            f"{statistic}_{prop}: statistic-of-composite must reproduce CBFV"
        )
        with np.errstate(divide="ignore", invalid="ignore"):
            wrong_way = (
                left[statistic] * right[statistic]
                if composite.operator == "*"
                else left[statistic] / right[statistic]
            )
        assert not np.allclose(wrong_way, cbfv, rtol=1e-12, atol=1e-12), (
            f"{statistic}_{prop}: the two orders agree, which cannot be right"
        )
        deviation = np.abs(wrong_way - cbfv) / np.maximum(np.abs(cbfv), np.finfo(float).tiny)
        finite = deviation[np.isfinite(deviation)]
        worst = max(worst, float(finite.max()) if finite.size else np.inf)

    assert worst >= REJECTED_ORDER_FLOOR, (
        f"{prop}: composite-of-statistic differs from CBFV by only {worst:.3e} relative — "
        f"measured, the smallest such gap over the five composites is 1.8e-2"
    )
