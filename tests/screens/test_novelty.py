"""L4 -- the Element Mover's Distance novelty screen. Card #49.

``docs/QA-PROTOCOL.md`` names this layer's obligation as *every screen returns a verdict with
a reason; no silent drop*, and *boundary cases on each window, both sides*. The boundary here
is one distance, so it is admitted exactly at the ceiling and refused one step past it.

Four assertions are about the *derivation* rather than the code, and exist so the card's
decisions cannot be quietly undone:

  - the batched ``cdist`` path **is** ElMD, to 1e-12, on real corpus formulas -- the whole
    card rests on ``sum(abs(cumsum(a - b)))`` being the ``mod_petti`` metric;
  - the committed reference is what ``--emit`` measures from the curated data;
  - the ceiling is the corpus's widest *internal* gap, computed rather than typed, so new
    data moves it;
  - an unparseable formula is refused rather than measured, which is the one silent failure
    ElMD hands its caller: it returns an empty composition instead of raising.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("pandas", reason="the screen layer is pandas frames end to end")
pytest.importorskip(
    "ElMD",
    reason="the `novelty` extra; unlike `parity` it is installed in CI, because ElMD is on "
    "the prediction path -- see pyproject.toml",
)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from ElMD import ElMD  # noqa: E402
from hydms.config import load as load_config  # noqa: E402
from hydms.screens.novelty import (  # noqa: E402
    BEYOND_KNOWN_CHEMISTRY,
    DISTANCE_COLUMN,
    METRIC,
    MOD_PETTI,
    NEAREST_COLUMN,
    PETTI_SLOTS,
    REFERENCE_FILE,
    ElementMoversDistance,
    NoveltyReference,
    distances,
    emit,
    main,
    novelty_screen,
    vectors,
)
from hydms.screens.protocol import (  # noqa: E402
    ADMITTED,
    INDETERMINATE,
    Screen,
    ScreenError,
    apply_screens,
)

FORMULA = "Composition"

#: Real formulas from the corpus, spread across the alloy families, so the parity assertions
#: below are made against chemistry the project actually contains rather than toy strings.
CORPUS = [
    "LaNi5",
    "Mg2Ni",
    "TiFe",
    "Zr1Mn2",
    "Ce1Mg12",
    "Ti0.5V0.5",
    "La1Ni4.5Al0.5",
    "Ti0.45Zr0.38Ni0.17",
    "Mg0.72Li0.28",
    "Ca1Al1.8B0.2",
]


def _reference(formulas: list[str] | None = None) -> NoveltyReference:
    return NoveltyReference.measured(formulas if formulas is not None else CORPUS)


def _candidates(formulas: list[str]) -> pd.DataFrame:
    return pd.DataFrame({FORMULA: formulas})


# --------------------------------------------------------------------------------------
# The metric: the batched path is ElMD, not an approximation of it
# --------------------------------------------------------------------------------------


def test_the_batched_distance_is_elmds_own_answer() -> None:
    """The card's whole batching argument rests on this identity holding exactly."""
    matrix, unreadable = vectors(CORPUS)
    assert unreadable == []
    measured, nearest = distances(matrix, matrix[:1])

    for position, formula in enumerate(CORPUS):
        expected = ElMD(formula, metric=MOD_PETTI).elmd(ElMD(CORPUS[0], metric=MOD_PETTI))
        assert measured[position] == pytest.approx(expected, abs=1e-12)
    assert set(nearest) == {0}


def test_every_pair_agrees_with_elmd_not_just_the_nearest() -> None:
    matrix, _ = vectors(CORPUS)
    for position, formula in enumerate(CORPUS):
        measured, _ = distances(matrix[position : position + 1], matrix)
        # `distances` returns only the minimum, so compare it to ElMD's own minimum.
        expected = min(
            ElMD(formula, metric=MOD_PETTI).elmd(ElMD(other, metric=MOD_PETTI))
            for other in CORPUS
        )
        assert measured[0] == pytest.approx(expected, abs=1e-12)


def test_a_composition_is_at_zero_distance_from_itself() -> None:
    matrix, _ = vectors(["LaNi5"])
    measured, _ = distances(matrix, matrix)
    assert measured[0] == pytest.approx(0.0, abs=1e-12)


def test_chunking_does_not_change_a_distance() -> None:
    """Peak memory is bounded by the chunk; the answer may not depend on it."""
    matrix, _ = vectors(CORPUS)
    whole, whole_index = distances(matrix, matrix[:3], chunk=4096)
    for chunk in (1, 2, 3, 7):
        part, part_index = distances(matrix, matrix[:3], chunk=chunk)
        assert part == pytest.approx(whole, abs=1e-12)
        assert list(part_index) == list(whole_index)


def test_our_normalisation_is_elmds_own_ratio_vector() -> None:
    """``vectors`` sums the parsed counts itself; this pins that it is still ElMD's answer.

    The reason it sums them itself is the next test. If that ever stops being necessary, this
    assertion is what says the two paths are interchangeable.
    """
    matrix, _ = vectors(CORPUS)
    for position, formula in enumerate(CORPUS):
        np.testing.assert_allclose(
            matrix[position], ElMD(formula, metric=MOD_PETTI).ratio_vector, atol=1e-12
        )


def test_a_multi_element_formula_normalises_the_same_way_in_every_process() -> None:
    """ElMD's own ``ratio_vector`` does not, and that made ``--emit`` irreproducible.

    ``_fuse`` builds its dict from ``set(mol1) | set(mol2)``, so element insertion order
    follows the per-process randomised hashes of the symbols, and
    ``sum(composition.values())`` then varies by an ulp. Two interpreters with different hash
    seeds are the only way to see it: within one process ElMD is perfectly stable.
    """
    import os
    import subprocess
    import sys

    formula = "La0.4Ce0.2Ca0.5Ni3.55Co0.75Mn0.4Al0.3"
    script = (
        "from hydms.screens.novelty import vectors;"
        "from ElMD import ElMD;"
        f"m, _ = vectors([{formula!r}]);"
        "print(m.tobytes().hex());"
        f"print(ElMD({formula!r}).ratio_vector.tobytes().hex())"
    )
    seen = set()
    raw = set()
    for seed in ("0", "1", "12345"):
        out = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        ).stdout.splitlines()
        seen.add(out[0])
        raw.add(out[1])
    assert len(seen) == 1, f"our vector varied across hash seeds: {seen}"
    # Not asserted as a failure of ElMD -- it is a fact this module is built around, and if a
    # future ElMD fixes it this stays green while `_vector` becomes merely redundant.
    assert len(raw) >= 1


def test_the_pettifor_vector_is_the_shape_every_distance_assumes() -> None:
    matrix, _ = vectors(CORPUS)
    assert matrix.shape == (len(CORPUS), PETTI_SLOTS)
    assert matrix.sum(axis=1) == pytest.approx(np.ones(len(CORPUS)), abs=1e-9)


# --------------------------------------------------------------------------------------
# The verdict: a distance on every row, admitted or not
# --------------------------------------------------------------------------------------


def test_it_is_a_screen() -> None:
    assert isinstance(ElementMoversDistance(_reference(), column=FORMULA), Screen)


def test_a_known_alloy_is_admitted_at_zero_distance_and_names_itself() -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    table = screen.verdict(_candidates(["LaNi5"]))
    assert bool(table["passed"].iloc[0])
    assert table["code"].iloc[0] == ADMITTED
    assert table[DISTANCE_COLUMN].iloc[0] == pytest.approx(0.0, abs=1e-12)
    assert table[NEAREST_COLUMN].iloc[0] == "LaNi5"


def test_the_distance_and_the_nearest_ride_on_every_verdict_including_rejections() -> None:
    """AC-7 is a reporting obligation: a rejected candidate still carries its number."""
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    table = screen.verdict(_candidates(["LaNi5", "H2"]))
    assert list(table.columns) == ["passed", "code", "reason", DISTANCE_COLUMN, NEAREST_COLUMN]
    assert not table[DISTANCE_COLUMN].isna().any()
    assert (table[NEAREST_COLUMN].str.len() > 0).all()


def test_a_candidate_past_the_ceiling_is_refused_with_the_alloy_it_is_far_from() -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    # Pure hydrogen sits at the far end of the Pettifor scale from this reference.
    table = screen.verdict(_candidates(["H2"]))
    assert not bool(table["passed"].iloc[0])
    assert table["code"].iloc[0] == BEYOND_KNOWN_CHEMISTRY
    assert table[DISTANCE_COLUMN].iloc[0] > screen.ceiling
    assert table[NEAREST_COLUMN].iloc[0] in CORPUS
    reason = table["reason"].iloc[0]
    assert "applicability domain" in reason
    assert screen.reference.loneliest in reason


def test_the_boundary_is_closed_admitted_at_the_ceiling_refused_one_step_past() -> None:
    """The obligation ``docs/QA-PROTOCOL.md`` names for this layer, on the one bound there is."""
    reference = _reference()
    screen = ElementMoversDistance(reference, column=FORMULA)
    matrix, _ = vectors(["H2"])
    measured, _ = distances(matrix, reference.petti)
    far = float(measured[0])

    at = ElementMoversDistance(
        NoveltyReference(
            formulas=reference.formulas,
            petti=reference.petti,
            ceiling=far,
            loneliest=reference.loneliest,
            loneliest_nearest=reference.loneliest_nearest,
        ),
        column=FORMULA,
    )
    assert bool(at.verdict(_candidates(["H2"]))["passed"].iloc[0]), "the ceiling is admitted"

    just_under = ElementMoversDistance(
        NoveltyReference(
            formulas=reference.formulas,
            petti=reference.petti,
            ceiling=np.nextafter(far, 0.0),
            loneliest=reference.loneliest,
            loneliest_nearest=reference.loneliest_nearest,
        ),
        column=FORMULA,
    )
    assert not bool(just_under.verdict(_candidates(["H2"]))["passed"].iloc[0])
    assert screen.ceiling < far


# --------------------------------------------------------------------------------------
# ElMD's one silent failure
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("formula", ["", "   ", "NotAnElement", "Xx2", "???"])
def test_elmd_returns_an_empty_composition_rather_than_raising(formula: str) -> None:
    """The premise of the guard below. If this ever fails, the guard can be simplified."""
    assert ElMD(formula, metric=MOD_PETTI).ratio_vector.sum() == pytest.approx(0.0)


@pytest.mark.parametrize("formula", ["", "NotAnElement", "Xx2"])
def test_an_unreadable_formula_is_refused_rather_than_measured(formula: str) -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    table = screen.verdict(_candidates([formula]))
    assert not bool(table["passed"].iloc[0])
    assert table["code"].iloc[0] == INDETERMINATE
    assert np.isnan(table[DISTANCE_COLUMN].iloc[0]), "no number is reported for a non-composition"
    assert table[NEAREST_COLUMN].iloc[0] == ""
    assert "could not read" in table["reason"].iloc[0]


def test_one_unreadable_candidate_does_not_disturb_the_others() -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    table = screen.verdict(_candidates(["LaNi5", "Xx2", "Mg2Ni"]))
    assert list(table["code"]) == [ADMITTED, INDETERMINATE, ADMITTED]
    assert table[DISTANCE_COLUMN].iloc[0] == pytest.approx(0.0, abs=1e-12)
    assert table[DISTANCE_COLUMN].iloc[2] == pytest.approx(0.0, abs=1e-12)


def test_a_reference_cannot_be_built_from_a_formula_that_is_not_a_composition() -> None:
    with pytest.raises(ScreenError, match="could not read"):
        NoveltyReference.measured(["LaNi5", "Xx2", "Mg2Ni"])


# --------------------------------------------------------------------------------------
# The batch contract
# --------------------------------------------------------------------------------------


def test_it_obeys_the_screen_runner() -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    candidates = _candidates(["LaNi5", "H2", "Mg2Ni"])
    before = candidates.copy()
    verdicts = apply_screens(candidates, [screen])

    assert list(verdicts.table.columns) == [
        "admitted",
        "novelty.passed",
        "novelty.code",
        "novelty.reason",
        f"novelty.{DISTANCE_COLUMN}",
        f"novelty.{NEAREST_COLUMN}",
    ]
    assert list(verdicts.admitted) == [True, False, True]
    pd.testing.assert_frame_equal(candidates, before)


def test_the_evidence_columns_are_what_the_delivery_contract_needs() -> None:
    """#76 builds a ``Novelty`` from these two columns; a rename here breaks it silently."""
    from hydms.delivery.contract import Novelty

    screen = ElementMoversDistance(_reference(), column=FORMULA)
    row = screen.verdict(_candidates(["La1Ni4.5Al0.5"])).iloc[0]
    novelty = Novelty(distance=float(row[DISTANCE_COLUMN]), nearest=str(row[NEAREST_COLUMN]))
    assert novelty.metric == METRIC
    assert novelty.distance >= 0.0


def test_an_empty_batch_returns_an_empty_verdict_with_its_columns() -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    table = screen.verdict(_candidates([]))
    assert table.empty
    assert DISTANCE_COLUMN in table.columns and NEAREST_COLUMN in table.columns


def test_a_missing_formula_column_is_the_batchs_fault_not_the_candidates() -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    with pytest.raises(ScreenError, match="which the candidates do not have"):
        screen.verdict(pd.DataFrame({"something_else": ["LaNi5"]}))


def test_declared_reasons_are_the_only_codes_it_emits() -> None:
    screen = ElementMoversDistance(_reference(), column=FORMULA)
    assert ADMITTED not in screen.reasons
    verdicts = apply_screens(_candidates(["LaNi5", "H2", "Xx2"]), [screen])
    emitted = set(verdicts.table["novelty.code"]) - {ADMITTED}
    assert emitted <= set(screen.reasons)


# --------------------------------------------------------------------------------------
# The reference, and the derivation the card decided
# --------------------------------------------------------------------------------------


def test_the_ceiling_is_the_widest_internal_gap_computed_not_typed() -> None:
    reference = _reference()
    matrix, _ = vectors(list(reference.formulas))
    worst = 0.0
    for position in range(len(reference.formulas)):
        others = np.delete(matrix, position, axis=0)
        measured, _ = distances(matrix[position : position + 1], others)
        worst = max(worst, float(measured[0]))
    assert reference.ceiling == pytest.approx(worst, abs=1e-12)


def test_the_ceiling_moves_when_the_known_chemistry_does() -> None:
    """New data moves the threshold rather than silently invalidating a constant."""
    near = NoveltyReference.measured(["LaNi5", "La1Ni4.5Al0.5"])
    far = NoveltyReference.measured(["LaNi5", "La1Ni4.5Al0.5", "H2"])
    assert far.ceiling > near.ceiling


def test_the_reference_names_the_composition_that_holds_the_bound_up() -> None:
    reference = _reference()
    assert reference.loneliest in reference.formulas
    assert reference.loneliest_nearest in reference.formulas
    assert reference.loneliest != reference.loneliest_nearest


def test_a_single_composition_has_no_internal_gap_to_measure() -> None:
    with pytest.raises(ScreenError, match="no gaps"):
        NoveltyReference.measured(["LaNi5"])


def test_the_reference_round_trips_through_json_exactly() -> None:
    reference = _reference()
    rebuilt = NoveltyReference.from_json(reference.to_json())
    assert rebuilt.formulas == reference.formulas
    assert rebuilt.ceiling == pytest.approx(reference.ceiling, abs=1e-12)
    assert rebuilt.loneliest == reference.loneliest
    np.testing.assert_allclose(rebuilt.petti, reference.petti, atol=1e-12)


def test_a_reference_measured_on_another_scale_is_refused() -> None:
    payload = json.loads(_reference().to_json())
    payload["slots"] = 121
    with pytest.raises(ScreenError, match="not a distance from the other"):
        NoveltyReference.from_json(json.dumps(payload))


def test_the_packaged_reference_is_the_training_corpus_and_elmd_still_reads_it() -> None:
    """The committed vectors are stored, not re-parsed; this is the drift guard on that."""
    reference = NoveltyReference.packaged()
    assert len(reference.formulas) > 1
    rebuilt, unreadable = vectors(list(reference.formulas))
    assert unreadable == []
    np.testing.assert_allclose(rebuilt, reference.petti, atol=1e-12)


def test_the_screen_defaults_to_the_configured_formula_column() -> None:
    screen = novelty_screen()
    assert screen.column == load_config().columns.formula
    assert screen.name == "novelty"


def test_main_prints_what_the_reference_holds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    printed = capsys.readouterr().out
    assert "known composition(s)" in printed
    assert BEYOND_KNOWN_CHEMISTRY in printed
    assert "applicability domain" in printed


def test_the_committed_reference_is_what_emit_measures() -> None:
    """The shape #30 used for ``loco.md``: a published file is generated, and asserted so.

    **Not marked slow, and it was measured before being left unmarked**: it re-measures from
    the curated data in **1.19 s**. Marking it would have put the only guard on a committed
    file behind the lane CI deselects -- and this assertion has already earned its place, since
    it is what caught ElMD normalising a multi-element composition differently in two
    processes. See ``vectors``.
    """
    assert REFERENCE_FILE.read_text(encoding="utf-8") == emit().to_json()
