"""``app/main.py`` executed: Streamlit's own test harness, driving the real script over a real socket.

Card #82's last box is "tick when the script has run". ``test_app.py`` proves everything the page
*decides*; this file proves the Streamlit layer on top of it runs -- every widget the script
creates, every call it makes, every branch it takes -- without a browser, through
:class:`streamlit.testing.v1.AppTest`.

**It skips wherever Streamlit is absent, and that is a stated gap rather than a guarantee.** The
`app` extra is not installed in CI (`.github/workflows/ci.yml`), so this file runs where the
maintainer has installed the pin in ``docs/ENVIRONMENT.md`` and nowhere else. What it guards is
the script's glue; every promise the page makes is already checked in the fast lane by
``test_app.py``, which is why the gap is tolerable and not why it is absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
pytest.importorskip("fastapi", reason="the `api` extra: pip install -e '.[api]'")
pytest.importorskip("ElMD", reason="the `novelty` extra; it is on the prediction path")
pytest.importorskip(
    "streamlit",
    reason="the `app` extra, pinned in docs/ENVIRONMENT.md; CI does not install it",
)

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[2] / "app" / "main.py"


@pytest.fixture()
def page(service, monkeypatch: pytest.MonkeyPatch):
    """A fresh run of the script against the fixture service."""
    monkeypatch.setenv("HYDMS_API_URL", service.base_url)

    def start() -> AppTest:
        app = AppTest.from_file(str(APP), default_timeout=120)
        app.run()
        assert not app.exception, [error.value for error in app.exception]
        return app

    return start


def _ask(app: AppTest, formula: str, kelvin: float, *, sweep: bool = False) -> AppTest:
    app.text_input[0].set_value(formula)
    app.number_input[0].set_value(kelvin)
    if sweep:
        app.checkbox[0].check()
    app.button[0].click()
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    return app


def test_the_script_loads_against_a_running_service(page) -> None:
    app = page()

    assert app.title[0].value == "Hydrogen storage capacity"
    assert "trained on" in app.number_input[0].label


def test_an_answer_shows_its_band_its_verdicts_its_neighbours_and_its_sweep(page) -> None:
    app = _ask(page(), "La1Ni5", 298.0, sweep=True)

    assert app.success, "an admitted answer leads with a success headline"
    headings = [heading.value for heading in app.subheader]
    assert "Why it was answered" in headings
    assert "The nearest known alloys, as measured" in headings
    assert "Across the trained temperature range" in headings
    assert app.table, "the neighbours' measured rows are tabulated"
    assert any("Answered by artifact version" in caption.value for caption in app.caption)


def test_a_refusal_shows_its_reason_and_no_neighbours(page) -> None:
    app = _ask(page(), "La1Ni5", 1000.0)

    assert app.error, "a refusal leads with an error headline"
    headings = [heading.value for heading in app.subheader]
    assert "Why it was refused" in headings
    assert "The nearest known alloys, as measured" not in headings


def test_a_blank_formula_is_an_invalid_request(page) -> None:
    app = _ask(page(), "   ", 298.0)

    assert app.warning and "No material was judged" in app.warning[0].value


def test_an_unreachable_service_is_said_and_the_page_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HYDMS_API_URL", "http://127.0.0.1:9")
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.run()

    assert not app.exception
    assert app.error and "not answering" in app.error[0].value
    assert not app.text_input, "no form is offered when there is nothing to ask"


def test_the_environment_variable_is_what_the_script_reads() -> None:
    """Guard on the fixture above: were the name to drift, every test here would hit port 8000."""
    assert "HYDMS_API_URL" in APP.read_text(encoding="utf-8")
