"""Card #21 — the parity gate, and the four things it has to get right.

1. **It passes over the real data**, and the numbers it reports are the numbers this card
   measured: 1,278 of 1,279 rows compared, one excluded, worst gap 2.728e-12 against a
   tolerance of 1e-9.
2. **It goes red on purpose.** `docs/QA-PROTOCOL.md` §5 will not trust a gate that has never
   failed, and a gate over a featuriser that is already correct never fails by itself. So the
   featuriser is perturbed by more than the tolerance and the result is required to name the
   column *and* the formula — the card's third done-when box, which a boolean cannot satisfy.
3. **It skips rather than passing when CBFV is absent.** CI's `suite` job installs no `parity`
   extra on purpose: CBFV carries no licence and must never become a dependency of a GPL-3.0
   deliverable. A gate that cannot be answered says so.
4. **It says what it does not establish.** Two lines of the message are required by the card —
   what was excluded from the comparison and why, and how many rows the *shipped* tables could
   not have featurised at all — because this gate reads CBFV's copy of the Oliynyk table,
   where the Gordy hole does not exist.
"""

from __future__ import annotations

import sys

import pytest
from hydms.config import Config, load
from hydms.gates import Status
from hydms.gates.ac2_featuriser_parity import GATE, TOLERANCE

pytestmark = pytest.mark.gate

#: Measured on this card over `data/raw/hydride_data.csv`, against CBFV 1.1.0.
#: 1,279 curated rows less the single europium one, which neither side can answer honestly.
CURATED_ROWS = 1279
COMPARED_ROWS = 1278
EXCLUDED = "Eu1Ni5"

#: The worst cell over all 22 columns and all 1,278 comparable rows: the residue of element
#: order (#17), three orders inside the tolerance this gate asserts. Pinned as a ceiling, not
#: as an equality — a smaller number is an improvement, a larger one is a finding.
WORST_GAP = 2.7285e-12

#: What the *shipped*, cited tables cannot featurise, and therefore what a green AC-2 does not
#: establish. #19 and #20 measured it; the gate is required to say it out loud.
SHIPPED_TABLE_REFUSALS = 266


@pytest.fixture(scope="module")
def cfg() -> Config:
    return load()


@pytest.fixture(scope="module")
def cbfv() -> None:
    pytest.importorskip(
        "CBFV.composition", reason="CBFV is only installed in the `parity` extra"
    )


@pytest.fixture(scope="module")
def passing(cbfv: None, cfg: Config):
    """One real run of the gate, shared: it featurises 1,279 rows three times over."""
    return GATE.check(cfg)


# ---------------------------------------------------------------------------------------
# The gate passes, and the run is the one this card measured
# ---------------------------------------------------------------------------------------


def test_the_featuriser_reproduces_cbfv_over_the_curated_formulae(passing) -> None:
    assert passing.status is Status.PASSED, passing.message
    assert isinstance(passing.measured, float)
    assert passing.measured <= WORST_GAP
    assert passing.threshold == TOLERANCE


def test_the_comparison_covers_every_row_but_the_one_neither_side_can_answer(passing) -> None:
    """A gate that quietly compared fewer rows would pass just as green.

    So the coverage is pinned rather than trusted: 1,278 of 1,279. The missing row is
    `Eu1Ni5`, and it is missing because CBFV drops europium from its JARVIS index and answers
    from an all-zero property vector while this layer refuses — a fabricated number and a
    refusal are not comparable.
    """
    assert f"{COMPARED_ROWS} of the {CURATED_ROWS} curated formulae" in passing.message
    assert f"Excluded and not compared: 1 of {CURATED_ROWS} rows" in passing.message
    assert EXCLUDED in passing.message
    assert "1 refused by this layer, 1 listed as skipped by CBFV" in passing.message


def test_the_result_says_what_a_green_run_does_not_establish(passing) -> None:
    """The card's fifth box. This gate reads CBFV's table, which has no Gordy hole in it."""
    assert f"could not have featurised {SHIPPED_TABLE_REFUSALS} of {CURATED_ROWS}" in (
        passing.message
    )
    assert "265 for dev_Gordy_electonegativity alone" in passing.message
    assert "A green AC-2 is not" in passing.message


def test_the_worst_cell_is_named_with_its_column_and_its_formula(passing) -> None:
    """Not only on failure. A pass that cannot say where it came closest is not evidence."""
    assert "Worst:" in passing.message
    assert "cbfv=" in passing.message and "hydms=" in passing.message


# ---------------------------------------------------------------------------------------
# The red demonstration
# ---------------------------------------------------------------------------------------


def _perturbed(offset: float):
    """A featuriser that is wrong by `offset` in one column, for one composition."""
    from hydms.descriptors import featurize as real

    def fake(formulas, temperatures, **kwargs):
        frame = real.featurize(formulas, temperatures, **kwargs)
        column = frame.columns.get_loc("range_Mulliken_EN")
        frame.iloc[0, column] = frame.iloc[0, column] + offset
        return frame

    return fake


def test_a_column_over_tolerance_is_named_with_the_worst_formula(
    cbfv: None, cfg: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The demonstration `docs/QA-PROTOCOL.md` §5 requires, and the card's third box.

    One cell of one column is moved by 1e-8. The gate must go red, name `range_Mulliken_EN`,
    name the formula that carries the offending row, and report both numbers — because a
    build that says only "parity failed" costs the next person a re-run over 1,279 rows.
    """
    monkeypatch.setattr(
        "hydms.gates.ac2_featuriser_parity.featurize", _perturbed(1e-8), raising=True
    )
    result = GATE.check(cfg)

    assert result.status is Status.FAILED
    assert "range_Mulliken_EN" in result.message
    assert "Mg1.5Ni1" in result.message, "the offending formula, not just its position"
    assert "cbfv=" in result.message and "hydms=" in result.message
    assert isinstance(result.measured, float)
    assert result.measured == pytest.approx(1e-8, rel=1e-6)


def test_a_perturbation_inside_the_tolerance_stays_green(
    cbfv: None, cfg: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half of the demonstration: the gate is a threshold, not a hair trigger."""
    monkeypatch.setattr(
        "hydms.gates.ac2_featuriser_parity.featurize", _perturbed(1e-11), raising=True
    )
    result = GATE.check(cfg)

    assert result.status is Status.PASSED
    assert isinstance(result.measured, float)
    assert result.measured < TOLERANCE


def test_a_comparison_over_nothing_is_a_failure_not_a_pass(
    cbfv: None, cfg: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A vacuous pass is the shape every hollow check regime has.

    If the exclusion ever grew to cover the whole dataset — a broken computability verdict, a
    CBFV that skips everything — this gate would compare zero rows and have nothing to report.
    It reports that as red.
    """
    monkeypatch.setattr(
        "hydms.gates.ac2_featuriser_parity._refusals",
        lambda contract, parsed, tables: dict.fromkeys(range(len(parsed))),
        raising=True,
    )
    result = GATE.check(cfg)

    assert result.status is Status.FAILED
    assert "would have passed over nothing" in result.message


# ---------------------------------------------------------------------------------------
# Without CBFV
# ---------------------------------------------------------------------------------------


def test_without_cbfv_the_gate_skips_and_names_the_extra(
    cfg: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """This is CI's path, so it is tested on every interpreter rather than only where CBFV is
    absent. A criterion that cannot be answered must not report a pass."""
    monkeypatch.setitem(sys.modules, "CBFV", None)
    monkeypatch.setitem(sys.modules, "CBFV.composition", None)
    result = GATE.check(cfg)

    assert result.status is Status.SKIPPED
    assert "parity" in result.message
    assert "run AC-2" in result.message, "the skip must say how to answer the question"


def test_the_gate_is_registered_in_the_fast_lane() -> None:
    """It needs no artifact and no retrain: 1,279 formulae, three featurisations, ~1.5 s."""
    from hydms.gates import Speed, select

    assert GATE in select(speed=Speed.FAST)
    assert GATE.card == 21
