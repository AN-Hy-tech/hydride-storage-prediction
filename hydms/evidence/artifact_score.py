"""L7 -- the deployed model's test-split score, committed where a reader can check it.

**The gap this closes.** Gates AC-1 and AC-3 measure the one model this project ships on the 254
held-out ``test`` rows: R² 0.7071 and a calibrated coverage of 0.7795. Until this module, those
numbers lived in the gate report sealed inside ``artifacts/<version>/manifest.json``, and
``/artifacts/`` is gitignored. So the headline score of the deployed model was verifiable on the
maintainer's machine and nowhere else, and the Chapter 1 revision (#37) had to mark it † as
tracing to no committed file. That is the same defect ``REPORT.md`` has, which is the one thing
the chapter cannot repeat.

**Read from the gate record, never re-scored.** :mod:`hydms.gates.ac3_conformal_coverage` is
"the one place the test split is read, it is read once, and nothing downstream of it adjusts
anything". A second reader of the test split, even one that adjusts nothing, would break that
sentence. The numbers were also *certified*, meaning a gate run was recorded against them and the
version was then promoted. A fresh scoring would be a new measurement that happened to agree. So
this module copies the certified record out of the sealed manifest and turns it into a table. It
fits nothing, loads no model, and needs neither CatBoost nor the data.

**Two steps, because only one of them can run in CI.**

  - ``--probe`` reads the promoted version's manifest, which is gitignored, and writes the AC-1
    and AC-3 records verbatim to :data:`RECORD` (``reports/model/artifact-gates.json``),
    together with the version, its manifest's SHA-256 and the manifest's own note. It needs the
    maintainer's ``artifacts/``.
  - ``--emit`` parses :data:`RECORD` into :data:`TABLE` (``reports/model/artifact-score.csv``). It
    reads only committed files, so a test can assert the committed bytes are what it produces.

**One cross-check, and why it is the important one.** AC-1's metrics are measured on a *refit*.
The gate runs the deployed fit twice to prove the seed reproduces it. AC-3 scores the *stored*
model. So the R² is strictly a claim about a fit that reproduces the shipped one. What ties them
together is that both gates report the calibrated coverage on the same 254 rows. :func:`table`
refuses unless the two agree to the precision AC-3 printed, so an R² from a model the delivery
path does not serve cannot be published through this table.

**What the table is not.** It is not the procedure's score. That is the out-of-fold R² over five
models in ``reports/model/evaluation.md``. It is also not ``conformal-coverage.csv``, which scores
the 172 *calibration* rows. Three readings, three files; ``CONTEXT.md`` names them.

Card #103.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, TextIO

from hydms.config import repo_root

__all__ = [
    "RECORD",
    "TABLE",
    "ScoreUnavailable",
    "emit",
    "main",
    "probe",
    "record",
    "rows",
    "table",
]

RECORD: Final = repo_root() / "reports" / "model" / "artifact-gates.json"
TABLE: Final = repo_root() / "reports" / "model" / "artifact-score.csv"

#: The gates whose records are published. AC-1 carries the point metrics, AC-3 the band.
GATES: Final = ("AC-1", "AC-3")

#: The only split either gate scores. Named, so a record that scored anything else is refused.
HELD_OUT: Final = "test"

COLUMNS: Final = ("quantity", "value", "unit", "gate", "split", "rows", "reading")

_RECORD_SCHEMA: Final = "hydms.artifact-gates/1"


class ScoreUnavailable(ValueError):
    """The gate record cannot honestly be turned into a published score. Says why."""


# -- probe: the gitignored manifest -> the committed record ------------------------------------


def record(*, store: Path | None = None) -> dict[str, Any]:
    """The promoted version's AC-1 and AC-3 records, copied verbatim with their provenance.

    Raises:
        ScoreUnavailable: nothing is promoted, the manifest carries no gate report, or either
            gate is absent or did not pass. A score from an uncertified or failing run is not
            the deployed model's score, so none is published.
    """
    from hydms import artifacts

    root = Path(store) if store is not None else repo_root() / "artifacts"
    version = artifacts.current(store=root)
    if version is None:
        raise ScoreUnavailable(
            f"no version is promoted in {root}, so there is no deployed model to report. "
            f"The score belongs to what `current.json` points at, never to the newest version."
        )
    path = artifacts.version_dir(version, store=root) / "manifest.json"
    raw = path.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    report = manifest.get("gates")
    if not isinstance(report, Mapping):
        raise ScoreUnavailable(f"{path} records no gate run, so {version} is not certified.")
    found = {g.get("name"): g for g in report.get("gates", []) if isinstance(g, Mapping)}
    for name in GATES:
        gate = found.get(name)
        if gate is None:
            raise ScoreUnavailable(f"{path}'s gate report has no {name} record.")
        if gate.get("status") != "PASSED":
            raise ScoreUnavailable(
                f"{name} is {gate.get('status')!r} in {path}, not PASSED. A score from a gate "
                f"that did not pass is not published as the deployed model's."
            )
    return {
        "schema": _RECORD_SCHEMA,
        "version": version,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "manifest_created_at": manifest.get("created_at"),
        "gate_run_started_at": report.get("started_at"),
        "notes": manifest.get("notes", ""),
        "gates": [dict(found[name]) for name in GATES],
    }


def probe(*, store: Path | None = None, out: Path = RECORD) -> Path:
    """Write :func:`record` to ``out``, then check it parses before anyone commits it."""
    payload = record(store=store)
    rows(payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8", newline="\n")
    return out


# -- emit: the committed record -> the committed table -----------------------------------------


@dataclass(frozen=True)
class _Row:
    quantity: str
    value: str
    unit: str
    gate: str
    rows: int
    reading: str

    def cells(self) -> tuple[str, ...]:
        return (
            self.quantity,
            self.value,
            self.unit,
            self.gate,
            HELD_OUT,
            str(self.rows),
            self.reading,
        )


_AC1: Final = re.compile(
    r"every metric is identical across the two runs: (?P<metrics>[^;]+); "
    r"conformal correction (?P<correction>[+-][0-9.]+); "
    r"(?P<trees>\d+) trees, best iteration (?P<best>\d+), "
    r"grown on (?P<grown>\d+) row\(s\) with (?P<calibration>\d+) carved for calibration\."
)
_AC1_ROWS: Final = re.compile(r"scored on (?P<n>\d+) row\(s\) of '(?P<split>[^']+)'")
_METRIC: Final = re.compile(r"^(?P<name>[a-z_0-9]+) (?P<value>-?[0-9.]+)$")

_AC3: Final = re.compile(
    r"(?P<n>\d+) held-out row\(s\) in '(?P<split>[^']+)'\. "
    r"Calibrated: coverage (?P<cov>[0-9.]+), mean width (?P<width>[0-9.]+) wt%\. "
    r"Raw \([^)]*\): coverage (?P<raw_cov>[0-9.]+), mean width (?P<raw_width>[0-9.]+) wt%"
)
_AC3_SE: Final = re.compile(r"standard error at this n and this nominal: (?P<se>[0-9.]+),")

#: AC-1's metric names, with the unit and the sentence that says what each one is. A metric
#: the gate starts reporting that is not listed here is refused rather than published unread.
_POINT: Final[Mapping[str, tuple[str, str]]] = {
    "r2": ("", "R² of the median head, computed in wt% (not log1p)"),
    "rmse": ("wt%", "RMSE of the median head"),
    "mae": ("wt%", "MAE of the median head"),
    "pinball": ("wt%", "pinball loss averaged over every head"),
    "interval_coverage": ("fraction", "calibrated band coverage, on the refit"),
    "interval_width": ("wt%", "calibrated band mean width, on the refit"),
    "crossings": ("fraction", "rows with any adjacent pair of heads out of order"),
}


def _match(pattern: re.Pattern[str], text: str, gate: str) -> re.Match[str]:
    found = pattern.search(text)
    if found is None:
        raise ScoreUnavailable(
            f"{gate}'s message no longer reads the way this parser expects "
            f"(/{pattern.pattern[:60]}.../). The gate's wording changed, so re-read it and "
            f"update the parser, rather than publishing a table that dropped a number."
        )
    return found


def rows(payload: Mapping[str, Any]) -> list[_Row]:
    """The published rows, in a fixed order. Every value is the gate's own text, never re-rounded.

    Raises:
        ScoreUnavailable: the record is the wrong schema, a gate is missing or did not pass, a
            message does not parse, a gate scored a split other than ``test``, the two gates
            disagree on the row count, or AC-1's refit coverage disagrees with AC-3's coverage
            of the stored model.
    """
    if payload.get("schema") != _RECORD_SCHEMA:
        raise ScoreUnavailable(f"{RECORD.name} has schema {payload.get('schema')!r}.")
    gates = {g.get("name"): g for g in payload.get("gates", [])}
    for name in GATES:
        if gates.get(name, {}).get("status") != "PASSED":
            raise ScoreUnavailable(f"{name} is absent from the record or did not pass.")

    one = str(gates["AC-1"]["message"])
    three = str(gates["AC-3"]["message"])
    fit = _match(_AC1, one, "AC-1")
    scored = _match(_AC1_ROWS, one, "AC-1")
    band = _match(_AC3, three, "AC-3")
    se = _match(_AC3_SE, three, "AC-3")

    for gate, split in (("AC-1", scored["split"]), ("AC-3", band["split"])):
        if split != HELD_OUT:
            raise ScoreUnavailable(f"{gate} scored {split!r}, not {HELD_OUT!r}.")
    n = int(scored["n"])
    if int(band["n"]) != n:
        raise ScoreUnavailable(
            f"AC-1 scored {n} rows and AC-3 scored {band['n']}. They are one split or they are "
            f"not the same claim."
        )

    metrics: dict[str, str] = {}
    for part in fit["metrics"].split(", "):
        pair = _METRIC.match(part.strip())
        if pair is None:
            raise ScoreUnavailable(f"AC-1 metric {part!r} does not read as `name value`.")
        metrics[pair["name"]] = pair["value"]
    unknown = sorted(set(metrics) - set(_POINT))
    missing = sorted(set(_POINT) - set(metrics))
    if unknown or missing:
        raise ScoreUnavailable(
            f"AC-1 metrics differ from the known set: new {unknown}, gone {missing}."
        )

    # The tie between the refit (AC-1) and the stored model (AC-3): same rows, same coverage.
    places = len(band["cov"].split(".")[1])
    if round(float(metrics["interval_coverage"]), places) != round(float(band["cov"]), places):
        raise ScoreUnavailable(
            f"AC-1's refit covers {metrics['interval_coverage']} of the test rows and AC-3's "
            f"stored model covers {band['cov']}. They are not the same model, so AC-1's R² "
            f"cannot be published as the deployed model's."
        )

    nominal = gates["AC-3"].get("threshold")
    if not isinstance(nominal, int | float):
        raise ScoreUnavailable(f"AC-3's threshold {nominal!r} is not a nominal level.")

    out = [
        _Row(name, metrics[name], unit, "AC-1", n, reading)
        for name, (unit, reading) in _POINT.items()
    ]
    out += [
        _Row(
            "coverage_calibrated",
            band["cov"],
            "fraction",
            "AC-3",
            n,
            "calibrated band coverage, stored model -- the AC-3 criterion",
        ),
        _Row(
            "width_calibrated",
            band["width"],
            "wt%",
            "AC-3",
            n,
            "calibrated band mean width, stored model",
        ),
        _Row(
            "coverage_raw",
            band["raw_cov"],
            "fraction",
            "AC-3",
            n,
            "the same heads with no conformal correction",
        ),
        _Row(
            "width_raw",
            band["raw_width"],
            "wt%",
            "AC-3",
            n,
            "the same heads with no conformal correction",
        ),
        _Row(
            "coverage_nominal",
            f"{nominal:g}",
            "fraction",
            "AC-3",
            n,
            "the level the stored correction was calibrated for",
        ),
        _Row(
            "coverage_standard_error",
            se["se"],
            "fraction",
            "AC-3",
            n,
            "binomial standard error at this n and the nominal level",
        ),
        _Row(
            "conformal_correction",
            fit["correction"],
            "log1p wt%",
            "AC-1",
            n,
            "constant added to the outer heads before expm1",
        ),
        _Row("trees", fit["trees"], "count", "AC-1", n, "trees grown"),
        _Row(
            "rows_grown_on",
            fit["grown"],
            "rows",
            "AC-1",
            n,
            "training rows the deployed model grew on",
        ),
        _Row(
            "rows_calibration",
            fit["calibration"],
            "rows",
            "AC-1",
            n,
            "rows carved out before fitting, for the conformal correction",
        ),
    ]
    return out


def table(payload: Mapping[str, Any]) -> str:
    """The CSV text: provenance as comment lines, then one row per quantity."""
    buffer = io.StringIO()
    buffer.write(
        f"# Deployed model {payload['version']}, scored once on the held-out test split by the "
        f"gates recorded in its manifest.\n"
        f"# manifest sha256 {payload['manifest_sha256']}; gate run {payload['gate_run_started_at']}.\n"
        f"# Generated from reports/model/artifact-gates.json by "
        f"`python -m hydms.evidence.artifact_score --emit`; do not edit.\n"
    )
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in rows(payload):
        writer.writerow(row.cells())
    return buffer.getvalue()


def emit(*, source: Path = RECORD, out: Path = TABLE) -> Path:
    """Rewrite :data:`TABLE` from the committed :data:`RECORD`. Needs no artifact."""
    payload = json.loads(source.read_text(encoding="utf-8"))
    out.write_text(table(payload), encoding="utf-8", newline="\n")
    return out


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    """``--probe`` refreshes the record from ``artifacts/``; ``--emit`` rewrites the table."""
    stream = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(
        prog="python -m hydms.evidence.artifact_score",
        description="The deployed model's test score, from its sealed gate record.",
    )
    parser.add_argument(
        "--probe", action="store_true", help=f"rewrite {RECORD.name} from artifacts/"
    )
    parser.add_argument("--emit", action="store_true", help=f"rewrite {TABLE.name}")
    args = parser.parse_args(argv)
    if args.probe:
        print(f"wrote {probe()}", file=stream)
    if args.emit:
        print(f"wrote {emit()}", file=stream)
    if not (args.probe or args.emit):
        print(table(json.loads(RECORD.read_text(encoding="utf-8"))), file=stream, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover - the command line
    raise SystemExit(main())
