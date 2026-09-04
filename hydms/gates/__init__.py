"""L0 -- the acceptance criteria and hardening gates as runnable checks.

Owns what 'passing' means. Criteria are executed, never remembered; an unimplemented gate
reports SKIPPED and never PASSED.

The PRD fixes eight acceptance criteria before results are seen (PRD section 10) and Phase H
adds four hardening gates (``docs/PHASE-H-RUNBOOK.md`` section 4). This package turns each of
those twelve sentences into a check that exits non-zero when it does not hold.

**One module per criterion.** Each declares a module-level ``GATE`` and nothing else is
needed to register it -- the registry scans this directory, so a criterion exists because a
file exists, not because something remembered to import it. Until the card that owns a
criterion lands, its module declares a :class:`~hydms.gates._core.Pending` gate, whose only
possible answer is SKIPPED.

Usage::

    python -m hydms.gates list             # what is promised, and who owes it
    python -m hydms.gates run --all        # every registered gate
    python -m hydms.gates run --fast       # the per-push lane (card #6)
    python -m hydms.gates run AC-2 HG-1    # named gates; a skip here is a failure

From Python::

    from hydms.config import load
    from hydms.gates import registry, run, select

    report = run(select(["HG-2"]), load(), strict=True)
    report.ok          # False while HG-2 is unimplemented -- you asked and got no answer

**Writing a gate.** Replace the ``Pending`` in the criterion's module with an object
carrying ``name``, ``title``, ``card``, ``speed`` and ``check(cfg) -> GateResult``. Return
``GateResult.fail(...)`` with ``measured`` and ``threshold`` filled in -- every gate card on
the board asks for the measured value rather than a boolean, because a red build that does
not say how far off costs the next person the run again. Then make it red on purpose and
record that you did, in the card's ``## Narrative``: ``docs/QA-PROTOCOL.md`` section 5 has
no exception for gates that "obviously" work.

Card #5.
"""

from ._core import (
    Gate,
    GateReport,
    GateResult,
    Pending,
    Speed,
    Status,
    UnknownGate,
    registry,
    run,
    select,
)
from ._report import render_registry, render_report, write_report

__all__ = [
    "Gate",
    "GateReport",
    "GateResult",
    "Pending",
    "Speed",
    "Status",
    "UnknownGate",
    "registry",
    "render_registry",
    "render_report",
    "run",
    "select",
    "write_report",
]
