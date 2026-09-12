"""The HTTP boundary: what it serves, what it refuses, and what it is not allowed to know.

Card #78's assertions. Gate HG-3 (#79) is where transport parity becomes a *gate* over the
deployed version; what is here is the same claim measured against a fixture fit, plus the
things that are this card's alone -- the error envelope, the batch limit, the startup refusal,
and the rule that no route handler may reach for the model.

**Three kinds of "no" and they must never be confused.** A 200 is an answer with a number in
it. A 422 carrying ``refused`` is a *material* the screens declined, with a reason. A 422
carrying ``error`` is a *request* that was rejected before any candidate existed. A 500 is the
deployment's own fault and says nothing about any candidate. Every one of those is asserted
here from both sides -- the status and the body -- because the runbook fixes a refusal and
card #78 fixes a malformed request at the same status code, so the body is the only thing that
separates them and a test that checked the code alone would pass on either.

**The response models are the one risk this layer adds.** A declared response model that
forgets a field drops it silently on the way out, which is precisely the narrowing the
contract exists to prevent. Two tests close it: one compares a served body to
:meth:`~hydms.delivery.contract.PredictionResult.to_dict` key for key and value for value, and
one walks the models' declared fields against the contract's own, so a contract that grows a
field turns this file red rather than the field vanishing at the transport.

Card #78.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")
pytest.importorskip("fastapi", reason="the `api` extra: pip install -e '.[api]'")
pytest.importorskip("httpx", reason="the FastAPI TestClient transport; the `dev` extra")
pytest.importorskip(
    "ElMD",
    reason="the `novelty` extra; it is on the prediction path -- see pyproject.toml",
)

import pandas as pd  # noqa: E402
from fastapi.exceptions import ResponseValidationError  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from hydms import artifacts  # noqa: E402
from hydms.delivery import api as api_package  # noqa: E402
from hydms.delivery.api import (  # noqa: E402
    MAX_BATCH_ROWS,
    create_app,
    schemas,
)
from hydms.delivery.api import service as service_module  # noqa: E402
from hydms.delivery.contract import (  # noqa: E402
    SCHEMA,
    ContractError,
    PredictionResult,
    Refusal,
    answer_from,
)
from hydms.delivery.modelcard import SCHEMA as MODEL_SCHEMA  # noqa: E402
from hydms.delivery.predict import (  # noqa: E402
    ArtifactBundle,
    DeliveryError,
    clear_cache,
    load_bundle,
    predict_capacity,
)
from hydms.descriptors.contract import PASSTHROUGH, FeatureContract  # noqa: E402
from hydms.descriptors.featurize import featurize  # noqa: E402
from hydms.gates._core import GateReport, GateResult  # noqa: E402
from hydms.surrogate.conformal import (  # noqa: E402
    CONFORMAL_PAYLOAD,
    calibration_slice,
    fit_conformal,
)
from hydms.surrogate.model import MODEL_PAYLOAD, ModelSettings, column_names  # noqa: E402
from hydms.surrogate.scaler import SCALER_PAYLOAD, fit_scaler  # noqa: E402

TARGET = "H2_W% (max)"
FORMULA = "Composition"
TEMPERATURE = PASSTHROUGH
QUANTILES = (0.1, 0.5, 0.9)
HEADS = column_names(QUANTILES)
CHEAP = {"iterations": 80, "depth": 4, "learning_rate": 0.3}
FEATURES = ("avg_valence_d", "dev_Pauling_Electronegativity", TEMPERATURE)

#: A composition the fixture fit answers, and one it refuses for being a long way from any
#: alloy it knows. Both are #76's, chosen there for reasons this file inherits rather than
#: re-derives: `K1Rb1` featurises cleanly and is 28.75 from its nearest neighbour.
KNOWN = "La1Ni5"
FAR = "K1Rb1"
WARM = 298.0
#: Outside the configured temperature window, so the *screens* refuse it -- a different door
#: from a formula that will not parse, and the pair is what makes "distinguishable" testable.
HOT = 1000.0


def _alloys() -> list[str]:
    """Forty AB5-family compositions near the corpus ElMD knows. See #76's fixture."""
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


def _frame(rows: int = 400) -> pd.DataFrame:
    """The fixture corpus, featurised for real. A small target keeps answers under the ceiling."""
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


@pytest.fixture(scope="module")
def store(tmp_path_factory) -> Path:
    """One promoted, gate-recorded version -- so `load_bundle` itself is the door under test."""
    pytest.importorskip("catboost", reason="the model behind predict() is CatBoost's")
    pytest.importorskip("mapie", reason="the band is MAPIE-calibrated; `pip install -e .[uq]`")
    from hydms.surrogate.model import fit_quantile_model

    frame = _frame()
    settings = ModelSettings(
        quantiles=QUANTILES,
        early_stopping_rounds=5,
        optuna_trials=1,
        stopping_folds=5,
        seed=42,
        features=FEATURES,
        screen_labels=False,
        target=TARGET,
        temperature=TEMPERATURE,
    )
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

    directory = tmp_path_factory.mktemp("artifacts")
    artifacts.save(
        {MODEL_PAYLOAD: model, CONFORMAL_PAYLOAD: conformal, SCALER_PAYLOAD: scaler},
        contract=FeatureContract.from_names(model.feature_names),
        gates=GateReport(
            results=tuple(
                GateResult.ok(name, "established") for name in ("AC-2", "AC-3", "AC-4")
            ),
            selection="--all",
            strict=False,
            started_at="2026-09-12T00:00:00+00:00",
            duration_s=0.0,
        ),
        store=directory,
    )
    artifacts.promote("v1", store=directory)
    return directory


@pytest.fixture(autouse=True)
def _forget_between_tests():
    """The delivery cache and the surrogate's, because a module-scoped store outlives a test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture(scope="module")
def bundle(store: Path) -> ArtifactBundle:
    """The library's own view of the same deployment, for comparing the transport against."""
    return load_bundle(store=store)


@pytest.fixture()
def client(store: Path):
    """A started service over the fixture store. The `with` block is what runs the lifespan."""
    with TestClient(create_app(resolve=lambda: load_bundle(store=store))) as started:
        yield started


def _ask(client: TestClient, formula: str, kelvin: float):
    return client.post("/v1/predict", json={"formula": formula, "temperature_k": kelvin})


def _numbers_in(payload: object) -> list[float]:
    """Every number anywhere in a body, however deeply nested. Booleans are not numbers here."""
    if isinstance(payload, bool):
        return []
    if isinstance(payload, int | float):
        return [float(payload)]
    if isinstance(payload, dict):
        return [n for value in payload.values() for n in _numbers_in(value)]
    if isinstance(payload, list):
        return [n for entry in payload for n in _numbers_in(entry)]
    return []


# --------------------------------------------------------------------------------------
# POST /v1/predict -- the full result, and the same one the library gives
# --------------------------------------------------------------------------------------


def test_an_answer_comes_back_whole_and_identical_to_the_librarys(
    client: TestClient, bundle: ArtifactBundle
) -> None:
    """HG-3's claim in miniature: the transport must not be a second, slightly different path."""
    response = _ask(client, KNOWN, WARM)

    assert response.status_code == 200
    assert response.json() == predict_capacity(KNOWN, WARM, bundle=bundle).to_dict()


def test_the_served_body_rebuilds_into_an_equal_answer(
    client: TestClient, bundle: ArtifactBundle
) -> None:
    """One door back from JSON, so a client needs to know nothing about the discriminator."""
    for formula, kelvin in ((KNOWN, WARM), (KNOWN, HOT), ("Xx2", WARM), (FAR, WARM)):
        served = answer_from(_ask(client, formula, kelvin).json())
        assert served == predict_capacity(formula, kelvin, bundle=bundle)


def test_an_answer_carries_the_interval_the_domain_verdict_and_the_version(
    client: TestClient,
) -> None:
    """The three HG-2 forbids dropping, checked at the edge of the system rather than in-process."""
    payload = _ask(client, KNOWN, WARM).json()

    assert payload["refused"] is False
    assert payload["schema"] == SCHEMA
    assert payload["interval"]["upper"] >= payload["interval"]["lower"]
    assert payload["interval"]["level"] == pytest.approx(0.80)
    assert payload["domain"]["admitted"] is True and payload["domain"]["reason"]
    assert payload["novelty"]["metric"] == "ElMD"
    assert payload["model_version"] == "v1"


def test_the_interval_bounds_survive_serialisation_to_full_precision(
    client: TestClient, bundle: ArtifactBundle
) -> None:
    """A float truncated by JSON is a band quietly narrower than the one that was calibrated."""
    expected = predict_capacity(KNOWN, WARM, bundle=bundle)
    assert isinstance(expected, PredictionResult)
    interval = _ask(client, KNOWN, WARM).json()["interval"]

    assert interval["lower"] == expected.interval.lower
    assert interval["upper"] == expected.interval.upper
    assert interval["width"] == expected.interval.width


# --------------------------------------------------------------------------------------
# A refusal is not an error, and is not a low prediction
# --------------------------------------------------------------------------------------


def test_a_refused_material_is_a_422_with_a_reason_and_no_number(client: TestClient) -> None:
    response = _ask(client, KNOWN, HOT)
    payload = response.json()

    assert response.status_code == 422
    assert payload["refused"] is True
    assert payload["code"] and payload["explanation"]
    assert "capacity" not in payload and "interval" not in payload
    # The request's own temperature is the only number a refusal may carry: it is the
    # question, not an answer to it.
    assert _numbers_in(payload) == [HOT]


def test_a_low_prediction_is_an_answer_and_is_not_dressed_as_a_refusal(
    client: TestClient, bundle: ArtifactBundle
) -> None:
    """The distinction #80 must be able to explain, measured rather than asserted in prose."""
    answered = predict_capacity(KNOWN, WARM, bundle=bundle)
    assert isinstance(answered, PredictionResult)
    assert answered.capacity < 2.0, "the fixture target is small on purpose; see _frame"

    response = _ask(client, KNOWN, WARM)
    assert response.status_code == 200
    assert response.json()["refused"] is False
    assert "code" not in response.json()


def test_a_refusal_and_an_invalid_request_share_a_status_and_nothing_else(
    client: TestClient,
) -> None:
    """422 twice over; the body is the whole of the difference, so both halves are checked."""
    refusal = _ask(client, KNOWN, HOT).json()
    invalid = client.post("/v1/predict", json={"formula": "", "temperature_k": WARM}).json()

    assert "refused" in refusal and "error" not in refusal
    assert "error" in invalid and "refused" not in invalid
    # A client reaching for the contract's own reader is told which it is holding rather than
    # being handed a half-understood payload.
    assert isinstance(answer_from(refusal), Refusal)
    with pytest.raises(ContractError, match="does not say whether it was refused"):
        answer_from(invalid)


def test_every_way_a_request_can_be_malformed_arrives_in_one_envelope(
    client: TestClient,
) -> None:
    """Four different noticers -- pydantic three ways and the contract once -- one shape out."""
    bodies = [
        {"temperature_k": WARM},  # missing formula
        {"formula": 5, "temperature_k": WARM},  # a part number where a composition belongs
        {"formula": KNOWN, "temperature_k": "warm"},  # a number sent as a string
        {"formula": KNOWN, "temperature_k": WARM, "version": "v1"},  # choosing the deployment
        {"formula": "   ", "temperature_k": WARM},  # the contract's own refusal
    ]
    for body in bodies:
        response = client.post("/v1/predict", json=body)
        payload = response.json()

        assert response.status_code == 422, body
        assert payload["error"] == "invalid_request", body
        assert payload["problems"], body
        assert all(problem["message"] for problem in payload["problems"]), body
        assert "refused" not in payload, body


def test_a_temperature_that_is_not_a_number_is_refused_with_the_contracts_sentence(
    client: TestClient,
) -> None:
    """`NaN` has to be *typed*, because a conforming client cannot send it.

    ``json.dumps`` in httpx serialises with ``allow_nan=False``, so ``float('nan')`` never
    leaves a well-behaved caller -- it is not JSON. The contract's finiteness guard is
    therefore reachable only from a client that emits the non-standard literal, which is
    exactly why the guard is kept rather than replaced by a pydantic constraint: the case is
    rare, real, and would otherwise arrive as a 500 from deep inside the request type.
    """
    for literal in ("NaN", "Infinity", "-Infinity"):
        response = client.post(
            "/v1/predict",
            content=f'{{"formula": "{KNOWN}", "temperature_k": {literal}}}',
            headers={"content-type": "application/json"},
        )
        payload = response.json()

        assert response.status_code == 422, literal
        assert payload["error"] == "invalid_request", literal
        assert payload["problems"][0]["kind"] == "contract", literal
        assert "finite" in payload["problems"][0]["message"], literal


def test_an_unknown_field_is_refused_rather_than_ignored(client: TestClient) -> None:
    """#75: a caller that could choose its screens could widen its own interval until it liked it."""
    response = client.post(
        "/v1/predict",
        json={"formula": KNOWN, "temperature_k": WARM, "screens": [], "confidence_level": 0.99},
    )
    named = {tuple(problem["location"]) for problem in response.json()["problems"]}

    assert response.status_code == 422
    assert named == {("body", "screens"), ("body", "confidence_level")}


def test_a_contract_refusal_says_where_in_the_request_it_was(client: TestClient) -> None:
    """It names the place, never the field: the sentence names the field and the type does not."""
    payload = client.post("/v1/predict", json={"formula": "", "temperature_k": WARM}).json()
    problem = payload["problems"][0]

    assert problem["location"] == ["body"]
    assert problem["kind"] == "contract"
    assert "empty" in problem["message"]


# --------------------------------------------------------------------------------------
# POST /v1/predict/batch
# --------------------------------------------------------------------------------------


def test_a_batch_answers_in_order_and_a_refused_row_does_not_fail_the_request(
    client: TestClient, bundle: ArtifactBundle
) -> None:
    asked = [(KNOWN, WARM), (KNOWN, HOT), (FAR, WARM), ("Xx2", WARM), (KNOWN, WARM)]
    response = client.post(
        "/v1/predict/batch",
        json={"candidates": [{"formula": f, "temperature_k": k} for f, k in asked]},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["schema"] == SCHEMA
    assert payload["count"] == len(asked)
    assert [answer["request"]["formula"] for answer in payload["answers"]] == [
        formula for formula, _ in asked
    ]
    assert [answer["refused"] for answer in payload["answers"]] == [
        False,
        True,
        True,
        True,
        False,
    ]
    for (formula, kelvin), answer in zip(asked, payload["answers"], strict=True):
        assert answer_from(answer) == predict_capacity(formula, kelvin, bundle=bundle)


def test_one_candidate_through_the_batch_equals_the_same_candidate_alone(
    client: TestClient,
) -> None:
    """Two routes, one path: a batch of one must not be a second implementation of predict."""
    alone = _ask(client, KNOWN, WARM).json()
    batched = client.post(
        "/v1/predict/batch", json={"candidates": [{"formula": KNOWN, "temperature_k": WARM}]}
    ).json()

    assert batched["answers"] == [alone]


def test_the_batch_limit_is_enforced_on_both_sides_of_itself(store: Path) -> None:
    """A limit tested only from above is half a test; three is accepted, four is not."""
    with TestClient(
        create_app(resolve=lambda: load_bundle(store=store), max_batch_rows=3)
    ) as client:
        row = {"formula": KNOWN, "temperature_k": WARM}

        assert client.post("/v1/predict/batch", json={"candidates": [row] * 3}).status_code == 200

        response = client.post("/v1/predict/batch", json={"candidates": [row] * 4})
        payload = response.json()
        assert response.status_code == 422
        assert payload["error"] == "batch_too_large"
        assert "4" in payload["message"] and "3" in payload["message"]
        assert client.get("/v1/health").json()["max_batch_rows"] == 3


def test_a_malformed_row_rejects_the_whole_batch_before_anything_is_predicted(
    client: TestClient, monkeypatch
) -> None:
    """Thirty-nine predictions a caller will never receive is thirty-nine it should not pay for."""
    called: list[str] = []
    monkeypatch.setattr(
        service_module,
        "predict_capacity",
        lambda *args, **kwargs: called.append(args[0]),
    )
    rows = [{"formula": KNOWN, "temperature_k": WARM}] * 3 + [
        {"formula": "", "temperature_k": WARM}
    ]

    response = client.post("/v1/predict/batch", json={"candidates": rows})
    payload = response.json()

    assert response.status_code == 422
    assert payload["error"] == "invalid_request"
    assert [problem["location"] for problem in payload["problems"]] == [["candidates", 3]]
    assert called == [], "rows before the malformed one were predicted anyway"


def test_every_malformed_row_is_reported_not_just_the_first(client: TestClient) -> None:
    """A client fixing an upload wants the whole list, not one line per attempt."""
    rows = [
        f'{{"formula": "{KNOWN}", "temperature_k": {WARM}}}',
        '{"formula": " ", "temperature_k": 298.0}',
        # Typed rather than passed as a float, for the reason the finiteness test above gives.
        f'{{"formula": "{KNOWN}", "temperature_k": Infinity}}',
    ]
    payload = client.post(
        "/v1/predict/batch",
        content='{"candidates": [' + ", ".join(rows) + "]}",
        headers={"content-type": "application/json"},
    ).json()

    assert [problem["location"] for problem in payload["problems"]] == [
        ["candidates", 1],
        ["candidates", 2],
    ]


def test_an_empty_batch_is_an_empty_answer_rather_than_an_error(client: TestClient) -> None:
    """Nothing asked is nothing refused; a caller looping over an empty CSV is not a fault."""
    response = client.post("/v1/predict/batch", json={"candidates": []})

    assert response.status_code == 200
    assert response.json()["answers"] == []


# --------------------------------------------------------------------------------------
# GET /v1/health and GET /v1/model
# --------------------------------------------------------------------------------------


def test_health_reports_liveness_and_the_version_that_is_answering(
    client: TestClient, bundle: ArtifactBundle
) -> None:
    """Liveness alone passes while the service answers from a model nobody meant to deploy."""
    payload = client.get("/v1/health").json()

    assert payload == {
        "status": "ok",
        "model_version": bundle.version,
        "max_batch_rows": MAX_BATCH_ROWS,
    }


def test_the_model_card_states_the_version_the_date_and_what_was_certified(
    client: TestClient, bundle: ArtifactBundle
) -> None:
    payload = client.get("/v1/model").json()

    assert payload["schema"] == MODEL_SCHEMA
    assert payload["version"] == bundle.version
    assert payload["trained_at"], "the training date is read from the version's own manifest"
    assert payload["provenance"]["python"]
    assert payload["features"] == list(bundle.feature_names)
    assert payload["interval"] == {
        "confidence_level": bundle.confidence_level,
        "basis": "nominal",
        "unit": "wt%",
        "space": "capacity",
    }
    assert payload["metrics"]["gates"] == {"recorded": True, "unestablished": []}


def test_the_model_card_reports_which_reference_each_screen_read(client: TestClient) -> None:
    """The inherited obligation from #76: a served answer must be able to say what judged it."""
    screens = {entry["name"]: entry for entry in client.get("/v1/model").json()["screens"]}

    assert set(screens) == {"temperature", "domain", "novelty"}
    assert len(screens["domain"]["reference_sha256"]) == 64
    assert len(screens["novelty"]["reference_sha256"]) == 64
    # The window judges from configuration rather than a committed file, so it has no digest
    # rather than an empty one -- absence is a statement here.
    assert screens["temperature"]["reference_sha256"] is None
    assert screens["temperature"]["limits"]["low"] == pytest.approx(195.0)
    assert screens["temperature"]["limits"]["high"] == pytest.approx(773.0)


def test_the_model_card_reports_the_trained_ranges_and_the_per_family_transfer(
    client: TestClient,
) -> None:
    payload = client.get("/v1/model").json()
    ranges = payload["trained_ranges"]

    assert ranges["temperature"]["low"] == pytest.approx(195.0)
    assert ranges["temperature"]["units"] == "K"
    # Named and united, not the reference's own `trained_min`: a bare 0.1 in a served payload is
    # a number whose meaning has to be looked up, and this layer knows the target is a capacity.
    assert ranges["capacity"]["low"] < ranges["capacity"]["high"]
    assert ranges["capacity"]["units"] == "wt%"
    assert ranges["capacity"]["cross_family_max"] == pytest.approx(5.19)
    assert ranges["feature_span"], "the applicability screen's own spans, as a caller needs them"
    transfer = payload["metrics"]["transfer_r2"]
    assert transfer and all(isinstance(value, float) for value in transfer.values())
    # #30 measured these two below zero; the card reports them rather than hiding them.
    assert transfer["Mg"] < 0.0 and transfer["HEA"] < 0.0


def test_a_model_card_over_a_bundle_with_no_manifest_says_so_rather_than_guessing(
    bundle: ArtifactBundle,
) -> None:
    """An absent record means unknown, never 'clean'. The gate door assembles such a bundle."""
    from dataclasses import replace

    from hydms.delivery.modelcard import model_card

    stated = model_card(replace(bundle, _manifest=None))

    assert stated["trained_at"] is None
    assert stated["provenance"] is None
    assert stated["metrics"]["gates"] is None
    assert stated["version"] == bundle.version, "everything else is still knowable"


# --------------------------------------------------------------------------------------
# What the service refuses to do at all
# --------------------------------------------------------------------------------------


def test_the_service_refuses_to_start_when_no_version_is_resolvable(tmp_path: Path) -> None:
    """No silent fallback: an empty store is a server that does not come up, not one that guesses."""
    from hydms.surrogate.predict import PredictionError

    empty = tmp_path / "artifacts"
    empty.mkdir()
    app = create_app(resolve=lambda: load_bundle(store=empty))

    with pytest.raises(PredictionError, match="nothing is promoted"), TestClient(app):
        pass


def test_a_request_before_startup_finished_is_not_answered_from_a_loaded_model(
    store: Path,
) -> None:
    """The dependency reads what startup put there; it never loads one of its own."""
    app = create_app(resolve=lambda: load_bundle(store=store))

    # No `with`: the lifespan never runs, so nothing was ever resolved.
    with pytest.raises(DeliveryError, match="startup did not complete"):
        TestClient(app).get("/v1/health")


def test_the_bundle_is_resolved_once_however_many_requests_arrive(store: Path) -> None:
    """"Loads once" is the guarantee every answer's version rests on."""
    resolved: list[int] = []

    def resolve() -> ArtifactBundle:
        resolved.append(1)
        return load_bundle(store=store)

    with TestClient(create_app(resolve=resolve)) as client:
        for _ in range(3):
            _ask(client, KNOWN, WARM)
        client.get("/v1/health")
        client.get("/v1/model")

    assert resolved == [1]


def test_create_app_loads_nothing(monkeypatch) -> None:
    """`uvicorn hydms.delivery.api:app` imports this module before it can report anything."""

    def explode(*args: object, **kwargs: object) -> ArtifactBundle:
        raise AssertionError("the application resolved an artifact at construction time")

    monkeypatch.setattr(service_module, "load_bundle", explode)
    create_app()


# --------------------------------------------------------------------------------------
# No ML logic in a route handler
# --------------------------------------------------------------------------------------

#: What a transport may not reach for. The list is layers, not libraries: `hydms.delivery`
#: itself is allowed, because delegating to the deep module is the whole design.
_FORBIDDEN = (
    "hydms.surrogate",
    "hydms.descriptors",
    "hydms.screens",
    "hydms.data",
    "hydms.artifacts",
    "hydms.pipeline",
    "hydms.search",
    "numpy",
    "pandas",
    "scipy",
    "sklearn",
    "catboost",
    "mapie",
    "ElMD",
)


def _imported(path: Path) -> set[str]:
    """Every module named in an import statement anywhere in a file, function bodies included."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
    return found


def test_no_module_in_the_api_package_imports_the_machinery(repo_root: Path) -> None:
    """The rule the card states in prose, made executable.

    It measures *direct* imports, not what ends up in the process: `hydms.delivery.predict`
    pulls pandas in behind it and must, because it is the path that predicts. What this
    forbids is the transport reaching past its own layer -- the first line of a route handler
    that featurises "just this once", which is how the API and the app begin to disagree.
    """
    package = repo_root / "hydms" / "delivery" / "api"
    offences = {
        path.name: sorted(
            name
            for name in _imported(path)
            if any(name == bad or name.startswith(bad + ".") for bad in _FORBIDDEN)
        )
        for path in sorted(package.glob("*.py"))
    }

    assert {name: bad for name, bad in offences.items() if bad} == {}


def test_no_handler_reaches_into_the_bundles_machinery(repo_root: Path) -> None:
    """The hole the import test leaves open, and the likelier one.

    A handler does not need to import anything to do ML: the bundle it is handed holds the
    surrogate, the feature contract and the screens, and ``bundle._surrogate.predict(...)``
    inside a route is a second prediction path with none of the guard rails on it. Those
    members are underscored for exactly this reason, so the rule is checkable: **no route
    handler touches a private attribute of anything.** Everything a transport may report is
    public on :class:`~hydms.delivery.predict.ArtifactBundle` by design (card #76).
    """
    source = (repo_root / "hydms" / "delivery" / "api" / "service.py").read_text(
        encoding="utf-8"
    )
    handlers = {
        node.name: node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
        and node.name in {"predict", "predict_batch", "health", "model"}
    }

    assert set(handlers) == {"predict", "predict_batch", "health", "model"}
    for name, handler in handlers.items():
        private = sorted(
            {
                child.attr
                for child in ast.walk(handler)
                if isinstance(child, ast.Attribute) and child.attr.startswith("_")
            }
        )
        assert not private, f"{name} reaches past the public surface: {private}"


# --------------------------------------------------------------------------------------
# The response models, and the one risk they add
# --------------------------------------------------------------------------------------


def _fields(model: type) -> set[str]:
    """A pydantic model's field names, under the names they serialise as."""
    return {
        (info.alias or name) for name, info in model.model_fields.items()  # type: ignore[attr-defined]
    }


def test_the_declared_response_models_carry_every_key_the_contract_writes(
    bundle: ArtifactBundle,
) -> None:
    """A response model that forgets a field drops it silently; this is what makes it loud."""
    answered = predict_capacity(KNOWN, WARM, bundle=bundle).to_dict()
    refused = predict_capacity(KNOWN, HOT, bundle=bundle).to_dict()

    assert _fields(schemas.PredictionResultBody) == set(answered)
    assert _fields(schemas.RefusalBody) == set(refused)
    assert _fields(schemas.RequestBody) == set(answered["request"])
    assert _fields(schemas.IntervalBody) == set(answered["interval"])
    assert _fields(schemas.DomainVerdictBody) == set(answered["domain"])
    assert _fields(schemas.NoveltyBody) == set(answered["novelty"])
    assert _fields(schemas.ScreenVerdictBody) == set(refused["screens"][0])


def test_a_field_the_transport_does_not_declare_is_loud_rather_than_dropped(
    client: TestClient, monkeypatch
) -> None:
    """Staged red: the failure mode a response model introduces, and how it is caught."""
    from hydms.delivery.contract import PredictionResult as Result

    original = Result.to_dict

    def widened(self: Result) -> dict:
        payload = original(self)
        payload["lcb"] = 0.0  # a field a later card might add, undeclared here
        return payload

    monkeypatch.setattr(Result, "to_dict", widened)
    # Staged red, and this is the exact error it produced: `extra_forbidden` naming `lcb`.
    # The same mechanism catches the opposite defect -- a model that *forgets* a contract
    # field leaves that field unexpected in the dict -- so one guard closes both directions.
    with pytest.raises(ResponseValidationError, match="lcb"):
        _ask(client, KNOWN, WARM)


# --------------------------------------------------------------------------------------
# The published document
# --------------------------------------------------------------------------------------


def test_the_openapi_document_declares_the_four_routes_and_their_refusals(
    client: TestClient,
) -> None:
    """#79 snapshots this; here it only has to exist and name what a caller must handle."""
    document = client.get("/openapi.json").json()
    paths = document["paths"]

    assert set(paths) == {"/v1/predict", "/v1/predict/batch", "/v1/health", "/v1/model"}
    assert "422" in paths["/v1/predict"]["post"]["responses"]
    assert "422" in paths["/v1/predict/batch"]["post"]["responses"]
    assert json.dumps(document), "the document must serialise; #79 writes it to disk"


def test_the_package_exposes_one_application_for_uvicorn() -> None:
    """`uvicorn hydms.delivery.api:app` is the documented command; it must find an app."""
    from fastapi import FastAPI

    def paths(application: FastAPI) -> list[str]:
        return sorted(
            path
            for route in application.routes
            if isinstance(path := getattr(route, "path", None), str)
        )

    assert isinstance(api_package.app, FastAPI)
    assert paths(api_package.app) == paths(create_app())
