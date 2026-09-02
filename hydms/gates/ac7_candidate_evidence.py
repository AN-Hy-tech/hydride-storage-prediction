"""AC-7 -- no candidate is published without both an ElMD distance and an interval width.

PRD section 10.7. A candidate list without those two columns cannot be read honestly: there
is no way to tell an interpolation from an extrapolation, or a confident prediction from a
wide one, and the reader will assume the flattering reading.

**Frozen.** Candidate lists are inverse design; see ``docs/FREEZE.md``. Registered here so
the registry stays the complete list of what this project has promised to check.

Owned by card #57, on the frozen board.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-7",
    title="Every candidate reports its ElMD distance and its interval width",
    card=57,
    speed=Speed.SLOW,
    blocked_by=(55,),
    reason="frozen with Phase A -- this phase publishes no candidate list (docs/FREEZE.md)",
)
