"""The coverage half of gate HG-1: is anything in the inventory unguarded?

The per-leak files beside this one answer "does this sentinel work". They cannot answer "is
there a sentinel for every leak", and that is the question HG-1 actually asks -- its failure
condition is *any leak in section 1 can be reintroduced without a test going red*, which is a
statement about the set, not about any member of it.

So this file checks the seams a green suite would otherwise hide:

  - the inventory in ``hydms/qa/leaks.py`` still matches the runbook's section 1 table,
  - every leak has a sentinel or a **recorded** deferral, and the card owing each one says so
    in its own text, where whoever works that card will actually read it,
  - every reproduction still goes red, and its corrected twin still goes green -- the
    executable form of "shown red when its leak is reintroduced", run on every build rather
    than done once by hand and remembered,
  - a sentinel whose subject module has appeared but which nobody has wired to it is a
    **failure**, not pending work.

Card #71.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
from hydms.config import Config, load
from hydms.gates import Status, run, select
from hydms.qa import DEFERRED, INVENTORY, SENTINELS, LeakDetected, audit
from hydms.qa.sentinels import Reproduction, Sentinel

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNBOOK = REPO_ROOT / "docs" / "PHASE-H-RUNBOOK.md"
BOARDS = ("kanban", "kanban-hardening")

# `| **L1** | `Catboostmodel.py:604-606` — ... | ... |`
_ROW = re.compile(r"^\|\s*\*\*(L\d+)\*\*\s*\|(.*)$", re.MULTILINE)


@pytest.fixture(scope="module")
def runbook_rows() -> dict[str, str]:
    rows = dict(_ROW.findall(RUNBOOK.read_text(encoding="utf-8")))
    assert rows, f"no leak table found in {RUNBOOK}"
    return rows


@pytest.fixture(scope="module")
def cards() -> dict[int, Path]:
    return {
        int(path.name[:3]): path
        for board in BOARDS
        for path in (REPO_ROOT / board).glob("[0-9][0-9][0-9]-*.md")
    }


@pytest.fixture(scope="module")
def cfg() -> Config:
    return load()


def _names_the_sentinel(card: Path, leak: str) -> bool:
    """Whether a card names this leak's sentinel, as opposed to merely containing its id.

    The bare id is not enough: every L1-layer card's header reads `**L1 Data**`, and `L1` is a
    substring of `L12`. The phrase "L9 sentinel" collides with neither.
    """
    return re.search(rf"\b{leak} sentinel\b", card.read_text(encoding="utf-8")) is not None


# --------------------------------------------------------------------------------------
# The inventory against the prose that owns it
# --------------------------------------------------------------------------------------


def test_the_inventory_matches_the_runbooks_leak_table(runbook_rows: dict[str, str]) -> None:
    """Thirteen. The PRD names three; the Phase H audit found ten more."""
    assert {leak.id for leak in INVENTORY} == set(runbook_rows)
    assert len(INVENTORY) == 13


def test_every_leak_names_the_site_the_runbook_gives_it(runbook_rows: dict[str, str]) -> None:
    """`docs/QA-PROTOCOL.md` section 2, L7: a number in prose traces to something that holds it.

    A site that has drifted is worse than no site: it sends the next reader to the wrong lines
    of an archival file they are not allowed to edit.
    """
    for leak in INVENTORY:
        assert leak.site in runbook_rows[leak.id], (
            f"{leak.id} is recorded at {leak.site}, which does not appear in the runbook's "
            f"row for it: {runbook_rows[leak.id].strip()}"
        )


def test_every_leak_is_closed_by_a_card_that_exists(cards: dict[int, Path]) -> None:
    for leak in INVENTORY:
        assert leak.closed_by in cards, (
            f"{leak.id} says card #{leak.closed_by} closes it, and no such card is on either "
            f"board. A leak owned by nobody is a leak nobody removes."
        )


# --------------------------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------------------------


def test_every_leak_has_a_sentinel_or_a_recorded_deferral() -> None:
    covered = {sentinel.leak for sentinel in SENTINELS}
    deferred = {entry.leak for entry in DEFERRED}
    assert not covered & deferred, "a leak cannot be both guarded and deferred"

    uncovered = {leak.id for leak in INVENTORY} - covered - deferred
    assert not uncovered, (
        f"{sorted(uncovered)} appear in the runbook's inventory with neither a sentinel nor a "
        f"deferral. Add one to hydms/qa/sentinels.py, or record who owes it and why."
    )


def test_each_sentinel_guards_a_leak_that_exists_exactly_once() -> None:
    guarded = [sentinel.leak for sentinel in SENTINELS]
    assert len(guarded) == len(set(guarded)), "two sentinels claim the same leak"
    known = {leak.id for leak in INVENTORY}
    assert set(guarded) <= known, f"sentinel(s) for unknown leak(s): {set(guarded) - known}"


def test_each_deferral_is_owed_by_a_card_whose_text_says_so(cards: dict[int, Path]) -> None:
    """A deferral recorded only in code is a deferral the owning card never hears about.

    A deferred leak is one whose sentinel cannot be written yet, and each one is a
    `## Done when` box on the card that will be able to write it. This is what turns "someone
    will remember" into work that has a place on the board. The count is deliberately not
    asserted here -- it falls as cards land, and a number in this docstring would be one more
    thing to update: card #26 wrote L12's and left L11 owed to #29.
    """
    for entry in DEFERRED:
        assert entry.owed_by in cards, f"{entry.leak} is deferred to a card that does not exist"
        assert _names_the_sentinel(cards[entry.owed_by], entry.leak), (
            f"{entry.leak} is deferred to card #{entry.owed_by}, whose text never mentions a "
            f"'{entry.leak} sentinel'. Add the box, or the deferral is only recorded where "
            f"nobody working that card will look."
        )


def test_each_sentinel_is_named_on_the_card_that_must_wire_it(cards: dict[int, Path]) -> None:
    """The `unwired` failure is only actionable if the card knows the sentinel is waiting."""
    for sentinel in SENTINELS:
        owner = next(leak.closed_by for leak in INVENTORY if leak.id == sentinel.leak)
        assert _names_the_sentinel(cards[owner], sentinel.leak), (
            f"the {sentinel.leak} sentinel expects card #{owner} to wire it to "
            f"{sentinel.subject}, and that card never mentions a '{sentinel.leak} sentinel'."
        )


def test_every_sentinel_subject_sits_under_a_package_that_exists() -> None:
    """The subject is a prediction about a module stages S2-S4 will write.

    It cannot be verified yet -- that is the point of the `unwired` state. What can be
    verified now is the parent package, which catches the failure that would otherwise stay
    invisible for weeks: a typo like `hydms.surogate.model`, whose spec lookup fails forever
    and whose sentinel therefore never notices its subject arriving.
    """
    for sentinel in SENTINELS:
        parent = sentinel.subject.rsplit(".", 1)[0]
        assert importlib.util.find_spec(parent) is not None, (
            f"the {sentinel.leak} sentinel names {sentinel.subject}, whose package {parent} "
            f"does not exist. It would never wire up."
        )


def test_every_leak_id_appears_in_this_directory() -> None:
    """One test per named leak -- asserted, rather than left to the file names looking right."""
    sources = "\n".join(
        path.read_text(encoding="utf-8") for path in Path(__file__).parent.glob("test_*.py")
    )
    for sentinel in SENTINELS:
        assert sentinel.leak in sources, f"{sentinel.leak} has a sentinel but no test names it"


# --------------------------------------------------------------------------------------
# Redness: the demonstration, run rather than remembered
# --------------------------------------------------------------------------------------


def _cases() -> list[tuple[Sentinel, Reproduction]]:
    return [(s, case) for s in SENTINELS for case in s.reproductions]


def _case_id(pair: tuple[Sentinel, Reproduction]) -> str:
    sentinel, case = pair
    return f"{sentinel.leak}-{case.label}"


@pytest.mark.parametrize("pair", _cases(), ids=_case_id)
def test_the_leaky_case_goes_red(pair: tuple[Sentinel, Reproduction]) -> None:
    """`docs/QA-PROTOCOL.md` section 1: a sentinel nobody has seen fail is an assumption."""
    sentinel, case = pair
    with pytest.raises(LeakDetected):
        case.leaky()
    assert sentinel.detector.startswith("hydms.qa.detectors.")


@pytest.mark.parametrize("pair", _cases(), ids=_case_id)
def test_the_corrected_twin_goes_green(pair: tuple[Sentinel, Reproduction]) -> None:
    """A detector that also rejects the fix is a detector nobody can satisfy."""
    _, case = pair
    case.clean()


# --------------------------------------------------------------------------------------
# The audit, and the gate that reads it
# --------------------------------------------------------------------------------------


def test_the_audit_covers_every_leak_in_order() -> None:
    assert [row.leak for row in audit()] == [leak.id for leak in INVENTORY]


def test_no_leak_is_uncovered_broken_or_unwired() -> None:
    """The three states HG-1 goes red for, asserted here so the failure names the leak.

    `unwired` is the one that fires without anyone changing this file: the moment a card
    creates the module a sentinel was written for, this test goes red until the sentinel is
    pointed at it.
    """
    red = [row for row in audit() if not row.ok]
    assert not red, "\n".join(f"{row.leak} [{row.status}] #{row.owed_by} -- {row.detail}" for row in red)


def test_every_pending_sentinel_names_the_card_that_will_wire_it() -> None:
    for row in audit():
        if row.status == "pending":
            assert f"#{row.owed_by}" in row.detail


def test_hg1_is_not_green_while_any_leak_is_unguarded(cfg: Config) -> None:
    """The gate reports the pipeline, not the miniatures.

    Ten sentinels going red on their reproductions proves the detectors work. It says nothing
    about a pipeline that has not been written, and HG-1 must not let those two claims be
    confused -- that is the whole reason `hydms/gates/` reports SKIPPED rather than PASSED for
    a criterion nobody has established.
    """
    result = run(select(["HG-1"]), cfg, selection="HG-1", strict=True).results[0]
    guarded = sum(1 for row in audit() if row.status == "green")

    if guarded == len(INVENTORY):
        assert result.status is Status.PASSED
    else:
        assert result.status is Status.SKIPPED, (
            f"HG-1 reported {result.status.value} while {len(INVENTORY) - guarded} leak(s) are "
            f"not yet guarded against the real pipeline: {result.message}"
        )
        assert result.measured == f"{guarded}/{len(INVENTORY)} leaks guarded in the pipeline"


def test_hg1_goes_red_when_a_sentinel_stops_detecting_its_leak(
    cfg: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The demonstration `docs/QA-PROTOCOL.md` section 5 requires of the gate itself.

    A sentinel is weakened -- its leaky case no longer raises, which is what happens when
    someone loosens an assertion to make a build pass. HG-1 must go red, name the leak, and say
    that it could now be reintroduced.
    """
    weakened = SENTINELS[0]
    neutered = Sentinel(
        leak=weakened.leak,
        title=weakened.title,
        detector=weakened.detector,
        subject=weakened.subject,
        reproductions=(
            Reproduction("weakened on purpose", lambda: None, lambda: None),
        ),
    )
    monkeypatch.setattr(
        "hydms.qa.sentinels.SENTINELS", (neutered, *SENTINELS[1:]), raising=True
    )

    result = run(select(["HG-1"]), cfg, selection="HG-1", strict=True).results[0]
    assert result.status is Status.FAILED
    assert weakened.leak in result.message
    assert "did not go red" in result.message
