"""AC-2 -- the reimplemented featuriser matches CBFV to 1e-9 on all 1,279 formulae.

PRD section 10.2. This is the hard gate of stage S3: if it fails, the reimplementation is
wrong, not CBFV. Card #21 additionally requires the failure output to name the offending
column and formula, because a boolean here sends the reader back to re-run 1,279 rows by
hand to find out which one moved.

The comparison needs CBFV, which is unlicensed and installed only through the ``parity``
extra -- it is the thing being replaced and must never become a runtime dependency.

Owned by card #21.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-2",
    title="Featuriser parity with CBFV to 1e-9",
    card=21,
    speed=Speed.FAST,
    reason=(
        "hydms.descriptors.featurize() landed with card #20 and takes the reference table as "
        "an argument; the comparison over all 1,279 formulae is #21's own work"
    ),
)
