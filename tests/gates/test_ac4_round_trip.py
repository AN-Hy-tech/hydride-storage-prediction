"""Card #33 — the round-trip gate, and the four things it has to get right.

1. **It passes over a real artifact.** The screening path and the training path agree to
   floating tolerance on rows the model actually grew on, across as many alloy classes as the
   fit supplies.
2. **It goes red on purpose, twice, for the two failures it names.** ``docs/QA-PROTOCOL.md`` §5
   will not trust a gate that has never failed. A refit scaler and a reordered feature matrix
   both produce numbers and raise nothing, so each is injected and the gate is required to
   catch it *and* to say which of the two it was — the card's "diagnosable" box, which a
   boolean cannot satisfy.
3. **It compares like with like.** The card's hardest box: ``predict()`` returns the calibrated
   band and ``model.predict`` is raw, so a naive round trip matches on the median and fails on
   the outer heads by the transformed correction on a pipeline that is working. Asserted by
   measuring that exact wrong comparison and requiring it to be the thing the gate does *not*
   do.
4. **It reaches a version whose gates are unestablished** — the knot card #33 untied. The gate
   scores an artifact that :func:`~hydms.surrogate.predict.load_surrogate` refuses, and the
   refusal is asserted in the same file so that the escape can never quietly widen.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from hydms.artifacts import GatesIncomplete  # noqa: E402
from hydms.descriptors.contract import PASSTHROUGH  # noqa: E402
from hydms.gates import Status  # noqa: E402
from hydms.gates.ac4_known_alloy_round_trip import GATE, ROWS, TOLERANCE, _spread  # noqa: E402
from hydms.surrogate import predict as _predict  # noqa: E402,F401  (imports the submodule too)

pytestmark = pytest.mark.gate

#: ``hydms.surrogate`` re-exports a *function* called ``predict``, which shadows the submodule
#: of that name on the package object -- so ``import hydms.surrogate.predict as m`` binds the
#: function and ``m.featurize`` raises. The module itself is reached through ``sys.modules``.
#: Named once here because all three injection tests below patch its featuriser.
PREDICT = sys.modules["hydms.surrogate.predict"]


@pytest.fixture
def scored(deployed, pointed_at):
    """The gate's result over one real, cheap, ungated artifact version."""
    cfg, settings, _frame, _split, fit = deployed
    return GATE.check(pointed_at(fit, cfg, settings))


# --------------------------------------------------------------------------------------
# It passes, and says what it established
# --------------------------------------------------------------------------------------


def test_the_two_paths_agree_on_known_training_alloys(scored) -> None:
    assert scored.status is Status.PASSED, scored.message
    assert float(scored.measured) <= TOLERANCE
    assert scored.threshold == TOLERANCE


def test_it_scores_ten_rows_across_several_alloy_classes(scored) -> None:
    assert f"{ROWS} row(s) the model actually grew on" in scored.message
    # The matrix carries ten alloy classes and the round robin takes one from each before it
    # takes a second from any, so ten rows are ten classes. Asserted as a floor rather than an
    # equality: a fit that dropped a whole class would still be a legitimate artifact.
    classes = int(scored.message.split("across ")[1].split(" alloy class")[0])
    assert classes >= 5, scored.message


def test_it_names_the_version_it_scored(scored) -> None:
    assert "v1" in scored.message
    assert "nothing is promoted yet" in scored.message


# --------------------------------------------------------------------------------------
# It goes red on purpose — the two silent failures the card names
# --------------------------------------------------------------------------------------


def test_a_screening_path_that_moved_is_caught_at_all(deployed, pointed_at, monkeypatch) -> None:
    """The gate has to be able to fail. Card #21's file makes the same argument for AC-2.

    The injection is a 1 % scaling of the screening path's features — a refit scaler, wearing
    the only clothes it ever wears: it raises nothing, it returns numbers, and the numbers are
    wrong. The gate must notice, and it must report *how far* wrong rather than a boolean.
    """
    cfg, settings, _frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)

    original = PREDICT.featurize
    monkeypatch.setattr(PREDICT, "featurize", lambda *a, **k: original(*a, **k) * 1.01)
    result = GATE.check(config)

    assert result.status is Status.FAILED, result.message
    assert float(result.measured) > TOLERANCE


def test_the_failure_names_the_formula_and_both_numbers(deployed, pointed_at, monkeypatch) -> None:
    cfg, settings, frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)

    original = PREDICT.featurize
    monkeypatch.setattr(PREDICT, "featurize", lambda *a, **k: original(*a, **k) * 1.05)
    result = GATE.check(config)

    chosen = _spread(frame, fit.model.record.fitted, cfg.columns.alloy_class, ROWS)
    formulas = {str(frame.loc[label, cfg.columns.formula]) for label in chosen}
    assert any(formula in result.message for formula in formulas), result.message
    assert "screening=" in result.message and "training=" in result.message


def test_a_failure_the_contract_did_not_cause_says_so_rather_than_blaming_it(
    deployed, pointed_at, monkeypatch
) -> None:
    """The diagnostic must not name the wrong culprit.

    Here the contract is innocent: re-featurising the ten formulae reproduces the training
    matrix exactly, and the divergence was injected further down the prediction path. The
    failure has to say that the contract is not what disagrees, and leave the remaining
    possibilities open instead of asserting one of them.
    """
    cfg, settings, _frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)

    original = PREDICT.featurize
    monkeypatch.setattr(PREDICT, "featurize", lambda *a, **k: original(*a, **k) * 1.01)
    result = GATE.check(config)

    assert "the contract is not what disagrees" in result.message, result.message
    assert "column ORDER" not in result.message, result.message


# --------------------------------------------------------------------------------------
# The diagnostic itself — the card's "diagnosable" box
#
# Exercised directly rather than through an injection, because the two verdicts it has to tell
# apart are properties of two *matrices*, and building those two matrices is the whole of the
# setup. Reaching them through `predict()` would mean the test could only ever produce one of
# them.
# --------------------------------------------------------------------------------------


class _Contract:
    """Just enough of a surrogate for :func:`_features`: the fitted column names."""

    def __init__(self, names: tuple[str, ...]) -> None:
        self.feature_names = names


#: Three real contract names. Not "a", "b", "c": `_features` builds a `FeatureContract` from
#: whatever names it is given, and the contract refuses one it cannot resolve -- so invented
#: names would make the diagnostic report a resolution failure instead of the verdict under
#: test.
_NAMES = ("avg_valence_d", "dev_Pauling_Electronegativity", PASSTHROUGH)


def _stored() -> pd.DataFrame:
    return pd.DataFrame(
        dict(zip(_NAMES, ([1.0, 2.0], [3.0, 4.0], [5.0, 6.0]), strict=True)),
        index=["r0", "r1"],
    )


def _two_matrices(monkeypatch, produced: pd.DataFrame, stored: pd.DataFrame) -> str:
    """Run the diagnostic with the featuriser returning ``produced`` against ``stored``."""
    import hydms.gates.ac4_known_alloy_round_trip as module

    formulas = pd.Series(["La1Ni5", "Ti1Fe1"], index=stored.index)
    temperatures = pd.Series([298.0, 298.0], index=stored.index)
    monkeypatch.setattr(
        "hydms.descriptors.featurize.featurize", lambda *a, **k: produced
    )
    return module._features(
        _Contract(tuple(stored.columns)), stored, formulas, temperatures
    )


def test_the_diagnostic_calls_a_reordering_a_reordering(monkeypatch) -> None:
    stored = _stored()
    rolled = pd.DataFrame(
        np.roll(stored.to_numpy(), 1, axis=1), index=stored.index, columns=stored.columns
    )
    said = _two_matrices(monkeypatch, rolled, stored)
    assert "column ORDER" in said
    assert "the same set of values" in said


def test_the_diagnostic_calls_a_transform_a_different_computation(monkeypatch) -> None:
    stored = _stored()
    said = _two_matrices(monkeypatch, stored * 1.01, stored)
    assert "different values" in said
    assert "column ORDER" not in said


def test_the_diagnostic_names_the_columns_that_moved(monkeypatch) -> None:
    stored = _stored()
    moved = stored.assign(**{_NAMES[1]: stored[_NAMES[1]] + 10.0})
    said = _two_matrices(monkeypatch, moved, stored)
    assert f"{_NAMES[1]} " in said and "1 of 3 feature column(s) differ" in said


# --------------------------------------------------------------------------------------
# Comparing like with like — the card's hardest box, measured
# --------------------------------------------------------------------------------------


def test_the_raw_heads_would_have_failed_this_gate_on_a_working_pipeline(deployed) -> None:
    """The comparison the card warns against, performed once so the warning is a measurement.

    ``model.predict`` is raw. If AC-4 had scored ``predict()`` against it, the median would
    match to floating tolerance and the outer two heads would be off by the transformed
    correction — on a pipeline with nothing wrong with it. That is why the gate builds its
    reference with ``calibrated_heads``.
    """
    from hydms.surrogate.conformal import calibrated_heads
    from hydms.surrogate.model import column_names

    cfg, _settings, frame, _split, fit = deployed
    chosen = list(_spread(frame, fit.model.record.fitted, cfg.columns.alloy_class, ROWS))
    rows = frame.loc[chosen]
    heads = list(column_names(fit.model.quantiles))

    raw = fit.model.predict(rows)[heads]
    calibrated = calibrated_heads(fit.model, rows, conformal=fit.conformal)[heads]

    median = fit.conformal.median
    assert float(np.max(np.abs(raw[median] - calibrated[median]))) <= TOLERANCE
    for outer in (fit.conformal.lower, fit.conformal.upper):
        assert float(np.max(np.abs(raw[outer] - calibrated[outer]))) > TOLERANCE


# --------------------------------------------------------------------------------------
# The knot: the gate reaches a version the delivery path refuses
# --------------------------------------------------------------------------------------


def test_the_version_this_gate_scored_is_one_predict_refuses(deployed, pointed_at) -> None:
    """Card #33's decision, pinned from both sides.

    The gate passes over the version, and ``load_surrogate`` still will not touch it. If a
    later change relaxes the delivery path's gate requirement, this test goes red and says so
    — which is the whole point of writing the escape as a split rather than as a flag.
    """
    from hydms.surrogate.predict import load_surrogate

    cfg, settings, _frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)

    assert GATE.check(config).status is Status.PASSED
    with pytest.raises(GatesIncomplete):
        load_surrogate("v1", store=config.paths.artifacts)


# --------------------------------------------------------------------------------------
# No artifact is a skip, never a pass
# --------------------------------------------------------------------------------------


def test_an_empty_store_is_skipped_with_the_command_that_fixes_it(deployed, tmp_path: Path) -> None:
    cfg, *_ = deployed
    empty = replace(cfg, paths=replace(cfg.paths, artifacts=tmp_path / "nothing"))
    result = GATE.check(empty)
    assert result.status is Status.SKIPPED
    assert "hydms.surrogate.calibrate" in result.message


# --------------------------------------------------------------------------------------
# The row choice
# --------------------------------------------------------------------------------------


def test_the_rows_are_spread_over_classes_before_they_are_deepened() -> None:
    """One per class, then a second per class — never ten of the first family in the file."""
    frame = pd.DataFrame(
        {"cls": ["AB2"] * 8 + ["AB5"] * 3 + ["Mg"] * 2},
        index=[f"r{i}" for i in range(13)],
    )
    picked = _spread(frame, tuple(frame.index), "cls", 6)
    assert [frame.loc[label, "cls"] for label in picked] == [
        "AB2",
        "AB5",
        "Mg",
        "AB2",
        "AB5",
        "Mg",
    ]


def test_rows_the_model_never_grew_on_are_not_offered() -> None:
    frame = pd.DataFrame({"cls": ["AB2", "AB5"]}, index=["kept", "absent"])
    assert _spread(frame, ("kept", "not-in-the-matrix"), "cls", 5) == ("kept",)
