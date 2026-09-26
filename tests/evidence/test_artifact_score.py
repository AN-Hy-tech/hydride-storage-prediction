"""``reports/model/artifact-score.csv``: the deployed model's test score, from its sealed gate record.

Card #103. The table is committed so the Chapter 1 revision (#37) can cite the artifact score
without pointing into the gitignored ``artifacts/``. Three properties, each a way it could go
wrong silently:

  - the committed table drifts from the committed record (the byte test, which runs in CI);
  - the parser publishes something it should have refused (one test per refusal);
  - the committed record drifts from the promoted manifest (the probe test). That test reads
    ``artifacts/``, so it **only runs on the maintainer's machine** and skips in CI. The skip is
    the honest state and is named in its reason, not hidden.
"""

from __future__ import annotations

import copy
import io
import json
from typing import Any

import pytest
from hydms.config import repo_root
from hydms.evidence import artifact_score
from hydms.evidence.artifact_score import RECORD, TABLE, ScoreUnavailable, rows, table


@pytest.fixture
def payload() -> dict[str, Any]:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _gate(payload: dict[str, Any], name: str) -> dict[str, Any]:
    return next(g for g in payload["gates"] if g["name"] == name)


def test_the_committed_table_is_what_the_record_produces(payload: dict[str, Any]) -> None:
    assert TABLE.read_bytes().decode("utf-8") == table(payload), (
        "reports/model/artifact-score.csv differs from its record. Regenerate it with "
        "`python -m hydms.evidence.artifact_score --emit`; never edit it."
    )


def test_the_sentence_column_is_description_not_reading() -> None:
    # #83: `reading` is the Evidence Reader's procedure | artifact | transfer. A column of the
    # same name holding a sentence, in the file that reader maps, is the crossing it invites.
    header = next(
        line for line in TABLE.read_text(encoding="utf-8").splitlines() if not line.startswith("#")
    )
    assert header.split(",") == ["quantity", "value", "unit", "gate", "split", "rows", "description"]


def test_the_headline_numbers_are_the_ones_the_chapter_cites(payload: dict[str, Any]) -> None:
    published = {row.quantity: row.value for row in rows(payload)}
    assert published["r2"] == "0.707064"
    assert published["coverage_calibrated"] == "0.7795"
    assert {row.rows for row in rows(payload)} == {254}


def test_a_gate_that_did_not_pass_is_refused(payload: dict[str, Any]) -> None:
    _gate(payload, "AC-1")["status"] = "FAILED"
    with pytest.raises(ScoreUnavailable, match="AC-1"):
        rows(payload)


def test_a_missing_gate_is_refused(payload: dict[str, Any]) -> None:
    payload["gates"] = [g for g in payload["gates"] if g["name"] != "AC-3"]
    with pytest.raises(ScoreUnavailable, match="AC-3"):
        rows(payload)


def test_a_refit_that_is_not_the_stored_model_is_refused(payload: dict[str, Any]) -> None:
    gate = _gate(payload, "AC-1")
    gate["message"] = gate["message"].replace(
        "interval_coverage 0.779528", "interval_coverage 0.811024"
    )
    with pytest.raises(ScoreUnavailable, match="not the same model"):
        rows(payload)


def test_a_split_other_than_test_is_refused(payload: dict[str, Any]) -> None:
    gate = _gate(payload, "AC-3")
    gate["message"] = gate["message"].replace("in 'test'", "in 'validation'")
    with pytest.raises(ScoreUnavailable, match="'validation'"):
        rows(payload)


def test_row_counts_that_disagree_are_refused(payload: dict[str, Any]) -> None:
    gate = _gate(payload, "AC-3")
    gate["message"] = gate["message"].replace("254 held-out", "253 held-out")
    with pytest.raises(ScoreUnavailable, match="253"):
        rows(payload)


def test_changed_gate_wording_is_refused_not_half_parsed(payload: dict[str, Any]) -> None:
    gate = _gate(payload, "AC-3")
    gate["message"] = gate["message"].replace("Calibrated: coverage", "Calibrated coverage")
    with pytest.raises(ScoreUnavailable, match="wording changed"):
        rows(payload)


def test_a_metric_the_parser_does_not_know_is_refused(payload: dict[str, Any]) -> None:
    gate = _gate(payload, "AC-1")
    gate["message"] = gate["message"].replace("r2 0.707064", "r2 0.707064, smape 0.1")
    with pytest.raises(ScoreUnavailable, match="smape"):
        rows(payload)


def test_the_value_is_the_gates_text_not_a_rounded_float(payload: dict[str, Any]) -> None:
    # "+0.037355" and "0.000000" survive as written; a float round-trip would print "0.037355" and "0.0".
    published = {row.quantity: row.value for row in rows(copy.deepcopy(payload))}
    assert published["conformal_correction"] == "+0.037355"
    assert published["crossings"] == "0.000000"


def test_no_argument_prints_the_table(payload: dict[str, Any]) -> None:
    out = io.StringIO()
    assert artifact_score.main([], out=out) == 0
    assert out.getvalue() == table(payload)


def test_the_committed_record_is_the_promoted_manifests(payload: dict[str, Any]) -> None:
    store = repo_root() / "artifacts"
    if not (store / "current.json").is_file():
        pytest.skip(
            "artifacts/ is gitignored, so this check runs only where the promoted version "
            "lives. CI verifies the table against the record, not the record against the model."
        )
    assert artifact_score.record(store=store) == payload, (
        "reports/model/artifact-gates.json no longer matches the promoted manifest. A new "
        "version was promoted: run `python -m hydms.evidence.artifact_score --probe --emit`."
    )
