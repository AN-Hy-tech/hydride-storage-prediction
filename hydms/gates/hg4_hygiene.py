"""HG-4 -- ruff, mypy and the coverage floor hold on ``hydms/``.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when ruff, mypy, or the coverage floor
fail on the package.

The three tools are configured in ``pyproject.toml`` and are **deliberately outside the
Project conda environment**: they need no scientific stack, and card #68 established that the
fast lane installs nothing and builds no environment. Card #86 wires them into CI in that
conda-free lane; this gate is how a local run asks the same question CI will ask.

Why it runs the tools rather than reading what a lane reported
---------------------------------------------------------------

A gate that parsed a CI log would establish that *some* run was green, not that this checkout
is. Both tools are cheap enough to simply re-ask -- measured on 2026-09-12 on the maintainer's
machine, ruff over all three target trees is **0.045 s** and a warm mypy is **2.33 s** -- so
the gate shells out. That number is why the gate is :data:`~hydms.gates.Speed.FAST` and why it
is not marked slow: a 2.4 s check that the whole registry run pays once is not worth hiding
behind a marker the fast lane would deselect.

Coverage is the exception, and it has to be. Measuring it means *running the suite*, and the
suite is what runs this gate -- so the gate reads the data file the run already produced
rather than recursing into itself. It therefore reports SKIPPED, loudly, in a checkout where
nobody has run ``pytest --cov``; the floor's enforcement on every push is the ``--cov-fail-under``
on CI's own pytest step, and this leg is how a local run sees the same number before pushing.

Where the tools come from, and why the versions are pinned
-----------------------------------------------------------

``ruff`` and ``mypy`` are resolved from ``PATH``, which on the maintainer's machine finds the
3.13 user-site executables rather than anything inside ``Project`` -- exactly the conda-free
lane's arrangement. In CI they come from the ``dev`` extra, which **pins them exactly** rather
than to a floor. That pin is not tidiness: ``.github/workflows/ci.yml`` already installs
``ruff==0.8.4`` and ``mypy==1.13.0`` by hand in the hygiene job, because a floor resolves to
whatever was released this week and the first run of that workflow failed on precisely that.
Before card #86 the ``dev`` extra still carried floors, so this gate -- which runs in CI's
``suite`` job, where ``dev`` is what is installed -- could have gone red against a ruff the
hygiene job never runs. ``tests/test_tooling.py`` now asserts the two agree.

A tool that is absent is a skip, never a pass. That is the harness's rule
(``docs/QA-PROTOCOL.md`` section 5) and it matters most here, because "the linter was not
installed" and "the code is clean" produce the same silence.

The coverage floor is a ratchet rather than a target. Lowering it to make a build pass is a
review conversation, and the reason goes in the card's narrative.

Owned by card #86.
"""

from __future__ import annotations

import io
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

from hydms.config import Config

from ._core import Gate, GateResult, Speed

__all__ = ["GATE", "LINT_TARGETS", "TIMEOUT_S"]

#: What ruff is pointed at. The same three trees ``.github/workflows/ci.yml`` names, because a
#: gate that checked a narrower set than CI would go green on a push CI then rejects. mypy is
#: not given targets: ``[tool.mypy] files = ["hydms"]`` already fixes them, and duplicating that
#: list here would be a second place for it to drift.
LINT_TARGETS: Final = ("hydms", "tests", "scripts")

#: Generous against the measured 0.045 s and 2.33 s. It exists so a tool that hangs -- mypy
#: waiting on a lock, ruff on a network mount -- is reported as a failed check rather than
#: holding CI open until the job's own timeout kills it with no message.
TIMEOUT_S: Final = 300


@dataclass(frozen=True)
class _Leg:
    """One of the three questions, and what asking it produced.

    ``ok is None`` means the question could not be asked at all -- the tool is absent, or no
    coverage data exists. That is a third state on purpose: collapsing it into ``False`` would
    make a missing linter look like dirty code, and collapsing it into ``True`` would make it
    look like clean code, which is the failure this harness exists to prevent.
    """

    name: str
    ok: bool | None
    detail: str
    measured: str
    #: The bar this leg was judged against, when it has a numeric one. Only coverage does:
    #: ruff and mypy are pass/fail by construction, and inventing a "0 violations" threshold
    #: for them would put a number in the report that nothing chose.
    threshold: str | None = None


def _run(tool: str, args: tuple[str, ...], root: Path) -> _Leg:
    """Ask one command-line tool, from ``root``, and read its exit code."""
    executable = shutil.which(tool)
    if executable is None:
        return _Leg(
            tool,
            None,
            f"{tool} is not on PATH, so this checkout was not checked by it. It is in the "
            f"`dev` extra (`pip install -e \".[dev]\"`) and on the maintainer's machine it "
            f"lives outside the Project environment by design (card #68).",
            "not run",
        )

    try:
        completed = subprocess.run(
            [executable, *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return _Leg(tool, False, f"{tool} did not finish within {TIMEOUT_S} s", "timed out")

    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode == 0:
        return _Leg(tool, True, output.splitlines()[-1] if output else f"{tool} is clean", "clean")

    # Every line matters to whoever has to fix it, so the whole of it is carried in `detail`
    # and the renderer shows the first line in the table and the rest below the red row.
    return _Leg(
        tool,
        False,
        f"{tool} exited {completed.returncode}:\n{output}",
        f"exit {completed.returncode}",
    )


def _ruff(targets: tuple[str, ...], root: Path) -> _Leg:
    """ruff over whichever of :data:`LINT_TARGETS` this checkout has."""
    if not targets:
        return _Leg(
            "ruff",
            None,
            f"none of {', '.join(LINT_TARGETS)} exists under {root}, so there was nothing to "
            f"lint. This gate answers about a checkout.",
            "not run",
        )
    return _run("ruff", ("check", *targets), root)


def _when(stamp: float) -> str:
    """A timestamp a reader can act on. Local time, because the reader is at the machine."""
    return datetime.fromtimestamp(stamp).isoformat(timespec="seconds")


def _coverage(root: Path) -> _Leg:
    """Read the floor and the measured total out of whatever the last suite run left behind.

    Both numbers come from ``pyproject.toml`` via coverage's own configuration reader rather
    than from a literal here: ``fail_under`` has exactly one owner and this is not it.
    """
    try:
        from coverage import Coverage
        from coverage.exceptions import CoverageException
    except ImportError:
        return _Leg(
            "coverage",
            None,
            "coverage is not importable in this interpreter, so the floor was not measured. "
            "It arrives with `pytest-cov`, which is in the `dev` extra; CI's suite job "
            "installs it and enforces the floor on the pytest step itself.",
            "not run",
        )

    cov = Coverage(config_file=str(root / "pyproject.toml"))
    configured = cov.get_option("report:fail_under")
    if not isinstance(configured, int | float | str):
        return _Leg(
            "coverage",
            None,
            f"[tool.coverage.report] fail_under is {configured!r}, which is not a number, so "
            f"there is no floor to hold this checkout to.",
            "no floor",
        )
    floor_value = float(configured)
    floor = f"{floor_value:g}%"

    data = Path(cov.config.data_file)
    if not data.is_absolute():
        data = root / data
    if not data.exists():
        return _Leg(
            "coverage",
            None,
            f"no coverage data at {data}. Run `python -m pytest --cov` first; this gate reads "
            f"what a suite run left behind rather than running the suite, because the suite is "
            f"what runs this gate.",
            "no data",
            floor,
        )

    # Coverage data that predates the code it claims to measure establishes nothing, and it
    # fails in both directions: a stale file can report a green total for a module that has
    # since been rewritten, or a red one for a gap that has since been filled. `pytest --cov`
    # only writes the data file when the run *ends*, so a gate running inside that very suite
    # is reading the previous run -- which is exactly when this matters.
    newest = max((p.stat().st_mtime for p in (root / "hydms").rglob("*.py")), default=0.0)
    age = data.stat().st_mtime
    if newest > age:
        return _Leg(
            "coverage",
            None,
            f"the coverage data at {data} was written {_when(age)}, before the most recent "
            f"change under hydms/ ({_when(newest)}), so it does not measure this code. "
            f"Re-run `python -m pytest --cov`.",
            "stale",
            floor,
        )

    try:
        cov.load()
        total = cov.report(file=io.StringIO())
    except CoverageException as error:
        return _Leg(
            "coverage", None, f"coverage data at {data} is unreadable: {error}", "no data", floor
        )

    measured = f"{total:.2f}%"
    as_of = f" (measured {_when(age)})"
    # 1e-12 is this project's float tolerance throughout: a total that lands exactly on the
    # floor must pass, and coverage's own percentage is arithmetic over two integers.
    if total + 1e-12 < floor_value:
        return _Leg(
            "coverage",
            False,
            f"line-and-branch coverage of hydms/ is {measured}, below the {floor} floor in "
            f"[tool.coverage.report]{as_of}. The floor is a ratchet: lowering it is a review "
            f"conversation, not a fix.",
            measured,
            floor,
        )
    return _Leg(
        "coverage",
        True,
        f"coverage is {measured}, at or above the {floor} floor{as_of}",
        measured,
        floor,
    )


@dataclass(frozen=True)
class Hygiene:
    """The gate. Three independent questions, all of them asked before any is reported."""

    name: str = "HG-4"
    title: str = "Hygiene: ruff, mypy and the coverage floor on hydms/"
    card: int = 86
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        root = cfg.root
        if not (root / "pyproject.toml").is_file():
            return GateResult.skip(
                self.name,
                f"{root} holds no pyproject.toml, so there is no source tree to lint and no "
                f"configuration to lint it by. This gate answers about a checkout; an "
                f"installed wheel is not one.",
            )

        # Only the trees this checkout actually has. ruff exits 2 on a path that does not
        # exist, which would report "the code is dirty" about a directory that is merely
        # absent -- and `scripts/` is not in the installed package at all.
        targets = tuple(name for name in LINT_TARGETS if (root / name).exists())

        # All three run even when the first has already failed: a red build that names one
        # problem and hides two costs the next person two more round trips.
        legs = (
            _ruff(targets, root),
            _run("mypy", (), root),
            _coverage(root),
        )
        measured = " · ".join(f"{leg.name} {leg.measured}" for leg in legs)
        floor = next((leg.threshold for leg in legs if leg.threshold is not None), None)

        failed = [leg for leg in legs if leg.ok is False]
        if failed:
            detail = "\n\n".join(leg.detail for leg in failed)
            return GateResult.fail(
                self.name,
                f"{', '.join(leg.name for leg in failed)} failed on this checkout.\n\n{detail}",
                measured=measured,
                threshold=floor,
            )

        unasked = [leg for leg in legs if leg.ok is None]
        if unasked:
            detail = "\n\n".join(leg.detail for leg in unasked)
            return GateResult.skip(
                self.name,
                f"{', '.join(leg.name for leg in unasked)} could not be asked, so hygiene is "
                f"not established for this checkout.\n\n{detail}",
            )

        return GateResult.ok(
            self.name,
            f"ruff and mypy are clean on {', '.join(targets)} and coverage holds the floor",
            measured=measured,
            threshold=floor,
        )


GATE: Gate = Hygiene()
