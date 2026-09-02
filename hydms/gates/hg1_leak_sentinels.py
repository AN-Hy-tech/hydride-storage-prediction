"""HG-1 -- every named leak has a sentinel, and every sentinel is green.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when any leak in the inventory could be
reintroduced without a test going red. Removing the thirteen leaks is stages S2 to S4;
*keeping* them removed is this gate, and it is what makes the phase durable rather than a
one-time cleanup.

The evidence is :func:`hydms.qa.audit`, which places each leak in one of six states. This
module does nothing but read those rows and decide, and the decision has three parts:

  - **Red** on ``broken``, ``unwired`` or ``uncovered``. The first means a detector stopped
    detecting its leak -- someone weakened an assertion, and the guard is now decoration. The
    second means the module a sentinel was written for has been created and nobody pointed the
    sentinel at it, which is how a suite of green tests ends up guarding nothing. The third
    means a leak in section 1 has neither a sentinel nor a recorded deferral.
  - **Green** only when every leak is checked against the real pipeline. Not when the
    miniatures pass: a reproduction going red proves the *detector* works, which is a
    different claim from "the pipeline is clean".
  - **Skipped** in between, naming what is still owed. ``docs/QA-PROTOCOL.md`` section 5: a
    skip is not a mild pass, and the harness prints it as loudly as a failure.

So HG-1 is red today for exactly one reason at a time and green only at the end of S4 -- which
is why ``docs/FREEZE.md`` can list it in the unfreeze condition and mean something by it. What
it *does* check from today is the part that can rot without anyone noticing: that every
sentinel still fires on the defect it was written for.

Card #71.
"""

from __future__ import annotations

from dataclasses import dataclass

from hydms.config import Config
from hydms.qa import audit
from hydms.qa.sentinels import SentinelReport

from ._core import Gate, GateResult, Speed, Status

__all__ = ["GATE"]


def _lines(rows: tuple[SentinelReport, ...], *, states: tuple[str, ...]) -> list[str]:
    return [f"  {r.leak} [{r.status}] #{r.owed_by} -- {r.detail}" for r in rows if r.status in states]


@dataclass(frozen=True)
class LeakSentinels:
    """The gate. Holds no state: every fact it reports comes from ``hydms.qa.audit()``."""

    name: str = "HG-1"
    title: str = "One sentinel per named leak, each demonstrated red"
    card: int = 71
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        rows = audit()
        total = len(rows)
        guarded = sum(1 for row in rows if row.status == "green")
        measured = f"{guarded}/{total} leaks guarded in the pipeline"
        threshold = f"{total}/{total}"

        red = [row for row in rows if not row.ok]
        if red:
            detail = "\n".join(_lines(rows, states=("broken", "unwired", "uncovered")))
            return GateResult.fail(
                self.name,
                f"{len(red)} of {total} leaks could be reintroduced without a test going "
                f"red:\n{detail}",
                measured=measured,
                threshold=threshold,
            )

        if guarded == total:
            return GateResult.ok(
                self.name,
                f"all {total} leaks are guarded against the real pipeline, and every sentinel "
                f"still goes red on the defect it was written for",
                measured=measured,
                threshold=threshold,
            )

        owing = sorted({row.owed_by for row in rows if row.status != "green"})
        detail = "\n".join(_lines(rows, states=("pending", "deferred")))
        return GateResult(
            self.name,
            Status.SKIPPED,
            f"{guarded} of {total} leaks are guarded against the real pipeline. The "
            f"sentinels for the rest are written and still go red on their miniatures, but "
            f"the modules they guard do not exist yet -- cards "
            f"{', '.join(f'#{card}' for card in owing)}:\n{detail}",
            measured=measured,
            threshold=threshold,
        )


GATE: Gate = LeakSentinels()
