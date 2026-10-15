"""Card #22 — the throughput benchmark, and the two ways a benchmark lies.

A benchmark is only evidence if the workload is the one the decision is about. Both of this
module's failure modes are about the workload rather than the clock:

1. **Measuring the cache.** Ten thousand repeats of four formulae answer the computability
   verdict from a memo nine thousand times out of ten, and #20's original figure did exactly
   that — it read 13x slower per *distinct* composition than the layer actually is, which is
   how a 97% hot spot stayed invisible through two cards. So distinctness is asserted here,
   not assumed.
2. **Measuring the parser and calling it the arithmetic.** They scale differently — one is per
   formula and stays in Python, the other is per batch and leaves it — so the split is part of
   the result and is checked to be a real split rather than a subtraction that could go
   negative.

The throughput floor is the card's own condition: *if throughput is under ~1k/s at batch 10k,
file a note against ticket 59 on feasibility.* It is asserted at 40x below what this machine
measures, so it is a regression detector rather than a timing test — a CI runner is allowed to
be much slower than a laptop, and a per-candidate cache miss is not.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the benchmark featurises real curated rows")

from hydms.config import load  # noqa: E402
from hydms.data.load import parse_formula  # noqa: E402
from hydms.descriptors.benchmark import (  # noqa: E402
    DEFAULT_SIZES,
    candidates,
    machine,
    main,
    measure,
    render,
)
from hydms.descriptors.contract import CONTRACT  # noqa: E402

#: The card's condition, and the only number in this file that is allowed to fail the build.
#: Measured on the development machine at ~41,000/s after the memo #22 found was added; a
#: build that drops below this has lost a cache, not a few percent.
FLOOR_PER_SECOND = 1_000
FLOOR_AT = 10_000

#: Small enough to run inside the normal suite. The batch-size *curve* is the card's
#: deliverable and lives in `docs/BENCHMARKS.md`; what is checked here is the shape of the
#: measurement, plus the floor at the size the card names.
QUICK = (1, 100)


@pytest.fixture(scope="module")
def universe() -> tuple[str, ...]:
    from hydms.descriptors.benchmark import _servable

    return _servable(CONTRACT, sorted({"La", "Ni", "Ti", "Fe", "Mg", "Al", "Zr", "Mn", "V"}))


# ---------------------------------------------------------------------------------------
# The candidates
# ---------------------------------------------------------------------------------------


def test_the_candidates_are_distinct(universe: tuple[str, ...]) -> None:
    """The whole point. A repeated formula is answered from the memo, not computed."""
    batch = candidates(2_000, universe, [2, 3, 4, 5], seed=42)
    assert len(batch) == 2_000
    assert len(set(batch)) == 2_000


def test_the_candidates_have_distinct_element_sets_too(universe: tuple[str, ...]) -> None:
    """Distinct *strings* would not be enough: the memo is keyed by the element set."""
    batch = candidates(500, universe, [3, 4, 5], seed=42)
    sets = {tuple(sorted(parse_formula(formula))) for formula in batch}
    assert len(sets) > 100, "the batch reuses one element set and would measure the memo"


def test_the_candidates_are_the_same_batch_for_the_same_seed(
    universe: tuple[str, ...],
) -> None:
    assert candidates(50, universe, [2, 3], seed=7) == candidates(
        50, universe, [2, 3], seed=7
    )
    assert candidates(50, universe, [2, 3], seed=7) != candidates(
        50, universe, [2, 3], seed=8
    )


def test_every_candidate_is_featurisable(universe: tuple[str, ...]) -> None:
    """The universe is drawn from what the contract can serve, so nothing is refused.

    If this fails the benchmark is measuring an exception path rather than featurisation.
    """
    for formula in candidates(200, universe, [2, 3, 4], seed=42):
        assert CONTRACT.computability(parse_formula(formula)).complete, formula


def test_an_arity_wider_than_the_universe_is_clamped() -> None:
    """`rng.choice(..., replace=False)` would raise rather than repeat an element."""
    batch = candidates(20, ("La", "Ni"), [2, 9], seed=42)
    assert len(batch) == 20
    assert all(len(parse_formula(formula)) <= 2 for formula in batch)


# ---------------------------------------------------------------------------------------
# The measurement
# ---------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def quick():
    return measure(QUICK, repeats=1, cfg=load())


def test_every_requested_size_is_measured_plus_the_curated_row(quick) -> None:
    assert [m.size for m in quick[: len(QUICK)]] == list(QUICK)
    assert quick[-1].label.startswith("curated ")
    assert quick[-1].size > 1_000, "the curated row is the real training-matrix workload"


def test_the_parse_half_is_reported_and_is_a_real_share(quick) -> None:
    for m in quick:
        assert m.parse_s >= 0.0
        assert m.arithmetic_s >= 0.0
        assert m.parse_s + m.arithmetic_s == pytest.approx(m.total_s, rel=1e-9)
        assert 0.0 <= m.parse_share <= 1.0


def test_throughput_and_cost_per_formula_agree(quick) -> None:
    for m in quick:
        assert m.per_second == pytest.approx(1e6 / m.us_per_formula, rel=1e-9)


def test_ten_thousand_distinct_candidates_stay_above_the_cards_floor() -> None:
    """The card's own feasibility condition, as a check rather than a printout.

    Card #22: *if throughput is under ~1k/s at batch 10k, file a note against ticket 59.*
    Ticket 59 is on the frozen board and cannot be edited while `docs/FREEZE.md` holds, so if
    this ever goes red the note belongs in `docs/BENCHMARKS.md` and the runbook instead.
    """
    measured = measure((FLOOR_AT,), repeats=1, cfg=load())[0]
    assert measured.size == FLOOR_AT
    assert measured.per_second > FLOOR_PER_SECOND, (
        f"{measured.per_second:,.0f} formulae/s at batch {FLOOR_AT:,} — below the floor "
        f"card #22 says makes NSGA-II's evaluation budget a feasibility question. The last "
        f"time this dropped it was a per-candidate cache miss, not the arithmetic."
    )


# ---------------------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------------------


def test_the_table_names_the_machine_and_every_row(quick) -> None:
    """A throughput without a machine is not a fact."""
    text = render(quick)
    assert machine() in text
    for m in quick:
        assert m.label in text
    assert "formulae/s" in text and "parse share" in text


def test_rendering_nothing_raises_rather_than_drawing_an_empty_table() -> None:
    with pytest.raises(ValueError, match="nothing was measured"):
        render([])


def test_the_cli_runs_the_sizes_it_is_given(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--sizes", "1,50", "--repeats", "1"]) == 0
    out = capsys.readouterr().out
    assert "synthetic 1 " in out and "synthetic 50 " in out


@pytest.mark.parametrize("argv", [["--sizes", "0"], ["--sizes", "x"], ["--repeats", "0"]])
def test_a_bad_invocation_is_loud(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([*argv])
    assert exc.value.code == 2


def test_the_default_sizes_are_the_cards_own() -> None:
    assert DEFAULT_SIZES == (1, 100, 10_000, 100_000)
