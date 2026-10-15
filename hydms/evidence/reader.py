"""L7 -- the Evidence Reader: every committed score, read once, with its reading and its run.

    evidence = reader.read()                 # never raises for absent or refused evidence
    evidence.score("transfer", "r2")         # a Score, possibly absent with its reason
    evidence.to_dict(), evidence.parity_dict()

**Why this module exists** (ADR 0007). The model-card page (#83) shows three scores, their
intervals, the per-family transfer scores and two parity panels, and all of it lives in tables
under ``reports/``. Whether a table is a probe's, whether its run record exists, and which of
the three scores a number is are decided **here, once**. The service calls :func:`read` at
startup and serves the result, so the page and the refusals it sits beside come from one
snapshot. No consumer opens these tables itself: that is how ``domain.transfer_table`` came to
serve a table without asking whether a probe wrote it (#105).

**It reads and never computes.** Every value is a cell of a committed table, copied. The
transfer score's interval is computed by ``python -m hydms.surrogate.loco --emit`` and the
procedure score's by ``python -m hydms.surrogate.evaluate``. The artifact score has none, and
says why. A number this module derived would be a fourth reading nobody generated.

**A score is never omitted and never guessed.** An absent table, an absent or unreadable run
record, or a record that says ``probe`` gives a :class:`Score` whose ``value`` is ``None`` and
whose ``absent_because`` says which. That is ``modelcard.py``'s rule ("an absent record is
reported as absent") applied to evidence. A page that dropped the row would let the optimistic
number stand alone, and that belief is what the page exists to counter.

**One mapping, in one place.** ``evaluation-metrics.csv`` calls its reading ``out-of-fold``, and
the leave-one-alloy-class-out rows are out-of-fold too. So ``out-of-fold`` means *procedure*
only when it comes from that file, and :data:`_EVALUATION_READING` is the only line that says
so.

Standard library only, like :mod:`hydms.provenance`: the service must be able to read its
evidence without the scientific stack, and a consumer must not need pandas to be told a number
is absent.

Card #83; ADR 0007.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from hydms import provenance
from hydms.config import repo_root

__all__ = [
    "ARTIFACT",
    "PROCEDURE",
    "READINGS",
    "SCHEMA",
    "TRANSFER",
    "Evidence",
    "Interval",
    "ParityRow",
    "Run",
    "Score",
    "read",
]

#: The payload's schema, served on ``GET /v1/evidence``. Bumped when a field changes meaning.
SCHEMA: Final = "hydms.evidence/1"

#: The three readings of one model (CONTEXT.md, **Score**). Nothing else is a reading.
PROCEDURE: Final = "procedure"
ARTIFACT: Final = "artifact"
TRANSFER: Final = "transfer"
READINGS: Final = (PROCEDURE, ARTIFACT, TRANSFER)

#: What ``evaluation-metrics.csv`` calls the procedure reading. The one place it is mapped.
_EVALUATION_READING: Final = {"out-of-fold": PROCEDURE}

#: The quantities served for each reading, with their units, in the order a page lists them.
QUANTITIES: Final[Mapping[str, str]] = {
    "r2": "",
    "rmse": "wt%",
    "mae": "wt%",
    "interval_coverage": "fraction",
    "interval_width": "wt%",
}

#: Where each table lives, relative to the repository root. Every file read is in the digest.
_MODEL: Final = Path("reports") / "model"
_LOCO: Final = Path("reports") / "loco"
EVALUATION_METRICS: Final = _MODEL / "evaluation-metrics.csv"
EVALUATION_SUBGROUPS: Final = _MODEL / "evaluation-subgroups.csv"
PROCEDURE_ROWS: Final = _MODEL / "model-out-of-fold.csv"
PROCEDURE_RECORD: Final = _MODEL / provenance.TRAIN_RECORD
ARTIFACT_SCORE: Final = _MODEL / "artifact-score.csv"
ARTIFACT_GATES: Final = _MODEL / "artifact-gates.json"
TRANSFER_SUMMARY: Final = _LOCO / "loco-summary.csv"
TRANSFER_PER_CLASS: Final = _LOCO / "loco-per-class.csv"
TRANSFER_INTERVALS: Final = _LOCO / "loco-intervals.csv"
TRANSFER_ROWS: Final = _LOCO / "loco-out-of-fold.csv"
TRANSFER_RECORD: Final = _LOCO / provenance.LOCO_RECORD

#: The resampling unit of the procedure score's published interval (``evaluate.GROUPS``).
_PROCEDURE_INTERVAL: Final = "out-of-fold canonical groups"

#: Facts about the deployed fit that the artifact table carries beside its scores, served as
#: they are written so the page can say what the artifact score is a score *of* (card #83):
#: how many rows the model grew on, how the band was calibrated, and against what.
ARTIFACT_FACTS: Final = (
    "rows_grown_on",
    "rows_calibration",
    "trees",
    "conformal_correction",
    "coverage_nominal",
    "coverage_standard_error",
    "coverage_raw",
    "width_raw",
)

#: Why the artifact score has no interval. A reason, served in place of one.
ARTIFACT_NO_INTERVAL: Final = (
    "scored once, on the held-out test split, which only gate AC-3 reads (card #103). A "
    "bootstrap of those 254 rows would be a second reader of the test split, so there is none"
)

#: The target column and the median head, as the scored-row tables name them.
_TARGET: Final = "H2_W% (max)"
_HEADS: Final = ("q0.1", "q0.5", "q0.9")


# --------------------------------------------------------------------------------------
# The objects
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Interval:
    """A score's confidence interval, with what it resampled and what it does not price."""

    low: float
    high: float
    confidence: float
    resampled: str
    caveat: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "low": self.low,
            "high": self.high,
            "confidence": self.confidence,
            "resampled": self.resampled,
            "caveat": self.caveat,
        }


@dataclass(frozen=True)
class Run:
    """Which run a score came from, as its own record states it.

    ``run_date`` is the record's ``started_at`` date, or ``None`` when the record predates the
    field. It is never filled from a commit (CONTEXT.md, **Run date**). ``committed_in`` is the
    commit that last changed the run's **scored table**, which is a commit's kind of fact and is
    labelled as one wherever it is shown. It is read off the table, not the record, because a
    rerun with unchanged settings writes a byte-identical pre-#105 record: the 2026-09-25 LOACO
    run left ``loco-run.csv`` as the 2026-09-06 run wrote it, and only its tables moved. ``version`` is set only for the artifact score, whose
    run is a gate run against an artifact version rather than a run of the pipeline.
    """

    record: str
    run_date: str | None
    started_at: str | None = None
    commit: str | None = None
    committed_in: str | None = None
    version: str | None = None
    kind: str = "run"

    @property
    def run_date_text(self) -> str:
        return self.run_date or provenance.NOT_RECORDED

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "record": self.record,
            "run_date": self.run_date,
            "run_date_text": self.run_date_text,
            "started_at": self.started_at,
            "commit": self.commit,
            "committed_in": self.committed_in,
            "version": self.version,
        }


@dataclass(frozen=True)
class Score:
    """One number about the model, with its reading, its interval or the reason it has none,
    and its run (CONTEXT.md, **Score**).

    ``subject`` is ``all`` for the model as a whole; ``macro`` and ``weighted`` for the two
    transfer averages; ``family:<class>`` for one alloy family's transfer score; and
    ``temperature:<bin>`` for one temperature bin of the procedure score. ``value`` is ``None``
    exactly when ``absent_because`` says why. A present value carries an interval **or**
    ``no_interval_because``, never both and never neither.
    """

    reading: str
    quantity: str
    subject: str
    value: float | None
    unit: str
    source: str
    run: Run
    rows: int | None = None
    interval: Interval | None = None
    no_interval_because: str | None = None
    absent_because: str | None = None

    def __post_init__(self) -> None:
        if self.reading not in READINGS:
            raise ValueError(f"{self.reading!r} is not a reading; the three are {READINGS}")
        if self.value is None:
            if not self.absent_because or self.interval is not None:
                raise ValueError(
                    f"{self.reading} {self.quantity}: an absent score carries its reason and "
                    f"no interval"
                )
            return
        if self.absent_because is not None:
            raise ValueError(f"{self.reading} {self.quantity}: a present score is not absent")
        if (self.interval is None) == (self.no_interval_because is None):
            raise ValueError(
                f"{self.reading} {self.quantity}: a present score carries an interval or the "
                f"reason it has none, exactly one of the two"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "reading": self.reading,
            "quantity": self.quantity,
            "subject": self.subject,
            "value": self.value,
            "unit": self.unit,
            "rows": self.rows,
            "interval": self.interval.to_dict() if self.interval is not None else None,
            "no_interval_because": self.no_interval_because,
            "absent_because": self.absent_because,
            "source": self.source,
            "run": self.run.to_dict(),
        }


@dataclass(frozen=True)
class ParityRow:
    """One scored row: the measurement, the median head, and the raw 10-90 band around it."""

    measured: float
    predicted: float
    lower: float
    upper: float
    fold: str
    temperature_k: float
    composition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "measured": self.measured,
            "predicted": self.predicted,
            "lower": self.lower,
            "upper": self.upper,
            "fold": self.fold,
            "temperature_k": self.temperature_k,
            "composition": self.composition,
        }


@dataclass(frozen=True)
class Evidence:
    """Everything :func:`read` found, and a digest of every byte it read."""

    scores: tuple[Score, ...]
    parity: Mapping[str, tuple[ParityRow, ...]]
    parity_absent: Mapping[str, str]
    parity_runs: Mapping[str, Run]
    digest: str
    sources: tuple[str, ...] = field(default_factory=tuple)
    artifact_facts: Mapping[str, float] = field(default_factory=dict)

    def score(self, reading: str, quantity: str, subject: str = "all") -> Score:
        """The one score for this reading, quantity and subject.

        Raises:
            KeyError: no such score was ever read. That is a programming error, not an absence:
                an absent score is still returned, with its reason.
        """
        for found in self.scores:
            if (found.reading, found.quantity, found.subject) == (reading, quantity, subject):
                return found
        raise KeyError(f"no {reading} {quantity} score for {subject!r}")

    def of(self, reading: str) -> tuple[Score, ...]:
        return tuple(found for found in self.scores if found.reading == reading)

    def to_dict(self) -> dict[str, Any]:
        """``GET /v1/evidence``: the scores, without the scored rows."""
        return {
            "schema": SCHEMA,
            "digest": self.digest,
            "sources": list(self.sources),
            "scores": [found.to_dict() for found in self.scores],
            "artifact_facts": dict(self.artifact_facts),
        }

    def parity_dict(self) -> dict[str, Any]:
        """``GET /v1/evidence/parity``: the scored rows, one list per reading, or its absence."""
        return {
            "schema": SCHEMA,
            "digest": self.digest,
            "level": 0.8,
            "band": "raw 10th to 90th percentile heads, before conformal calibration",
            "readings": {
                reading: {
                    "rows": [row.to_dict() for row in self.parity.get(reading, ())],
                    "absent_because": self.parity_absent.get(reading),
                    "run": self.parity_runs[reading].to_dict(),
                }
                for reading in (PROCEDURE, TRANSFER)
            },
        }


# --------------------------------------------------------------------------------------
# Reading the files
# --------------------------------------------------------------------------------------


class _Files:
    """Every file :func:`read` opens, so the digest covers exactly what was served."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.read: dict[str, bytes] = {}

    def text(self, relative: Path) -> str | None:
        path = self.root / relative
        try:
            data = path.read_bytes()
        except OSError:
            return None
        self.read[relative.as_posix()] = data
        return data.decode("utf-8")

    def rows(self, relative: Path) -> list[dict[str, str]] | None:
        text = self.text(relative)
        if text is None:
            return None
        lines = [line for line in text.splitlines() if not line.startswith("#")]
        return [dict(row) for row in csv.DictReader(lines)]

    def digest(self) -> str:
        hasher = hashlib.sha256()
        for name in sorted(self.read):
            hasher.update(name.encode("utf-8") + b"\0")
            hasher.update(hashlib.sha256(self.read[name]).digest())
        return hasher.hexdigest()


def _number(text: str | None) -> float | None:
    if text is None or text.strip() == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _committed_in(root: Path, relative: Path) -> str | None:
    """The short commit that last changed ``relative``, or ``None`` when git cannot say."""
    try:
        done = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", relative.as_posix()],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = done.stdout.strip()
    return sha or None


#: The table whose commit names each run: the one the run itself wrote and every rerun rewrites.
_SCORED_BY: Final[Mapping[Path, Path]] = {
    PROCEDURE_RECORD: PROCEDURE_ROWS,
    TRANSFER_RECORD: TRANSFER_PER_CLASS,
}


def _run(root: Path, files: _Files, relative: Path) -> tuple[Run, str | None]:
    """The run behind a record, and why its tables are not a result -- or ``None`` if they are."""
    files.text(relative)
    record = provenance.read(root / relative)
    run = Run(
        record=relative.as_posix(),
        run_date=record.run_date,
        started_at=record.get("started_at") or None,
        commit=record.get("git_sha") or None,
        committed_in=(
            _committed_in(root, _SCORED_BY.get(relative, relative))
            if record.state != "absent"
            else None
        ),
    )
    return run, record.refusal()


def _absent(
    reading: str, subject: str, source: Path, run: Run, why: str, quantities: Iterable[str]
) -> list[Score]:
    return [
        Score(
            reading=reading,
            quantity=name,
            subject=subject,
            value=None,
            unit=QUANTITIES.get(name, ""),
            source=source.as_posix(),
            run=run,
            absent_because=why,
        )
        for name in quantities
    ]


# --------------------------------------------------------------------------------------
# The three readings
# --------------------------------------------------------------------------------------


def _procedure(root: Path, files: _Files) -> list[Score]:
    run, refused = _run(root, files, PROCEDURE_RECORD)
    table = files.rows(EVALUATION_METRICS)
    if refused is not None:
        return _absent(PROCEDURE, "all", EVALUATION_METRICS, run, refused, QUANTITIES)
    if table is None:
        why = (
            f"{EVALUATION_METRICS.as_posix()} is not on disk. It is written by "
            f"`python -m hydms.surrogate.evaluate`, from the training run's tables."
        )
        return _absent(PROCEDURE, "all", EVALUATION_METRICS, run, why, QUANTITIES)

    scores = []
    for name, unit in QUANTITIES.items():
        match = [
            row
            for row in table
            if _EVALUATION_READING.get(row.get("reading", "")) == PROCEDURE
            and row.get("scale") == "wt_pct"
            and row.get("subgroup") == "all"
            and row.get("interval_from") == _PROCEDURE_INTERVAL
            and row.get("metric") == name
        ]
        scores.append(
            _from_evaluation(match, name, unit, "all", run, EVALUATION_METRICS)
        )

    subgroups = files.rows(EVALUATION_SUBGROUPS) or []
    for row in subgroups:
        if (
            _EVALUATION_READING.get(row.get("reading", "")) == PROCEDURE
            and row.get("scale") == "wt_pct"
            and row.get("subgroup") == "temperature"
            and row.get("metric") == "r2"
        ):
            subject = f"temperature:{row.get('subgroup_value', '')}"
            scores.append(_from_evaluation([row], "r2", "", subject, run, EVALUATION_SUBGROUPS))
    return scores


def _from_evaluation(
    match: list[dict[str, str]], name: str, unit: str, subject: str, run: Run, source: Path
) -> Score:
    if len(match) != 1:
        return Score(
            reading=PROCEDURE,
            quantity=name,
            subject=subject,
            value=None,
            unit=unit,
            source=source.as_posix(),
            run=run,
            absent_because=(
                f"{source.as_posix()} holds {len(match)} out-of-fold row(s) for {name} over "
                f"canonical groups in wt%, where one was expected"
            ),
        )
    row = match[0]
    value = _number(row.get("point"))
    low, high = _number(row.get("ci_low")), _number(row.get("ci_high"))
    confidence = _number(row.get("confidence"))
    if value is None:
        return Score(
            reading=PROCEDURE, quantity=name, subject=subject, value=None, unit=unit,
            source=source.as_posix(), run=run,
            absent_because=f"{source.as_posix()} holds no finite {name} for {subject!r}",
        )
    interval = (
        Interval(
            low=low,
            high=high,
            confidence=confidence,
            resampled=row.get("interval_from", ""),
            caveat=row.get("interval_caveat", ""),
        )
        if low is not None and high is not None and confidence is not None
        else None
    )
    rows = _number(row.get("rows"))
    return Score(
        reading=PROCEDURE,
        quantity=name,
        subject=subject,
        value=value,
        unit=unit,
        source=source.as_posix(),
        run=run,
        rows=int(rows) if rows is not None else None,
        interval=interval,
        no_interval_because=(
            None if interval is not None else f"{source.as_posix()} records no finite bounds"
        ),
    )


#: The artifact table's quantities, by the name this module serves them under.
_ARTIFACT_QUANTITY: Final[Mapping[str, tuple[str, str]]] = {
    "r2": ("r2", "AC-1"),
    "rmse": ("rmse", "AC-1"),
    "mae": ("mae", "AC-1"),
    "interval_coverage": ("coverage_calibrated", "AC-3"),
    "interval_width": ("width_calibrated", "AC-3"),
}


def _artifact(root: Path, files: _Files) -> list[Score]:
    gates_text = files.text(ARTIFACT_GATES)
    gates: dict[str, Any] = {}
    if gates_text is not None:
        try:
            loaded = json.loads(gates_text)
            gates = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            gates = {}
    started = gates.get("gate_run_started_at")
    run = Run(
        record=ARTIFACT_GATES.as_posix(),
        run_date=str(started)[:10] if started else None,
        started_at=str(started) if started else None,
        committed_in=_committed_in(root, ARTIFACT_GATES) if gates_text is not None else None,
        version=str(gates["version"]) if gates.get("version") else None,
        kind="gate run",
    )
    table = files.rows(ARTIFACT_SCORE)
    if table is None or not gates:
        why = (
            f"{ARTIFACT_SCORE.as_posix()} or its sealed record {ARTIFACT_GATES.as_posix()} is "
            f"not on disk. Both are written by `python -m hydms.evidence.artifact_score "
            f"--probe --emit` after a promotion (card #103)."
        )
        return _absent(ARTIFACT, "all", ARTIFACT_SCORE, run, why, QUANTITIES)

    by_name = {row.get("quantity", ""): row for row in table}
    scores = []
    for name, unit in QUANTITIES.items():
        column, gate = _ARTIFACT_QUANTITY[name]
        row = by_name.get(column)
        value = _number(row.get("value")) if row is not None else None
        if row is None or value is None or row.get("gate") != gate:
            scores.append(
                Score(
                    reading=ARTIFACT, quantity=name, subject="all", value=None, unit=unit,
                    source=ARTIFACT_SCORE.as_posix(), run=run,
                    absent_because=(
                        f"{ARTIFACT_SCORE.as_posix()} has no {column} row from {gate}"
                    ),
                )
            )
            continue
        rows = _number(row.get("rows"))
        scores.append(
            Score(
                reading=ARTIFACT,
                quantity=name,
                subject="all",
                value=value,
                unit=unit,
                source=ARTIFACT_SCORE.as_posix(),
                run=run,
                rows=int(rows) if rows is not None else None,
                no_interval_because=ARTIFACT_NO_INTERVAL,
            )
        )
    return scores


def _artifact_facts(files: _Files) -> dict[str, float]:
    """:data:`ARTIFACT_FACTS` from the artifact table; a fact it does not hold is left out."""
    facts: dict[str, float] = {}
    for row in files.rows(ARTIFACT_SCORE) or ():
        name = row.get("quantity", "")
        value = _number(row.get("value"))
        if name in ARTIFACT_FACTS and value is not None:
            facts[name] = value
    return facts


def _transfer(root: Path, files: _Files) -> list[Score]:
    run, refused = _run(root, files, TRANSFER_RECORD)
    summary = files.rows(TRANSFER_SUMMARY)
    per_class = files.rows(TRANSFER_PER_CLASS)
    intervals = files.rows(TRANSFER_INTERVALS)
    wanted = ("r2", "mae")
    if refused is not None:
        return _absent(TRANSFER, "macro", TRANSFER_SUMMARY, run, refused, wanted)
    if summary is None or per_class is None or len(summary) != 1:
        why = (
            f"{TRANSFER_SUMMARY.as_posix()} and {TRANSFER_PER_CLASS.as_posix()} are not both on "
            f"disk with one model. They are written by `python -m hydms.surrogate.loco "
            f"--target capacity`, a run of about five hours (card #30)."
        )
        return _absent(TRANSFER, "macro", TRANSFER_SUMMARY, run, why, wanted)

    bounds = {row.get("subject", ""): row for row in intervals or ()}
    no_interval = (
        f"{TRANSFER_INTERVALS.as_posix()} is not on disk. It is written by "
        f"`python -m hydms.surrogate.loco --emit` from the committed scored rows."
    )

    def scored(subject: str, value: float | None, source: Path, rows: int | None) -> Score:
        if value is None:
            return Score(
                reading=TRANSFER, quantity="r2", subject=subject, value=None, unit="",
                source=source.as_posix(), run=run,
                absent_because=f"{source.as_posix()} holds no finite R2 for {subject!r}",
            )
        row = bounds.get(subject if not subject.startswith("family:") else
                         "class:" + subject.split(":", 1)[1])
        interval = None
        if row is not None:
            low, high = _number(row.get("ci_low")), _number(row.get("ci_high"))
            confidence = _number(row.get("confidence"))
            if low is not None and high is not None and confidence is not None:
                interval = Interval(
                    low=low,
                    high=high,
                    confidence=confidence,
                    resampled=row.get("interval_from", ""),
                    caveat=row.get("interval_caveat", ""),
                )
        return Score(
            reading=TRANSFER,
            quantity="r2",
            subject=subject,
            value=value,
            unit="",
            source=source.as_posix(),
            run=run,
            rows=rows,
            interval=interval,
            no_interval_because=None if interval is not None else no_interval,
        )

    once = summary[0]
    rows_scored = _number(once.get("rows_scored"))
    support = int(rows_scored) if rows_scored is not None else None
    macro_mae = _number(once.get("macro_mae"))
    scores = [
        scored("macro", _number(once.get("macro_r2")), TRANSFER_SUMMARY, support),
        scored("weighted", _number(once.get("weighted_r2")), TRANSFER_SUMMARY, support),
        Score(
            reading=TRANSFER,
            quantity="mae",
            subject="macro",
            value=macro_mae,
            unit="wt%",
            source=TRANSFER_SUMMARY.as_posix(),
            run=run,
            rows=support,
            no_interval_because=(
                "the transfer intervals are computed for R2 only (`loco --emit`)"
                if macro_mae is not None
                else None
            ),
            absent_because=(
                None if macro_mae is not None
                else f"{TRANSFER_SUMMARY.as_posix()} holds no finite macro_mae"
            ),
        ),
    ]
    for row in sorted(per_class, key=lambda found: found.get("alloy_class", "")):
        family = row.get("alloy_class", "")
        held_out = _number(row.get("rows_scored"))
        if row.get("estimable", "").strip().lower() not in ("true", "1"):
            scores.append(
                Score(
                    reading=TRANSFER, quantity="r2", subject=f"family:{family}", value=None,
                    unit="", source=TRANSFER_PER_CLASS.as_posix(), run=run,
                    rows=int(held_out) if held_out is not None else None,
                    absent_because=(
                        f"not estimable: {row.get('not_estimable_because') or 'no reason given'}"
                    ),
                )
            )
            continue
        scores.append(
            scored(f"family:{family}", _number(row.get("r2")), TRANSFER_PER_CLASS,
                   int(held_out) if held_out is not None else None)
        )
    return scores


def _parity(
    root: Path, files: _Files, reading: str, table: Path, record: Path
) -> tuple[tuple[ParityRow, ...], str | None, Run]:
    run, refused = _run(root, files, record)
    if refused is not None:
        return (), refused, run
    rows = files.rows(table)
    if rows is None:
        return (), f"{table.as_posix()} is not on disk, so this panel has no rows to draw.", run
    parsed = []
    for row in rows:
        values = [_number(row.get(name)) for name in (_TARGET, *_HEADS, "temperature(K)")]
        if any(value is None for value in values):
            return (), (
                f"{table.as_posix()} has a row without a finite measurement, head or "
                f"temperature, so it is not served as a partial panel"
            ), run
        measured, lower, predicted, upper, kelvin = (float(v) for v in values if v is not None)
        parsed.append(
            ParityRow(
                measured=measured,
                predicted=predicted,
                lower=lower,
                upper=upper,
                fold=row.get("fold", ""),
                temperature_k=kelvin,
                composition=row.get("canonical_key", ""),
            )
        )
    if not parsed:
        return (), f"{table.as_posix()} holds no scored rows.", run
    return tuple(parsed), None, run


def read(root: Path | None = None) -> Evidence:
    """Read every committed score and both sets of scored rows. Never raises for missing or
    refused evidence; each absence is a :class:`Score` or a parity entry with its reason."""
    base = root if root is not None else repo_root()
    files = _Files(base)
    scores = (*_procedure(base, files), *_artifact(base, files), *_transfer(base, files))
    parity: dict[str, tuple[ParityRow, ...]] = {}
    absent: dict[str, str] = {}
    runs: dict[str, Run] = {}
    for reading, table, record in (
        (PROCEDURE, PROCEDURE_ROWS, PROCEDURE_RECORD),
        (TRANSFER, TRANSFER_ROWS, TRANSFER_RECORD),
    ):
        rows, why, run = _parity(base, files, reading, table, record)
        runs[reading] = run
        if why is None:
            parity[reading] = rows
        else:
            absent[reading] = why
    return Evidence(
        scores=tuple(scores),
        parity=parity,
        parity_absent=absent,
        parity_runs=runs,
        digest=files.digest(),
        sources=tuple(sorted(files.read)),
        artifact_facts=_artifact_facts(files),
    )
