"""The committed contract, and the comparator gate HG-3 reads it with.

Card #79. The snapshot is a *generated* file: ``python -m hydms.delivery.api.openapi --emit``
writes it, and the first test here asserts the committed bytes are what that command produces.
That is the same rule ``docs/REFUSALS.md``, the two screen reference JSONs and the smoke fixture
live under -- a hand-edit fails the suite, because a contract somebody edited by hand is no
longer a record of what the service serves.

The rest is the comparator. HG-3 uses :func:`~hydms.delivery.api.openapi.differences` twice --
once on the document, once on every served answer against the library's -- so a comparison that
quietly returned nothing would take the gate's whole parity claim with it. It is therefore
tested on a difference of each kind: a value that changed, a key that appeared, and a key that
went away.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="the `api` extra: pip install -e '.[api]'")

from hydms.delivery.api import openapi  # noqa: E402
from hydms.delivery.contract import SCHEMA  # noqa: E402


def test_the_committed_openapi_document_is_what_the_code_produces() -> None:
    """Generated, never edited. Regenerate with `--emit` and commit the diff deliberately.

    Named `openapi` rather than `document` because `tests/surrogate/test_loco.py` already owns
    the short name for *its* generated file, and `docs/PHASE-H-RUNBOOK.md` §5 names that test in
    prose. Two tests under one name would make that sentence ambiguous the day one of them fails.
    """
    assert openapi.SNAPSHOT_FILE.read_text(encoding="utf-8") == openapi.serialise(
        openapi.document()
    )


def test_the_document_describes_the_four_routes_and_declares_its_schema_version() -> None:
    doc = openapi.document()

    assert sorted(doc["paths"]) == [
        "/v1/health",
        "/v1/model",
        "/v1/predict",
        "/v1/predict/batch",
    ]
    assert doc["info"]["version"] == SCHEMA


def test_an_answer_and_a_refusal_are_told_apart_by_one_documented_key() -> None:
    """The discriminator is in the document, so a client is not left to infer it from fields."""
    responses = openapi.document()["paths"]["/v1/predict"]["post"]["responses"]
    ok = responses["200"]["content"]["application/json"]["schema"]

    assert ok["discriminator"]["propertyName"] == "refused"
    assert "422" in responses


def test_emit_writes_the_document_and_leaves_nothing_to_compare(
    monkeypatch, tmp_path: Path
) -> None:
    snapshot = tmp_path / "openapi.json"
    monkeypatch.setattr(openapi, "SNAPSHOT_FILE", snapshot)

    assert openapi.emit() == snapshot
    assert openapi.drift() == []
    assert json.loads(snapshot.read_text(encoding="utf-8")) == openapi.document()


def test_a_stale_snapshot_is_reported_by_pointer_and_exits_non_zero(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    stale = openapi.document()
    stale["info"]["title"] = "Something else"
    snapshot = tmp_path / "openapi.json"
    snapshot.write_text(openapi.serialise(stale), encoding="utf-8")
    monkeypatch.setattr(openapi, "SNAPSHOT_FILE", snapshot)

    assert openapi.main([]) == 1
    printed = capsys.readouterr().out
    assert "/info/title" in printed
    assert "Something else" in printed


def test_an_absent_snapshot_exits_non_zero_and_names_the_command(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    """A missing contract is a failure, never an absent check."""
    monkeypatch.setattr(openapi, "SNAPSHOT_FILE", tmp_path / "nothing.json")

    assert openapi.main([]) == 1
    assert "--emit" in capsys.readouterr().out


def test_a_current_snapshot_exits_zero_and_says_so(capsys) -> None:
    assert openapi.main([]) == 0
    assert "is current" in capsys.readouterr().out


def test_emit_through_the_command_line_rewrites_the_file(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    snapshot = tmp_path / "openapi.json"
    monkeypatch.setattr(openapi, "SNAPSHOT_FILE", snapshot)

    assert openapi.main(["--emit"]) == 0
    assert snapshot.is_file()
    assert "wrote" in capsys.readouterr().out


# --------------------------------------------------------------------------------------
# The comparator, which HG-3 uses on answers as well as on documents
# --------------------------------------------------------------------------------------


def test_equal_documents_have_no_differences() -> None:
    doc = openapi.document()

    assert openapi.differences(doc, json.loads(json.dumps(doc))) == []


def test_a_changed_value_is_named_by_its_pointer_with_both_sides() -> None:
    found = openapi.differences(
        {"interval": {"lower": 1.2345678901234}},
        {"interval": {"lower": 1.23}},
        left_name="the library",
        right_name="served",
    )

    assert len(found) == 1
    assert found[0].startswith("/interval/lower: the library 1.2345678901234, served 1.23")


def test_a_key_that_appeared_and_a_key_that_went_away_are_both_reported() -> None:
    """A response model that forgot a field is the second; one that invented one is the first."""
    found = openapi.differences({"capacity": 1.0, "interval": {}}, {"capacity": 1.0, "novelty": 1})

    assert any("/interval: in committed" in line and "absent from produced" in line for line in found)
    assert any("/novelty: in produced" in line and "absent from committed" in line for line in found)


def test_a_key_whose_value_is_empty_is_still_compared() -> None:
    """An empty container is a leaf, or a dropped `screens: []` would compare equal to nothing.

    Found by the test above: recursing into `{}` emits no pointers at all, so the key vanished
    from both sides of the comparison and the difference was reported as no difference.
    """
    (gone,) = openapi.differences({"capacity": 1.0, "screens": []}, {"capacity": 1.0})
    (added,) = openapi.differences({"capacity": 1.0}, {"capacity": 1.0, "domain": {}})

    assert gone.startswith("/screens: in committed ([])")
    assert added.startswith("/domain: in produced ({})")


def test_a_slash_in_a_key_is_escaped_so_the_pointer_stays_readable() -> None:
    (found,) = openapi.differences({"paths": {"/v1/predict": 1}}, {"paths": {"/v1/predict": 2}})

    assert found.startswith("/paths/~1v1~1predict: ")


def test_list_positions_are_part_of_the_pointer() -> None:
    (found,) = openapi.differences({"screens": ["window", "domain"]}, {"screens": ["window", "novelty"]})

    assert found.startswith("/screens/1: ")


def test_a_long_value_is_truncated_rather_than_printed_whole() -> None:
    """A diff that prints two 4 kB schema objects in full is a diff nobody reads to the end."""
    (found,) = openapi.differences({"description": "x" * 500}, {"description": "y" * 500})

    assert "..." in found
    assert len(found) < 300
