"""HG-1 -- every named leak has a sentinel, and every sentinel is green.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when any leak in the inventory could
be reintroduced without a test going red. Removing the thirteen leaks is stages S2 to S4;
*keeping* them removed is this gate, and it is what makes the phase durable rather than a
one-time cleanup.

Card #71 will implement it as the ``tests/leaks/`` suite, selected by the ``leak`` marker.
Two properties matter more than the count: a sentinel must pass **only** because its leak is
absent, and each must have been seen red with the leak deliberately put back. A sentinel
nobody has watched fail is an assumption with a test's name on it.

Owned by card #71 -- unblocked by this card.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="HG-1",
    title="One sentinel per named leak, each demonstrated red",
    card=71,
    speed=Speed.FAST,
    reason="tests/leaks/ is card #71, whose only remaining blocker was this harness",
)
