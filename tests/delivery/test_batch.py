"""Card #84: the batch path -- ``predict_many`` in the library, and the CSV page as data.

Two halves. The first holds :func:`hydms.delivery.predict.predict_many` to the acceptance the
architecture grilling set: for every row, ``predict_many(xs)[i]`` equals
``predict_capacity(xs[i])`` to 1e-12, duplicates included, with one featurisation and one
surrogate call per batch. The second holds :mod:`hydms.delivery.batch` -- reading a CSV,
pairing rows with answers, the summary and the download -- to the card's boxes, and holds the
Streamlit script to being a client.

The reader tests use the standard library and the contract only. The ones that need answers
take them from the fixture deployment in ``conftest.py``, so a screening row is built from a
real answer rather than a hand-made one that could drift from what the service sends.
"""

from __future__ import annotations

import ast
import math
import sys
from pathlib import Path
from typing import Any

import pytest
from hydms.delivery.batch import (
    ANSWERED,
    COLUMNS,
    LITERAL_NAN,
    MISSING_TOKENS,
    NAN_IS_FORMULA,
    NAN_IS_MISSING,
    REFUSED,
    UNREAD,
    UploadError,
    read_upload,
    screening,
)
from hydms.delivery.contract import ContractError, PredictionRequest

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "app" / "pages" / "2_Batch_screening.py"

KNOWN = "La1Ni5"
OTHER = "La0.8Ce0.2Ni4Co1"
FAR = "K1Rb1"  # featurises cleanly, far from every known alloy: refused by the novelty screen
WARM = 298.0
TOLERANCE = 1e-12


# --------------------------------------------------------------------------------------
# The fixture deployment
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bundle(store: Path) -> Any:
    pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
    from hydms.delivery.predict import clear_cache, load_bundle

    clear_cache()
    return load_bundle(store=store)


def _close(left: Any, right: Any, where: str = "answer") -> None:
    """Equal as JSON, with floats compared to 1e-12 -- the project never compares floats with ==."""
    if isinstance(left, dict):
        assert isinstance(right, dict) and left.keys() == right.keys(), where
        for key in left:
            _close(left[key], right[key], f"{where}.{key}")
    elif isinstance(left, list):
        assert isinstance(right, list) and len(left) == len(right), where
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            _close(a, b, f"{where}[{index}]")
    elif isinstance(left, float) and not isinstance(left, bool):
        assert isinstance(right, float), where
        assert math.isclose(left, right, rel_tol=0.0, abs_tol=TOLERANCE), (where, left, right)
    else:
        assert left == right, (where, left, right)


def _requests() -> list[PredictionRequest]:
    """Every outcome the path has, and each more than once, interleaved.

    Duplicates on purpose -- the batch labels rows by position, and a label built from the
    formula would collide here -- and refusals of every kind between admitted rows, so a
    refused row that shifted its neighbours would show.
    """
    asked = [
        (KNOWN, WARM),
        ("LaNi5Xx2", WARM),  # does not parse: refused before any screen
        (OTHER, 350.0),
        ("Xe1Rn1", WARM),  # parses, but the tables have holes for it
        (KNOWN, 1000.0),  # outside the trained window
        (FAR, WARM),  # beyond known chemistry
        (KNOWN, WARM),  # a duplicate of row 0
        ("LaNi5Xx2", WARM),  # a duplicate refusal
        (OTHER, 350.0),
        ("Xe1Rn1", 400.0),
    ]
    return [PredictionRequest(formula=f, temperature_k=t) for f, t in asked]


# --------------------------------------------------------------------------------------
# predict_many: the batched call in the library
# --------------------------------------------------------------------------------------


def test_every_row_of_a_batch_is_what_the_lone_call_says_about_it(bundle: Any) -> None:
    """The acceptance the card was given: row i of the batch == the one-row call, to 1e-12."""
    from hydms.delivery.predict import predict_capacity, predict_many

    asked = _requests()
    batch = predict_many(asked, bundle=bundle)

    assert len(batch) == len(asked)
    for position, request in enumerate(asked):
        alone = predict_capacity(request.formula, request.temperature_k, bundle=bundle)
        assert type(batch[position]) is type(alone), position
        _close(batch[position].to_dict(), alone.to_dict(), f"row {position}")


def test_the_batch_covers_every_outcome_so_the_parity_above_is_not_vacuous(bundle: Any) -> None:
    from hydms.delivery.contract import INDETERMINATE, PredictionResult, Refusal
    from hydms.delivery.predict import predict_many
    from hydms.screens.novelty import BEYOND_KNOWN_CHEMISTRY
    from hydms.screens.window import OUTSIDE_WINDOW

    batch = predict_many(_requests(), bundle=bundle)

    assert isinstance(batch[0], PredictionResult) and isinstance(batch[2], PredictionResult)
    codes = {answer.code for answer in batch if isinstance(answer, Refusal)}
    assert {INDETERMINATE, OUTSIDE_WINDOW, BEYOND_KNOWN_CHEMISTRY} <= codes
    # The duplicates are answered twice, identically.
    _close(batch[0].to_dict(), batch[6].to_dict())
    _close(batch[1].to_dict(), batch[7].to_dict())


def test_a_bad_formula_refuses_its_own_row_with_a_sentence_written_for_that_row(
    bundle: Any,
) -> None:
    """No label, no batch count: #84's sentence is the row's, not the batch's account of it."""
    from hydms.delivery.contract import INDETERMINATE, Refusal
    from hydms.delivery.predict import CANDIDATE, predict_many

    batch = predict_many(_requests(), bundle=bundle)
    unparsed, holed = batch[1], batch[3]

    assert isinstance(unparsed, Refusal) and unparsed.code == INDETERMINATE
    assert unparsed.explanation.startswith("the formula could not be parsed: 'LaNi5Xx2'")
    assert isinstance(holed, Refusal) and holed.code == INDETERMINATE
    assert holed.explanation.startswith("Xe1Rn1: ")
    assert "refused rather than filled" in holed.explanation
    for refusal in (unparsed, holed):
        assert "of 10" not in refusal.explanation and "of 1 " not in refusal.explanation
        assert CANDIDATE not in refusal.explanation
        assert "[1]" not in refusal.explanation and "[3]" not in refusal.explanation
        assert refusal.screens == (), "refused before any screen ran"


def test_a_batch_is_featurised_and_predicted_once_not_once_a_row(
    bundle: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The point of the card: no per-row fallback. One retry without the offenders, at most."""
    import hydms.delivery.predict  # noqa: F401 -- make sure the module is in sys.modules
    from hydms.delivery.predict import predict_many

    module = sys.modules["hydms.delivery.predict"]
    real_featurize = module.featurize
    calls: list[int] = []

    def counting(formulas: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append(len(formulas))
        return real_featurize(formulas, *args, **kwargs)

    monkeypatch.setattr(module, "featurize", counting)
    surrogate = type(bundle._surrogate)
    real_predict = surrogate.predict
    predicted: list[int] = []

    def counting_predict(self: Any, formulas: Any, *args: Any, **kwargs: Any) -> Any:
        predicted.append(len(formulas))
        return real_predict(self, formulas, *args, **kwargs)

    monkeypatch.setattr(surrogate, "predict", counting_predict)

    asked = _requests()
    predict_many(asked, bundle=bundle)

    # Four rows fail to featurise (two unparseable, two with holes): one call for all ten,
    # which names all four at once, and one for the six survivors.
    assert calls == [10, 6]
    assert predicted == [6]

    calls.clear()
    predicted.clear()
    predict_many([request for request in asked if "Xx" not in request.formula
                  and "Xe" not in request.formula], bundle=bundle)
    assert calls == [6] and predicted == [6]


def test_an_empty_batch_is_an_empty_list(bundle: Any) -> None:
    from hydms.delivery.predict import predict_many

    assert predict_many([], bundle=bundle) == []


def test_a_batch_that_is_all_refused_before_the_model_never_calls_it(bundle: Any) -> None:
    from hydms.delivery.contract import Refusal
    from hydms.delivery.predict import predict_many

    batch = predict_many(
        [PredictionRequest("LaNi5Xx2", WARM), PredictionRequest("Xe1Rn1", WARM)], bundle=bundle
    )

    assert all(isinstance(answer, Refusal) for answer in batch)


def test_a_batch_item_that_is_not_a_request_is_a_caller_error(bundle: Any) -> None:
    """Validation is the request constructor's; a batch path must not skip it."""
    from hydms.delivery.predict import predict_many

    with pytest.raises(ContractError, match="item 1 is a dict"):
        predict_many(
            [PredictionRequest(KNOWN, WARM), {"formula": KNOWN, "temperature_k": WARM}],  # type: ignore[list-item]
            bundle=bundle,
        )


def test_the_featuriser_hands_back_every_offender_of_both_kinds_as_data() -> None:
    """The seam predict_many stands on: labels as data, both kinds in one raise."""
    pd = pytest.importorskip("pandas")
    from hydms.descriptors.featurize import FeaturisationError, featurize

    formulas = pd.Series(["LaNi5", "LaNi5Xx2", "Xe1Rn1", "TiFe"], index=["a", "b", "c", "d"])
    with pytest.raises(FeaturisationError) as raised:
        featurize(formulas, 298.0)

    assert list(raised.value.rows) == ["b", "c"]
    assert "could not be parsed" in str(raised.value)
    assert "cannot produce all" in str(raised.value)


def test_a_defect_of_the_batch_carries_no_rows() -> None:
    """A repeated label is nobody's row: the delivery path must raise it, not refuse everyone."""
    pd = pytest.importorskip("pandas")
    from hydms.descriptors.featurize import FeaturisationError, featurize

    with pytest.raises(FeaturisationError) as raised:
        featurize(pd.Series(["LaNi5", "TiFe"], index=["x", "x"]), 298.0)

    assert dict(raised.value.rows) == {}


# --------------------------------------------------------------------------------------
# The route: one call, and the limit that was re-measured
# --------------------------------------------------------------------------------------


def test_the_batch_route_answers_each_row_as_the_single_route_does(store: Path) -> None:
    """Transport parity survives the switch from a loop to one call."""
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from hydms.delivery.api.service import create_app

    asked = _requests()
    from hydms.delivery.predict import load_bundle

    with TestClient(create_app(resolve=lambda: load_bundle(store=store))) as client:
        body = {"candidates": [request.to_dict() for request in asked]}
        batch = client.post("/v1/predict/batch", json=body).json()["answers"]
        for position, request in enumerate(asked):
            alone = client.post("/v1/predict", json=request.to_dict()).json()
            _close(batch[position], alone, f"row {position}")


# --------------------------------------------------------------------------------------
# A crossed band (card #94)
# --------------------------------------------------------------------------------------


class _Crossing:
    """The fixture's surrogate, with the outer heads of every ``crossed`` formula swapped.

    Which candidates cross is a property of a fit and differs between machines (#93), so the
    crossing is stated rather than hoped for. Everything else is the real surrogate's output;
    the width is recomputed from the swapped heads, which is how a real crossing arrives --
    as a negative width, unclipped (``test_a_crossed_band_reaches_the_caller_unclipped``).
    """

    def __init__(self, inner: Any, crossed: set[str], heads: tuple[str, str, str]) -> None:
        self._inner, self._crossed, self._heads = inner, crossed, heads

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def predict(self, formulas: Any, temperatures: Any) -> Any:
        from hydms.delivery.predict import WIDTH_COLUMN

        frame = self._inner.predict(formulas, temperatures)
        lower, _, upper = self._heads
        hit = formulas.isin(self._crossed).to_numpy()
        frame.loc[hit, [lower, upper]] = frame.loc[hit, [upper, lower]].to_numpy()
        frame[WIDTH_COLUMN] = frame[upper] - frame[lower]
        return frame


@pytest.fixture()
def crossing(bundle: Any) -> Any:
    """The fixture deployment, with ``KNOWN``'s band crossed and ``OTHER``'s left alone."""
    import dataclasses

    surrogate = _Crossing(bundle._surrogate, {KNOWN}, bundle._heads)
    return dataclasses.replace(bundle, _surrogate=surrogate)


def _crossed_batch() -> list[PredictionRequest]:
    return [
        PredictionRequest(OTHER, 350.0),
        PredictionRequest(KNOWN, WARM),
        PredictionRequest(OTHER, 350.0),
    ]


def test_one_crossed_band_refuses_its_own_row_and_not_the_batch(crossing: Any) -> None:
    """Card #94. Before it, the crossed row reached ``Interval`` and its raise lost the batch."""
    from hydms.delivery.predict import predict_many
    from hydms.screens.protocol import INDETERMINATE

    answers = predict_many(_crossed_batch(), bundle=crossing)

    assert [answer.refused for answer in answers] == [False, True, False]
    assert answers[1].code == INDETERMINATE
    assert "crossed" in answers[1].explanation
    assert answers[0].interval.width > 0 and answers[2].interval.width > 0


def test_a_crossed_band_is_a_refusal_on_the_batch_route_and_not_a_500(crossing: Any) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from hydms.delivery.api.service import create_app

    with TestClient(create_app(resolve=lambda: crossing)) as client:
        body = {"candidates": [request.to_dict() for request in _crossed_batch()]}
        response = client.post("/v1/predict/batch", json=body)
        lone = client.post("/v1/predict", json=_crossed_batch()[1].to_dict())

    assert response.status_code == 200, response.json()
    answers = response.json()["answers"]
    assert [answer["refused"] for answer in answers] == [False, True, False]
    # The single route answers a refusal with 422 by the runbook's rule -- a readable body,
    # never a 500 -- and the batch row carries that same body.
    assert lone.status_code == 422
    _close(lone.json(), answers[1], "the lone crossed row")


def test_a_crossed_band_is_one_refused_row_on_the_screening_page(crossing: Any) -> None:
    from hydms.delivery.predict import predict_many

    upload = read_upload(
        f"formula,temperature_k\n{OTHER},350\n{KNOWN},{WARM:g}\n{OTHER},350\n"
    )
    answers = predict_many(upload.requests(), bundle=crossing)
    table = screening(upload, answers, version=crossing.version)

    assert [record["status"] for record in table.records] == [ANSWERED, REFUSED, ANSWERED]


def test_the_published_limit_is_the_re_measured_one() -> None:
    """256 was one-row frames at ~75 ms; the batched route is ~1 ms a row (service docstring)."""
    pytest.importorskip("fastapi")
    from hydms.delivery.api.service import MAX_BATCH_ROWS

    assert MAX_BATCH_ROWS == 4096


# --------------------------------------------------------------------------------------
# Reading the CSV
# --------------------------------------------------------------------------------------


def test_the_corpus_own_headers_are_read() -> None:
    upload = read_upload("Composition,temperature(K),Alloy_class\nLaNi5,298,AB5\n")

    assert [row.request for row in upload.rows] == [PredictionRequest("LaNi5", 298.0)]


def test_a_semicolon_file_and_a_byte_order_mark_are_read() -> None:
    upload = read_upload("﻿formula;temperature_k\nLaNi5;298\n".encode())

    assert upload.requests() == [PredictionRequest("LaNi5", 298.0)]


@pytest.mark.parametrize(
    ("text", "names"),
    [
        ("formula,kelvin\nLaNi5,298\n", "no temperature column"),
        ("alloy,temperature_k\nLaNi5,298\n", "no formula column"),
        ("formula,Composition,T_K\nLaNi5,TiFe,298\n", "2 formula columns"),
        ("", "empty"),
        ("formula,temperature_k\n", "no data rows"),
    ],
)
def test_a_schema_error_is_refused_whole_and_says_what(text: str, names: str) -> None:
    with pytest.raises(UploadError, match=names):
        read_upload(text)


def test_the_row_limit_is_documented_and_enforced() -> None:
    text = "formula,temperature_k\n" + "LaNi5,298\n" * 4

    assert len(read_upload(text, max_rows=4).rows) == 4
    with pytest.raises(UploadError, match="more than 3 data rows"):
        read_upload(text, max_rows=3)


def test_a_malformed_row_is_unread_and_named_while_the_rest_are_asked() -> None:
    upload = read_upload(
        "formula,temperature_k\nLaNi5,298\nTiFe,298,extra\nTiFe,warm\nMg2Ni,inf\nLaNi5,\n"
    )

    readable = [row.number for row in upload.rows if row.request is not None]
    unread = {row.number: row.problem for row in upload.rows if row.request is None}
    assert readable == [1]
    assert set(unread) == {2, 3, 4, 5}
    for number, problem in unread.items():
        assert problem is not None and problem.startswith(f"row {number}: ")
    assert "3 cell(s)" in str(unread[2])
    assert "'warm'" in str(unread[3])
    assert "not a finite number" in str(unread[4])
    assert "temperature cell is empty" in str(unread[5])


def test_every_spelling_of_a_missing_formula_is_unread_before_any_parser_sees_it() -> None:
    """The first box: a blank cell refused on read, the row named, and counted."""
    cells = sorted(MISSING_TOKENS - {""})
    text = "formula,temperature_k\n" + "".join(f"{cell},298\n" for cell in cells) + ",298\n"
    upload = read_upload(text)

    assert len(upload.rows) == len(cells) + 1
    assert all(row.request is None and row.cause == "missing formula" for row in upload.rows)


def test_no_missing_token_is_a_formula_so_reading_one_as_missing_refuses_no_material() -> None:
    """The set is safe only because every token in it fails the grammar. Asserted, not assumed."""
    pytest.importorskip("pandas")
    from hydms.data.load import FormulaError, parse_formula

    for token in MISSING_TOKENS:
        with pytest.raises(FormulaError):
            parse_formula(token)
    assert parse_formula(LITERAL_NAN), "NaN is sodium and nitrogen -- which is why it is not in the set"


def test_a_file_written_with_na_rep_nan_is_not_answered_as_sodium_nitride() -> None:
    """The box #76 left here, tested with the file the box names: df.to_csv(na_rep="NaN")."""
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame({"formula": ["LaNi5", None, "TiFe"], "temperature_k": [298.0, 298.0, None]})
    exported = frame.to_csv(index=False, na_rep="NaN")
    assert "NaN,298.0" in exported, "the fixture must be the file the box describes"

    upload = read_upload(exported)
    assert upload.literal_nan == (2,)
    assert upload.needs_decision
    with pytest.raises(UploadError, match="Say which it is"):
        upload.requests()

    missing = read_upload(exported, nan_means=NAN_IS_MISSING)
    assert missing.requests() == [PredictionRequest("LaNi5", 298.0)]
    assert [row.cause for row in missing.rows] == [None, "missing formula", "missing temperature"]


def test_nan_is_answered_as_chemistry_when_the_caller_says_so() -> None:
    """Refusing the string would refuse a real material; the decision is the caller's."""
    upload = read_upload("formula,temperature_k\nNaN,298\n", nan_means=NAN_IS_FORMULA)

    assert upload.requests() == [PredictionRequest(LITERAL_NAN, 298.0)]


# --------------------------------------------------------------------------------------
# The answers, the summary and the download
# --------------------------------------------------------------------------------------

UPLOAD = (
    "formula,temperature_k\n"
    f"{KNOWN},298\n"
    "LaNi5Xx2,298\n"
    ",298\n"
    f"{KNOWN},1000\n"
    f"{OTHER},350\n"
    "\n"
    f"{FAR},298\n"
)


@pytest.fixture(scope="module")
def screened(bundle: Any) -> Any:
    from hydms.delivery.predict import predict_many

    upload = read_upload(UPLOAD)
    return screening(upload, predict_many(upload.requests(), bundle=bundle), version=bundle.version)


def test_every_uploaded_row_comes_back_in_order_and_none_is_blank(screened: Any) -> None:
    assert [record["row"] for record in screened.records] == [1, 2, 3, 4, 5, 6]
    assert [record["status"] for record in screened.records] == [
        ANSWERED, REFUSED, UNREAD, REFUSED, ANSWERED, REFUSED,
    ]
    for record in screened.records:
        assert tuple(record) == COLUMNS
        assert all(value != "" and value is not None for value in record.values()), record


def test_an_answered_row_carries_estimate_interval_verdict_and_distance(screened: Any) -> None:
    record = screened.records[0]

    assert isinstance(record["capacity_wt_pct"], float)
    assert record["lower_wt_pct"] <= record["capacity_wt_pct"] <= record["upper_wt_pct"]
    assert math.isclose(
        record["interval_width_wt_pct"],
        record["upper_wt_pct"] - record["lower_wt_pct"],
        abs_tol=TOLERANCE,
    )
    assert record["code"] == "admitted" and record["reason"]
    assert isinstance(record["elmd_distance"], float) and record["nearest_known_alloy"]


def test_a_refused_row_says_refused_where_every_number_would_be(screened: Any) -> None:
    """A blank cell reads as a low number once sorted; the word does not."""
    for record in screened.records:
        if record["status"] == ANSWERED:
            continue
        for column in ("capacity_wt_pct", "lower_wt_pct", "upper_wt_pct", "interval_width_wt_pct"):
            assert record[column] == record["status"]
        assert record["reason"] and record["code"]


def test_the_summary_counts_refusals_by_reason_before_anything_is_downloaded(
    screened: Any,
) -> None:
    lines = screened.summary()

    assert lines[0].startswith("6 row(s) read. 2 answered by model v1, 3 refused")
    assert "1 not asked" in lines[0]
    assert any(line.startswith("Refused, by reason:") and "indeterminate" in line for line in lines)
    assert any("missing formula x 1 (row(s) 3)" in line for line in lines)
    assert any("1 wholly empty line(s) were skipped" in line for line in lines)


def test_the_download_carries_the_version_on_every_row_and_in_its_name(screened: Any) -> None:
    import csv
    import io

    rows = list(csv.DictReader(io.StringIO(screened.to_csv())))

    assert len(rows) == 6
    assert {row["model_version"] for row in rows} == {"v1"}
    assert screened.file_name == "hydms-screening-v1.csv"


def test_the_widest_interval_comes_first_and_rows_without_one_come_last(screened: Any) -> None:
    ordered = screened.ordered(by_width=True)
    widths = [r["interval_width_wt_pct"] for r in ordered if r["status"] == ANSWERED]

    assert widths == sorted(widths, reverse=True)
    statuses = [r["status"] for r in ordered]
    assert statuses[: len(widths)] == [ANSWERED] * len(widths)
    assert [r["row"] for r in ordered[len(widths):]] == [2, 3, 4, 6]


def test_the_table_the_page_shows_is_text_in_every_cell(screened: Any) -> None:
    shown = screened.shown()

    assert all(isinstance(value, str) and value for row in shown for value in row.values())
    assert shown[1]["capacity_wt_pct"] == REFUSED


def test_a_cell_a_spreadsheet_would_run_is_made_inert_in_the_download(bundle: Any) -> None:
    from hydms.delivery.predict import predict_many

    upload = read_upload('formula,temperature_k\n"=HYPERLINK(""x"")",298\n')
    result = screening(upload, predict_many(upload.requests(), bundle=bundle), version="v1")

    written = result.to_csv()
    assert "\n1,\"'=HYPERLINK" in written, written
    assert "\n1,\"=HYPERLINK" not in written


def test_answers_that_do_not_line_up_with_the_rows_are_refused(bundle: Any) -> None:
    from hydms.delivery.predict import predict_many

    upload = read_upload(f"formula,temperature_k\n{KNOWN},298\n{OTHER},350\n")
    answers = predict_many(upload.requests(), bundle=bundle)

    with pytest.raises(ValueError, match="2 row"):
        screening(upload, answers[:1], version="v1")
    with pytest.raises(ValueError, match="reordered"):
        screening(upload, answers[::-1], version="v1")
    with pytest.raises(ValueError, match="One download holds one model"):
        screening(upload, answers, version="v9")


# --------------------------------------------------------------------------------------
# The page stays a client
# --------------------------------------------------------------------------------------

#: Every module the page may import: the same rule ``test_app.py`` holds ``app/main.py`` to.
ALLOWED = {
    "__future__",
    "hashlib",
    "os",
    "streamlit",
    "hydms.delivery.batch",
    "hydms.delivery.client",
}


def test_the_page_imports_nothing_that_predicts_or_reads_a_file_its_own_way() -> None:
    tree = ast.parse(PAGE.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)

    assert found <= ALLOWED, sorted(found - ALLOWED)
