"""Which criteria a Phase H promotion may waive, derived from the board rather than recalled.

Card #34 hit a wall: `hydms.artifacts.promote` requires every registered criterion to have
passed, and three of them belong to phases `docs/FREEZE.md` has frozen. The resolution was a
**waiver** -- named at promotion, recorded in `current.json`, never covering a failure. See
`hydms.artifacts.store`'s docstring for why it lives there and not in the manifest or the gate
harness.

The risk that mechanism carries is that "out of scope" quietly widens into "not done yet". This
file is the guard, and it is here rather than in `scripts/check_board.py` because `artifacts/` is
gitignored: a rule written against a committed `current.json` would never see one, and a
guarantee nothing checks is not a guarantee (`docs/QA-PROTOCOL.md` section 5).

So the set is *derived*, not listed. Every registered gate names the card that owes it; every
card lives in exactly one of the two board directories; a criterion is out of Phase H's reach if
and only if its card is on the frozen board. The pinned expectation below is what that
derivation currently yields, so a card crossing between boards -- or a new criterion registered
against a frozen phase -- goes red and makes somebody say so out loud.

Card #34.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_BOARD = ROOT / "kanban-hardening"
FROZEN_BOARD = ROOT / "kanban"

#: The criteria whose card is on the frozen board, and therefore the only ones a Phase H
#: promotion may waive. Each is a criterion about a deliverable this phase does not produce:
#: AC-5 an entropy model, AC-7 a candidate list, AC-8 a search. Derived below rather than
#: trusted -- this is the expected value of the derivation, not its input.
FROZEN_PHASE_CRITERIA = frozenset({"AC-5", "AC-7", "AC-8"})

_CARD_ID = re.compile(r"^(\d+)-")


def board_of(card: int) -> str:
    """Which board directory holds this card, by the id its filename carries."""
    for board in (ACTIVE_BOARD, FROZEN_BOARD):
        for path in board.rglob("*.md"):
            match = _CARD_ID.match(path.name)
            if match and int(match.group(1)) == card:
                return board.name
    return "nowhere"


@pytest.fixture(scope="module")
def owners() -> dict[str, int]:
    """Every registered criterion and the card that owes it."""
    from hydms.gates import registry

    return {gate.name: gate.card for gate in registry()}


def test_every_registered_criterion_names_a_card_that_exists(owners: dict[str, int]) -> None:
    """A criterion whose card cannot be found is one whose scope cannot be decided at all."""
    orphans = {name: card for name, card in owners.items() if board_of(card) == "nowhere"}
    assert not orphans, f"registered criteria naming no card on either board: {orphans}"


def test_the_waivable_set_is_exactly_the_criteria_a_frozen_phase_owns(
    owners: dict[str, int],
) -> None:
    """The derivation, and the pin.

    If this fails after a card moved between boards, the fix is not to edit the constant until
    it agrees. It is to decide, deliberately, whether the criterion that moved is now something
    this phase must establish -- in which case it stops being waivable and the work is owed --
    or something a later phase owns.
    """
    derived = frozenset(name for name, card in owners.items() if board_of(card) == "kanban")
    assert derived == FROZEN_PHASE_CRITERIA, (
        f"the set of criteria owned by the frozen board has changed: {sorted(derived)} against "
        f"the pinned {sorted(FROZEN_PHASE_CRITERIA)}. A criterion crossing that line changes "
        f"what a Phase H promotion is allowed to proceed without."
    )


def test_the_reachable_criteria_are_owed_by_the_active_board(owners: dict[str, int]) -> None:
    """Everything not waivable is work, and work has a card on the board being worked.

    The complement of the test above, asserted separately because it is the half that matters
    when someone reaches for `--waive` to get past a gate nobody has written yet: AC-6, HG-2,
    HG-3 and HG-4 are skipped today and every one of them is Phase H's to land.
    """
    reachable = {name for name in owners if name not in FROZEN_PHASE_CRITERIA}
    misplaced = {name: board_of(owners[name]) for name in reachable}
    assert all(board == "kanban-hardening" for board in misplaced.values()), (
        f"a criterion outside the frozen set is not owed by the active board: {misplaced}"
    )
