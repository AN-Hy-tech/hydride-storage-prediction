"""HG-3 -- the API's answer equals the library's answer.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when the API's answer differs from
``predict_capacity()``'s for the same input.

AC-4 checks that known alloys round-trip through the library. It says nothing about the
transport boundary, where a float can be truncated by serialisation, a column reordered by a
dict round trip, and an interval dropped by a response model that forgot a field. This gate
extends AC-4 to the edge of the system, and snapshots the OpenAPI document so a breaking
contract change is a visible diff rather than a surprise for whoever wrote a client.

It covers the Streamlit app too, because the app is an HTTP client rather than an in-process
caller -- which is exactly why it was built that way.

Owned by card #79.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="HG-3",
    title="Transport parity: the API's answer equals predict_capacity()'s",
    card=79,
    speed=Speed.FAST,
    blocked_by=(78,),
    reason="needs the FastAPI service from card #78",
)
