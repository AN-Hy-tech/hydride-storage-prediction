"""AC-8 -- at least half the top 20 candidates sit inside the guard rails.

PRD section 10.8: half of the top 20 must fall inside the applicability-domain ceiling and
inside the family-specific VEC window. If fewer do, the guard rails are too weak -- tighten
and re-run. It is a criterion about the *screens*, not about the candidates.

**Frozen.** See ``docs/FREEZE.md``. Registered so the registry stays complete.

Owned by card #56, on the frozen board.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-8",
    title="At least half the top 20 sit inside the AD ceiling and the VEC window",
    card=56,
    speed=Speed.SLOW,
    blocked_by=(55,),
    reason="frozen with Phase A -- this phase runs no search (docs/FREEZE.md)",
)
