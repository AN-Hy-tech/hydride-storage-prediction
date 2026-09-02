"""AC-6 -- leave-one-alloy-class-out R2 is reported beside the random-split number.

PRD section 10.6, and the single most important validation number in the thesis: hydride
models are accurate within a family and poor across families, so the random-split score
measures interpolation and says little about the extrapolation the inverse design needs.

Expect it to be substantially worse, and report it anyway. This gate checks that it is
reported at all -- not that it clears a bar.

Slow lane: one refit per alloy class. It was blocked for a structural reason, not a
scheduling one -- ``extract_features_cbfv.py`` destroys ``Alloy_class`` (leak L13), so the
grouping this gate needs did not survive the archival pipeline.

Owned by card #30.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-6",
    title="Leave-one-alloy-class-out R2 reported beside the random split",
    card=30,
    speed=Speed.SLOW,
    blocked_by=(12, 28),
    reason="needs Alloy_class re-joined on the canonical key (#12, via #87) and predict() (#28)",
)
