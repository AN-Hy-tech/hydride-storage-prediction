"""AC-4 -- known training alloys round-trip through the screening path.

PRD section 10.4: ten known training alloys fed through the screening path reproduce the
trained model's predictions on those same rows.

It exists for two silent failures that raise no error on their own -- a refit scaler and a
reordered feature matrix. Both produce numbers, and both produce the wrong ones.

Owned by card #33.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-4",
    title="Known alloys round-trip through predict()",
    card=33,
    speed=Speed.FAST,
    blocked_by=(28,),
    reason="needs the surrogate's public predict() from card #28",
)
