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


# --------------------------------------------------------------------------------------
# The model-card page (card #83)
# --------------------------------------------------------------------------------------

CARD_PAGE = APP.parent / "pages" / "1_Model_card.py"


def test_the_model_card_page_runs_and_draws_every_section(service, monkeypatch, repo_root) -> None:
    from hydms.delivery.modelcard_page import model_card_view

    if not (repo_root / "reports" / "model" / "evaluation-metrics.csv").is_file():
        pytest.skip("no committed evidence in this checkout")
    monkeypatch.setenv("HYDMS_API_URL", service.base_url)
    app = AppTest.from_file(str(CARD_PAGE), default_timeout=120)
    app.run()
    assert not app.exception, [error.value for error in app.exception]

    view = model_card_view(service.evidence(), service.parity(), service.model())
    assert [header.value for header in app.header] == [section.title for section in view.sections]
    assert len(app.table) == sum(section.table is not None for section in view.sections)
    assert not app.error


def test_the_model_card_page_says_so_when_the_service_is_down(monkeypatch) -> None:
    monkeypatch.setenv("HYDMS_API_URL", "http://127.0.0.1:9")
    app = AppTest.from_file(str(CARD_PAGE), default_timeout=60)
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert app.error and "not reachable" in app.error[0].value


# --------------------------------------------------------------------------------------
# The batch screening page (card #84)
# --------------------------------------------------------------------------------------

BATCH_PAGE = APP.parent / "pages" / "2_Batch_screening.py"


class _Uploaded:
    """What ``st.file_uploader`` hands back, as far as the script reads it."""

    def __init__(self, text: str) -> None:
        self._data = text.encode("utf-8")

    def getvalue(self) -> bytes:
        return self._data


def _batch_page(service, monkeypatch: pytest.MonkeyPatch, text: str | None) -> AppTest:
    """The page with a file already chosen. AppTest cannot drive an upload, so it is handed one."""
    import streamlit

    monkeypatch.setenv("HYDMS_API_URL", service.base_url)
    monkeypatch.setattr(
        streamlit, "file_uploader", lambda *a, **k: None if text is None else _Uploaded(text)
    )
    app = AppTest.from_file(str(BATCH_PAGE), default_timeout=120)
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    return app


def test_the_batch_page_waits_for_a_file(service, monkeypatch) -> None:
    app = _batch_page(service, monkeypatch, None)

    assert not app.button and not app.info and not app.error


def test_the_batch_page_screens_a_file_and_says_what_happened_first(service, monkeypatch) -> None:
    app = _batch_page(
        service,
        monkeypatch,
        "formula,temperature_k\nLa1Ni5,298\nLaNi5Xx2,298\n,298\nLa1Ni5,1000\n",
    )
    assert app.button[0].label == "Screen 3 row(s)"

    app.button[0].click()
    app.run()
    assert not app.exception, [error.value for error in app.exception]

    summary = [info.value for info in app.info]
    assert summary[0].startswith("4 row(s) read. 1 answered by model v1, 2 refused")
    assert any("missing formula x 1 (row(s) 3)" in line for line in summary)
    shown = app.dataframe[0].value
    assert list(shown["status"]) == ["answered", "refused", "unread", "refused"]
    assert list(shown["capacity_wt_pct"])[1:] == ["refused", "unread", "refused"]


def test_the_batch_page_asks_what_nan_means_before_asking_the_model(service, monkeypatch) -> None:
    app = _batch_page(service, monkeypatch, "formula,temperature_k\nLa1Ni5,298\nNaN,298\n")

    assert app.warning and "read exactly `NaN`" in app.warning[0].value
    assert app.radio and app.radio[0].value is None
    assert not app.button, "nothing may be asked while NaN is undecided"

    app.radio[0].set_value("missing")
    app.run()
    assert not app.exception, [error.value for error in app.exception]
    assert app.button[0].label == "Screen 1 row(s)"


def test_the_batch_page_refuses_a_file_it_cannot_read_whole(service, monkeypatch) -> None:
    app = _batch_page(service, monkeypatch, "alloy,kelvin\nLaNi5,298\n")

    assert app.error and "cannot be read as a whole" in app.error[0].value
    assert "no formula column" in app.caption[-1].value
