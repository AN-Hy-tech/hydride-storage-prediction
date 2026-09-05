"""The surrogate's public interface: what comes back, what stays hidden, what it refuses.

Four of these are the assertions card #28 names, and each is written to measure a consequence
rather than to restate a sentence in a docstring.

**The scaler is never applied.** The card's box says the persisted scaler must not be applied
on the way in -- CatBoost splits on thresholds, ``FittedScaler`` is affine, and card #26
therefore fits on raw features. A comment saying so is worth nothing, so a version is stored
whose scaler *raises* on ``transform`` and the same numbers are demanded from it.

**MAPIE is not on the prediction path.** Card #27 stores a float rather than a calibrator, and
a ``predict()`` that reached the library would undo that. It is a claim about an import graph,
so it is checked in an interpreter that has not already imported it -- the same shape as
``test_applying_a_stored_correction_does_not_import_mapie``.

**Nothing is clipped.** A negative lower bound is the signal cards #48 and #77 act on, so it
has to survive this layer intact.

**Callers never see the machinery.** Checked by walking the public attribute surface, because
"hidden" is otherwise a property nobody notices losing.

Card #28.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")

import pandas as pd  # noqa: E402
from hydms import artifacts  # noqa: E402
from hydms.artifacts import GatesIncomplete  # noqa: E402
from hydms.descriptors.contract import PASSTHROUGH, FeatureContract  # noqa: E402
from hydms.descriptors.featurize import FeaturisationError, featurize  # noqa: E402
from hydms.gates._core import GateReport, GateResult  # noqa: E402
from hydms.surrogate.conformal import (  # noqa: E402
    CONFORMAL_PAYLOAD,
    FittedConformal,
    calibrated_heads,
    calibration_slice,
    fit_conformal,
)
from hydms.surrogate.model import (  # noqa: E402
    MODEL_PAYLOAD,
    ModelError,
    ModelSettings,
    column_names,
    model_from,
    quantile_metrics,
)
from hydms.surrogate.predict import (  # noqa: E402
    INTERVAL_WIDTH,
    LOWER_BOUND,
    PredictionError,
    Surrogate,
    _with_bound_and_width,
    clear_cache,
    load_surrogate,
    predict,
)
from hydms.surrogate.scaler import SCALER_PAYLOAD, FittedScaler  # noqa: E402

TARGET = "H2_W% (max)"
TEMPERATURE = PASSTHROUGH
FORMULA = "Composition"
QUANTILES = (0.1, 0.5, 0.9)
HEADS = column_names(QUANTILES)
CHEAP = {"iterations": 80, "depth": 4, "learning_rate": 0.3}

#: Three real contract names, not the fourteen of `SELECTED`. The card is about the interface,
#: and every extra descriptor is parse-and-arithmetic per row in a fixture that fits a model.
FEATURES = ("avg_valence_d", "dev_Pauling_Electronegativity", TEMPERATURE)


# --------------------------------------------------------------------------------------
# Fixtures: one fitted, calibrated, promoted artifact version
# --------------------------------------------------------------------------------------


def _settings(**overrides: object) -> ModelSettings:
    return ModelSettings(
        **{  # type: ignore[arg-type]
            "quantiles": QUANTILES,
            "early_stopping_rounds": 5,
            "optuna_trials": 1,
            "stopping_folds": 5,
            "seed": 42,
            "features": FEATURES,
            "screen_labels": False,
            "target": TARGET,
            "temperature": TEMPERATURE,
            **overrides,
        }
    )


def _frame(rows: int = 400) -> pd.DataFrame:
    """Forty distinct La-Ni compositions over `rows` rows, featurised for real.

    Featurised rather than faked, because the point of this file is the path from a formula
    string to an interval: a frame of hand-written numbers would test the second half only.
    """
    rng = np.random.default_rng(7)
    labels = pd.Index([f"row-{i}" for i in range(rows)])
    formulas = pd.Series([f"La1Ni{i % 40 + 1}" for i in range(rows)], index=labels)
    kelvin = rng.uniform(250.0, 600.0, size=rows)
    features = featurize(formulas, kelvin, contract=FeatureContract.from_names(FEATURES))
    target = (
        1.2 * features["avg_valence_d"]
        + 0.004 * features[TEMPERATURE]
        + rng.normal(scale=0.3, size=rows)
        + 1.5
    )
    return features.assign(**{FORMULA: formulas, TARGET: target})


def report(*pairs: tuple[str, str]) -> GateReport:
    """A real `GateReport`, so this file cannot drift from the shape the harness writes."""
    builders = {
        "PASSED": lambda name: GateResult.ok(name, "established"),
        "SKIPPED": lambda name: GateResult.skip(name, "not implemented"),
    }
    return GateReport(
        results=tuple(builders[status](name) for name, status in pairs),
        selection="--all",
        strict=False,
        started_at="2026-09-05T00:00:00+00:00",
        duration_s=0.0,
    )


GREEN = (("AC-2", "PASSED"), ("AC-3", "PASSED"), ("AC-4", "PASSED"))


class _ExplodingScaler(FittedScaler):
    """A stored scaler that refuses to be used. The whole of the "never applied" assertion."""

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        raise AssertionError(
            "predict() applied the persisted scaler. The model was fitted on RAW features "
            "(card #26), so scaling on the way in feeds it a matrix it never saw."
        )


@pytest.fixture(scope="module")
def fitted():
    """One fitted model, its calibration and a scaler over the same columns.

    Module-scoped: the CatBoost fit costs about a second and every test here wants the same
    artifact. Not marked `slow` -- a test the fast lane deselects does not guard AC-4's
    interface.
    """
    pytest.importorskip("catboost", reason="the model behind predict() is CatBoost's")
    pytest.importorskip("mapie", reason="the band is MAPIE-calibrated; `pip install -e .[uq]`")
    from hydms.surrogate.model import fit_quantile_model
    from hydms.surrogate.scaler import fit_scaler

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

    split = pd.Series("train", index=frame.index)
    split.loc[val] = "val"
    split.loc[test] = "test"
    scaler = fit_scaler(frame.loc[:, list(FEATURES)], split)
    return frame, model, conformal, scaler, tuple(test)


@pytest.fixture(scope="module")
def store(tmp_path_factory, fitted) -> Path:
    """An artifact directory holding two promoted-quality versions of the same model.

    ``v1`` carries an ordinary scaler and is the promoted one. ``v2`` carries
    :class:`_ExplodingScaler` and exists for one test: predicting from it must produce v1's
    numbers exactly, which is only possible if nothing touched the scaler.
    """
    _, model, conformal, scaler, _ = fitted
    directory = tmp_path_factory.mktemp("artifacts")
    contract = FeatureContract.from_names(model.feature_names)
    for stored in (scaler, _ExplodingScaler(**{f: getattr(scaler, f) for f in scaler.__dataclass_fields__})):
        artifacts.save(
            {MODEL_PAYLOAD: model, CONFORMAL_PAYLOAD: conformal, SCALER_PAYLOAD: stored},
            contract=contract,
            gates=report(*GREEN),
            store=directory,
        )
    artifacts.promote("v1", store=directory)
    return directory


@pytest.fixture(autouse=True)
def _forget_between_tests():
    """The loader caches by (store, version); a fixture that writes a new store must not hit it."""
    clear_cache()
    yield
    clear_cache()


CANDIDATES = ["La1Ni5", "Ti1Fe1", "Mg2Ni1"]


# --------------------------------------------------------------------------------------
# What comes back
# --------------------------------------------------------------------------------------


def test_predict_returns_the_heads_then_the_bound_then_the_width(store: Path) -> None:
    frame = predict(CANDIDATES, 298.0, store=store)

    assert list(frame.columns) == [*HEADS, LOWER_BOUND, INTERVAL_WIDTH]
    assert len(frame) == len(CANDIDATES)
    assert all(dtype == np.dtype("float64") for dtype in frame.dtypes)
    assert np.isfinite(frame.to_numpy()).all()


def test_the_heads_are_not_renamed_or_reordered_on_the_way_out(store: Path, fitted) -> None:
    """`quantile_metrics` must score this frame with no new measurement code (card #29).

    That is the whole reason the heads keep `column_names`' spelling rather than the card's
    `p10/p50/p90`: the metric function reads the head columns by that name and by their order.
    """
    frame, _, _, _, test = fitted
    rows = frame.loc[list(test)[:40]]
    predicted = predict(rows[FORMULA], rows[TEMPERATURE].to_numpy(), store=store)

    metrics = quantile_metrics(rows[TARGET], predicted.loc[:, list(HEADS)], QUANTILES)
    assert "interval_coverage" in metrics
    assert 0.0 <= metrics["interval_coverage"] <= 1.0


def test_a_series_of_formulas_keeps_its_own_index(store: Path) -> None:
    formulas = pd.Series(CANDIDATES, index=["a", "b", "c"])
    assert list(predict(formulas, 298.0, store=store).index) == ["a", "b", "c"]


def test_the_bound_is_the_calibrated_lower_head_and_not_the_raw_one(store: Path, fitted) -> None:
    """`lcb` is the ranking key, and the point of it is that the RAW P10 does not mean 10%.

    So it is checked against `calibrated_heads` -- the widened band -- and asserted to differ
    from the model's own uncalibrated lower head by the transformed correction.
    """
    _, model, conformal, _, _ = fitted
    features = featurize(CANDIDATES, 298.0, contract=FeatureContract.from_names(FEATURES))

    frame = predict(CANDIDATES, 298.0, store=store)
    widened = calibrated_heads(model, features, conformal=conformal)
    raw = model.predict(features)

    assert np.allclose(frame[LOWER_BOUND], widened[conformal.lower], rtol=0, atol=1e-12)
    assert (frame[LOWER_BOUND] < raw[conformal.lower]).all()


def test_the_width_is_the_calibrated_span_and_varies_row_to_row(store: Path) -> None:
    """The correction is one constant in model space; the width in weight percent is not.

    `expm1` is convex, so the same widening is a wider band at a high prediction than at a low
    one -- which is why a width column says something the stored number cannot.
    """
    frame = predict(CANDIDATES, [250.0, 400.0, 600.0], store=store)

    assert np.allclose(
        frame[INTERVAL_WIDTH], frame[HEADS[-1]] - frame[HEADS[0]], rtol=0, atol=1e-12
    )
    assert (frame[INTERVAL_WIDTH] > 0.0).all()
    assert frame[INTERVAL_WIDTH].nunique() == len(frame)


def test_an_empty_batch_is_an_empty_frame_with_the_right_columns(store: Path) -> None:
    """Card #84 screens a CSV and may keep nothing; that must not reach the booster."""
    frame = predict([], 298.0, store=store)

    assert list(frame.columns) == [*HEADS, LOWER_BOUND, INTERVAL_WIDTH]
    assert len(frame) == 0
    assert all(dtype == np.dtype("float64") for dtype in frame.dtypes)


def test_nothing_is_clipped_when_the_calibrated_band_reaches_below_zero() -> None:
    """A negative lower bound is the signal cards #48 and #77 act on.

    Asserted on the assembly step directly: a real fit on real capacities does not produce one
    on demand, and suppressing it is a one-character change that no fitted-model test would
    catch.
    """
    correction = FittedConformal(
        correction=0.031,
        confidence_level=0.8,
        quantiles=QUANTILES,
        lower=HEADS[0],
        upper=HEADS[-1],
        median=HEADS[1],
        calibration_rows=172,
        fitted_on="train",
    )
    heads = pd.DataFrame(
        {HEADS[0]: [-0.4, 0.2], HEADS[1]: [0.3, 1.0], HEADS[2]: [1.1, 1.9]}
    )

    frame = _with_bound_and_width(heads, correction)
    assert frame[LOWER_BOUND].iloc[0] == pytest.approx(-0.4)
    assert frame[INTERVAL_WIDTH].iloc[0] == pytest.approx(1.5)


def test_the_bound_is_read_by_name_rather_than_by_position() -> None:
    """`conformal.lower` names the head the constant widened downward. Picking column 0 would
    be the positional assumption `column_names` exists to remove."""
    correction = FittedConformal(
        correction=0.1,
        confidence_level=0.8,
        quantiles=QUANTILES,
        lower=HEADS[2],  # deliberately not column 0
        upper=HEADS[0],
        median=HEADS[1],
        calibration_rows=10,
        fitted_on="train",
    )
    heads = pd.DataFrame({HEADS[0]: [3.0], HEADS[1]: [2.0], HEADS[2]: [1.0]})

    frame = _with_bound_and_width(heads, correction)
    assert frame[LOWER_BOUND].iloc[0] == pytest.approx(1.0)
    assert frame[INTERVAL_WIDTH].iloc[0] == pytest.approx(2.0)


# --------------------------------------------------------------------------------------
# What stays hidden
# --------------------------------------------------------------------------------------


def test_the_stored_scaler_is_never_applied(store: Path) -> None:
    """`v2` holds a scaler that raises on `transform`, and must answer exactly as `v1` does.

    The card's own box is wrong about where the scaler is applied and right about persisting
    it: the model consumes raw features (card #26), and the applicability domain (#48) is what
    the stored scaler is for.
    """
    # Armed first. A trap that quietly failed to survive joblib would make the assertion
    # below pass for the wrong reason, which is the one way this test could be worthless.
    stored = artifacts.load("v2", store=store)[SCALER_PAYLOAD]
    assert isinstance(stored, _ExplodingScaler)
    with pytest.raises(AssertionError, match="applied the persisted scaler"):
        stored.transform(pd.DataFrame({name: [0.0] for name in FEATURES}))

    promoted = predict(CANDIDATES, 298.0, store=store)
    exploding = predict(CANDIDATES, 298.0, version="v2", store=store)

    pd.testing.assert_frame_equal(promoted, exploding)


def test_callers_never_see_the_model_the_scaler_or_the_calibrator(store: Path) -> None:
    """The information-hiding check card #28 sets: swapping the regressor changes nothing
    outside this layer, which is only true while nothing outside it holds one."""
    surrogate = load_surrogate(store=store)

    public = {name: getattr(surrogate, name) for name in dir(surrogate) if not name.startswith("_")}
    leaked = {
        name: type(value).__name__
        for name, value in public.items()
        if type(value).__name__ in {"QuantileModel", "FittedScaler", "FittedConformal", "CatBoostRegressor"}
    }
    assert not leaked, leaked
    assert "booster" not in public


def test_what_a_caller_may_know_is_facts_rather_than_objects(store: Path, fitted) -> None:
    _, model, conformal, _, _ = fitted
    surrogate = load_surrogate(store=store)

    assert surrogate.version == "v1"
    assert surrogate.quantiles == tuple(model.quantiles)
    assert surrogate.feature_names == tuple(model.feature_names)
    assert surrogate.confidence_level == conformal.confidence_level
    assert surrogate.columns == (*HEADS, LOWER_BOUND, INTERVAL_WIDTH)


def test_describe_is_one_row_naming_the_version_that_answered(store: Path) -> None:
    described = load_surrogate(store=store).describe()

    assert len(described) == 1
    assert described["version"].iloc[0] == "v1"
    assert described["confidence_level"].iloc[0] == pytest.approx(0.8)


def test_predicting_does_not_import_mapie(store: Path) -> None:
    """"MAPIE is a fit-time dependency" is a claim about an import graph, and the only honest
    way to check it is in an interpreter that has not already imported it.

    Card #27 stores a float rather than a calibrator precisely so this holds; a `predict()`
    that reached the library would make a saved version's behaviour a function of MAPIE's
    version, which is the failure AC-1 exists to detect.
    """
    script = textwrap.dedent(
        f"""
        import sys
        from hydms.surrogate.predict import predict

        frame = predict(["La1Ni5", "Ti1Fe1"], 298.0, store=r{str(store)!r})
        assert len(frame) == 2, frame
        assert "lcb" in frame.columns, list(frame.columns)
        assert "mapie" not in sys.modules, sorted(n for n in sys.modules if "mapie" in n)
        print("clean")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout


# --------------------------------------------------------------------------------------
# What it refuses
# --------------------------------------------------------------------------------------


def test_an_unpromoted_store_refuses_rather_than_guessing(tmp_path: Path) -> None:
    with pytest.raises(PredictionError, match="nothing is promoted"):
        predict(CANDIDATES, 298.0, store=tmp_path / "empty")


def test_a_version_whose_gates_are_not_established_cannot_predict(
    tmp_path: Path, fitted
) -> None:
    """The gate check is never relaxed here. `artifacts.load` takes a `require_gates=False`
    for the card that has just written a version; this path does not forward it, so a SKIPPED
    criterion -- a gate nobody ran -- stops a prediction rather than annotating it."""
    _, model, conformal, scaler, _ = fitted
    directory = tmp_path / "artifacts"
    artifacts.save(
        {MODEL_PAYLOAD: model, CONFORMAL_PAYLOAD: conformal, SCALER_PAYLOAD: scaler},
        contract=FeatureContract.from_names(model.feature_names),
        gates=report(("AC-2", "PASSED"), ("AC-3", "SKIPPED")),
        store=directory,
    )

    with pytest.raises(GatesIncomplete, match="AC-3 SKIPPED"):
        predict(CANDIDATES, 298.0, version="v1", store=directory)


def test_a_model_fitted_outside_its_own_contract_is_refused(tmp_path: Path, fitted) -> None:
    """A model and a manifest from two different runs. The featuriser is driven by the fitted
    names, so a name the contract does not declare is a column nothing can build."""
    _, model, conformal, _, _ = fitted
    directory = tmp_path / "artifacts"
    artifacts.save(
        {MODEL_PAYLOAD: model, CONFORMAL_PAYLOAD: conformal},
        contract=FeatureContract.from_names(("avg_is_alkaline", TEMPERATURE)),
        gates=report(*GREEN),
        store=directory,
    )

    with pytest.raises(PredictionError, match="different runs"):
        load_surrogate("v1", store=directory)


def test_a_formula_the_contract_cannot_serve_names_the_row_rather_than_dropping_it(
    store: Path,
) -> None:
    with pytest.raises(FeaturisationError) as raised:
        predict(["La1Ni5", "Xx2"], 298.0, store=store)
    assert "Xx2" in str(raised.value)


def test_a_bare_string_is_refused_rather_than_iterated(store: Path) -> None:
    with pytest.raises(FeaturisationError):
        predict("La1Ni5", 298.0, store=store)  # type: ignore[arg-type]


def test_a_bare_booster_in_the_model_payload_is_refused(fitted) -> None:
    """A `CatBoostRegressor` unpickles happily and has its own `predict`, which returns an
    unnamed array -- the positional trap, one layer down."""
    _, model, _, _, _ = fitted

    class _Bundle(dict):
        version = "v1"

        def get(self, name, default=None):
            return dict.get(self, name, default)

    with pytest.raises(ModelError, match="not a QuantileModel"):
        model_from(_Bundle({MODEL_PAYLOAD: model.booster}))


def test_a_model_that_records_no_fitted_columns_is_refused(fitted) -> None:
    import dataclasses

    _, model, _, _, _ = fitted

    class _Bundle(dict):
        version = "v1"

        def get(self, name, default=None):
            return dict.get(self, name, default)

    empty = dataclasses.replace(model, feature_names=())
    with pytest.raises(ModelError, match="no fitted columns"):
        model_from(_Bundle({MODEL_PAYLOAD: empty}))


# --------------------------------------------------------------------------------------
# The pin, and the cache behind it
# --------------------------------------------------------------------------------------


def test_a_version_is_loaded_once_and_held(store: Path) -> None:
    """An artifact version is written once and never edited, so caching by version cannot go
    stale; unpickling a booster per candidate batch would make the app unusable."""
    assert load_surrogate(store=store) is load_surrogate(store=store)


def test_clearing_the_cache_reloads(store: Path) -> None:
    first = load_surrogate(store=store)
    clear_cache()
    assert load_surrogate(store=store) is not first


def test_the_promotion_pointer_is_re_read_rather_than_cached(store: Path, tmp_path: Path) -> None:
    """Rollback is a one-line write (card #7). It must take effect on the next prediction, not
    on the next process."""
    import shutil

    directory = tmp_path / "rollback"
    shutil.copytree(store, directory)

    assert load_surrogate(store=directory).version == "v1"
    artifacts.promote("v2", store=directory)
    assert load_surrogate(store=directory).version == "v2"


def test_the_surrogate_is_immutable(store: Path) -> None:
    surrogate = load_surrogate(store=store)
    with pytest.raises(Exception):  # noqa: B017 -- FrozenInstanceError is a dataclasses detail
        surrogate.version = "v9"  # type: ignore[misc]
    assert isinstance(surrogate, Surrogate)
