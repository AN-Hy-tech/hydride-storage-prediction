"""AC-1 -- the same seed reproduces identical metrics.

PRD section 10.1: the pipeline runs end to end from the raw data with one command, with no
absolute paths, and re-running with the same seed reproduces identical metrics.

Slow lane: establishing it means running the pipeline twice. Card #32 also fixes what is
compared -- the metrics table, not model file bytes, which may legitimately differ.

Owned by card #32.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-1",
    title="Same seed reproduces identical metrics",
    card=32,
    speed=Speed.SLOW,
    blocked_by=(26,),
    reason="needs a trainable pipeline end to end, which begins at the surrogate (#26)",
)
