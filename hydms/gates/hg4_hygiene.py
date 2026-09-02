"""HG-4 -- ruff, mypy and the coverage floor hold on ``hydms/``.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when ruff, mypy, or the coverage floor
fail on the package.

The three tools are configured in ``pyproject.toml`` and are **deliberately outside the
Project conda environment**: they need no scientific stack, and card #68 established that the
fast lane installs nothing and builds no environment. Card #86 wires them into CI in that
conda-free lane; this gate is how a local run asks the same question CI will ask.

The coverage floor is a ratchet rather than a target. Lowering it to make a build pass is a
review conversation, and the reason goes in the card's narrative
(``docs/QA-PROTOCOL.md`` section 5).

Owned by card #86.
"""

from __future__ import annotations

from ._core import Gate, Pending, Speed

GATE: Gate = Pending(
    name="HG-4",
    title="Hygiene: ruff, mypy and the coverage floor on hydms/",
    card=86,
    speed=Speed.FAST,
    blocked_by=(6, 79),
    reason="the CI lanes it reports on are cards #6 and #79",
)
