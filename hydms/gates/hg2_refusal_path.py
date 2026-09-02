"""HG-2 -- no prediction path returns a bare number.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when any prediction path returns a
point estimate without an interval **and** a domain verdict.

It is the card the whole phase exists for. A tree ensemble extrapolates as a constant, so
outside the training hull the model returns a plausible flat number rather than an obvious
failure (risk R1) -- the interval and the domain verdict are what make that visible, and a
refusal with a stated reason is what makes it unmissable. "Contains Tc, which appears in no
training alloy" tells a user what to do next; "cannot predict" only sends them away.

The guarantee is meant to be structural: the result type cannot be constructed without both
fields (card #75), and this gate checks that no path evades it.

Owned by card #77.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="HG-2",
    title="Never a bare number: every answer carries an interval and a domain verdict",
    card=77,
    speed=Speed.FAST,
    blocked_by=(76,),
    reason="needs predict_capacity() over an artifact bundle (#76)",
)
