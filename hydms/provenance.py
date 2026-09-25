"""The run record: which run wrote a directory of tables, and the one rule for reading it back.

    stamp = provenance.begin(cfg.root, protocol=RANDOM_SPLIT, probe=probe, settings={...})
    ...                                              # the fit, which may take hours
    provenance.write(destination / TRAIN_RECORD, stamp.finish())

    provenance.result(directory / LOCO_RECORD)       # a RunRecord, or NotAResult saying why

**Why this module exists.** A probe's tables and a real run's tables are the same shape: same
file names, same columns, same row counts. Before card #105 the only thing separating them was a
single-row ``*-run.csv`` of settings, and four consumers each asked it "is this a result?" in
their own words -- ``evaluate`` with ``bool(...)`` on pandas, AC-6 with
``in ("true", "1", "yes")``, ``tests/test_figures.py`` with ``== "False"``, and
``hydms.screens.domain.transfer_table`` **not at all**, so a ``loco --trials 1`` into
``reports/loco/`` followed by ``domain --emit`` would have put probe transfer scores into the
*served* domain reference. And no record carried a date or a commit, so card #83's caption had
no run date to state (CONTEXT.md, **Run date**).

**What is hidden here.** How a record is spelled on disk (a single CSV row, every value a
string), how ``probe`` is parsed from every way pandas or ``csv`` can write a boolean, what an
absent or pre-#105 record means, and which environment facts are worth a column. Callers see
:func:`begin`, :meth:`Stamp.finish`, :func:`write`, :func:`read` and :func:`result`.

**Two readers, on purpose.** :func:`read` never raises -- ``evaluate`` needs to *describe* a
probe in a banner, not refuse it. :func:`result` is the question every other consumer is
actually asking, and it refuses unless the record positively says the run was full. An absent
record, an unreadable one and a ``probe`` cell nobody can parse are all refused: defaulting an
unlabelled run to the good case is how a cost check becomes a thesis number.

**Three decisions that are easy to get wrong the other way.**

  - ``started_at`` and ``code_modified`` are taken in :func:`begin`, **before the fit**. A run
    writes its own tables into the un-ignored ``reports/``; git state read afterwards describes
    the run's output, not the code that produced it. ``describe_git`` already excludes the
    output directories, and reading it first closes the rest of that gap.
  - **A record without ``started_at`` has no run date.** It predates this card. It is reported
    as *not recorded* and is never backfilled from the commit date, which can be hours later and
    on another day (CONTEXT.md, **Run date**).
  - ``protocol`` and ``probe`` are different fields. ``protocol`` is the kind of run (random
    split, leave-one-alloy-class-out); ``probe`` is the reduced budget. A leave-one-class-out
    probe is still a leave-one-class-out run.

Standard library only, and no pandas: a gate must be able to read a record on an interpreter
without the scientific stack. It sits beside ``hydms.artifacts`` rather than inside it because a
run record is never a model's -- a model is identified by its artifact version.

Card #105; ADR 0007.
"""

from __future__ import annotations

import csv
import os
import platform as _platform
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Final

from hydms.artifacts.manifest import describe_git, resolved_packages

__all__ = [
    "BOOTSTRAP_INTERVALS",
    "CALIBRATE_RECORD",
    "DEPLOYED_FIT",
    "EVALUATE_RECORD",
    "LEAVE_ONE_CLASS_OUT",
    "LOCO_RECORD",
    "NOT_RECORDED",
    "PACKAGES",
    "RANDOM_SPLIT",
    "RECORD_SUFFIX",
    "THREAD_VARIABLES",
    "TRAIN_RECORD",
    "NotAResult",
    "RunRecord",
    "Stamp",
    "begin",
    "read",
    "result",
    "write",
]

#: Every run record's file name ends with this. The source-parsing test in
#: ``tests/test_provenance.py`` uses it to find a consumer reading a record by hand.
RECORD_SUFFIX: Final = "-run.csv"

#: ``python -m hydms.surrogate.train`` writes this beside its tables.
TRAIN_RECORD: Final = "model-run.csv"

#: ``python -m hydms.surrogate.loco`` writes this beside its tables, and AC-6 reads it.
LOCO_RECORD: Final = "loco-run.csv"

#: ``python -m hydms.surrogate.evaluate`` writes this beside ``evaluation-*.csv``.
EVALUATE_RECORD: Final = "evaluation-run.csv"

#: ``python -m hydms.surrogate.calibrate`` writes this beside ``conformal*.csv``.
CALIBRATE_RECORD: Final = "conformal-run.csv"

#: The kinds of run. ``protocol`` names which one; whether it was reduced is ``probe``.
RANDOM_SPLIT: Final = "random-split"
LEAVE_ONE_CLASS_OUT: Final = "leave-one-alloy-class-out"
#: ``evaluate``: intervals over a fit that already happened, by resampling compositions.
BOOTSTRAP_INTERVALS: Final = "bootstrap-intervals"
#: ``calibrate``: the one deployed fit, its conformal correction and its explanation tables.
DEPLOYED_FIT: Final = "deployed-fit"

#: What a missing run date is called, wherever one is stated.
NOT_RECORDED: Final = "not recorded"

#: The distributions that can move a number, one ``pkg_<name>`` column each. Distribution names
#: as :data:`hydms.artifacts.manifest.RECORDED_PACKAGES` spells them; the column is lowercased.
PACKAGES: Final[tuple[str, ...]] = (
    "numpy",
    "pandas",
    "scikit-learn",
    "catboost",
    "optuna",
    "cleanlab",
    "mapie",
    "Boruta",
)

#: The environment variables that set native thread pools. Recorded as ``unset`` when absent,
#: because an unset variable and one set to an empty string are different machines.
THREAD_VARIABLES: Final[tuple[str, ...]] = ("OMP_NUM_THREADS", "MKL_NUM_THREADS")

#: Every spelling of a boolean that pandas or ``csv`` writes, lowercased. pandas writes
#: ``True``; a column that went through a numeric dtype writes ``1`` or ``1.0``.
_TRUE: Final = frozenset({"true", "1", "1.0", "yes"})
_FALSE: Final = frozenset({"false", "0", "0.0", "no"})

#: The index column pandas ``to_csv`` writes by default, under both names it can come back as.
#: Records written before #105 carry it; it is not a field.
_INDEX_COLUMNS: Final = frozenset({"", "Unnamed: 0"})


class NotAResult(ValueError):
    """The tables beside this record are not a result, and the message says why."""


def _cell(value: object) -> str:
    """One value as the string a record stores. ``None`` is an empty cell."""
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _flag(text: str | None) -> bool | None:
    """A stored boolean, or ``None`` when absent or unparseable. Never guessed."""
    if text is None:
        return None
    lowered = text.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    return None


def _now() -> datetime:
    """The local wall clock with its offset: the day the maintainer would call it."""
    return datetime.now().astimezone()


# --------------------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Stamp:
    """Everything a record states that must be read **before** the fit.

    Made by :func:`begin`; :meth:`finish` adds the end time and returns the row to write.
    """

    protocol: str
    probe: bool
    settings: Mapping[str, object]
    run_id: str
    started_at: datetime
    started_clock: float
    git_sha: str | None
    code_modified: bool | None
    environment: Mapping[str, str] = field(default_factory=dict)

    def finish(self) -> dict[str, str]:
        """The record's row: settings first, as the pre-#105 files had them, then the rest."""
        finished = _now()
        elapsed = time.perf_counter() - self.started_clock
        row: dict[str, str] = {"probe": _cell(self.probe), "protocol": self.protocol}
        for name, value in self.settings.items():
            if name in row:
                raise ValueError(f"setting {name!r} would overwrite the record's own field")
            row[name] = _cell(value)
        row.update(
            {
                "run_id": self.run_id,
                "started_at": self.started_at.isoformat(timespec="seconds"),
                "finished_at": finished.isoformat(timespec="seconds"),
                "elapsed_s": f"{elapsed:.1f}",
                "git_sha": _cell(self.git_sha),
                "code_modified": _cell(self.code_modified),
            }
        )
        for name, value in self.environment.items():
            if name in row:
                raise ValueError(f"setting {name!r} collides with an environment column")
            row[name] = value
        return row


def begin(
    root: Path,
    *,
    protocol: str,
    probe: bool,
    settings: Mapping[str, object],
    catboost_thread_count: int | None = None,
) -> Stamp:
    """Stamp a run as it starts. Call it before the fit, never after.

    Args:
        root: The work tree, for the commit and whether its code was modified.
        protocol: :data:`RANDOM_SPLIT`, :data:`LEAVE_ONE_CLASS_OUT`, or another command's name.
        probe: Whether the budget was reduced. A probe is never a result.
        settings: The command's own settings, in the order its record had them.
        catboost_thread_count: What the fit passes CatBoost, or ``None`` for its default
            (every core -- ``hydms.surrogate.model.FIXED`` does not pin it, card #32).
    """
    git = describe_git(root)
    packages = resolved_packages()
    environment = {
        "python": _platform.python_version(),
        "platform": _platform.platform(),
        "cpu_count": _cell(os.cpu_count()),
        "catboost_thread_count": (
            "default" if catboost_thread_count is None else str(catboost_thread_count)
        ),
    }
    for variable in THREAD_VARIABLES:
        environment[variable] = os.environ.get(variable, "unset")
    for name in PACKAGES:
        environment[f"pkg_{name.lower()}"] = _cell(packages.get(name))
    return Stamp(
        protocol=protocol,
        probe=probe,
        settings=dict(settings),
        run_id=str(uuid.uuid4()),
        started_at=_now(),
        started_clock=time.perf_counter(),
        git_sha=git.sha,
        code_modified=git.code_modified,
        environment=environment,
    )


def write(path: Path, row: Mapping[str, str]) -> Path:
    """Write one record as a header and a single row. Returns the path.

    ``\\n`` line endings on every platform, so a record committed from Windows diffs cleanly.
    """
    if not path.name.endswith(RECORD_SUFFIX):
        raise ValueError(f"a run record's name ends with {RECORD_SUFFIX!r}; got {path.name!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row), lineterminator="\n")
        writer.writeheader()
        writer.writerow(dict(row))
    return path


# --------------------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RunRecord:
    """A record as read back. ``fields`` is empty when there was nothing to read.

    ``state`` is ``"absent"``, ``"unreadable"`` or ``"recorded"``; ``detail`` says why when it
    is not the last.
    """

    path: Path
    state: str
    fields: Mapping[str, str] = field(default_factory=dict)
    detail: str = ""

    def get(self, name: str) -> str | None:
        """One field as stored, or ``None`` if the record has no such column."""
        return self.fields.get(name)

    def flag(self, name: str) -> bool | None:
        """A boolean field in any spelling pandas or ``csv`` writes; ``None`` if unreadable."""
        return _flag(self.get(name))

    @property
    def probe(self) -> bool | None:
        """``True`` for a probe, ``False`` for a full run, ``None`` if nobody can say."""
        return self.flag("probe")

    @property
    def protocol(self) -> str | None:
        return self.get("protocol") or None

    @property
    def run_date(self) -> str | None:
        """The date the run started, ``YYYY-MM-DD``. ``None`` for a record that predates it."""
        started = self.get("started_at")
        return started[:10] if started else None

    @property
    def run_date_text(self) -> str:
        """The run date as prose says it: the date, or :data:`NOT_RECORDED`."""
        return self.run_date or NOT_RECORDED

    def refusal(self) -> str | None:
        """Why these tables are not a result, or ``None`` when the record says they are."""
        if self.state == "absent":
            return (
                f"no run record at {self.path}: nothing says which run wrote the tables beside "
                f"it, so they are not a result. A probe's tables are the same shape as a real "
                f"run's; an unlabelled directory is not assumed to be the good case."
            )
        if self.state != "recorded":
            return f"{self.path} could not be read ({self.detail}), so it is not a result."
        probe = self.probe
        if probe is None:
            return (
                f"{self.path} records probe={self.get('probe')!r}, which is not a boolean, so "
                f"nobody can say whether these tables are a probe. Not a result."
            )
        if probe:
            return (
                f"{self.path} records probe=True: these tables came from a reduced run "
                f"({self.get('optuna_trials') or '?'} trial(s) against the configured "
                f"{self.get('configured_optuna_trials') or '?'}), which is a cost check and not "
                f"a result."
            )
        return None

    @property
    def is_result(self) -> bool:
        return self.refusal() is None


def read(path: Path) -> RunRecord:
    """Read a record without judging it. Never raises; see :attr:`RunRecord.state`."""
    if not path.is_file():
        return RunRecord(path=path, state="absent")
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        return RunRecord(path=path, state="unreadable", detail=str(error))
    if len(rows) != 1:
        return RunRecord(
            path=path,
            state="unreadable",
            detail=f"a run record holds one row and this holds {len(rows)}",
        )
    fields = {
        str(name): (value or "")
        for name, value in rows[0].items()
        if name is not None and name not in _INDEX_COLUMNS
    }
    return RunRecord(path=path, state="recorded", fields=fields)


def result(path: Path) -> RunRecord:
    """The record, if and only if it says the tables beside it are a result.

    Raises:
        NotAResult: the record is absent, unreadable, a probe, or silent on ``probe``.
    """
    record = read(path)
    why = record.refusal()
    if why is not None:
        raise NotAResult(why)
    return record
