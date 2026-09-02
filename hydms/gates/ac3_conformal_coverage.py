"""AC-3 -- conformal interval coverage matches its nominal level.

PRD section 10.3: empirical coverage on the held-out test set is within a few points of
nominal. The nominal level is ``conformal.confidence_level`` in the pipeline config, so this
gate reads its own threshold from the same place the calibrator does.

It is the load-bearing check for risk R1: ranking uses the lower confidence bound, and a
bound whose coverage is unverified makes every ranked list downstream meaningless.

Owned by card #31.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-3",
    title="Conformal coverage matches nominal",
    card=31,
    speed=Speed.FAST,
    blocked_by=(27,),
    reason="needs the MAPIE-calibrated surrogate from card #27",
)
