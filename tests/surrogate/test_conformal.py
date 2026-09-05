"""Conformal calibration: the constant, where its rows come from, and what stores it.

Three of these are the assertions card #27 names explicitly.

**Parity.** The artifact stores a float rather than a MAPIE object, so the claim that the
float *is* the calibration has to be checked against MAPIE's own output. The test builds the
reference call itself rather than reading it back out of :func:`fit_conformal` -- the same
shape as gate AC-2, which diffs the featuriser against CBFV rather than against its own
intermediate.

**The positional trap.** MAPIE's prefit list is ``[lower, upper, median]`` with the median
*last*, and nothing in the library checks that a caller agrees. It is the ``column_names``
trap reappearing at the library boundary, so it gets the same treatment: an assertion against
a fitted object, not a sentence in a docstring.

**MAPIE at predict time.** "It is a fit-time dependency" is a claim about an import graph, and
the only honest way to check it is in an interpreter that has not already imported it.

Card #27.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")

import pandas as pd  # noqa: E402
from hydms.config import ConfigError, load  # noqa: E402
from hydms.data.canonical import group_keys  # noqa: E402
from hydms.data.target import to_wt_pct  # noqa: E402
from hydms.qa.detectors import LeakDetected  # noqa: E402
from hydms.surrogate.conformal import (  # noqa: E402
    CONFORMAL_PAYLOAD,
    PARITY_TOLERANCE,
    SYMMETRIC,
    ConformalError,
    FittedConformal,
    calibrated_heads,
    calibration_groups,
    calibration_slice,
    conformal_from,
    fit_conformal,
)
from hydms.surrogate.model import (  # noqa: E402
    ModelSettings,
    quantile_metrics,
)

TARGET = "H2_W% (max)"
TEMPERATURE = "temperature(K)"
FORMULA = "Composition"
QUANTILES = (0.1, 0.5, 0.9)
CHEAP = {"iterations": 80, "depth": 4, "learning_rate": 0.3}


def _settings(**overrides: object) -> ModelSettings:
    return ModelSettings(
        **{  # type: ignore[arg-type]
            "quantiles": QUANTILES,
            "early_stopping_rounds": 5,
            "optuna_trials": 1,
            "stopping_folds": 5,
            "seed": 42,
            "features": ("avg_atomic_mass", TEMPERATURE),
            "screen_labels": False,
            "target": TARGET,
            "temperature": TEMPERATURE,
            **overrides,
        }
    )


def _frame(rows: int = 400) -> pd.DataFrame:
    """Forty distinct compositions over `rows` rows, so a grouped fifth is cuttable."""
    rng = np.random.default_rng(7)
    mass = rng.uniform(20.0, 140.0, size=rows)
    return pd.DataFrame(
        {
            FORMULA: [f"La1Ni{i % 40 + 1}" for i in range(rows)],
            TEMPERATURE: rng.uniform(250.0, 600.0, size=rows),
            "avg_atomic_mass": mass,
            TARGET: 0.02 * mass + rng.normal(scale=0.4, size=rows) + 1.5,
        },
        index=[f"row-{i}" for i in range(rows)],
    )


def _correction(value: float = 0.25, **overrides: object) -> FittedConformal:
    return FittedConformal(
        **{  # type: ignore[arg-type]
            "correction": value,
            "confidence_level": 0.8,
            "quantiles": QUANTILES,
            "lower": "q0.1",
            "upper": "q0.9",
            "median": "q0.5",
            "calibration_rows": 172,
            "fitted_on": "train",
            **overrides,
        }
    )


def _heads(rows: int = 5) -> pd.DataFrame:
    base = np.arange(rows, dtype="float64")
    return pd.DataFrame(
        {"q0.1": base - 1.0, "q0.5": base, "q0.9": base + 1.0},
        index=[f"row-{i}" for i in range(rows)],
    )


# --------------------------------------------------------------------------------------
# The band and the heads are one statement
# --------------------------------------------------------------------------------------


def test_the_shipped_band_satisfies_mapies_prefit_contract() -> None:
    """`conformal.confidence_level` and `model.quantiles` describe the same interval.

    The file shipped asserting two incompatible things -- an 80% band of heads beside a
    confidence level of 0.90 -- and nothing raised, because nothing read either key. This is
    what stops them drifting apart again.
    """
    cfg = load()
    level = cfg.conformal.confidence_level
    quantiles = cfg.model.quantiles
    assert abs(quantiles[0] - (1.0 - level) / 2.0) <= PARITY_TOLERANCE
    assert abs(quantiles[-1] - (1.0 + level) / 2.0) <= PARITY_TOLERANCE
    assert any(abs(q - 0.5) <= PARITY_TOLERANCE for q in quantiles)


def test_a_confidence_level_that_contradicts_the_heads_is_refused(tmp_path, repo_root) -> None:
    """0.90 beside [0.1, 0.5, 0.9] is the contradiction this card found and removed."""
    text = (repo_root / "hydms" / "config" / "pipeline.yaml").read_text(encoding="utf-8")
    assert "  confidence_level: 0.80" in text
    broken = tmp_path / "pipeline.yaml"
    broken.write_text(
        text.replace("  confidence_level: 0.80", "  confidence_level: 0.90"), encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="prefit CQR contract"):
        load(broken)


def test_quantiles_with_no_median_head_are_refused(tmp_path, repo_root) -> None:
    """CQR reports its interval around the median, and MAPIE takes it as the third estimator."""
    text = (repo_root / "hydms" / "config" / "pipeline.yaml").read_text(encoding="utf-8")
    broken = tmp_path / "pipeline.yaml"
    broken.write_text(
        text.replace("  quantiles: [0.1, 0.5, 0.9]", "  quantiles: [0.1, 0.4, 0.9]"),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="no median head"):
        load(broken)


# --------------------------------------------------------------------------------------
# The stored value
# --------------------------------------------------------------------------------------


def test_the_correction_widens_both_outer_heads_and_leaves_the_median() -> None:
    """CQR corrects the band, never the point. The columns come back in the same order, which
    is what lets `quantile_metrics` score raw and calibrated without new measurement code."""
    heads = _heads()
    widened = _correction(0.25).apply(heads)

    assert list(widened.columns) == list(heads.columns)
    assert widened.index.equals(heads.index)
    np.testing.assert_allclose(widened["q0.1"], heads["q0.1"] - 0.25, rtol=0, atol=1e-15)
    np.testing.assert_allclose(widened["q0.9"], heads["q0.9"] + 0.25, rtol=0, atol=1e-15)
    np.testing.assert_array_equal(widened["q0.5"], heads["q0.5"])
    # The input is not modified.
    np.testing.assert_array_equal(heads["q0.1"], np.arange(5, dtype="float64") - 1.0)


def test_a_negative_correction_narrows_the_band_rather_than_being_refused() -> None:
    """Raw heads that over-cover produce a negative constant. That is a legal calibration and
    refusing it would replace a measured result with a floor nobody fitted."""
    widened = _correction(-0.1).apply(_heads())
    assert (widened["q0.9"] - widened["q0.1"] < 2.0).all()


def test_the_correction_refuses_a_frame_that_is_not_its_heads() -> None:
    heads = _heads().rename(columns={"q0.9": "q0.95"})
    with pytest.raises(ConformalError, match="belongs to heads"):
        _correction().apply(heads)


def test_the_correction_refuses_reordered_columns() -> None:
    """Position identifies a quantile in CatBoost's output and nothing else does."""
    heads = _heads()[["q0.9", "q0.5", "q0.1"]]
    with pytest.raises(ConformalError, match="belongs to heads"):
        _correction().apply(heads)


def test_the_correction_refuses_an_array() -> None:
    with pytest.raises(ConformalError, match="not a ndarray"):
        _correction().apply(_heads().to_numpy())


def test_a_head_that_is_not_finite_is_refused_rather_than_widened() -> None:
    heads = _heads()
    heads.loc["row-2", "q0.9"] = np.nan
    with pytest.raises(ConformalError, match="not a finite number"):
        _correction().apply(heads)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"correction": float("nan")}, "not a finite number"),
        ({"correction": float("inf")}, "not a finite number"),
        ({"confidence_level": 1.5}, "not a coverage probability"),
        ({"calibration_rows": 0}, "not a conformal guarantee"),
        ({"lower": "q0.05"}, "not heads of the quantiles"),
        ({"lower": "q0.9"}, "same column"),
    ],
)
def test_a_correction_that_cannot_mean_anything_is_refused(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ConformalError, match=message):
        _correction(**overrides)


@pytest.mark.parametrize("method", ["fit", "conformalize"])
def test_a_fitted_correction_cannot_be_refitted(method: str) -> None:
    """The same structural refusal `FittedScaler` makes, for the same reason: re-estimating
    the constant from the rows being predicted gives nominal coverage by construction and no
    guarantee at all."""
    with pytest.raises(ConformalError, match="does not exist on a fitted correction"):
        getattr(_correction(), method)()


def test_describe_is_one_row_that_says_what_the_number_means() -> None:
    described = _correction().describe()
    assert len(described) == 1
    assert described.loc["conformal", "confidence_level"] == 0.8
    assert described.loc["conformal", "calibration_rows"] == 172
    assert bool(described.loc["conformal", "symmetric"]) is SYMMETRIC


# --------------------------------------------------------------------------------------
# Where the calibration rows come from
# --------------------------------------------------------------------------------------


def test_the_calibration_slice_is_grouped_and_disjoint() -> None:
    """A calibration row whose composition the trees already fitted gives a conformity score
    that is a training residual -- the constant comes out too small and the band under-covers
    exactly where it claims not to. Leak L8 at a new stage."""
    frame = _frame()
    labels = list(frame.index[:300])
    fitting, calibrating = calibration_slice(frame, labels, settings=_settings())

    assert set(fitting) | set(calibrating) == set(labels)
    assert not set(fitting) & set(calibrating)
    keys = group_keys(frame)
    assert not set(keys.loc[list(fitting)]) & set(keys.loc[list(calibrating)])
    calibration_groups(frame, fitting, calibrating)


def test_the_calibration_slice_is_about_a_fifth_at_five_folds() -> None:
    frame = _frame()
    labels = list(frame.index[:300])
    _, calibrating = calibration_slice(frame, labels, settings=_settings())
    assert 0.12 < len(calibrating) / len(labels) < 0.30


def test_a_carve_that_splits_a_composition_is_caught() -> None:
    """`grouped_folds` cannot produce this; a resumed run or a hand-built probe can."""
    frame = _frame()
    both = [label for label in frame.index if frame.loc[label, FORMULA] == "La1Ni1"]
    assert len(both) > 1
    with pytest.raises(LeakDetected, match="canonical composition"):
        calibration_groups(frame, [both[0]], [both[1]])


def test_the_calibration_slice_refuses_rows_it_was_not_given() -> None:
    from hydms.surrogate.model import ModelError

    frame = _frame()
    with pytest.raises(ModelError, match="not in the frame"):
        calibration_slice(frame, ["row-0", "nowhere"], settings=_settings())


# --------------------------------------------------------------------------------------
# The fit -- these need MAPIE and CatBoost
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def calibrated():
    """One fitted model and its calibration, reused: the fit costs about a second.

    Not marked `slow`. The parity assertion is the whole point of the card and a test the
    fast lane deselects does not make it.
    """
    pytest.importorskip("catboost", reason="the model being calibrated is CatBoost's")
    pytest.importorskip("mapie", reason="the calibration is MAPIE's; `pip install -e .[uq]`")
    from hydms.surrogate.model import fit_quantile_model

    frame = _frame()
    settings = _settings()
    train = list(frame.index[:280])
    val = list(frame.index[280:330])
    test = list(frame.index[330:])
    fitting, calibrating = calibration_slice(frame, train, settings=settings)
    model = fit_quantile_model(
        frame,
        train=fitting,
        eval_on=val,
        scored_on=test,
        where="final fit",
        params=CHEAP,
        settings=settings,
    )
    conformal = fit_conformal(frame, model, calibrate_on=calibrating)
    return frame, model, conformal, tuple(calibrating), tuple(test)


def test_the_stored_constant_reproduces_mapies_own_interval(calibrated) -> None:
    """The parity assertion, made against MAPIE directly rather than against `fit_conformal`'s
    own intermediate -- gate AC-2's pattern.

    This is what buys the right to throw MAPIE away. A wrong conformal constant is invisible:
    it under- or over-covers by a few points, which is precisely and only what AC-3 measures,
    so a check that went through the same code path would certify nothing.
    """
    from hydms.surrogate.conformal import _Head
    from mapie.regression import ConformalizedQuantileRegressor

    frame, model, conformal, calibrating, _ = calibrated
    rows = frame.loc[list(calibrating)]
    truth = np.log1p(rows[TARGET].to_numpy(dtype="float64"))

    reference = ConformalizedQuantileRegressor(
        estimator=[_Head(model, "q0.1"), _Head(model, "q0.9"), _Head(model, "q0.5")],
        confidence_level=conformal.confidence_level,
        prefit=True,
    )
    reference.conformalize(rows, truth)
    point, intervals = reference.predict_interval(rows, symmetric_correction=SYMMETRIC)

    ours = conformal.apply(model.predict_model_space(rows))
    assert np.max(np.abs(ours["q0.1"].to_numpy() - intervals[:, 0, 0])) <= PARITY_TOLERANCE
    assert np.max(np.abs(ours["q0.9"].to_numpy() - intervals[:, 1, 0])) <= PARITY_TOLERANCE
    assert np.max(np.abs(ours["q0.5"].to_numpy() - np.asarray(point))) <= PARITY_TOLERANCE


def test_mapie_reads_the_prefit_list_as_lower_upper_median(calibrated) -> None:
    """The positional trap, asserted against a fitted object.

    `_MapieQuantileRegressor` sets `single_estimator_ = estimators_[2]` and reports it as the
    point prediction. If the list were ever read as [lower, median, upper] this returns the
    *upper* head, and the whole interval would be conformalised around the wrong number.
    """
    from hydms.surrogate.conformal import _Head
    from mapie.regression import ConformalizedQuantileRegressor

    frame, model, conformal, calibrating, _ = calibrated
    rows = frame.loc[list(calibrating)]
    truth = np.log1p(rows[TARGET].to_numpy(dtype="float64"))

    reference = ConformalizedQuantileRegressor(
        estimator=[_Head(model, "q0.1"), _Head(model, "q0.9"), _Head(model, "q0.5")],
        confidence_level=conformal.confidence_level,
        prefit=True,
    )
    reference.conformalize(rows, truth)

    heads = model.predict_model_space(rows)
    point = np.asarray(reference.predict(rows), dtype="float64")
    assert np.max(np.abs(point - heads["q0.5"].to_numpy())) <= PARITY_TOLERANCE
    # And it is not either of the other two, which is what makes the check above load-bearing.
    assert np.max(np.abs(point - heads["q0.9"].to_numpy())) > PARITY_TOLERANCE


def test_a_swapped_prefit_order_is_caught_rather_than_calibrated(
    calibrated, monkeypatch
) -> None:
    """Handing MAPIE [lower, median, upper] must raise, not return a plausible interval.

    The failure this simulates is not hypothetical carelessness: it is what happens if MAPIE
    changes which position `single_estimator_` reads, under a pinned artifact, with no error.
    """
    import hydms.surrogate.conformal as module

    frame, model, _, calibrating, _ = calibrated
    original = module._Head
    reordered = {"q0.1": "q0.1", "q0.9": "q0.5", "q0.5": "q0.9"}
    monkeypatch.setattr(
        module, "_Head", lambda model_, column: original(model_, reordered[column])
    )
    with pytest.raises(ConformalError, match="prefit list"):
        fit_conformal(frame, model, calibrate_on=list(calibrating))


def test_calibration_moves_coverage_toward_nominal(calibrated) -> None:
    """The card's whole claim, measured. On the calibration rows the calibrated coverage is
    nominal *by construction* -- that is what makes this a check of the arithmetic rather than
    of generalisation, which is gate AC-3's question and reads the test split."""
    frame, model, conformal, calibrating, _ = calibrated
    rows = frame.loc[list(calibrating)]
    raw = quantile_metrics(rows[TARGET], model.predict(rows), model.quantiles)
    fixed = quantile_metrics(
        rows[TARGET], calibrated_heads(model, rows, conformal=conformal), model.quantiles
    )
    nominal = conformal.confidence_level
    assert abs(fixed["interval_coverage"] - nominal) <= abs(
        raw["interval_coverage"] - nominal
    ) + 1e-9
    assert abs(fixed["interval_coverage"] - nominal) < 0.06


def test_the_widened_band_keeps_the_spread_that_makes_cqr_worth_choosing(calibrated) -> None:
    """A constant added to both heads leaves the width *distribution* intact up to a shift --
    which is why this is CQR and not split conformal around the median, where every row would
    receive the same width and LCB ranking would collapse to mean ranking."""
    frame, model, conformal, _, test = calibrated
    rows = frame.loc[list(test)]
    raw = model.predict_model_space(rows)
    fixed = conformal.apply(raw)
    raw_width = (raw["q0.9"] - raw["q0.1"]).to_numpy()
    fixed_width = (fixed["q0.9"] - fixed["q0.1"]).to_numpy()
    np.testing.assert_allclose(fixed_width - raw_width, 2.0 * conformal.correction, atol=1e-12)
    assert float(np.std(fixed_width)) > 0.0


def test_calibrated_heads_is_expm1_of_the_widened_model_space(calibrated) -> None:
    """A monotone map on a calibrated interval preserves both its ordering and its coverage."""
    frame, model, conformal, _, test = calibrated
    rows = frame.loc[list(test)]
    direct = calibrated_heads(model, rows, conformal=conformal)
    stepwise = conformal.apply(model.predict_model_space(rows))
    for name in direct.columns:
        np.testing.assert_allclose(direct[name], to_wt_pct(stepwise[name]), rtol=0, atol=1e-12)


@pytest.mark.parametrize("role", ["fitted", "eval_on", "scored_on"])
def test_a_calibration_row_the_fit_already_saw_is_refused(calibrated, role: str) -> None:
    """Read off the fit's own record, not assumed from a split name. The early-stopping rows
    are a *cut* made per fit, so the only place that says which rows they were is the record."""
    frame, model, _, _, _ = calibrated
    seen = list(getattr(model.record, role))[:20]
    with pytest.raises(ConformalError, match="not a residual"):
        fit_conformal(frame, model, calibrate_on=seen)


def test_a_model_whose_heads_are_not_the_configured_band_is_refused(calibrated) -> None:
    """MAPIE does not check the prefit contract, so a mismatch calibrates the wrong band
    silently and only AC-3 would ever notice."""
    from dataclasses import replace

    frame, model, _, calibrating, _ = calibrated
    cfg = replace(load(), conformal=replace(load().conformal, confidence_level=0.9))
    with pytest.raises(ConformalError, match="prefit CQR contract"):
        fit_conformal(frame, model, calibrate_on=list(calibrating), config=cfg)


# --------------------------------------------------------------------------------------
# What is stored, and what is not
# --------------------------------------------------------------------------------------


def test_applying_a_stored_correction_does_not_import_mapie() -> None:
    """"MAPIE is a fit-time dependency" is a claim about an import graph, and the only honest
    way to check it is in an interpreter that has not already imported it.

    It matters beyond tidiness: a stored artifact holding a MAPIE object would need MAPIE at
    predict time and could change what a saved `v1` does under a MAPIE upgrade, which is
    exactly the failure AC-1 exists to detect.
    """
    script = textwrap.dedent(
        """
        import sys
        import pandas as pd
        from hydms.surrogate.conformal import FittedConformal

        correction = FittedConformal(
            correction=0.031, confidence_level=0.8, quantiles=(0.1, 0.5, 0.9),
            lower="q0.1", upper="q0.9", median="q0.5",
            calibration_rows=172, fitted_on="train",
        )
        heads = pd.DataFrame({"q0.1": [1.0], "q0.5": [2.0], "q0.9": [3.0]})
        widened = correction.apply(heads)
        assert abs(float(widened["q0.9"].iloc[0]) - 3.031) < 1e-12
        assert "mapie" not in sys.modules, sorted(n for n in sys.modules if "mapie" in n)
        print("clean")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout


def test_a_pickled_calibrator_in_the_payload_is_refused() -> None:
    """A version written against an earlier design holds a MAPIE object. Reading it back as a
    calibration would need MAPIE installed and would make the saved version's behaviour a
    function of MAPIE's version."""

    class _Bundle(dict):
        version = "v1"

        def get(self, name, default=None):
            return dict.get(self, name, default)

    with pytest.raises(ConformalError, match="not a FittedConformal"):
        conformal_from(_Bundle({CONFORMAL_PAYLOAD: object()}))


def test_a_correction_and_a_model_from_different_runs_are_refused() -> None:
    class _Model:
        quantiles = (0.05, 0.5, 0.95)

    class _Bundle(dict):
        version = "v1"

        def get(self, name, default=None):
            return dict.get(self, name, default)

    bundle = _Bundle({CONFORMAL_PAYLOAD: _correction(), "model": _Model()})
    with pytest.raises(ConformalError, match="different runs"):
        conformal_from(bundle)


def test_a_bundle_with_no_model_still_yields_its_correction() -> None:
    """`conformal_from` is also how a person inspects a hand-built bundle; "this object has no
    model" is not a finding about the correction."""

    class _Bundle(dict):
        version = "v1"

        def get(self, name, default=None):
            return dict.get(self, name, default)

    stored = _correction()
    assert conformal_from(_Bundle({CONFORMAL_PAYLOAD: stored})) is stored
