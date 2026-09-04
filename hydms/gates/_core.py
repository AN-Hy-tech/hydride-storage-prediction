"""Execution machinery for the gate harness: the protocol, the result, and the registry.

Nothing in here knows what any individual criterion means. That knowledge lives in one
module per criterion beside this file, which is the point: adding a gate is adding a file,
and the harness cannot be edited into agreeing with a gate that does not hold.

Three properties are load-bearing, each corresponding to a way a check regime lies:

  - **A gate that was not run never reports PASSED.** Absence of evidence is reported as
    ``SKIPPED`` and rendered as loudly as a failure. ``docs/QA-PROTOCOL.md`` section 5
    states the rule; :class:`Pending` enforces it for a criterion nobody has written yet.
  - **A gate that raises is red, not absent.** An exception inside ``check()`` becomes
    ``ERRORED``, and so does a module that will not import. The registry's size is a fact
    about the repository, not about which imports happened to succeed today.
  - **A gate may only report on itself.** A result whose ``name`` differs from the gate that
    produced it is discarded as ``ERRORED``: without this, one gate could quietly report a
    pass on another's behalf and the table would look complete.

Card #5.
"""

from __future__ import annotations

import importlib
import pkgutil
import time
import traceback
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from hydms.config import Config

__all__ = [
    "Gate",
    "GateReport",
    "GateResult",
    "Pending",
    "Speed",
    "Status",
    "UnknownGate",
    "registry",
    "run",
    "select",
]

# The report's own version, written into every JSON report so a consumer -- card #4's
# artifact manifest first -- can tell whether it is reading a shape it understands.
SCHEMA = "hydms.gates/1"

_PACKAGE = __name__.rsplit(".", 1)[0]
_HERE = Path(__file__).resolve().parent


class Status(str, Enum):
    """The four things a gate run can honestly say.

    ``SKIPPED`` is not a mild pass. It means the criterion was **not** established, and the
    renderer treats it as loudly as a failure.
    """

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERRORED = "ERRORED"


class Speed(str, Enum):
    """Whether a gate belongs in the per-push lane.

    ``FAST`` means "answerable against the published artifact"; ``SLOW`` means "needs a
    retrain". That split is the CI lane split (cards #6 and #7), declared here so a gate
    author decides it once, next to the check, rather than a workflow file deciding it later.
    """

    FAST = "fast"
    SLOW = "slow"


class UnknownGate(LookupError):
    """A gate was requested by a name nothing is registered under."""


@dataclass(frozen=True)
class GateResult:
    """What one gate concluded, in a shape that survives a JSON round trip.

    ``measured`` and ``threshold`` are why this is not a boolean. Every gate card on the
    board says some version of "failure reports the measured value, not just a boolean",
    because a red build that does not say *how far off* costs the next person the run again.
    """

    name: str
    status: Status
    message: str
    measured: float | str | None = None
    threshold: float | str | None = None
    duration_s: float = 0.0

    @property
    def passed(self) -> bool:
        return self.status is Status.PASSED

    @classmethod
    def ok(
        cls,
        name: str,
        message: str,
        *,
        measured: float | str | None = None,
        threshold: float | str | None = None,
    ) -> GateResult:
        return cls(name, Status.PASSED, message, measured, threshold)

    @classmethod
    def fail(
        cls,
        name: str,
        message: str,
        *,
        measured: float | str | None = None,
        threshold: float | str | None = None,
    ) -> GateResult:
        return cls(name, Status.FAILED, message, measured, threshold)

    @classmethod
    def skip(cls, name: str, reason: str) -> GateResult:
        return cls(name, Status.SKIPPED, reason)

    @classmethod
    def error(cls, name: str, detail: str) -> GateResult:
        return cls(name, Status.ERRORED, detail)

    def to_dict(self) -> dict[str, Any]:
        # `passed` is redundant beside `status` and is written anyway: card #5 names it in
        # the result contract, and a consumer reading one boolean should not have to know
        # that SKIPPED and ERRORED both mean "not passed".
        return {
            "name": self.name,
            "status": self.status.value,
            "passed": self.passed,
            "measured": self.measured,
            "threshold": self.threshold,
            "message": self.message,
            "duration_s": round(self.duration_s, 4),
        }


@runtime_checkable
class Gate(Protocol):
    """What every criterion module's ``GATE`` object must provide.

    ``check`` receives the loaded :class:`~hydms.config.Config` and nothing else. That is
    the whole seam: a gate reads its thresholds and its artifact location from config, so a
    gate cannot grow a path literal or a hand-tuned tolerance without it showing up as a
    change to ``hydms/config/pipeline.yaml``.
    """

    @property
    def name(self) -> str:
        """The CLI's addressing scheme: 'AC-2', 'HG-1'."""

    @property
    def title(self) -> str:
        """One line, stating the criterion rather than naming it."""

    @property
    def card(self) -> int:
        """The board card that owes this check."""

    @property
    def speed(self) -> Speed:
        """Which CI lane it belongs to."""

    def check(self, cfg: Config) -> GateResult: ...


@dataclass(frozen=True)
class Pending:
    """A registered criterion whose check has not been written yet.

    It exists so an unimplemented gate is *visible* rather than missing. The registry is
    then a complete list of what this project has promised to check, and a run can state how
    much of that promise is currently unverified instead of quietly checking less.

    It has exactly one behaviour and no way to acquire another: it returns ``SKIPPED``.
    """

    name: str
    title: str
    card: int
    speed: Speed
    reason: str
    blocked_by: tuple[int, ...] = ()

    def check(self, cfg: Config) -> GateResult:
        blockers = ""
        if self.blocked_by:
            blockers = " blocked by " + ", ".join(f"#{i}" for i in self.blocked_by) + ";"
        return GateResult.skip(
            self.name, f"not implemented -- card #{self.card};{blockers} {self.reason}"
        )


@dataclass(frozen=True)
class Broken:
    """A criterion module that would not import, or that declares no usable ``GATE``.

    Registered in place of the gate it failed to provide, so the number of registered gates
    stays a property of the repository rather than of today's import luck.
    """

    name: str
    title: str
    detail: str
    card: int = 0
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        return GateResult.error(self.name, self.detail)


# --------------------------------------------------------------------------------------
# Registry
#
# Discovery is by module, not by decorator. A decorator only registers a gate if something
# imported its module, which makes the registry depend on import order; scanning the package
# directory makes "this criterion exists" a fact about the filesystem instead.
# --------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _discover() -> tuple[Gate, ...]:
    found: list[Gate] = []
    for info in sorted(pkgutil.iter_modules([str(_HERE)]), key=lambda m: m.name):
        if info.name.startswith("_"):
            continue  # harness internals: _core, _report
        found.append(_load(info.name))

    seen: dict[str, str] = {}
    for gate in found:
        if gate.name in seen:
            raise RuntimeError(
                f"two gate modules both register {gate.name}: {seen[gate.name]} and "
                f"{type(gate).__module__}. Gate names are the CLI's addressing scheme "
                f"and must be unique."
            )
        seen[gate.name] = type(gate).__module__
    return tuple(sorted(found, key=lambda g: g.name))


def _load(module_name: str) -> Gate:
    """Import one criterion module and return its gate, or a :class:`Broken` stand-in."""
    try:
        module = importlib.import_module(f"{_PACKAGE}.{module_name}")
    except Exception:  # a broken module is reported, never raised past
        return Broken(
            name=module_name,
            title="(module failed to import)",
            detail=f"{module_name} could not be imported:\n{traceback.format_exc()}",
        )

    gate = getattr(module, "GATE", None)
    if gate is None:
        return Broken(
            name=module_name,
            title="(no GATE)",
            detail=f"{module_name} defines no module-level GATE object",
        )
    if not isinstance(gate, Gate):
        return Broken(
            name=str(getattr(gate, "name", module_name)),
            title="(not a Gate)",
            detail=(
                f"{module_name}.GATE does not satisfy the Gate protocol: it needs "
                f"name, title, card, speed and check(cfg)"
            ),
        )
    return gate


def registry() -> tuple[Gate, ...]:
    """Every registered gate, ordered by name. Discovery happens once per process."""
    return _discover()


def select(names: Sequence[str] | None = None, *, speed: Speed | None = None) -> tuple[Gate, ...]:
    """Choose gates by name, by lane, or take them all.

    Raises:
        UnknownGate: A requested name is not registered. Deliberately loud -- a typo in a CI
            workflow that silently selected nothing would report a green run over zero
            checks, which is the exact failure this harness exists to make impossible.
    """
    gates = registry()
    if names:
        by_name = {g.name.upper(): g for g in gates}
        chosen: list[Gate] = []
        for raw in names:
            gate = by_name.get(raw.strip().upper())
            if gate is None:
                known = ", ".join(g.name for g in gates)
                raise UnknownGate(f"no gate named {raw!r}. Registered gates: {known}")
            if gate not in chosen:
                chosen.append(gate)
        return tuple(chosen)
    if speed is not None:
        return tuple(g for g in gates if g.speed is speed)
    return gates


# --------------------------------------------------------------------------------------
# Running
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class GateReport:
    """The outcome of one harness run, and the object card #4's manifest embeds."""

    results: tuple[GateResult, ...]
    selection: str
    strict: bool
    started_at: str
    duration_s: float

    @property
    def counts(self) -> dict[str, int]:
        return {
            status.value.lower(): sum(1 for r in self.results if r.status is status)
            for status in Status
        }

    @property
    def ok(self) -> bool:
        """Whether this run may be called green.

        A skip is tolerated under a broad selection and fatal under an explicit one. Asking
        for ``HG-2`` and being told the criterion is unimplemented is not a pass -- you asked
        a question and did not get an answer. Asking for the whole registry while most of the
        phase is unwritten is a different situation, and failing there would leave CI
        permanently red and therefore permanently ignored.
        """
        if any(r.status in (Status.FAILED, Status.ERRORED) for r in self.results):
            return False
        return not (self.strict and any(r.status is Status.SKIPPED for r in self.results))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "selection": self.selection,
            "strict": self.strict,
            "started_at": self.started_at,
            "duration_s": round(self.duration_s, 4),
            "summary": self.counts,
            "ok": self.ok,
            "gates": [r.to_dict() for r in self.results],
        }


def run(
    gates: Iterable[Gate],
    cfg: Config,
    *,
    selection: str = "",
    strict: bool = False,
) -> GateReport:
    """Execute the given gates and collect their results.

    No gate can end this call early: an exception is caught, timed, and recorded against the
    gate that raised it, so one broken check cannot hide the state of the others.
    """
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    wall = time.perf_counter()

    results = [_run_one(gate, cfg) for gate in gates]

    return GateReport(
        results=tuple(results),
        selection=selection,
        strict=strict,
        started_at=started,
        duration_s=time.perf_counter() - wall,
    )


def _run_one(gate: Gate, cfg: Config) -> GateResult:
    clock = time.perf_counter()
    try:
        result = gate.check(cfg)
    except Exception:  # the harness reports failures, it does not propagate them
        return GateResult(
            gate.name,
            Status.ERRORED,
            f"{gate.name} raised during check():\n{traceback.format_exc()}",
            duration_s=time.perf_counter() - clock,
        )

    elapsed = time.perf_counter() - clock
    if not isinstance(result, GateResult):
        return GateResult(
            gate.name,
            Status.ERRORED,
            f"{gate.name}.check() returned {type(result).__name__}, not a GateResult",
            duration_s=elapsed,
        )
    if result.name != gate.name:
        return GateResult(
            gate.name,
            Status.ERRORED,
            (
                f"{gate.name}.check() returned a result named {result.name!r}. A gate may "
                f"only report on itself, or the table shows a pass nobody established."
            ),
            duration_s=elapsed,
        )
    return GateResult(
        result.name,
        result.status,
        result.message,
        result.measured,
        result.threshold,
        elapsed,
    )
