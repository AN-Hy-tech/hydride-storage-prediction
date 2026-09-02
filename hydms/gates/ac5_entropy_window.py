"""AC-5 -- predicted entropy clusters near -130 J/(mol H2 K).

PRD section 10.5. The cheapest physics check in the project: entropy of hydride formation is
dominated by the loss of gas-phase H2 entropy and sits near -130 across systems, so a model
that misses it has a target-column or a sign-convention error no metric would reveal.

**Frozen.** Its card lives on the frozen board with the rest of the thermodynamics work; see
``docs/FREEZE.md``. It is registered here so the registry is the complete list of what this
project has promised to check, and so its absence from a run is stated rather than assumed.

Owned by card #41, on the frozen board.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="AC-5",
    title="Predicted entropy clusters near -130 J/(mol H2 K)",
    card=41,
    speed=Speed.FAST,
    blocked_by=(40,),
    reason="frozen with Phase T -- there is no entropy model in this phase (docs/FREEZE.md)",
)
