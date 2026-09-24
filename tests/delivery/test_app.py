"""The forward-prediction page: a real service, a real socket, and what the page makes of it.

Card #82. The app is an HTTP client, so these tests stand the service up on a loopback port
under uvicorn and talk to it through :class:`~hydms.delivery.client.ServiceClient` -- not
through FastAPI's ``TestClient``, which never opens a socket and so could not tell this file
that the client's handling of a real ``422`` (which :mod:`urllib` raises) is right.

What the page shows is asserted on :mod:`hydms.delivery.page`, which is Streamlit-free and runs
in the fast lane. ``app/main.py`` is held to being a thin layer over it by reading its imports:
Streamlit is in the ``app`` extra, which is not in ``Project`` or CI (the card records why), so
the script itself cannot be executed here and must not be where anything is decided.
"""

from __future__ import annotations

import ast
import json
import socket
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")
pytest.importorskip("fastapi", reason="the `api` extra: pip install -e '.[api]'")
pytest.importorskip("uvicorn", reason="the `api` extra serves the app over a real socket")
pytest.importorskip(
    "ElMD",
    reason="the `novelty` extra; it is on the prediction path -- see pyproject.toml",
)

from hydms.delivery.client import (  # noqa: E402
    InvalidRequest,
    ServiceClient,
    ServiceError,
    ServiceUnreachable,
)
from hydms.delivery.contract import (  # noqa: E402
    PredictionRequest,
    PredictionResult,
    Refusal,
)
from hydms.delivery.page import (  # noqa: E402
    ANSWERED,
    INVALID_REQUEST,
    REFUSED,
    UNREACHABLE,
    PageError,
    PageView,
    prediction_view,
    reference_from,
    unreachable_view,
)
from hydms.delivery.predict import clear_cache, load_bundle, predict_capacity  # noqa: E402
from hydms.figures import Figure  # noqa: E402

#: The same pair ``test_api.py`` uses, for the reasons it gives: the fixture fit answers the
#: first, and refuses the second as 28.75 from any alloy it knows.
KNOWN = "La1Ni5"
FAR = "K1Rb1"
WARM = 298.0
#: Outside the configured window -- the temperature screen refuses it, not the parser.
HOT = 1000.0

APP = Path(__file__).resolve().parents[2] / "app" / "main.py"


def _free_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    return sock


@pytest.fixture(scope="module")
def service(store: Path) -> Iterator[ServiceClient]:
    """The fixture deployment, served by uvicorn on a loopback port for this module."""
    import uvicorn
    from hydms.delivery.api import create_app

    clear_cache()
    app = create_app(resolve=lambda: load_bundle(store=store))
    sock = _free_socket()
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning", lifespan="on"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 60.0
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            raise RuntimeError("the fixture service did not start")
        time.sleep(0.05)
    try:
        yield ServiceClient(f"http://127.0.0.1:{port}")
    finally:
        server.should_exit = True
        thread.join(timeout=10.0)
        sock.close()
        clear_cache()


@pytest.fixture(scope="module")
def card(service: ServiceClient) -> dict:
    return service.model()


# --------------------------------------------------------------------------------------
# The client: four outcomes, never two confused
# --------------------------------------------------------------------------------------


def test_an_answer_over_the_wire_is_the_librarys_answer(service: ServiceClient, store: Path) -> None:
    """The page's number is HG-3's number: one prediction path, reached over HTTP."""
    served = service.predict(KNOWN, WARM)

    assert isinstance(served, PredictionResult)
    library = predict_capacity(KNOWN, WARM, bundle=load_bundle(store=store))
    assert served.to_dict() == library.to_dict()


@pytest.mark.parametrize(("formula", "kelvin", "code"), [(FAR, WARM, None), (KNOWN, HOT, "outside-window")])
def test_a_declined_material_comes_back_as_a_refusal_not_an_error(
    service: ServiceClient, formula: str, kelvin: float, code: str | None
) -> None:
    """urllib raises on a 422; the client must read that body as the answer it is."""
    served = service.predict(formula, kelvin)

    assert isinstance(served, Refusal)
    assert served.explanation
    if code is not None:
        assert served.code == code


def test_an_unreadable_request_is_an_invalid_request_not_a_refusal(service: ServiceClient) -> None:
    """Same status as a refusal, nothing else in common -- the page must not say "declined"."""
    served = service.predict("  ", WARM)

    assert isinstance(served, InvalidRequest)
    assert served.refused is False
    assert served.problems and all(problem.strip() for problem in served.problems)


def test_no_service_raises_unreachable_rather_than_answering() -> None:
    sock = _free_socket()
    port = sock.getsockname()[1]
    sock.close()  # bound and released: nothing is listening there now
    client = ServiceClient(f"http://127.0.0.1:{port}", timeout=5.0)

    with pytest.raises(ServiceUnreachable, match="Nothing on this page is a prediction"):
        client.predict(KNOWN, WARM)


def test_a_batch_is_chunked_and_answers_in_the_order_it_was_asked(
    service: ServiceClient,
) -> None:
    asked = [
        PredictionRequest(formula=KNOWN, temperature_k=WARM),
        PredictionRequest(formula=KNOWN, temperature_k=HOT),
        PredictionRequest(formula=FAR, temperature_k=WARM),
    ]

    answers = service.predict_many(asked, batch_rows=2)

    assert isinstance(answers, list)
    assert [answer.request for answer in answers] == asked
    assert [answer.refused for answer in answers] == [False, True, True]
    assert answers[0].to_dict() == service.predict(KNOWN, WARM).to_dict()


def test_the_batch_limit_is_read_from_the_service_when_not_given(service: ServiceClient) -> None:
    answers = service.predict_many([PredictionRequest(formula=KNOWN, temperature_k=WARM)])

    assert isinstance(answers, list) and len(answers) == 1


class _Misbehaving(BaseHTTPRequestHandler):
    """A server that answers, but not with the contract. Which way is set per test."""

    status = 500
    body = b"Internal Server Error"

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(self.status)
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (500, b"Internal Server Error"),
        (200, json.dumps({"capacity": 1.5}).encode()),
        (422, json.dumps({"refused": False, "schema": "hydms.delivery/1"}).encode()),
    ],
    ids=["a 500", "a bare number with no refused key", "a 422 that says it was not refused"],
)
def test_an_answer_outside_the_contract_is_an_error_never_an_outcome(
    status: int, body: bytes
) -> None:
    handler = type("Handler", (_Misbehaving,), {"status": status, "body": body})
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = ServiceClient(f"http://127.0.0.1:{server.server_address[1]}", timeout=5.0)
        with pytest.raises(ServiceError):
            client.predict(KNOWN, WARM)
    finally:
        server.shutdown()
        server.server_close()


def test_a_client_refuses_an_address_that_is_not_http() -> None:
    with pytest.raises(ValueError, match="not an http"):
        ServiceClient("file:///etc/passwd")


# --------------------------------------------------------------------------------------
# The page: what each outcome shows
# --------------------------------------------------------------------------------------


def test_an_answer_is_shown_inside_its_interval_with_its_version(
    service: ServiceClient, card: dict
) -> None:
    result = service.predict(KNOWN, WARM)
    assert isinstance(result, PredictionResult)

    view = prediction_view(result, card=card)

    assert view.kind == ANSWERED
    interval = result.interval
    for number in (result.capacity, interval.lower, interval.upper):
        assert f"{number:.2f}" in view.headline
    assert "nominal" in view.headline
    assert isinstance(view.figure, Figure)
    assert view.figure.name == "prediction-band"
    assert view.version == result.model_version == card["version"]


def test_an_admitted_answer_lists_every_screen_with_its_reason(
    service: ServiceClient, card: dict
) -> None:
    """ "Admitted" is a finding the reader can check, not an absence of warnings."""
    result = service.predict(KNOWN, WARM)
    view = prediction_view(result, card=card)

    assert [row.screen for row in view.verdicts] == [s["name"] for s in card["screens"]]
    assert all(row.passed and row.reason.strip() for row in view.verdicts)


def test_an_answer_states_the_material_versus_system_caveat(
    service: ServiceClient, card: dict
) -> None:
    view = prediction_view(service.predict(KNOWN, WARM), card=card)

    assert any("DOE" in sentence and "system" in sentence for sentence in view.detail)


@pytest.mark.parametrize(("formula", "kelvin"), [(FAR, WARM), (KNOWN, HOT)])
def test_a_refusal_is_shown_as_a_refusal_with_its_reason_and_no_number(
    service: ServiceClient, card: dict, formula: str, kelvin: float
) -> None:
    refusal = service.predict(formula, kelvin)
    assert isinstance(refusal, Refusal)

    view = prediction_view(refusal, card=card)

    assert view.kind == REFUSED
    assert view.figure is None
    assert "not a low capacity" in view.headline
    assert refusal.code in view.headline
    assert view.detail == (refusal.explanation,)
    assert any(not row.passed for row in view.verdicts)
    assert view.version == card["version"]


def test_a_refusal_headline_carries_no_number_but_the_temperature_asked(
    service: ServiceClient, card: dict
) -> None:
    """Strike the inputs out, then look for a number: none may be left to read as an estimate."""
    view = prediction_view(service.predict(FAR, WARM), card=card)

    remainder = view.headline.replace(FAR, "").replace(f"{WARM:g} K", "")
    assert not any(character.isdigit() for character in remainder), remainder


def test_an_invalid_request_says_nothing_was_judged(service: ServiceClient, card: dict) -> None:
    view = prediction_view(service.predict("  ", WARM), card=card)

    assert view.kind == INVALID_REQUEST
    assert view.figure is None
    assert "No material was judged" in view.headline
    assert view.detail and view.verdicts == ()


def test_an_unreachable_service_is_said_and_nothing_else_is_shown() -> None:
    view = unreachable_view(ServiceUnreachable("the prediction service at x did not answer"))

    assert view.kind == UNREACHABLE
    assert "not answering" in view.headline
    assert view.figure is None and view.verdicts == () and view.version is None


def test_a_view_cannot_carry_a_figure_unless_it_is_an_answer(
    service: ServiceClient, card: dict
) -> None:
    drawn = prediction_view(service.predict(KNOWN, WARM), card=card).figure
    assert drawn is not None

    with pytest.raises(PageError):
        PageView(kind=REFUSED, headline="declined", figure=drawn)
    with pytest.raises(PageError):
        PageView(kind=ANSWERED, headline="an answer with nothing drawn")


# --------------------------------------------------------------------------------------
# The reference the band is drawn against
# --------------------------------------------------------------------------------------


def test_the_band_is_drawn_against_the_deployments_reference(card: dict) -> None:
    reference = reference_from(card)
    capacity = card["trained_ranges"]["capacity"]

    assert (reference.trained_min, reference.trained_max) == (capacity["low"], capacity["high"])
    assert reference.rows == capacity["rows"]
    assert reference.sole_family == capacity["sole_family"]


def test_a_card_without_the_trained_range_is_refused_rather_than_defaulted(card: dict) -> None:
    """Falling back to the installed package's reference would draw against another deployment."""
    stripped = {**card, "trained_ranges": {"temperature": card["trained_ranges"]["temperature"]}}

    with pytest.raises(PageError, match="trained capacity range"):
        reference_from(stripped)


# --------------------------------------------------------------------------------------
# app/main.py stays a client
# --------------------------------------------------------------------------------------

#: Every module the script may import. Anything else -- a plotting library, the surrogate, the
#: featuriser, the in-process predictor, the service itself -- is a second prediction path or a
#: second way to draw, and is what this card exists to prevent.
ALLOWED = {
    "__future__",
    "os",
    "streamlit",
    "hydms.delivery.client",
    "hydms.delivery.page",
    "hydms.figures.render",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_the_app_imports_nothing_that_predicts_or_draws_on_its_own() -> None:
    imported = _imports(APP)

    assert imported <= ALLOWED, sorted(imported - ALLOWED)
    assert not any("matplotlib" in name for name in imported)


def test_the_app_import_check_would_catch_a_plotting_import(tmp_path: Path) -> None:
    """The check above, fed the thing it exists to catch, so a vacuous pass cannot hide."""
    rogue = tmp_path / "main.py"
    rogue.write_text(
        APP.read_text(encoding="utf-8") + "\nimport matplotlib.pyplot as plt\n"
        "from hydms.delivery.predict import predict_capacity\n",
        encoding="utf-8",
    )

    assert _imports(rogue) - ALLOWED == {"matplotlib.pyplot", "hydms.delivery.predict"}
