"""The one prediction path: what it answers, what it refuses, and what it never leaks.

Card #76's assertions, each written to measure a consequence rather than to restate a
sentence in a docstring.

**A rejected candidate has no number anywhere in its payload.** Not "the caller should not
read it" -- :class:`~hydms.delivery.contract.Refusal` has no field for it, and the test walks
the serialised dict rather than the object, because the dict is what crosses the transport in
#78 and #79.

**The point estimate is the median head.** Reporting ``lcb`` instead would understate every
answer by design, and the two are numerically close enough that only an explicit comparison
against the surrogate's own frame can tell.

**The bundle loads once.** Two calls return the identical object, and the surrogate inside it
is the one the surrogate layer memoised rather than a second unpickling of the same booster.

**The scaler is never applied.** A version is stored whose scaler raises on ``transform`` and
the same numbers are demanded from it -- the same shape as #28's own assertion, repeated here
because #76 is where a well-meaning "restore the scaling" would go.

**Every spelling of a missing value.** Card #49's QA pass found that ``str(pd.NA)`` reads as
nitrogen to ElMD; #76 was handed a box saying a null check belongs on this path. The box is
answered by measurement rather than by code -- see
``test_every_spelling_of_a_missing_value_is_refused_except_the_one_that_is_chemistry``.

Card #76.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")
pytest.importorskip(
    "ElMD",
    reason="the `novelty` extra; unlike `parity` it is installed in CI, because ElMD is on "
    "the prediction path -- see pyproject.toml",
)

import pandas as pd  # noqa: E402
from hydms import artifacts  # noqa: E402
from hydms.config import load as load_config  # noqa: E402
from hydms.delivery.contract import (  # noqa: E402
    ADMITTED,
    INDETERMINATE,
    SPACE,
    UNIT,
    ContractError,
    PredictionResult,
    Refusal,
    answer_from,
    delivery_screens,
    reason_codes,
)
from hydms.delivery.predict import (  # noqa: E402
    CANDIDATE,
    WIDTH_COLUMN,
    ArtifactBundle,
    DeliveryError,
    clear_cache,
    load_bundle,
    predict_capacity,
)
from hydms.descriptors.contract import PASSTHROUGH, FeatureContract  # noqa: E402
from hydms.descriptors.featurize import featurize  # noqa: E402
from hydms.gates._core import GateReport, GateResult  # noqa: E402
from hydms.screens.domain import OUT_OF_DOMAIN  # noqa: E402
from hydms.screens.novelty import BEYOND_KNOWN_CHEMISTRY  # noqa: E402
from hydms.screens.window import OUTSIDE_WINDOW  # noqa: E402
from hydms.surrogate.conformal import (  # noqa: E402
    CONFORMAL_PAYLOAD,
    calibration_slice,
    fit_conformal,
)
from hydms.surrogate.model import (  # noqa: E402
    MODEL_PAYLOAD,
    ModelSettings,
    column_names,
)
from hydms.surrogate.predict import LOWER_BOUND  # noqa: E402
from hydms.surrogate.predict import predict as surrogate_predict  # noqa: E402
from hydms.surrogate.scaler import SCALER_PAYLOAD, FittedScaler  # noqa: E402

TARGET = "H2_W% (max)"
TEMPERATURE = PASSTHROUGH
FORMULA = "Composition"
QUANTILES = (0.1, 0.5, 0.9)
HEADS = column_names(QUANTILES)
CHEAP = {"iterations": 80, "depth": 4, "learning_rate": 0.3}

#: Three real contract names. Two of them -- `avg_valence_d` and
#: `dev_Pauling_Electronegativity` -- are among the fourteen spans the committed
#: applicability-domain reference range-checks, which is what keeps `outside-feature-range`
#: judgeable on this fixture rather than silently absent.
FEATURES = ("avg_valence_d", "dev_Pauling_Electronegativity", TEMPERATURE)


def _alloys() -> list[str]:
    """Forty distinct AB5-family compositions, all near the corpus ElMD knows.

    The family matters: a fixture of `La1Ni40` would sit past the novelty ceiling and every
    answer would be refused as beyond known chemistry, which is a true verdict about a fake
    alloy and tells this card nothing.
    """
    out: list[str] = []
    for cobalt in (0.0, 0.5, 1.0, 1.5, 2.0):
        for cerium in (0.0, 0.1, 0.2, 0.3):
            for nickel in (4.5, 5.0):
                lanthanum = 1.0 - cerium
                terms = [f"La{lanthanum:g}"]
                if cerium:
                    terms.append(f"Ce{cerium:g}")
                terms.append(f"Ni{nickel - cobalt:g}")
                if cobalt:
                    terms.append(f"Co{cobalt:g}")
                out.append("".join(terms))
    return out


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
    """The fixture corpus, featurised for real -- the path from a formula string matters here.

    The target is deliberately small. A synthetic target in the 8-11 wt% range would put every
    candidate above the 5.19 wt% cross-family ceiling and above its own physical ceiling, so
    every answer would be a refusal and the admitted branch would never run.
    """
    rng = np.random.default_rng(7)
    alloys = _alloys()
    labels = pd.Index([f"row-{i}" for i in range(rows)])
    formulas = pd.Series([alloys[i % len(alloys)] for i in range(rows)], index=labels)
    kelvin = rng.uniform(250.0, 600.0, size=rows)
    features = featurize(formulas, kelvin, contract=FeatureContract.from_names(FEATURES))
    target = (
        0.20 * features["avg_valence_d"]
        + 0.0005 * features[TEMPERATURE]
        + rng.normal(scale=0.08, size=rows)
        + 0.45
    )
    return features.assign(**{FORMULA: formulas, TARGET: target})


def _report() -> GateReport:
    """A real `GateReport`, so this file cannot drift from the shape the harness writes."""
    return GateReport(
        results=tuple(
            GateResult.ok(name, "established") for name in ("AC-2", "AC-3", "AC-4")
        ),
        selection="--all",
        strict=False,
        started_at="2026-09-11T00:00:00+00:00",
        duration_s=0.0,
    )


class _ExplodingScaler(FittedScaler):
    """A stored scaler that refuses to be used. The whole of the "never applied" assertion."""

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        raise AssertionError(
            "the delivery path applied the persisted scaler. The model was fitted on RAW "
            "features (card #26), so scaling on the way in feeds it a matrix it never saw."
        )


@pytest.fixture(scope="module")
def fitted():
    """One fitted model and its calibration, over the fixture corpus."""
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
    return frame, model, conformal, scaler, tuple(train)


@pytest.fixture(scope="module")
def store(tmp_path_factory, fitted) -> Path:
    """Two versions of the same model: `v1` promoted, `v2` with a scaler that raises."""
    _, model, conformal, scaler, _ = fitted
    directory = tmp_path_factory.mktemp("artifacts")
    contract = FeatureContract.from_names(model.feature_names)
    exploding = _ExplodingScaler(
        **{name: getattr(scaler, name) for name in scaler.__dataclass_fields__}
    )
    for stored in (scaler, exploding):
        artifacts.save(
            {MODEL_PAYLOAD: model, CONFORMAL_PAYLOAD: conformal, SCALER_PAYLOAD: stored},
            contract=contract,
            gates=_report(),
            store=directory,
        )
    artifacts.promote("v1", store=directory)
    return directory


@pytest.fixture(autouse=True)
def _forget_between_tests():
    """Both caches, because a fixture that writes a new store must hit neither."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture()
def bundle(store: Path) -> ArtifactBundle:
    return load_bundle(store=store)


KNOWN = "La1Ni5"
WARM = 298.0

#: A composition that **featurises cleanly and is 28.75 from the nearest known alloy**, against
#: an ElMD ceiling of 11.73. Both halves are needed and neither is obvious: `Xe1Rn1` is further
#: still and never reaches a screen, because the property tables have no entry for it and
#: `featurize` raises first -- so it exercises the parse refusal, not the novelty one. Two
#: alkali metals are the honest probe: real elements, real descriptors, no hydride chemistry.
FAR = "K1Rb1"


# --------------------------------------------------------------------------------------
# What an answer carries
# --------------------------------------------------------------------------------------


def test_an_admitted_candidate_comes_back_with_all_seven(bundle: ArtifactBundle) -> None:
    answer = predict_capacity(KNOWN, WARM, bundle=bundle)

    assert isinstance(answer, PredictionResult), getattr(answer, "explanation", "")
    assert not answer.refused
    assert answer.request.formula == KNOWN
    assert answer.interval.upper >= answer.interval.lower
    assert answer.domain.admitted and answer.domain.code == ADMITTED
    assert answer.model_version == "v1"
    assert answer.unit == UNIT and answer.space == SPACE
    assert answer.novelty is not None, "the novelty screen runs on every delivery call"
    assert answer.novelty.metric == "ElMD"


def test_the_estimate_is_the_median_head_and_not_the_ranking_bound(
    bundle: ArtifactBundle, store: Path
) -> None:
    """`lcb` is deliberately conservative; reporting it would understate every answer."""
    answer = predict_capacity(KNOWN, WARM, bundle=bundle)
    assert isinstance(answer, PredictionResult)

    frame = surrogate_predict([KNOWN], WARM, store=store)
    assert answer.capacity == pytest.approx(frame[HEADS[1]].iloc[0], abs=1e-12)
    assert answer.interval.lower == pytest.approx(frame[LOWER_BOUND].iloc[0], abs=1e-12)
    assert answer.capacity != frame[LOWER_BOUND].iloc[0]


def test_the_interval_width_is_the_surrogates_own_width(
    bundle: ArtifactBundle, store: Path
) -> None:
    """Read by head name, not as `lcb + width`: that sum is the upper head only to a rounding."""
    answer = predict_capacity(KNOWN, WARM, bundle=bundle)
    assert isinstance(answer, PredictionResult)

    frame = surrogate_predict([KNOWN], WARM, store=store)
    assert answer.interval.width == pytest.approx(frame[WIDTH_COLUMN].iloc[0], abs=1e-12)


def test_ten_known_alloys_reproduce_the_surrogates_own_numbers(
    bundle: ArtifactBundle, store: Path, fitted
) -> None:
    """AC-4 at this layer: the deep module must not be a second, slightly different path."""
    frame, _, _, _, train = fitted
    rows = frame.loc[list(train)[:10]]
    expected = surrogate_predict(rows[FORMULA], rows[TEMPERATURE].to_numpy(), store=store)

    for label in rows.index:
        answer = predict_capacity(
            rows.loc[label, FORMULA], float(rows.loc[label, TEMPERATURE]), bundle=bundle
        )
        assert isinstance(answer, PredictionResult), getattr(answer, "explanation", "")
        assert answer.capacity == pytest.approx(expected.loc[label, HEADS[1]], abs=1e-12)
        assert answer.interval.lower == pytest.approx(
            expected.loc[label, LOWER_BOUND], abs=1e-12
        )


def test_an_answer_survives_the_json_round_trip_as_an_equal_object(
    bundle: ArtifactBundle,
) -> None:
    """#79 compares what the API returned against this; both sides come back through one door."""
    for formula, kelvin in ((KNOWN, WARM), (KNOWN, 1000.0), ("Xx2", WARM)):
        answer = predict_capacity(formula, kelvin, bundle=bundle)
        assert answer_from(json.loads(json.dumps(answer.to_dict()))) == answer


# --------------------------------------------------------------------------------------
# What it refuses, and that a refusal carries no number
# --------------------------------------------------------------------------------------


def _numbers_in(payload: object) -> list[float]:
    """Every float anywhere in a serialised answer, however deeply nested."""
    if isinstance(payload, bool):
        return []
    if isinstance(payload, int | float):
        return [float(payload)]
    if isinstance(payload, dict):
        return [n for value in payload.values() for n in _numbers_in(value)]
    if isinstance(payload, list):
        return [n for entry in payload for n in _numbers_in(entry)]
    return []


def test_an_unparseable_formula_is_indeterminate_and_carries_the_parse_error(
    bundle: ArtifactBundle,
) -> None:
    answer = predict_capacity("Xx2", WARM, bundle=bundle)

    assert isinstance(answer, Refusal)
    assert answer.refused
    assert answer.code == INDETERMINATE
    assert "Xx" in answer.explanation
    assert answer.model_version == "v1"


def test_a_partially_parsed_formula_is_refused_rather_than_answered_as_its_prefix(
    bundle: ArtifactBundle,
) -> None:
    """#49's defect: `LaNi5Xx2` reads to `LaNi5` in ElMD, distance zero, a typo made famous."""
    answer = predict_capacity("LaNi5Xx2", WARM, bundle=bundle)

    assert isinstance(answer, Refusal)
    assert answer.code == INDETERMINATE


def test_a_temperature_outside_the_trained_window_is_refused_with_the_range(
    bundle: ArtifactBundle,
) -> None:
    cfg = load_config()
    answer = predict_capacity(KNOWN, 1000.0, bundle=bundle)

    assert isinstance(answer, Refusal)
    assert answer.code == OUTSIDE_WINDOW
    assert f"{cfg.domain.temperature_max_k:g}" in answer.explanation
    assert [verdict.screen for verdict in answer.screens] == list(bundle.screens)


def test_a_refusal_payload_holds_no_number_at_all(bundle: ArtifactBundle) -> None:
    """Not a rule about what callers read: there is no field, and the dict is what crosses."""
    answer = predict_capacity(KNOWN, 1000.0, bundle=bundle)
    payload = answer.to_dict()

    assert payload["refused"] is True
    assert "capacity" not in payload
    assert "interval" not in payload
    # The request's own temperature is the only number a refusal may carry, because it is the
    # question rather than an answer to it.
    assert _numbers_in(payload) == [1000.0]


def test_a_candidate_rejected_by_two_screens_reports_the_first_and_explains_both(
    bundle: ArtifactBundle,
) -> None:
    """`resolve()` is called, not re-derived -- the catalogue and the API say the same thing."""
    answer = predict_capacity(FAR, 1000.0, bundle=bundle)
    assert isinstance(answer, Refusal)

    rejecting = [verdict for verdict in answer.screens if not verdict.passed]
    assert len(rejecting) >= 2, [v.code for v in answer.screens]
    assert answer.code == rejecting[0].code
    for verdict in rejecting:
        assert verdict.reason in answer.explanation


def test_the_novelty_screen_can_refuse_and_says_it_is_about_chemistry(
    bundle: ArtifactBundle,
) -> None:
    """#48 measured that the novelty ceiling is not the applicability domain; the words differ."""
    answer = predict_capacity(FAR, WARM, bundle=bundle)

    assert isinstance(answer, Refusal)
    codes = {verdict.code for verdict in answer.screens if not verdict.passed}
    assert BEYOND_KNOWN_CHEMISTRY in codes


def test_every_refusal_code_this_path_can_reach_is_declared_by_a_screen(
    bundle: ArtifactBundle,
) -> None:
    declared = set(reason_codes())
    probes = [
        ("Xx2", WARM),
        ("LaNi5Xx2", WARM),
        (KNOWN, 1000.0),
        (KNOWN, 100.0),
        (FAR, WARM),
        (FAR, 1000.0),
    ]
    reached = set()
    for formula, kelvin in probes:
        answer = predict_capacity(formula, kelvin, bundle=bundle)
        assert isinstance(answer, Refusal), f"{formula} at {kelvin} K was answered"
        reached.add(answer.code)
    assert reached <= declared
    assert OUTSIDE_WINDOW in reached and INDETERMINATE in reached


# --------------------------------------------------------------------------------------
# Every spelling of a missing value -- the box #49 left on this card
# --------------------------------------------------------------------------------------


def test_every_spelling_of_a_missing_value_is_refused_except_the_one_that_is_chemistry(
    bundle: ArtifactBundle,
) -> None:
    """The card asked for a null check here. Measured, the guards already exist -- bar one.

    Every **object** null is refused by :class:`~hydms.delivery.contract.PredictionRequest`
    before a parser sees it, and every **stringified** null is refused by the featuriser's
    grammar, which names the offending character. A null check added here would duplicate
    three existing guards.

    ``"NaN"`` is the exception and it cannot be guarded at this layer: it is sodium and
    nitrogen, it parses cleanly in *both* parsers, and refusing it would refuse real
    chemistry. That is why the obligation moves to the boundary that turns a missing value
    into text -- card #84 reads a user's CSV and chooses its own `na_values` -- rather than
    living here as a blocklist that is wrong about one real material.

    This test is the pin. If any of the three guards relaxes, a null starts being answered
    with a confident capacity, and this goes red naming which spelling got through.
    """
    for missing in (None, float("nan"), np.nan, pd.NA, pd.NaT, ""):
        with pytest.raises(ContractError):
            predict_capacity(missing, WARM, bundle=bundle)  # type: ignore[arg-type]

    for text in ("nan", "<NA>", "None", "NaT", "N/A", "null"):
        answer = predict_capacity(text, WARM, bundle=bundle)
        assert isinstance(answer, Refusal), f"{text!r} was answered with a number"
        assert answer.code == INDETERMINATE

    chemistry = predict_capacity("NaN", WARM, bundle=bundle)
    assert not isinstance(chemistry, Refusal) or chemistry.code != INDETERMINATE, (
        "'NaN' is sodium and nitrogen to both parsers. If this ever becomes an "
        "INDETERMINATE refusal, a null blocklist was added here and it is refusing a real "
        "material -- card #84 owns the boundary where a missing value becomes text."
    )


# --------------------------------------------------------------------------------------
# The bundle: loaded once, immutable, and nothing of its machinery reachable
# --------------------------------------------------------------------------------------


def test_bundle_from_assembles_the_same_bundle_without_the_version_lookup(
    store: Path,
) -> None:
    """Card #77's seam: gate HG-2 has to reach a version whose gate run it is producing.

    The same split card #33 made on ``load_surrogate``, one layer up. What it must *not* be is
    a second assembly -- the duplication AC-4 exists to catch, arriving in the checker -- so
    the two doors are compared field by field on everything a caller can see.
    """
    from hydms.delivery.predict import bundle_from
    from hydms.surrogate.predict import load_surrogate

    deployed = load_bundle(store=store)
    assembled = bundle_from(load_surrogate("v1", store=store))

    assert assembled.version == deployed.version
    assert assembled.screens == deployed.screens
    assert assembled.feature_names == deployed.feature_names
    assert assembled.confidence_level == deployed.confidence_level
    assert assembled.reference_digests == deployed.reference_digests
    assert assembled.median_head == deployed.median_head


def test_a_bundle_assembled_from_a_surrogate_is_not_put_in_the_deployments_cache(
    store: Path,
) -> None:
    """It was given no store, so it has no key it could honestly use."""
    from hydms.delivery.predict import bundle_from
    from hydms.surrogate.predict import load_surrogate

    assembled = bundle_from(load_surrogate("v1", store=store))

    assert load_bundle(store=store) is not assembled


def test_a_formula_that_is_not_a_string_names_the_type_rather_than_calling_it_empty(
    bundle: ArtifactBundle,
) -> None:
    """#76's QA finding, at the entry point a transport actually hands it to."""
    with pytest.raises(ContractError) as raised:
        predict_capacity(5, WARM, bundle=bundle)  # type: ignore[arg-type]

    assert "int" in str(raised.value)
    assert "empty" not in str(raised.value)


def test_the_bundle_is_assembled_once_and_reused(store: Path) -> None:
    first = load_bundle(store=store)
    second = load_bundle(store=store)

    assert first is second
    assert first._surrogate is second._surrogate


def test_a_bundle_built_with_its_own_screens_is_not_put_in_the_deployments_cache(
    store: Path,
) -> None:
    """A test's narrowed screen set must never answer a later caller's prediction."""
    from hydms.screens.window import temperature_window

    narrowed = load_bundle(store=store, screens=(temperature_window(),))
    assert narrowed.screens == ("temperature",)
    assert load_bundle(store=store).screens == tuple(
        screen.name for screen in delivery_screens()
    )


def test_the_bundle_is_immutable(bundle: ArtifactBundle) -> None:
    """A frozen dataclass, so "pinned to one version for its lifetime" is a type, not a habit."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.version = "v9"  # type: ignore[misc]


def test_the_bundle_reports_which_reference_each_screen_read(bundle: ArtifactBundle) -> None:
    """Provenance beside the numbers: an absent record means unknown, never 'matching'."""
    digests = bundle.reference_digests

    assert set(digests) == {"domain", "novelty"}
    assert all(len(value) == 64 for value in digests.values())
    # The temperature window judges from config, not from a committed reference, so it has no
    # digest rather than an empty one.
    assert "temperature" not in digests


def test_clearing_the_cache_clears_the_surrogate_underneath_it(store: Path) -> None:
    from hydms.surrogate.predict import _LOADED

    load_bundle(store=store)
    assert _LOADED
    clear_cache()
    assert not _LOADED


def test_nothing_of_the_machinery_is_reachable_from_a_bundle(bundle: ArtifactBundle) -> None:
    """"Hidden" is otherwise a property nobody notices losing."""
    public = {name for name in dir(bundle) if not name.startswith("_")}

    assert public == {
        "confidence_level",
        "feature_names",
        "lower_head",
        # Card #78 added it: the manifest is a *record* about the version — when it was
        # fitted, from which sha, what a gate established — and `GET /v1/model` reports it.
        # It passes the two checks below like every other member, which is the point: it
        # hands out facts and nothing that could be refitted or predicted from.
        "manifest",
        "median_head",
        "reference_digests",
        "screens",
        "upper_head",
        "version",
    }
    for name in public:
        value = getattr(bundle, name)
        assert not hasattr(value, "fit"), f"{name} hands out something refittable"
        assert not hasattr(value, "predict"), f"{name} hands out a predictor"


def test_the_stored_scaler_is_never_applied(store: Path) -> None:
    """`v2` carries a scaler that raises; it must answer with `v1`'s numbers exactly."""
    first = predict_capacity(KNOWN, WARM, version="v1", store=store)
    second = predict_capacity(KNOWN, WARM, version="v2", store=store)

    assert isinstance(first, PredictionResult) and isinstance(second, PredictionResult)
    assert second.capacity == pytest.approx(first.capacity, abs=1e-12)
    assert second.model_version == "v2"


# --------------------------------------------------------------------------------------
# What the deployment refuses to do at all
# --------------------------------------------------------------------------------------


def test_a_bundle_with_no_screens_is_refused(store: Path) -> None:
    """An answer nothing judged is the one way a bare number survives every type in #75."""
    with pytest.raises(DeliveryError, match="no screens"):
        load_bundle(store=store, screens=())


def test_an_artifact_whose_median_head_the_screens_would_not_read_is_refused(
    store: Path,
) -> None:
    """Otherwise the domain screen quietly drops the two rules that bound the number itself."""
    cfg = load_config()
    shifted = dataclasses.replace(cfg.model, quantiles=(0.2, 0.6, 0.95))
    with pytest.raises(DeliveryError, match="point estimate"):
        load_bundle(store=store, cfg=dataclasses.replace(cfg, model=shifted))


def _aimed(cfg, **overrides: object):
    """``delivery_screens(cfg)`` with the domain screen's column names moved."""
    from hydms.screens.domain import applicability_domain
    from hydms.screens.novelty import novelty_screen
    from hydms.screens.window import temperature_window

    domain = dataclasses.replace(applicability_domain(cfg), **overrides)  # type: ignore[arg-type]
    return (temperature_window(cfg), domain, novelty_screen(cfg))


def test_a_screen_aimed_at_a_width_column_this_path_does_not_write_is_refused(
    store: Path,
) -> None:
    """The third rule the domain screen can silently drop, and the only one reading the band.

    Found by #76's QA pass, and it is the same defect the median-head check was written for
    rather than a new one. ``ApplicabilityDomain`` evaluates whichever signals a frame carries,
    so a ``width`` it cannot find does not raise: ``high-uncertainty`` simply never fires and
    the screen reports ``admitted``. The check was reading *config* -- which can only ever
    describe the screens ``load_bundle`` builds itself, the one case where it is redundant --
    so an explicitly supplied screen set, which the signature exists to allow, was unchecked in
    both columns.
    """
    cfg = load_config()
    with pytest.raises(DeliveryError, match="interval width"):
        load_bundle(store=store, cfg=cfg, screens=_aimed(cfg, width="band_width"))


def test_a_screen_aimed_at_a_head_this_path_does_not_write_is_refused(store: Path) -> None:
    """The same check, reaching the screen it was handed rather than the config beside it."""
    cfg = load_config()
    with pytest.raises(DeliveryError, match="point estimate"):
        load_bundle(store=store, cfg=cfg, screens=_aimed(cfg, prediction="q0.42"))


def test_the_alloy_class_column_is_not_required_of_a_screen(store: Path) -> None:
    """The third optional input is a *stated* absence, not an oversight the check forgot.

    ``alloy_class`` is declared by the same screen and is deliberately never written by
    :func:`_candidate`, so requiring it would refuse every deployment. The distinction is
    pinned here because a reader of ``_REQUIRED_COLUMNS`` would otherwise see two of three and
    wonder about the third.
    """
    cfg = load_config()
    bundle = load_bundle(store=store, cfg=cfg, screens=_aimed(cfg, alloy_class="not-a-column"))
    assert isinstance(predict_capacity(KNOWN, WARM, bundle=bundle), PredictionResult)


def test_the_candidate_frame_carries_the_features_in_fitting_order(
    bundle: ArtifactBundle,
) -> None:
    """Column order is asserted against the contract, not assumed."""
    from hydms.delivery.contract import PredictionRequest
    from hydms.delivery.predict import _candidate

    request = PredictionRequest(formula=KNOWN, temperature_k=WARM)
    formulas = pd.Series([KNOWN], index=pd.Index([CANDIDATE]))
    features = featurize(
        formulas, pd.Series([WARM], index=pd.Index([CANDIDATE])), contract=bundle._contract
    )
    intervals = bundle._surrogate.predict(formulas, formulas.map(lambda _: WARM))
    frame = _candidate(bundle, request, features, intervals)

    assert list(frame.columns)[: len(bundle.feature_names)] == list(bundle.feature_names)
    assert frame.index.tolist() == [CANDIDATE]
    assert FORMULA in frame.columns and WIDTH_COLUMN in frame.columns


def test_the_alloy_class_is_not_supplied_so_untrusted_family_is_not_reachable_here(
    bundle: ArtifactBundle,
) -> None:
    """A novel composition has no family. Supplying an unknown one refuses it for the wrong reason.

    Stated as a test rather than as prose because ``docs/REFUSALS.md`` documents
    ``untrusted-family`` and a reader would otherwise conclude this function can produce it.
    """
    from hydms.delivery.contract import PredictionRequest
    from hydms.delivery.predict import _candidate

    request = PredictionRequest(formula=KNOWN, temperature_k=WARM)
    formulas = pd.Series([KNOWN], index=pd.Index([CANDIDATE]))
    features = featurize(
        formulas, pd.Series([WARM], index=pd.Index([CANDIDATE])), contract=bundle._contract
    )
    intervals = bundle._surrogate.predict(formulas, pd.Series([WARM], index=formulas.index))

    assert load_config().columns.alloy_class not in _candidate(
        bundle, request, features, intervals
    )


def test_out_of_domain_is_reachable_when_the_model_predicts_above_the_ceiling(
    bundle: ArtifactBundle, store: Path
) -> None:
    """The ceiling bounds the *median* head -- the number shown, not the conservative bound."""
    reference = bundle._screens[1].reference
    assert reference.cross_family_max > 0.0
    frame = surrogate_predict([KNOWN], WARM, store=store)
    assert frame[HEADS[1]].iloc[0] < reference.cross_family_max, (
        "the fixture is calibrated to sit below the cross-family ceiling; if it drifts above "
        "it, every admitted-path test in this file becomes an out-of-domain refusal"
    )
    assert OUT_OF_DOMAIN in reason_codes()
