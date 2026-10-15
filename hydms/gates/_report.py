"""Rendering a gate run: the terminal table, and the JSON the artifact manifest embeds.

Separated from ``_core`` because how a result is *shown* is a different kind of knowledge
from how it is produced, and because two consumers read the same run: a person scrolling a
CI log, and card #4's manifest.

The table has one job beyond legibility -- **a skip must not read like a pass.** A row that
says "not checked" beside a green summary line is how a check regime ends up reporting
safety it never established, so skips are counted separately, listed by name, and given a
banner that says in words what the run did not establish.
"""

from __future__ import annotations

import json
from pathlib import Path

from ._core import Gate, GateReport, Status

__all__ = ["render_registry", "render_report", "write_report"]

# The status column is padded to this width so the shapes of PASSED / FAILED / SKIPPED line
# up in a log where nothing else is aligned.
_STATUS_WIDTH = max(len(s.value) for s in Status)


def _cell(value: float | str | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _first_line(message: str) -> str:
    """The table shows one line per gate; a traceback's full text is printed below it."""
    return message.strip().splitlines()[0] if message.strip() else ""


def render_report(report: GateReport, gates: tuple[Gate, ...] = ()) -> str:
    """The human-readable run: a table, a summary, and the detail behind any red row.

    ``gates`` is optional and only supplies the owning card number for each row. The report
    is the authority on what happened; the registry is the authority on who owns it.
    """
    owner = {g.name: g.card for g in gates}

    header = ("GATE", "STATUS", "MEASURED", "THRESHOLD", "CARD", "DETAIL")
    rows: list[tuple[str, str, str, str, str, str]] = []
    for result in report.results:
        card = owner.get(result.name)
        rows.append(
            (
                result.name,
                result.status.value,
                _cell(result.measured),
                _cell(result.threshold),
                f"#{card}" if card else "-",
                _first_line(result.message),
            )
        )

    widths = [max(len(header[i]), *(len(r[i]) for r in rows)) if rows else len(header[i])
              for i in range(len(header))]
    widths[1] = max(widths[1], _STATUS_WIDTH)

    def line(cells: tuple[str, ...]) -> str:
        # The last column is not padded: nothing follows it, and trailing space in a CI log
        # is noise in every diff of that log.
        padded = [cells[i].ljust(widths[i]) for i in range(len(cells) - 1)]
        return "  ".join([*padded, cells[-1]]).rstrip()

    out: list[str] = [line(header), "  ".join("-" * w for w in widths)]
    out.extend(line(r) for r in rows)

    counts = report.counts
    out.append("")
    out.append(
        f"{counts['passed']} passed  {counts['failed']} failed  "
        f"{counts['skipped']} skipped  {counts['errored']} errored  "
        f"({report.duration_s:.2f}s)"
    )

    skipped = [r.name for r in report.results if r.status is Status.SKIPPED]
    if skipped:
        out.append("")
        out.append(
            f"NOT CHECKED: {', '.join(skipped)}. This run establishes nothing about "
            f"{'them' if len(skipped) > 1 else 'it'}."
        )

    # Multi-line detail -- tracebacks, per-column diffs, the caveats behind a green row --
    # goes below the table rather than into it, so a wide message cannot destroy the
    # alignment of every other row.
    #
    # Any status, not only the red ones. AC-2 is why (card #21): it passes, and the two
    # things it is *required* to say are what the comparison excluded and what a green run
    # does not establish. A pass with caveats that only reaches the JSON report is a pass
    # whose caveats nobody reads.
    for result in report.results:
        if "\n" in result.message.strip():
            out.append("")
            out.append(f"--- {result.name} ---")
            out.append(result.message.rstrip())

    return "\n".join(out)


def render_registry(gates: tuple[Gate, ...]) -> str:
    """What this project has promised to check, and which card owes each check."""
    header = ("GATE", "LANE", "CARD", "TITLE")
    rows = [(g.name, g.speed.value, f"#{g.card}" if g.card else "-", g.title) for g in gates]
    widths = [max(len(header[i]), *(len(r[i]) for r in rows)) if rows else len(header[i])
              for i in range(len(header))]

    def line(cells: tuple[str, ...]) -> str:
        padded = [cells[i].ljust(widths[i]) for i in range(len(cells) - 1)]
        return "  ".join([*padded, cells[-1]]).rstrip()

    out = [line(header), "  ".join("-" * w for w in widths)]
    out.extend(line(r) for r in rows)
    out.append("")
    out.append(f"{len(gates)} gates registered.")
    return "\n".join(out)


def write_report(report: GateReport, destination: Path) -> Path:
    """Write the run as JSON, creating the directory if it is not there yet.

    Card #5 requires gate results in the artifact manifest. This writes the object to a
    standalone file under the configured artifacts directory; ``hydms.artifacts.save`` embeds
    the same object, unmodified, under its manifest's ``gates`` key rather than carrying a
    second format. The ``schema`` field is what lets it know it can -- the store restates it
    as ``hydms.artifacts.manifest.GATE_SCHEMA`` and a test asserts the two still agree.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return destination
