"""L6 -- the batch screening page, as data: a CSV of candidates in, a CSV of answers out.

``app/pages/2_Batch_screening.py`` (card #84) is a Streamlit script, and Streamlit is in the
``app`` extra CI does not install. So everything the page *promises* is decided here, where the
fast lane runs it, and the script only lays out what this module returns -- the split
:mod:`hydms.delivery.page` makes for the forward page, for the same reason.

The risk a batch path introduces is that refusals become invisible: a spreadsheet of numbers
with a few blank cells reads as a spreadsheet of numbers. So:

* **Every row goes out.** One output row per input row, in input order, whatever happened to it
  -- answered, refused by the model's screens, or never asked because the row could not be
  read. There is no code path that returns fewer rows than it read.
* **A row with no number says so in every number's place.** A refused or unread row carries its
  status word in the capacity and interval columns, never an empty cell, so a sorted or filtered
  spreadsheet cannot turn it into a low prediction.
* **The summary comes first.** :meth:`Screening.summary` counts the refusals by code and the
  unread rows by cause, and the page shows it above the download.
* **The version is on every row**, and in the file name.

How a missing value is read -- and why ``NaN`` is not one by default
--------------------------------------------------------------------

This module reads CSV with the standard library, which turns nothing into anything: every cell
is the text that was in the file. That is the decision #76 left here, made explicit. pandas'
default ``na_values`` would turn a cell reading ``NaN`` into a float -- and **``NaN`` is a
formula**: sodium and nitrogen, to both parsers in this project, featurising to real numbers and
answerable with a confident capacity. #76 measured every other spelling of a missing value and
each one is refused by the grammar; ``NaN`` is the one that survives, and once it is a string
it is indistinguishable from chemistry. So:

* A cell that is empty, or reads as one of :data:`MISSING_TOKENS`, is **missing**: the row is
  not asked, and the summary names it. Every token in that set fails the formula grammar
  (``tests/delivery/test_batch.py`` checks it against the real parser), so reading it as
  missing can never refuse a real material.
* A formula cell reading exactly ``NaN`` is **ambiguous**, and the reader does not guess.
  ``df.to_csv(na_rep="NaN")`` writes exactly that for a missing value, and a chemist may write
  it for sodium nitride. :func:`read_upload` reports the rows (:attr:`Upload.literal_nan`) and
  refuses to produce requests until the caller says which it is (``nan_means``). Refusing the
  string outright would refuse a real material; answering it would answer a blank cell.

Card #84. The batched call it rides on is :func:`hydms.delivery.predict.predict_many`.
"""

from __future__ import annotations

import csv
import io
import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from hydms.delivery.contract import (
    Answer,
    ContractError,
    PredictionRequest,
    PredictionResult,
    Refusal,
)

__all__ = [
    "ANSWERED",
    "COLUMNS",
    "EMPTY_CELL",
    "FORMULA_HEADERS",
    "LITERAL_NAN",
    "MAX_UPLOAD_ROWS",
    "MISSING_TOKENS",
    "NAN_IS_FORMULA",
    "NAN_IS_MISSING",
    "REFUSED",
    "TEMPERATURE_HEADERS",
    "UNREAD",
    "Row",
    "Screening",
    "Upload",
    "UploadError",
    "read_upload",
    "screening",
]

#: The most data rows one upload may carry. The service answers at 0.7-1.0 ms a row end to
#: end (``hydms.delivery.api.service.MAX_BATCH_ROWS`` has the measurement), so 10,000 rows is
#: about ten seconds in three requests, and about 11 MB of answers held by the page. Past that
#: the page is the wrong tool: call :func:`~hydms.delivery.predict.predict_many` directly.
MAX_UPLOAD_ROWS = 10_000

#: Header names accepted for the two columns, compared case-insensitively after stripping.
#: ``Composition`` and ``temperature(K)`` are the curated corpus' own spellings, so the
#: project's data file can be uploaded as it is.
FORMULA_HEADERS = ("formula", "composition")
TEMPERATURE_HEADERS = ("temperature_k", "temperature(k)", "temperature", "t_k")

#: Cell texts read as a missing value, after stripping. Each fails
#: :func:`~hydms.data.load.parse_formula` -- asserted by the tests, since a token here that
#: parsed would be a real material refused as a blank. ``NaN`` is deliberately absent: see
#: the module docstring.
MISSING_TOKENS = frozenset(
    {"", "nan", "NA", "N/A", "n/a", "#N/A", "null", "NULL", "None", "none", "<NA>", "NaT", "-"}
)

#: The one spelling of a missing value that is also a formula.
LITERAL_NAN = "NaN"
#: The caller's two possible readings of a formula cell that says :data:`LITERAL_NAN`.
NAN_IS_MISSING = "missing"
NAN_IS_FORMULA = "formula"

#: A row's status: the model answered it, the model's screens refused it, or it was never asked.
ANSWERED = "answered"
REFUSED = "refused"
UNREAD = "unread"

#: How an input cell that was empty is echoed in the output.
EMPTY_CELL = "(empty)"

#: The download's columns, in order. ``status`` comes before any number so that a reader who
#: sees one sees the other.
COLUMNS = (
    "row",
    "formula",
    "temperature_k",
    "status",
    "code",
    "reason",
    "capacity_wt_pct",
    "lower_wt_pct",
    "upper_wt_pct",
    "interval_width_wt_pct",
    "interval_level",
    "elmd_distance",
    "nearest_known_alloy",
    "model_version",
)


class UploadError(ValueError):
    """The file as a whole cannot be read: no header, a missing column, too many rows.

    A problem with one *row* is never this: that row is read as :data:`UNREAD`, named in the
    summary, and carried to the output like every other.
    """


@dataclass(frozen=True)
class Row:
    """One data row of the upload, as read.

    Attributes:
        number: The row's position among the data rows, from 1 -- what a spreadsheet user
            counts. :attr:`line` is the file line, header included, for an editor.
        line: The line in the file the row starts on.
        formula: The formula cell's text, exactly as written.
        temperature: The temperature cell's text, exactly as written.
        request: The request built from it, or ``None`` if the row cannot be asked.
        problem: Why the row cannot be asked -- a sentence naming the row -- or ``None``.
        cause: A short fixed label for :attr:`problem`, for counting in the summary.
    """

    number: int
    line: int
    formula: str
    temperature: str
    request: PredictionRequest | None
    problem: str | None = None
    cause: str | None = None


@dataclass(frozen=True)
class Upload:
    """A CSV as read: every data row, and the one decision the reader would not make alone.

    Attributes:
        rows: Every non-blank data row, in file order.
        blank_lines: How many wholly empty lines were skipped. Counted, because a line that is
            not read should still be accounted for.
        literal_nan: Row numbers whose formula cell reads exactly :data:`LITERAL_NAN`.
        nan_means: The caller's reading of those cells, or ``None`` if not yet given.
    """

    rows: tuple[Row, ...]
    blank_lines: int
    literal_nan: tuple[int, ...]
    nan_means: str | None

    @property
    def needs_decision(self) -> bool:
        """True while some formula cell reads ``NaN`` and nobody has said what it means."""
        return bool(self.literal_nan) and self.nan_means is None

    def requests(self) -> list[PredictionRequest]:
        """The readable rows' requests, in row order -- what goes to the service.

        Raises:
            UploadError: a ``NaN`` formula cell is still undecided. Answering it would be
                answering either a blank cell or sodium nitride without knowing which.
        """
        if self.needs_decision:
            raise UploadError(_undecided(self.literal_nan))
        return [row.request for row in self.rows if row.request is not None]


def _undecided(numbers: Sequence[int]) -> str:
    return (
        f"{len(numbers)} formula cell(s) read exactly {LITERAL_NAN!r} (row(s) "
        f"{_listed(numbers)}). That is sodium nitride to the parser and it is also what "
        f"pandas writes for a missing value (to_csv(na_rep='NaN')). Say which it is: "
        f"nan_means={NAN_IS_MISSING!r} or nan_means={NAN_IS_FORMULA!r}."
    )


def _listed(numbers: Sequence[int], limit: int = 8) -> str:
    shown = ", ".join(str(number) for number in numbers[:limit])
    return shown if len(numbers) <= limit else f"{shown}, ... ({len(numbers) - limit} more)"


def _column(header: Sequence[str], accepted: Sequence[str], what: str) -> int:
    folded = [cell.strip().lower() for cell in header]
    found = [index for index, cell in enumerate(folded) if cell in accepted]
    if not found:
        raise UploadError(
            f"the file has no {what} column. Its header is {list(header)!r}; the {what} column "
            f"must be named one of {', '.join(repr(name) for name in accepted)} (any case)."
        )
    if len(found) > 1:
        raise UploadError(
            f"the file has {len(found)} {what} columns ({', '.join(repr(header[i]) for i in found)}), "
            f"and which one to read is not this page's guess. Keep one."
        )
    return found[0]


def _dialect(text: str) -> type[csv.Dialect] | csv.Dialect:
    """Comma, semicolon or tab, whichever the header uses; comma when it cannot tell."""
    first = text.split("\n", 1)[0]
    try:
        return csv.Sniffer().sniff(first, delimiters=",;\t")
    except csv.Error:
        return csv.excel


def read_upload(
    data: bytes | str,
    *,
    nan_means: str | None = None,
    max_rows: int = MAX_UPLOAD_ROWS,
) -> Upload:
    """Read a CSV of candidates: a formula column and a temperature column, in kelvin.

    Args:
        data: The file's bytes (UTF-8, with or without Excel's byte-order mark) or its text.
        nan_means: What a formula cell reading exactly ``NaN`` means -- :data:`NAN_IS_MISSING`
            or :data:`NAN_IS_FORMULA`. ``None`` leaves the question open, and
            :meth:`Upload.requests` refuses until it is answered.
        max_rows: The row limit; :data:`MAX_UPLOAD_ROWS` unless a caller has its own.

    Returns:
        An :class:`Upload` with every non-blank data row, readable or not.

    Raises:
        UploadError: the file is not UTF-8, has no header, lacks either column, names one
            twice, or has more than ``max_rows`` rows. Each sentence says which.
    """
    if nan_means not in (None, NAN_IS_MISSING, NAN_IS_FORMULA):
        raise ValueError(
            f"nan_means is {nan_means!r}; it is {NAN_IS_MISSING!r}, {NAN_IS_FORMULA!r} or None."
        )
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise UploadError(
                f"the file is not UTF-8 text (byte {error.start} cannot be decoded). Save it "
                f"as CSV UTF-8 and upload it again."
            ) from error
    else:
        text = data.removeprefix("﻿")

    reader = csv.reader(io.StringIO(text, newline=""), _dialect(text))
    header = next(reader, None)
    if header is None or not any(cell.strip() for cell in header):
        raise UploadError("the file is empty; it needs a header row and at least one data row.")
    at_formula = _column(header, FORMULA_HEADERS, "formula")
    at_kelvin = _column(header, TEMPERATURE_HEADERS, "temperature")

    rows: list[Row] = []
    blank = 0
    nans: list[int] = []
    for cells in reader:
        if not any(cell.strip() for cell in cells):
            blank += 1
            continue
        number = len(rows) + 1
        if number > max_rows:
            raise UploadError(
                f"the file has more than {max_rows:,} data rows, which is this page's limit. "
                f"Split it, or call hydms.delivery.predict_many() directly."
            )
        row = _row(number, reader.line_num, cells, len(header), at_formula, at_kelvin, nan_means)
        if row.formula.strip() == LITERAL_NAN:
            nans.append(number)
        rows.append(row)
    if not rows:
        raise UploadError("the file has a header and no data rows.")
    return Upload(rows=tuple(rows), blank_lines=blank, literal_nan=tuple(nans), nan_means=nan_means)


def _row(
    number: int,
    line: int,
    cells: Sequence[str],
    width: int,
    at_formula: int,
    at_kelvin: int,
    nan_means: str | None,
) -> Row:
    """One data row, and either its request or the sentence saying why it has none."""
    formula = cells[at_formula] if at_formula < len(cells) else ""
    kelvin = cells[at_kelvin] if at_kelvin < len(cells) else ""

    def unread(cause: str, sentence: str) -> Row:
        return Row(number, line, formula, kelvin, None, f"row {number}: {sentence}", cause)

    if len(cells) != width:
        return unread(
            "wrong number of cells",
            f"it has {len(cells)} cell(s) and the header has {width}, so which cell is which "
            f"column is a guess. Fix the row.",
        )
    stripped = formula.strip()
    if stripped in MISSING_TOKENS:
        return unread(
            "missing formula",
            "the formula cell is empty"
            + (f" (it reads {stripped!r}, a spelling of a missing value)" if stripped else "")
            + ". Nothing was asked about this row.",
        )
    if stripped == LITERAL_NAN and nan_means != NAN_IS_FORMULA:
        if nan_means is None:
            # Not asked yet, and not asked at all until the caller decides: `requests()`
            # refuses while any of these are open.
            return Row(number, line, formula, kelvin, None, None, None)
        return unread(
            "missing formula",
            f"the formula cell reads {LITERAL_NAN!r}, which you said this file uses for a "
            f"missing value. Nothing was asked about this row.",
        )
    if kelvin.strip() in MISSING_TOKENS or kelvin.strip() == LITERAL_NAN:
        return unread(
            "missing temperature",
            "the temperature cell is empty. The model needs a temperature in kelvin for every "
            "row; it is one of the features.",
        )
    try:
        value = float(kelvin.strip())
    except ValueError:
        return unread(
            "unreadable temperature",
            f"the temperature cell reads {kelvin.strip()!r}, which is not a number. Write it in "
            f"kelvin with no unit, e.g. 298.",
        )
    if not math.isfinite(value):
        return unread(
            "unreadable temperature",
            f"the temperature cell reads {kelvin.strip()!r}, which is not a finite number of "
            f"kelvin.",
        )
    try:
        request = PredictionRequest(formula=formula, temperature_k=value)
    except ContractError as error:  # pragma: no cover -- every case above is caught first
        return unread("unreadable row", str(error))
    return Row(number, line, formula, kelvin, request)


# --------------------------------------------------------------------------------------
# The answers, as a table and a summary
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Screening:
    """The upload beside its answers: one output row per input row, in input order.

    Built by :func:`screening`. ``records`` are the download's rows as dicts keyed by
    :data:`COLUMNS`, every value a string or a number and none of them empty.
    """

    records: tuple[dict[str, object], ...]
    version: str
    blank_lines: int

    def count(self, status: str) -> int:
        return sum(1 for record in self.records if record["status"] == status)

    def summary(self) -> list[str]:
        """What happened to the file, in sentences, refusals first. Shown before any download."""
        total = len(self.records)
        answered, refused, unread = (self.count(s) for s in (ANSWERED, REFUSED, UNREAD))
        lines = [
            f"{total:,} row(s) read. {answered:,} answered by model {self.version}, "
            f"{refused:,} refused by the model's screens, {unread:,} not asked because the "
            f"row could not be read."
        ]
        by_code = Counter(str(r["code"]) for r in self.records if r["status"] == REFUSED)
        if by_code:
            lines.append(
                "Refused, by reason: "
                + "; ".join(f"{code} x {n:,}" for code, n in by_code.most_common())
                + ". A refused row is not a low prediction: there is no number for it."
            )
        by_cause = Counter(str(r["code"]) for r in self.records if r["status"] == UNREAD)
        if by_cause:
            lines.append(
                "Not asked, by cause: "
                + "; ".join(
                    f"{cause} x {n:,} (row(s) {_listed(self._rows(cause))})"
                    for cause, n in by_cause.most_common()
                )
                + "."
            )
        if self.blank_lines:
            lines.append(f"{self.blank_lines:,} wholly empty line(s) were skipped.")
        return lines

    def _rows(self, cause: str) -> list[int]:
        return [
            int(str(r["row"]))
            for r in self.records
            if r["status"] == UNREAD and r["code"] == cause
        ]

    def ordered(self, by_width: bool = False) -> list[dict[str, object]]:
        """The rows as uploaded, or the widest interval first.

        Widest first is how the least certain answers are found. Rows with no interval --
        refused and unread -- come after every answered row, in upload order: they are not
        narrow and not wide, and sorting them among the numbers would give them a place on a
        scale they are not on.
        """
        if not by_width:
            return list(self.records)
        answered = [r for r in self.records if r["status"] == ANSWERED]
        rest = [r for r in self.records if r["status"] != ANSWERED]
        answered.sort(key=lambda r: -float(str(r["interval_width_wt_pct"])))
        return answered + rest

    def shown(self, by_width: bool = False) -> list[dict[str, str]]:
        """:meth:`ordered`, every cell as text, numbers to four significant figures.

        For the page's table. A column that mixes numbers with the word ``refused`` is exactly
        what the download must carry, and exactly what a typed table widget cannot hold; text
        in every cell keeps the word where the number would be. The download keeps full
        precision.
        """
        return [
            {
                column: f"{value:.4g}" if isinstance(value, float) else str(value)
                for column, value in record.items()
            }
            for record in self.ordered(by_width)
        ]

    def to_csv(self, by_width: bool = False) -> str:

        """The download: :data:`COLUMNS`, one row per uploaded row, the version on each."""
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {column: _inert(value) for column, value in record.items()}
            for record in self.ordered(by_width)
        )
        return out.getvalue()

    @property
    def file_name(self) -> str:
        return f"hydms-screening-{self.version}.csv"


def screening(upload: Upload, answers: Sequence[Answer], *, version: str) -> Screening:
    """Pair every uploaded row with its answer, or with the reason it was never asked.

    Args:
        upload: What :func:`read_upload` returned, with its ``NaN`` question settled.
        answers: The service's answers to ``upload.requests()``, in that order.
        version: The artifact version the service reported. Every answer carries its own and
            they are checked against it, because a download that mixed two versions would be
            two models' numbers in one column.

    Raises:
        UploadError: the ``NaN`` question is open.
        ValueError: the answers do not line up with the requests, or name another version.
    """
    asked = upload.requests()
    if len(answers) != len(asked):
        raise ValueError(
            f"{len(asked)} row(s) were asked and {len(answers)} answer(s) came back; pairing "
            f"them would attach answers to the wrong rows."
        )
    pending = iter(answers)
    records: list[dict[str, object]] = []
    for row in upload.rows:
        if row.request is None:
            records.append(_unread(row, version))
            continue
        answer = next(pending)
        if answer.request != row.request:
            raise ValueError(
                f"row {row.number} asked {row.request.to_dict()} and the answer in its place is "
                f"about {answer.request.to_dict()}; the service reordered the batch."
            )
        if answer.model_version != version:
            raise ValueError(
                f"row {row.number} was answered by model {answer.model_version!r} and the "
                f"service reports {version!r}. One download holds one model's answers."
            )
        records.append(_answered(row, answer) if not answer.refused else _refused(row, answer))
    return Screening(records=tuple(records), version=version, blank_lines=upload.blank_lines)


#: A cell starting with one of these is run as a formula by Excel and LibreOffice (OWASP's
#: "CSV injection"). The download echoes the uploaded formula and temperature cells, so a
#: file shared onward could carry one; no chemical formula this project parses starts with
#: any of them, so prefixing an apostrophe changes no composition anyone could have meant.
_ACTIVE = ("=", "+", "-", "@", "\t", "\r")


def _inert(value: object) -> object:
    if isinstance(value, str) and value.startswith(_ACTIVE):
        return "'" + value
    return value


def _base(row: Row, status: str, code: str, reason: str, version: str) -> dict[str, object]:

    given = {
        "row": row.number,
        # An empty input cell is echoed as a word, not as an empty cell: the row's reason
        # says the cell was empty, and a blank here would be the one blank in the file.
        "formula": row.formula or EMPTY_CELL,
        "temperature_k": row.temperature.strip() or EMPTY_CELL,
        "status": status,
        "code": code,
        "reason": reason,
        "model_version": version,
    }
    # Never an empty cell where a number would be: the status word, so a sorted or filtered
    # spreadsheet cannot turn a refusal into a low prediction. Built in `COLUMNS` order, so a
    # record read as a row is already in the download's order.
    return {column: given.get(column, status) for column in COLUMNS}


def _unread(row: Row, version: str) -> dict[str, object]:
    assert row.problem is not None and row.cause is not None
    return _base(row, UNREAD, row.cause, row.problem, version)


def _refused(row: Row, answer: Answer) -> dict[str, object]:
    assert isinstance(answer, Refusal)
    return _base(row, REFUSED, answer.code, answer.explanation, str(answer.model_version))


def _answered(row: Row, answer: Answer) -> dict[str, object]:
    assert isinstance(answer, PredictionResult)
    record = _base(row, ANSWERED, answer.domain.code, answer.domain.reason, answer.model_version)
    record.update(
        {
            "capacity_wt_pct": answer.capacity,
            "lower_wt_pct": answer.interval.lower,
            "upper_wt_pct": answer.interval.upper,
            "interval_width_wt_pct": answer.interval.width,
            "interval_level": answer.interval.level,
        }
    )
    if answer.novelty is not None:
        record["elmd_distance"] = answer.novelty.distance
        record["nearest_known_alloy"] = answer.novelty.nearest
    else:
        # A bundle assembled without the novelty screen; the deployment's own never is.
        record["elmd_distance"] = "not measured"
        record["nearest_known_alloy"] = "not measured"
    return record
