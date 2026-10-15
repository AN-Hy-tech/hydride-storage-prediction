"""The gate harness command line.

    python -m hydms.gates list
    python -m hydms.gates run --all
    python -m hydms.gates run --fast
    python -m hydms.gates run AC-2 HG-1

Exit codes, which are the whole contract as far as CI is concerned:

    0   every selected gate that ran, passed
    1   a gate FAILED, ERRORED, an explicitly named gate was SKIPPED, or --strict and a skip
    2   the invocation itself was wrong (unknown gate name, unreadable config)

The asymmetry between a named gate and a lane is deliberate and is explained on
``GateReport.ok``: asking for AC-5 and being told it is unimplemented is not a pass, while
failing a whole-registry run for the same reason would leave CI red for the length of the
phase and therefore ignored.

Card #5.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from hydms.config import Config, ConfigError, load

from ._core import GateReport, Speed, Status, UnknownGate, registry, run, select
from ._report import render_registry, render_report, write_report

# Written under the configured artifacts directory, beside the version directories. A saved
# artifact embeds this same object under its manifest's `gates` key (hydms.artifacts.save),
# and a version whose recorded gates did not all pass will not load and cannot be promoted.
REPORT_NAME = "gate-results.json"

EXIT_OK = 0
EXIT_GATE_FAILED = 1
EXIT_BAD_INVOCATION = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.gates",
        description="Run the PRD acceptance criteria and the Phase H hardening gates.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # `list` reads the registry, not the config: what is promised is a fact about the package,
    # and answering it must keep working when the configuration does not load.
    sub.add_parser("list", help="show every registered gate and the card that owes it")

    runner = sub.add_parser("run", help="run gates and report pass/fail")
    runner.add_argument(
        "names",
        nargs="*",
        metavar="GATE",
        help="gate names, e.g. AC-2 HG-1. A skip is a failure when a gate is named.",
    )
    lane = runner.add_mutually_exclusive_group()
    lane.add_argument("--all", action="store_true", help="every registered gate")
    lane.add_argument(
        "--fast",
        action="store_true",
        help="only gates answerable against the published artifact (the CI fast lane)",
    )
    lane.add_argument("--slow", action="store_true", help="only gates that need a retrain")
    runner.add_argument(
        "--strict",
        action="store_true",
        help="treat SKIPPED as failure, so an unimplemented gate cannot look green",
    )
    runner.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    runner.add_argument(
        "--report",
        type=Path,
        default=None,
        help=f"where to write the JSON report; defaults to <artifacts>/{REPORT_NAME}",
    )
    runner.add_argument("--no-report", action="store_true", help="do not write a JSON report")
    # The consumer this exists for is `$GITHUB_STEP_SUMMARY`, which GitHub gives every step as
    # a path to append markdown to. Taking a path rather than reading that variable keeps the
    # CLI honest about what it writes and where -- and testable without inventing an
    # environment.
    runner.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="append the one-line verdict to this file, e.g. $GITHUB_STEP_SUMMARY",
    )
    return parser


def _load_config(path: Path | None) -> Config:
    return load(path)


def _run(args: argparse.Namespace, stream: TextIO) -> int:
    if not (args.names or args.all or args.fast or args.slow):
        print(
            "nothing selected. Pass gate names, or --all / --fast / --slow.",
            file=sys.stderr,
        )
        return EXIT_BAD_INVOCATION

    try:
        cfg = _load_config(args.config)
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    speed = Speed.FAST if args.fast else Speed.SLOW if args.slow else None
    try:
        gates = select(args.names, speed=speed)
    except UnknownGate as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_BAD_INVOCATION

    selection = " ".join(args.names) if args.names else ("--fast" if args.fast else
                                                         "--slow" if args.slow else "--all")
    # A named selection is strict by construction: you asked a specific question and a
    # SKIPPED answer is not an answer. --strict extends that to a lane.
    strict = bool(args.names) or args.strict

    report = run(gates, cfg, selection=selection, strict=strict)
    print(render_report(report, gates), file=stream)

    if not args.no_report:
        destination = args.report or (cfg.paths.artifacts / REPORT_NAME)
        written = write_report(report, destination)
        print(f"\nreport: {written}", file=stream)

    if args.summary is not None:
        # Append: a CI step summary is accumulated by every step in the job, and truncating it
        # would delete what ran before this. A failure to write it must not change the
        # verdict -- the gates are the answer, the summary is only how it is shown.
        try:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            with args.summary.open("a", encoding="utf-8") as handle:
                handle.write(summarise(report) + "\n")
        except OSError as exc:
            print(f"could not write the summary to {args.summary}: {exc}", file=sys.stderr)

    return EXIT_OK if report.ok else EXIT_GATE_FAILED


def _list(stream: TextIO) -> int:
    print(render_registry(registry()), file=stream)
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "list":
        return _list(sys.stdout)
    return _run(args, sys.stdout)


def summarise(report: GateReport) -> str:
    """One line for a CI step summary or a commit comment, **naming** what was not green.

    The counts alone were not enough, and the way that was missed is worth recording. The
    original version returned only the tallies, and its test looked like it checked the
    naming -- it asserted the gate's name appeared in the line. It did, but only because
    ``report.selection`` echoes the names you asked for: under ``--fast`` the selection is the
    literal string ``--fast``, and the line named nothing. Measured on 2026-09-12 against the
    real fast lane, it read ``gates --fast: green -- 7 passed, 0 failed, 2 skipped, 0
    errored`` while AC-5 and HG-4 were the skips, and a reader could not tell which.

    Card #86 asks that a failure name which gate failed, so the names are appended here and
    the test now asks the question under a selection that does not contain them.
    """
    counts = report.counts
    verdict = "green" if report.ok else "RED"
    line = (
        f"gates {report.selection}: {verdict} -- {counts['passed']} passed, "
        f"{counts['failed']} failed, {counts['skipped']} skipped, {counts['errored']} errored"
    )

    # Ordered worst-first, and skips are named even when the run is green: a lane tolerates
    # them (see GateReport.ok), which is exactly why they have to stay visible.
    for status, label in (
        (Status.ERRORED, "errored"),
        (Status.FAILED, "failed"),
        (Status.SKIPPED, "skipped"),
    ):
        named = [r.name for r in report.results if r.status is status]
        if named:
            line += f"; {label}: {', '.join(named)}"
    return line


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
