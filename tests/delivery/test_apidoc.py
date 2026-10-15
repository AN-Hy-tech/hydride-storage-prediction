"""The API reference: that it is generated, that it is current, and that it has no gaps.

Card #80's boxes. The page's *argument* cannot be asserted -- it is prose, and card #90 already
established that every rule statable about a reason's shape passes on a sentence written for a
different defect. So nothing here pretends to test whether the document is persuasive. What is
tested is everything around it:

  - the committed ``docs/API.md`` is byte-for-byte what the code produces, which is what makes a
    number that has gone stale a diff line rather than a discovery;
  - every declared reason code has advice, and no advice exists for a code nothing declares --
    both directions, because a caller meeting an undocumented refusal is exactly the misuse the
    page exists to prevent;
  - every endpoint in the committed OpenAPI document appears on the page with a real exchange,
    so a route added without an example fails here rather than shipping undocumented;
  - the captured examples name a real artifact version, so a page whose numbers came from
    nowhere cannot be published.

**None of this needs an artifact**, and that is deliberate rather than incidental.
``artifacts/`` is gitignored, so a test that loaded a model would skip on every CI runner and
on every fresh clone -- an unchecked guarantee wearing a green tick. The generator is split for
exactly this reason: ``--probe`` needs the fit and is a maintainer's command, ``--emit`` needs
only the committed fixture, and this file exercises the second half.

Card #80.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest import mock

import pytest

pytest.importorskip("pandas", reason="delivery_screens() is pandas code")

from hydms.delivery import apidoc  # noqa: E402
from hydms.delivery.api.openapi import SNAPSHOT_FILE  # noqa: E402
from hydms.delivery.apidoc import (  # noqa: E402 -- after the pandas guard
    ADVICE,
    DOCUMENT,
    EXAMPLES_FILE,
    EXAMPLES_SCHEMA,
    SECTIONS,
    ApiDocError,
    document,
    drift,
    examples,
)
from hydms.delivery.contract import reason_codes  # noqa: E402


def test_the_committed_page_is_what_the_code_produces() -> None:
    """The whole point of generating it. A stale number must land on a diff line.

    If this fails, do not edit ``docs/API.md``: run
    ``python -m hydms.delivery.apidoc --emit`` and read the diff.
    """
    assert drift() == [], "\n".join(drift())


def test_the_page_exists_and_says_it_is_generated() -> None:
    """A reader who opens the file must be told not to edit it, before anything else."""
    assert DOCUMENT.exists(), f"{DOCUMENT} is missing; run --emit"
    head = DOCUMENT.read_text(encoding="utf-8").splitlines()[:4]
    assert any("Do not edit" in line for line in head)
    assert any("hydms.delivery.apidoc" in line for line in head)


def test_every_declared_code_has_advice_and_no_advice_is_invented() -> None:
    """Both directions. The first is the one that matters to a caller.

    A declared code with no advice is a refusal somebody can receive and find nothing written
    about. Advice for a code nothing declares is this page describing a system that does not
    exist -- harmless to a caller and a lie to a maintainer, so it fails too.
    """
    declared = set(reason_codes())
    assert declared - set(ADVICE) == set(), "declared reason codes with no advice on the page"
    assert set(ADVICE) - declared == set(), "advice for codes no screen declares"


def test_every_published_route_has_a_worked_example() -> None:
    """A route added to the service without an example fails here, not in review."""
    spec = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    published = {
        (method.upper(), path)
        for path, operations in spec["paths"].items()
        for method in operations
    }
    exchanges = examples()["exchanges"]
    shown = {(exchanges[label]["method"], exchanges[label]["path"]) for label, _ in SECTIONS}
    assert published - shown == set(), "endpoints with no request/response example on the page"


def test_the_examples_name_the_version_that_produced_them() -> None:
    """A number with no run behind it is not evidence, and the page says so in its header."""
    data = examples()
    assert data["schema"] == EXAMPLES_SCHEMA
    assert data["model_version"], "the capture names no artifact version"
    assert data["probed_at"], "the capture is undated"
    assert data["model_version"] in DOCUMENT.read_text(encoding="utf-8")


def test_every_exchange_is_a_real_response_with_a_status() -> None:
    """No hand-written 'illustrative' payloads: each carries the status the service returned."""
    for label, _ in SECTIONS:
        exchange = examples()["exchanges"][label]
        assert exchange["status"] in {200, 422}, f"{label} carries status {exchange['status']}"
        assert isinstance(exchange["response"], dict), f"{label} has no response body"


def test_a_refusal_example_carries_no_capacity_key() -> None:
    """The page's central claim, asserted against the captured bodies rather than restated.

    'A refusal has no field a number could hide in' is the sentence a caller is asked to rely
    on. It is checked here so that a contract change which added ``capacity`` to a refusal
    would fail rather than quietly making the page's first section false.
    """
    exchanges = examples()["exchanges"]
    refusals = [
        body
        for body in (exchange["response"] for exchange in exchanges.values())
        if body.get("refused") is True
    ]
    assert refusals, "no refusal among the captured examples; the page's main point is unshown"
    for body in refusals:
        assert "capacity" not in body
        assert "interval" not in body
        assert body["code"] in set(reason_codes())

    answers = [
        body
        for body in (exchange["response"] for exchange in exchanges.values())
        if body.get("refused") is False
    ]
    assert answers, "no admitted answer among the captured examples"
    for body in answers:
        assert "capacity" in body and "interval" in body and "domain" in body


def test_a_missing_example_refuses_to_publish() -> None:
    """A capture that lost a section fails loudly rather than emitting an empty heading."""
    data = examples()
    short = {**data, "exchanges": {k: v for k, v in data["exchanges"].items() if k != "health"}}
    with pytest.raises(ApiDocError, match="missing"):
        document(short)


def test_the_fixture_is_committed_and_readable() -> None:
    """``--emit`` must work in a checkout with no model; the fixture is how."""
    assert EXAMPLES_FILE.exists(), f"{EXAMPLES_FILE} is missing; run --probe on a fitted machine"
    assert json.loads(EXAMPLES_FILE.read_text(encoding="utf-8"))["schema"] == EXAMPLES_SCHEMA


# --------------------------------------------------------------------------------------
# The failure paths.
#
# Every one of these runs with no artifact, and each exists because the sentence it checks is
# a *fix instruction*: "run --probe", "run --emit", "run openapi --emit". This repository has
# already been bitten by a guard that learned a new failure mode and kept its old reason
# (#90), so the wording is probed rather than assumed to follow the code.
# --------------------------------------------------------------------------------------


def test_an_absent_fixture_names_the_command_that_makes_one(tmp_path: Path) -> None:
    """The only step that needs a fit is the one the message must name."""
    with pytest.raises(ApiDocError) as caught:
        examples(tmp_path / "nothing.json")
    message = str(caught.value)
    assert "--probe" in message
    assert "needs one" in message, "the message must say the artifact is only needed here"


def test_an_unreadable_fixture_says_so_rather_than_raising_json_noise(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(ApiDocError, match="not readable JSON"):
        examples(broken)


def test_a_fixture_under_an_unknown_schema_is_refused_not_guessed_at(tmp_path: Path) -> None:
    """The convention the whole project uses: meet an unknown schema, say so."""
    alien = tmp_path / "alien.json"
    alien.write_text(json.dumps({"schema": "something/else"}), encoding="utf-8")
    with pytest.raises(ApiDocError) as caught:
        examples(alien)
    assert EXAMPLES_SCHEMA in str(caught.value)
    assert "hand-editing" in str(caught.value), "it must say re-probe, not edit"


def test_advice_for_a_code_nothing_declares_refuses_to_publish() -> None:
    """The guard in `document()`, not just the standing assertion about ADVICE.

    Checked by publishing with a *narrowed* vocabulary rather than by adding a fake code: the
    contract derives the vocabulary from the screens and would refuse an invented one a
    construction earlier, so the reachable way to make the two disagree is to take one away.
    """
    real = set(reason_codes())
    assert "admitted" in real
    narrowed = {code: "..." for code in real - {"admitted"}}
    with (
        mock.patch.object(apidoc, "ADVICE", narrowed),
        pytest.raises(ApiDocError) as caught,
    ):
        document(examples())
    assert "admitted" in str(caught.value)
    assert "--emit" not in str(caught.value), "this one is not fixed by regenerating"


def test_drift_reports_the_first_differing_line_and_the_fix(tmp_path: Path) -> None:
    """A stale page must say *where* it went stale, and what to run."""
    page = DOCUMENT.read_text(encoding="utf-8")
    lines = page.splitlines()
    lines[0] = "# Something Else Entirely"
    differences = drift("\n".join(lines) + "\n")
    assert differences, "a changed first line must be reported"
    assert "line 1" in differences[0]
    assert any("--emit" in line for line in differences)


def test_drift_reports_a_length_difference_when_no_line_differs() -> None:
    """A page truncated at the end differs from the code without any line disagreeing."""
    page = DOCUMENT.read_text(encoding="utf-8")
    truncated = "\n".join(page.splitlines()[:-5]) + "\n"
    differences = drift(truncated)
    assert differences
    assert "line(s)" in differences[0]
    assert "--emit" in differences[0]


def test_drift_is_empty_against_the_page_the_code_produces() -> None:
    """The positive case, spelled separately so a broken comparator cannot pass by accident."""
    assert drift(DOCUMENT.read_text(encoding="utf-8")) == []


def test_the_check_command_exits_zero_and_says_what_it_checked() -> None:
    """`python -m hydms.delivery.apidoc` with no flags is the CI check."""
    stream = io.StringIO()
    assert apidoc.main([], out=stream) == 0
    said = stream.getvalue()
    assert "is current" in said
    assert examples()["model_version"] in said


def test_the_check_command_exits_non_zero_on_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-zero is the whole of what CI reads, so it is asserted rather than assumed."""
    monkeypatch.setattr(apidoc, "document", lambda *a, **k: "# not the committed page\n")
    stream = io.StringIO()
    assert apidoc.main([], out=stream) == 1
    assert "--emit" in stream.getvalue()


def test_an_over_long_batch_request_is_shortened_and_says_that_it_was() -> None:
    """A reader must be able to tell a shortened example from a short one."""
    rendered = document(examples())
    exchange = examples()["exchanges"]["batch-too-large"]
    sent = exchange["candidates_total"]
    assert sent > 3, "the fixture no longer carries an over-long batch"
    assert len(exchange["request"]["candidates"]) <= 3, "stored shortened, count beside it"
    assert "Shortened for reading" in rendered
    assert f"**{sent}** candidates" in rendered
    assert f"this request carries {sent} candidates" in exchange["response"]["message"], (
        "the recorded count must be the one the service saw"
    )

