"""The five composition statistics, and the two things about them that are counter-intuitive.

Card #17. What is being defended here is not that a weighted mean is a weighted mean.

**``dev`` is not a standard deviation.** It is the fraction-weighted mean absolute deviation
about the fraction-weighted mean. Every plausible alternative reading differs in the third
significant figure, not the twelfth, so this is not a rounding question and no tolerance
would catch it -- ``test_dev_is_not_any_kind_of_standard_deviation`` pins the gap.

**The reduction has to run down the leading axis.** Reducing the caller-natural
``(n_compositions, arity)`` shape over its fast axis makes numpy sum pairwise, which
reorders the additions; over the leading axis it accumulates sequentially, and adding an
exactly-zero padded term to a finite float is exact. Measured against CBFV over both tables,
the wrong axis costs up to 2.794e-09 -- above gate AC-2's 1e-9 -- and the right one costs
exactly nothing. ``test_padding_changes_nothing_at_all`` and
``test_a_composition_does_not_depend_on_its_batch`` are that property stated as arithmetic
rather than as a shape, so they stay true if the implementation is rewritten.

The parity fixture is CBFV 1.1.0's own output, committed by
``scripts/build_element_tables.py --cbfv-statistics``. CBFV is not imported here and cannot
be: it is unlicensed and lives in the optional ``parity`` extra, which CI does not install.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pytest
from hydms.data.load import parse_formula
from hydms.descriptors.element_data import load_table
from hydms.descriptors.stats import STATISTICS, CompositionError, Statistics, statistics

DATA = Path(__file__).parent / "data"
FIXTURE = DATA / "cbfv_statistics_reference.csv"
CBFV_OLIYNYK = DATA / "cbfv_oliynyk_reference.csv"

#: Measured, not chosen. Against CBFV's own table in CBFV's own element order the oliynyk
#: half reproduces to **0.0**; through ``parse_formula``, which sorts elements by symbol and
#: so accumulates in a different order, the worst cell moves by 1.705e-13. The jarvis half
#: additionally carries the 7.3e-12 difference between NIST's ``Elements.json`` and CBFV's
#: copy of it (card #16), and lands at 9.095e-13 absolute, 1.323e-14 relative. A mixed
#: tolerance is what makes one constant serve both: ``atom_mass_mult_therm_cond`` reaches
#: 2.2e4, where a pure absolute bound would be measuring the magnitude rather than the code.
PARITY_RTOL = 1e-12
PARITY_ATOL = 1e-12

#: Permuting the elements of every formula needs rtol >= 4.313e-16 with this atol; scaling
#: every weight by 7 needs 5.283e-15. Both are ulps of the value, not errors of the method --
#: see the module docstring of ``hydms.descriptors.stats``. ``docs/QA-PROTOCOL.md`` §L2 asks
#: for these two invariances, and neither is exact, in this module or in CBFV.
INVARIANCE_RTOL = 1e-12
INVARIANCE_ATOL = 1e-12


# ---------------------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------------------


def _cbfv_oliynyk() -> dict[str, dict[str, float]]:
    with CBFV_OLIYNYK.open(encoding="utf-8", newline="") as handle:
        return {
            row["element"]: {k: float(v) for k, v in row.items() if k != "element" and v != ""}
            for row in csv.DictReader(handle)
        }


def _fixture() -> list[dict[str, str]]:
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def pack(
    formulae: list[str], value_of: object
) -> tuple[np.ndarray, np.ndarray]:
    """Formulae to the ``(n_compositions, max_arity)`` pair :func:`statistics` takes.

    This is what card #20 will do for real. Elements come out of ``parse_formula`` sorted
    by symbol, which is *not* CBFV's parse order -- the reason parity below is a tolerance
    rather than an equality.
    """
    parsed = [list(parse_formula(f).items()) for f in formulae]
    width = max(len(p) for p in parsed)
    weights = np.zeros((len(parsed), width))
    values = np.full((len(parsed), width), np.nan)  # padding is nan, and must not matter
    for row, items in enumerate(parsed):
        for column, (element, amount) in enumerate(items):
            weights[row, column] = amount
            values[row, column] = value_of(element)  # type: ignore[operator]
    return weights, values


@pytest.fixture(scope="module")
def oliynyk_reference() -> dict[str, dict[str, float]]:
    return _cbfv_oliynyk()


# ---------------------------------------------------------------------------------------
# Parity with CBFV, over both tables
# ---------------------------------------------------------------------------------------


def test_the_fixture_covers_both_tables_and_every_arity() -> None:
    """A golden that stops covering a case reports agreement it never checked (card #15)."""
    rows = _fixture()
    assert {row["table"] for row in rows} == {"oliynyk", "jarvis"}
    arities = {len(parse_formula(row["formula"])) for row in rows}
    assert arities == set(range(2, 11)), f"arities covered: {sorted(arities)}"
    assert set(rows[0]) == {"formula", "table", "property", *STATISTICS}


@pytest.mark.parametrize("table", ["oliynyk", "jarvis"])
def test_reproduces_cbfv(table: str, oliynyk_reference: dict[str, dict[str, float]]) -> None:
    """Every statistic CBFV emitted, recomputed here without importing CBFV.

    Both tables, because a single-table result cannot pass AC-2 no matter how correct its
    oliynyk half is: six of the 22 selected features come from jarvis, and the
    highest-SHAP feature in the whole model is one of them.
    """
    rows = [row for row in _fixture() if row["table"] == table]
    assert rows, f"no {table} rows in the fixture"
    jarvis = load_table("jarvis") if table == "jarvis" else None

    checked = 0
    for prop in sorted({row["property"] for row in rows}):
        these = [row for row in rows if row["property"] == prop]
        formulae = [row["formula"] for row in these]
        if table == "oliynyk":
            weights, values = pack(formulae, lambda e, p=prop: oliynyk_reference[e][p])
        else:
            assert jarvis is not None
            weights, values = pack(formulae, lambda e, p=prop: jarvis.value(e, p))
        got = statistics(weights, values)
        for statistic in STATISTICS:
            expected = np.array([float(row[statistic]) for row in these])
            worst = int(np.argmax(np.abs(got[statistic] - expected)))
            assert np.allclose(
                got[statistic], expected, rtol=PARITY_RTOL, atol=PARITY_ATOL
            ), (
                f"{statistic}_{prop} disagrees with CBFV; worst at {formulae[worst]}: "
                f"got {got[statistic][worst]!r}, CBFV {expected[worst]!r}, "
                f"difference {abs(got[statistic][worst] - expected[worst]):.3e}"
            )
            checked += len(these)
    assert checked == len(rows) * len(STATISTICS)


# ---------------------------------------------------------------------------------------
# What `dev` is, and what it is not
# ---------------------------------------------------------------------------------------


def test_dev_is_the_fraction_weighted_mean_absolute_deviation() -> None:
    """Hand-computed, so the definition is legible without running CBFV.

    ``Mg1.5Ni1``: fractions 0.6 / 0.4 over Pauling electronegativities 1.31 / 1.91.
    """
    weights = np.array([[1.5, 1.0]])
    values = np.array([[1.31, 1.91]])
    got = statistics(weights, values)

    avg = 0.6 * 1.31 + 0.4 * 1.91
    dev = 0.6 * abs(1.31 - avg) + 0.4 * abs(1.91 - avg)
    assert got.avg[0] == pytest.approx(avg, abs=1e-15)
    assert got.dev[0] == pytest.approx(dev, abs=1e-15)
    # And it is CBFV's number: the fixture row for this formula and property.
    row = next(
        r
        for r in _fixture()
        if r["formula"] == "Mg1.5Ni1" and r["property"] == "Pauling_Electronegativity"
    )
    assert got.dev[0] == pytest.approx(float(row["dev"]), rel=PARITY_RTOL, abs=PARITY_ATOL)


def test_dev_is_not_any_kind_of_standard_deviation() -> None:
    """The three readings a reader might reach for, and how far each is from the truth.

    Measured over all 1,279 formulae and every oliynyk property, the gaps are 328.8
    (fraction-weighted population sd), 1172.2 (unweighted sd) and 1094.9 (unweighted mean
    absolute deviation). This asserts the same thing on one row: the difference is in the
    leading figures, so no tolerance anywhere in this project would absorb it.
    """
    weights = np.array([[1.5, 1.0]])
    values = np.array([[1.31, 1.91]])
    got = statistics(weights, values)

    fractions = np.array([0.6, 0.4])
    properties = np.array([1.31, 1.91])
    avg = float((fractions * properties).sum())
    weighted_sd = math.sqrt(float((fractions * (properties - avg) ** 2).sum()))
    unweighted_sd = float(properties.std())
    unweighted_mad = float(np.abs(properties - properties.mean()).mean())

    assert got.dev[0] == pytest.approx(0.288, abs=1e-12)
    for name, rival in (
        ("fraction-weighted sd", weighted_sd),
        ("unweighted sd", unweighted_sd),
        ("unweighted mad", unweighted_mad),
    ):
        assert abs(got.dev[0] - rival) > 1e-3, f"{name} is indistinguishable from dev here"


def test_range_max_and_min_ignore_the_fractions_entirely() -> None:
    """They are taken over the distinct elements present, not over the mixture.

    Two compositions of the same two elements in wildly different proportions share a
    ``range``, a ``max`` and a ``min`` exactly, and share neither ``avg`` nor ``dev``.
    """
    values = np.array([[1.31, 1.91], [1.31, 1.91]])
    got = statistics(np.array([[1.5, 1.0], [0.01, 9.99]]), values)

    assert got.max[0] == got.max[1] == 1.91
    assert got.min[0] == got.min[1] == 1.31
    assert got.range[0] == got.range[1]
    assert got.range[0] == pytest.approx(1.91 - 1.31, abs=1e-15)
    assert got.avg[0] != got.avg[1]
    assert got.dev[0] != got.dev[1]


def test_a_one_element_composition_has_no_spread() -> None:
    got = statistics(np.array([[3.0, 0.0]]), np.array([[7.25, np.nan]]))
    assert got.avg[0] == 7.25
    assert got.max[0] == got.min[0] == 7.25
    assert got.dev[0] == 0.0
    assert got.range[0] == 0.0


# ---------------------------------------------------------------------------------------
# The arithmetic properties that make the vectorisation legitimate
# ---------------------------------------------------------------------------------------


def test_padding_changes_nothing_at_all() -> None:
    """Exactly, not approximately -- and that is the whole design.

    Widening the batch with all-zero columns is what happens whenever one formula in a batch
    has more elements than another. A padded term enters the accumulation as an exact 0.0
    and a sequential accumulation is unchanged by it; a *pairwise* one is not, because the
    padding changes how the additions are grouped. If this ever fails by an ulp, the
    reduction has drifted off the leading axis and gate AC-2 is next.
    """
    rng = np.random.default_rng(17)
    weights = rng.uniform(0.05, 5.0, size=(64, 4))
    values = rng.uniform(-2.0e4, 2.0e4, size=(64, 4))
    narrow = statistics(weights, values)

    for extra in (1, 3, 6):
        wide_w = np.hstack([weights, np.zeros((64, extra))])
        wide_v = np.hstack([values, np.full((64, extra), np.nan)])
        wide = statistics(wide_w, wide_v)
        for statistic in STATISTICS:
            assert np.array_equal(wide[statistic], narrow[statistic]), (
                f"{extra} columns of padding moved {statistic}"
            )


def test_a_composition_does_not_depend_on_its_batch() -> None:
    """Row i of a batched call equals the same row computed alone. Exactly.

    **The arity here is ten, and that is the whole test.** At five, which is what this test
    used until card #20, it passes whether or not the module handles a batch of one --
    because a lone composition transposes to a *contiguous* reduction axis, numpy sums it
    pairwise, and its contiguous sum only starts regrouping the additions at eight elements.
    From arity 8 a batch of one disagreed with the same composition inside a batch by up to
    5.5e-12 on ``avg`` and ``dev``; eleven of the 1,279 curated rows are that wide, and
    featurising one formula alone is what the app does. `statistics` now reduces a duplicated
    pair and discards the copy. Drop that and this goes red at arity 8, not at arity 5.
    """
    rng = np.random.default_rng(1717)
    weights = rng.uniform(0.05, 5.0, size=(32, 10))
    weights[::3, 8:] = 0.0  # a mix of arities, as any real batch has
    weights[::7, 3:] = 0.0
    values = rng.uniform(-2.0e4, 2.0e4, size=(32, 10))
    batched = statistics(weights, values)

    for row in range(weights.shape[0]):
        alone = statistics(weights[row : row + 1], values[row : row + 1])
        for statistic in STATISTICS:
            assert alone[statistic][0] == batched[statistic][row], (
                f"row {row}'s {statistic} depends on what else was in the batch"
            )


@pytest.mark.parametrize("table", ["oliynyk", "jarvis"])
def test_invariant_to_element_order(table: str) -> None:
    """QA-PROTOCOL §L2's permutation invariance -- to a measured tolerance, not to the bit.

    Over the real tables and 400 real formulae, permuting the elements moves a statistic by
    up to 1.364e-12 (oliynyk) and 2.794e-09 (jarvis). The second number is not a defect: one
    ulp at jarvis's largest value, 2.15e7, is 3.7e-09. CBFV behaves identically, which is
    why parity with it is stated to 1e-9 and never as equality.
    """
    weights, values = _real_batch(table)
    base = statistics(weights, values)

    rng = np.random.default_rng(17)
    permuted_w, permuted_v = weights.copy(), values.copy()
    for row in range(weights.shape[0]):
        arity = int((weights[row] != 0.0).sum())
        order = rng.permutation(arity)
        permuted_w[row, :arity] = weights[row, order]
        permuted_v[row, :arity] = values[row, order]
    permuted = statistics(permuted_w, permuted_v)

    for statistic in STATISTICS:
        assert np.allclose(
            permuted[statistic], base[statistic],
            rtol=INVARIANCE_RTOL, atol=INVARIANCE_ATOL,
        ), f"{statistic} moved when the elements were reordered"


@pytest.mark.parametrize("table", ["oliynyk", "jarvis"])
@pytest.mark.parametrize("factor", [0.1, 7.0, 1000.0])
def test_invariant_to_rescaling_the_weights(table: str, factor: float) -> None:
    """``La1Ni5`` and ``La2Ni10`` are the same material and must featurise the same.

    The module normalises internally, which is the only reason this holds at all -- and it
    holds to 5.283e-15 relative rather than exactly, because rescaling re-rounds the
    division. Deciding that two formulae *are* the same material is the canonical key's job
    (card #87); this is only the arithmetic not getting in its way.
    """
    weights, values = _real_batch(table)
    base = statistics(weights, values)
    scaled = statistics(weights * factor, values)

    for statistic in STATISTICS:
        assert np.allclose(
            scaled[statistic], base[statistic],
            rtol=INVARIANCE_RTOL, atol=INVARIANCE_ATOL,
        ), f"{statistic} moved when every weight was multiplied by {factor}"


def _real_batch(table: str) -> tuple[np.ndarray, np.ndarray]:
    """A batch built from the committed tables, so both are exercised for real.

    The property is chosen for magnitude: ``heat_of_vaporization_kj_mol`` reaches ~672 and
    ``atom_mass_mult_therm_cond`` ~2.2e4, which is where an absolute tolerance stops being
    a statement about the code. Elements with a hole are skipped rather than worked around
    -- ``gordy_en`` is empty for 21 of the 55 elements and every jarvis property of europium
    is a sentinel (card #16), and this test is not the place to decide what to do about it.
    """
    loaded = load_table(table)
    prop = "heat_of_vaporization_kj_mol" if table == "oliynyk" else "atom_mass_mult_therm_cond"
    formulae = [row["formula"] for row in _fixture() if row["table"] == table]
    usable = [f for f in dict.fromkeys(formulae) if all(loaded.has(e, prop) for e in parse_formula(f))]
    assert len(usable) >= 8, f"only {len(usable)} usable formulae for {table}/{prop}"
    return pack(usable, lambda e: loaded.value(e, prop))


# ---------------------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------------------


def test_refuses_mismatched_shapes() -> None:
    with pytest.raises(CompositionError, match="same shape"):
        statistics(np.ones((3, 2)), np.ones((3, 4)))


def test_refuses_a_single_composition_passed_flat() -> None:
    """And the message says how to fix it, because it is the obvious first mistake."""
    with pytest.raises(CompositionError, match=r"batch of one"):
        statistics(np.array([1.5, 1.0]), np.array([1.31, 1.91]))


def test_refuses_a_negative_amount() -> None:
    """CBFV accepts these; ``parse_formula`` does not, and neither does this."""
    with pytest.raises(CompositionError, match="negative element amount"):
        statistics(np.array([[1.5, -1.0]]), np.array([[1.31, 1.91]]))


def test_refuses_a_composition_with_no_elements() -> None:
    """CBFV dies here with `zero-size array to reduction operation maximum`."""
    with pytest.raises(CompositionError, match="no elements at all"):
        statistics(np.array([[1.5, 1.0], [0.0, 0.0]]), np.array([[1.31, 1.91], [1.0, 2.0]]))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_refuses_a_non_finite_value_that_is_not_padding(bad: float) -> None:
    """A hole must not become a number. It is how the published matrix got its europium row."""
    with pytest.raises(CompositionError, match="non-finite property value"):
        statistics(np.array([[1.5, 1.0]]), np.array([[1.31, bad]]))


def test_padding_may_hold_anything() -> None:
    """The corollary: a slot with zero weight is not there, so its value is never read."""
    weights = np.array([[1.5, 1.0, 0.0]])
    reference = statistics(weights[:, :2], np.array([[1.31, 1.91]]))
    for filler in (0.0, np.nan, np.inf, -1e300):
        got = statistics(weights, np.array([[1.31, 1.91, filler]]))
        for statistic in STATISTICS:
            assert got[statistic][0] == reference[statistic][0], f"{filler!r} leaked into {statistic}"


# ---------------------------------------------------------------------------------------
# The result type
# ---------------------------------------------------------------------------------------


def test_indexable_by_the_half_of_a_feature_name() -> None:
    """``f"{prefix}_{property}"`` is the feature column, so the prefix must reach the column."""
    got = statistics(np.array([[1.5, 1.0]]), np.array([[1.31, 1.91]]))
    for statistic in STATISTICS:
        assert got[statistic] is getattr(got, statistic)


def test_mode_is_refused_by_name() -> None:
    """CBFV's sixth statistic. No selected feature uses it, and the message says so."""
    got = statistics(np.array([[1.5, 1.0]]), np.array([[1.31, 1.91]]))
    with pytest.raises(KeyError, match="mode"):
        got["mode"]


def test_statistics_are_frozen() -> None:
    got = statistics(np.array([[1.5, 1.0]]), np.array([[1.31, 1.91]]))
    assert isinstance(got, Statistics)
    with pytest.raises(AttributeError):
        got.avg = np.zeros(1)  # type: ignore[misc]
