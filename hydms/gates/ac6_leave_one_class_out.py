"""AC-6 -- leave-one-alloy-class-out R2 is reported beside the random-split number.

PRD section 10.6, and the single most important validation number in the thesis: hydride
models are accurate within a family and poor across families, so the random-split score
measures interpolation and says little about the extrapolation the inverse design needs.

Expect it to be substantially worse, and report it anyway. **This gate checks that it is
reported at all -- not that it clears a bar**, which is exactly what the criterion says. A
threshold here would be this project deciding in advance what hydride chemistry is allowed to
do, and then quietly tuning until the answer came out above it.

**Why this reads a committed table instead of fitting anything.** The protocol behind the
number is ``python -m hydms.surrogate.loco``: ten class folds through the same nested search
``train`` uses, measured at about **4.7 hours** on this machine, roughly twice the random-split
run. A gate cannot pay that, and a gate that fitted a *cheaper* version of it would certify a
number nobody publishes. So the run happens once, deliberately, and commits its tables; this
gate reads them and asserts the criterion over what was published. That is the same shape card
#29 gave the evaluation document -- the slow run writes CSVs, the cheap path reads them -- and
it is why ``reports/loco/`` is un-ignored in ``.gitignore``. **A gate reading a gitignored
directory is a gate that can only ever pass on somebody's laptop**, which is the trap card #34
found on ``artifacts/current.json`` the same day.

**Three verdicts, and the middle one is the point.**

  - No tables: ``SKIPPED``. The run has not happened, nothing is established, and the message
    names the command that would establish it. ``hydms.artifacts.promote`` treats this exactly
    as it treats a failure, which is correct -- an unrun protocol is not evidence.
  - Tables from a **probe**: ``FAILED``, not skipped. ``loco-run.csv`` records ``probe``, and a
    probe's tables are the same shape as a real run's. Committed probe numbers are a defect
    somebody introduced, not an absence somebody has yet to fill, and the two deserve different
    words.
  - Tables with the class figure but **no random-split figure beside it**: ``FAILED``. The
    criterion is the word *alongside*. A leave-one-class-out R2 published on its own is the
    failure this gate exists to catch, because the number it must be read against is the one a
    reader already has in their head.

The lane is ``FAST``. It was declared ``SLOW`` while it was a stub, on the reasoning that one
refit per alloy class is a retrain -- true of the protocol, and not of this check, which opens
two CSVs. The refit is real and is card #30's command; what the gate does is read.

Owned by card #30.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hydms.config import Config

from ._core import Gate, GateResult, Speed

__all__ = ["GATE"]

#: The directory ``python -m hydms.surrogate.loco`` writes, under the configured reports path.
#: Named here rather than imported from :mod:`hydms.surrogate.loco`, because a gate must be
#: readable on an interpreter that has no pandas and no CatBoost -- the same reason
#: :data:`hydms.artifacts.manifest.GATE_SCHEMA` is restated rather than imported. A test
#: asserts the two agree, which is the check that matters.
REPORTS = "loco"

#: The one table the criterion lives in: it carries both figures in a single row, so neither
#: can be published without the other.
SUMMARY = "loco-summary.csv"

#: The provenance row. A probe's tables are the same shape as a result's, so this is the only
#: thing standing between a cost check and a published claim.
RUN = "loco-run.csv"


def _read(path: Path) -> list[dict[str, str]]:
    """One CSV as rows of strings, using the stdlib.

    ``csv`` rather than pandas on purpose: this gate is the cheap half of a protocol whose
    expensive half already ran, and it should not need the scientific stack to say whether two
    numbers were published together.
    """
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _number(value: str | None) -> float | None:
    """A cell as a float, or ``None`` for a blank, a NaN or anything unparseable.

    A NaN is what :func:`hydms.surrogate.loco.summary` writes when no random-split run is on
    disk, and it must read as *absent* here rather than as a number -- otherwise "reported
    alongside" would be satisfied by a column of nothing.
    """
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return None if parsed != parsed else parsed


@dataclass(frozen=True)
class LeaveOneClassOut:
    """The gate. It reads two committed tables and asserts the criterion over them."""

    name: str = "AC-6"
    title: str = "Leave-one-alloy-class-out R2 reported beside the random split"
    card: int = 30
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        directory = cfg.paths.reports / REPORTS
        summary_path = directory / SUMMARY
        run_path = directory / RUN

        absent = [p.name for p in (summary_path, run_path) if not p.is_file()]
        if absent:
            return GateResult.skip(
                self.name,
                f"{directory} has no {', '.join(absent)}, so leave-one-alloy-class-out has "
                f"not been run and nothing about cross-family transfer is established. Run "
                f"`python -m hydms.surrogate.loco --target capacity` (about 4.7 h; "
                f"`--budget` costs it first) and commit its tables.",
            )

        try:
            summary = _read(summary_path)
            run = _read(run_path)
        except (OSError, UnicodeDecodeError) as error:
            return GateResult.fail(self.name, f"{directory} could not be read: {error}")

        if not summary or not run:
            return GateResult.fail(
                self.name,
                f"{summary_path.name} or {run_path.name} has a header and no rows, so the "
                f"protocol wrote a table and recorded nothing in it.",
            )

        if str(run[0].get("probe", "")).strip().lower() in ("true", "1", "yes"):
            return GateResult.fail(
                self.name,
                f"{run_path.name} records probe=True: these tables came from a reduced run "
                f"({run[0].get('optuna_trials', '?')} trial(s) against the configured "
                f"{run[0].get('configured_optuna_trials', '?')}), which is a cost check and "
                f"not a result. A probe's tables are the same shape as a real run's, which is "
                f"why this is checked rather than assumed.",
                measured="probe",
                threshold="a full run",
            )

        row = summary[0]
        loco_r2 = _number(row.get("macro_r2"))
        random_r2 = _number(row.get("random_split_r2"))
        scored = row.get("classes_scored", "?")
        classes = row.get("classes", "?")

        if loco_r2 is None:
            return GateResult.fail(
                self.name,
                f"{summary_path.name} reports no leave-one-alloy-class-out R2 "
                f"(macro_r2 is {row.get('macro_r2', 'absent')!r}). {scored} of {classes} "
                f"class(es) were estimable.",
            )
        if random_r2 is None:
            return GateResult.fail(
                self.name,
                f"leave-one-alloy-class-out R2 is {loco_r2:.4f}, but no random-split number is "
                f"published beside it (random_split_r2 is "
                f"{row.get('random_split_r2', 'absent')!r}). The criterion is the word "
                f"*alongside*: this figure read on its own is the misreading it exists to "
                f"prevent, because the number it must be compared against is the one a reader "
                f"already has in mind. Run `python -m hydms.surrogate.train` so "
                f"model-record.csv exists, then `loco --emit`.",
                measured=f"{loco_r2:.4f} alone",
                threshold="both figures in one row",
            )

        gap = random_r2 - loco_r2
        return GateResult.ok(
            self.name,
            f"reported side by side: leave-one-alloy-class-out R2 {loco_r2:.4f} over {scored} "
            f"of {classes} class(es), against the random-split {random_r2:.4f} -- a gap of "
            f"{gap:+.4f}. The size of that gap is a finding about hydride chemistry and is "
            f"deliberately not what this gate measures; that both numbers are published is.",
            measured=f"{loco_r2:.4f} vs {random_r2:.4f}",
            threshold="both reported",
        )


GATE: Gate = LeaveOneClassOut()
