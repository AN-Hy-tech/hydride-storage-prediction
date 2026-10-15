"""The model-card page: the evidence routes, what the page says, and the app staying a client.

Card #83; ADR 0007. Three layers, tested where each one decides something:

  - **The service serves the reader's evidence, read once.** ``GET /v1/evidence`` is
    :func:`hydms.evidence.reader.read`'s payload and nothing else, over a real socket, and the
    evidence is read at startup and never per request, so the page and the refusals beside it
    cannot disagree after a regeneration.
  - **The page says what the card requires, from the payloads alone.** Asserted on
    :func:`hydms.delivery.modelcard_page.model_card_view`, which is Streamlit-free. Each box
    on the card has a test here, and each number is checked against the payload it came from.
  - **The typed limits are recomputed from their sources.** :data:`LIMIT_FACTS` is the one
    place the page states a number no route serves. Each fact is rebuilt from its committed
    table or from the data, so an edit to either goes red here.
"""

from __future__ import annotations

import ast
import csv
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
pytest.importorskip("fastapi", reason="the `api` extra: pip install -e '.[api]'")
pytest.importorskip("uvicorn", reason="the `api` extra serves the app over a real socket")
pytest.importorskip("ElMD", reason="the `novelty` extra; it is on the prediction path")

from hydms.delivery.client import ServiceClient  # noqa: E402
from hydms.delivery.modelcard_page import (  # noqa: E402
    ARCHIVE_TAG,
    LIMIT_FACTS,
    RECONCILIATION,
    CardPageError,
    model_card_view,
)
from hydms.evidence import reader  # noqa: E402

PAGE = Path(__file__).resolve().parents[2] / "app" / "pages" / "1_Model_card.py"


@pytest.fixture(scope="module")
def payloads(service: ServiceClient, repo_root: Path) -> tuple[dict, dict, dict]:
    if not (repo_root / reader.EVALUATION_METRICS).is_file():
        pytest.skip("no committed evidence in this checkout")
    return service.evidence(), service.parity(), service.model()


@pytest.fixture(scope="module")
def view(payloads):
    return model_card_view(*payloads)


# --------------------------------------------------------------------------------------
# The service: the reader's evidence, read once
# --------------------------------------------------------------------------------------


def test_the_served_evidence_is_the_readers_payload(payloads, repo_root: Path) -> None:
    evidence, parity, _ = payloads
    read = reader.read(repo_root)
    assert evidence == read.to_dict()
    assert parity == read.parity_dict()


def test_health_names_the_digest_of_the_evidence_it_serves(service: ServiceClient, payloads) -> None:
    assert service.health()["evidence_sha256"] == payloads[0]["digest"]


def test_the_evidence_is_read_once_at_startup_and_never_per_request(store: Path) -> None:
    from fastapi.testclient import TestClient
    from hydms.delivery.api import create_app
    from hydms.delivery.predict import load_bundle

    calls: list[int] = []

    def counted() -> reader.Evidence:
        calls.append(1)
        return reader.read()

    with TestClient(create_app(resolve=lambda: load_bundle(store=store), evidence=counted)) as client:
        for _ in range(3):
            assert client.get("/v1/evidence").status_code == 200
            assert client.get("/v1/evidence/parity").status_code == 200
            assert client.get("/v1/health").status_code == 200
    assert calls == [1]


def test_missing_evidence_serves_absences_and_still_predicts(store: Path, tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from hydms.delivery.api import create_app
    from hydms.delivery.predict import load_bundle

    app = create_app(resolve=lambda: load_bundle(store=store), evidence=lambda: reader.read(tmp_path))
    with TestClient(app) as client:
        scores = client.get("/v1/evidence").json()["scores"]
        assert scores and all(s["value"] is None and s["absent_because"] for s in scores)
        answer = client.post("/v1/predict", json={"formula": "La1Ni5", "temperature_k": 298.0})
        assert answer.status_code == 200


# --------------------------------------------------------------------------------------
# What the page says, box by box
# --------------------------------------------------------------------------------------


def _row(view, section: str, first: str) -> tuple[str, ...]:
    table = view.section(section).table
    assert table is not None
    for row in table.rows:
        if row[0] == first:
            return row
    raise AssertionError(f"no row {first!r} in {section}")


def test_random_split_and_leave_one_family_out_are_side_by_side_at_one_scale(view, payloads) -> None:
    procedure = _row(view, "scores", "Procedure score")
    transfer = _row(view, "scores", "Transfer score")
    by_key = {(s["reading"], s["subject"]): s for s in payloads[0]["scores"] if s["quantity"] == "r2"}
    assert procedure[1] == f"{by_key[('procedure', 'all')]['value']:.4f}"
    assert transfer[1] == f"{by_key[('transfer', 'macro')]['value']:.4f}"
    figure = view.section("parity").figure
    assert figure is not None and len(figure.panels) == 2
    assert set(figure.shared) == {"x", "y"}
    assert [panel.title.split(" (n")[0] for panel in figure.panels] == [
        "random split, out-of-fold",
        "leave one alloy family out",
    ]


def test_every_interval_is_shown_or_its_absence_is_explained(view) -> None:
    table = view.section("scores").table
    assert table is not None
    for row in table.rows:
        assert row[2].startswith("[") or row[2].startswith("none: "), row
    artifact = _row(view, "scores", "Artifact score")
    assert "AC-3" in artifact[2]


def test_three_r2_values_with_a_sentence_saying_which_is_which(view, payloads) -> None:
    text = " ".join(view.section("scores").paragraphs)
    facts = payloads[0]["artifact_facts"]
    assert "Three R² values" in text
    assert f"grew on {int(facts['rows_grown_on'])} rows" in text
    assert "not the same number" in text


def test_the_training_data_is_described_from_the_model_card(view, payloads) -> None:
    card = payloads[2]
    table = view.section("data").table
    assert table is not None
    facts = dict(table.rows)
    assert facts["training rows"] == str(card["trained_ranges"]["capacity"]["rows"])
    assert facts["distinct canonical compositions"] == str(card["trained_ranges"]["corpus"]["compositions"])
    assert facts["alloy families"] == "10"
    assert facts["elements present"].startswith(f"{len(card['trained_ranges']['corpus']['elements'])}:")
    assert facts["temperature"].endswith("K")


def test_the_applicability_domain_is_stated_as_rules_a_reader_can_apply(view) -> None:
    text = " ".join(view.section("domain").paragraphs)
    for rule in ("Temperature", "Capacity", "Certainty", "Novelty"):
        assert f"**{rule}.**" in text


def test_the_material_versus_system_caveat_is_on_the_page(view) -> None:
    text = " ".join(view.section("system").paragraphs)
    assert "material" in text and "system" in text and "DOE" in text and "twice" in text


def test_the_reconciliation_is_cited_at_the_archive_tag(view) -> None:
    """It lives only at the tag (card #107); citing it without the tag would be a dead path."""
    assert f"`{RECONCILIATION}` at the git tag `{ARCHIVE_TAG}`" in view.text


def test_the_limits_include_pressure_filler_stability_the_bad_label_ambient_and_the_band(view) -> None:
    text = " ".join(view.section("limits").paragraphs)
    for phrase in (
        "No pressure data",
        "reversible",
        "filler values",
        "consensus, not a discovery",
        "physically impossible",
        "weakest where storage has to work",
        "wide relative to the physics",
    ):
        assert phrase in text, phrase


def test_the_near_ambient_bin_is_quoted_with_its_interval_not_rounded(view, payloads) -> None:
    coldest = min(
        (s for s in payloads[0]["scores"] if s["subject"].startswith("temperature:")),
        key=lambda s: float(s["subject"].split("(")[1].split(",")[0]),
    )
    text = " ".join(view.section("limits").paragraphs)
    assert f"{coldest['value']:.4f}" in text
    assert f"[{coldest['interval']['low']:.4f}, {coldest['interval']['high']:.4f}]" in text


def test_the_artifact_version_and_training_date_are_stated(view, payloads) -> None:
    card = payloads[2]
    what = view.section("what")
    assert card["version"] in what.paragraphs[0]
    assert card["trained_at"] in what.paragraphs[0]
    notes = (card.get("provenance") or {}).get("notes")
    assert what.caption == (f"The manifest's own note on this version: {notes}" if notes else "")


def test_the_transfer_panel_names_its_run_by_commit_not_by_a_borrowed_date(view) -> None:
    caption = view.section("parity").caption
    assert "run date not recorded" in caption
    assert "a commit, not a run date" in caption
    assert "#104" in caption


def test_without_the_transfer_rows_the_page_says_so_and_draws_no_single_panel(payloads) -> None:
    evidence, parity, card = payloads
    starved = {
        **parity,
        "readings": {
            **parity["readings"],
            "transfer": {**parity["readings"]["transfer"], "rows": [], "absent_because": "a probe"},
        },
    }
    section = model_card_view(evidence, starved, card).section("parity")
    assert section.figure is None
    assert "a probe" in " ".join(section.paragraphs)


def test_an_absent_transfer_score_is_a_row_that_says_absent(payloads) -> None:
    evidence, parity, card = payloads
    scores = [
        {**s, "value": None, "interval": None, "no_interval_because": None,
         "absent_because": "its record says probe=True"}
        if s["reading"] == "transfer" else s
        for s in evidence["scores"]
    ]
    view = model_card_view({**evidence, "scores": scores}, parity, card)
    row = _row(view, "scores", "Transfer score")
    assert row[1] == "absent" and "probe=True" in row[2]


def test_no_scores_at_all_is_refused_rather_than_drawn_as_a_clean_card(payloads) -> None:
    with pytest.raises(CardPageError, match="no scores"):
        model_card_view({"scores": []}, payloads[1], payloads[2])


# --------------------------------------------------------------------------------------
# The typed limits, recomputed from their sources
# --------------------------------------------------------------------------------------


def _csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))


def test_the_gordy_filler_count_is_the_feature_cost_tables(repo_root: Path) -> None:
    rows = _csv(repo_root / "reports" / "feature_selection" / "feature-row-cost.csv")
    (gordy,) = [row for row in rows if row["feature"] == "dev_Gordy_electonegativity"]
    assert int(gordy["rows_blocked"]) == LIMIT_FACTS["gordy_rows_blocked"]
    assert int(gordy["of"]) == LIMIT_FACTS["curated_rows"]


def test_the_selection_stability_counts_are_the_published_tables(repo_root: Path) -> None:
    rows = _csv(repo_root / "reports" / "feature_selection" / "selection-stability.csv")
    assert len(rows) == LIMIT_FACTS["selection_candidates"]
    assert all(int(row["folds"]) >= 1 for row in rows)
    unanimous = [row for row in rows if row["folds"] == row["of"]]
    assert len(unanimous) == LIMIT_FACTS["selection_unanimous"]
    assert {int(row["of"]) for row in rows} == {LIMIT_FACTS["selection_folds"]}


def test_the_placeholder_exposure_is_measured_on_the_data(raw_data_path: Path) -> None:
    from hydms.surrogate.comparison import placeholder_exposure

    exposure = placeholder_exposure()
    assert exposure.per_element[LIMIT_FACTS["placeholder_element"]] == LIMIT_FACTS["placeholder_rows"]


def test_the_impossible_label_is_in_the_data_and_in_val(raw_data_path: Path) -> None:
    from hydms.data.load import load_hydride_data
    from hydms.data.splits import assign_splits

    data = load_hydride_data()
    split = assign_splits(data)
    rows = data[data["Composition"] == LIMIT_FACTS["impossible_formula"]]
    assert len(rows) == 1
    assert float(rows["H2_W% (max)"].iloc[0]) == pytest.approx(LIMIT_FACTS["impossible_capacity"])
    assert split.loc[rows.index[0]] == LIMIT_FACTS["impossible_split"]


# --------------------------------------------------------------------------------------
# The Streamlit page stays a client
# --------------------------------------------------------------------------------------

#: Every module the page may import. The forward page's set, with this page's view module in
#: place of the forward page's.
ALLOWED = {
    "__future__",
    "os",
    "streamlit",
    "hydms.delivery.client",
    "hydms.delivery.modelcard_page",
    "hydms.figures.render",
}


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_the_page_imports_nothing_that_reads_evidence_or_draws_on_its_own() -> None:
    imported = _imports(PAGE)
    assert imported <= ALLOWED, sorted(imported - ALLOWED)


def test_the_page_import_check_would_catch_a_direct_evidence_read(tmp_path: Path) -> None:
    rogue = tmp_path / "page.py"
    rogue.write_text(
        PAGE.read_text(encoding="utf-8") + "\nfrom hydms.evidence.reader import read\n"
        "import matplotlib.pyplot as plt\n",
        encoding="utf-8",
    )
    assert _imports(rogue) - ALLOWED == {"hydms.evidence.reader", "matplotlib.pyplot"}
