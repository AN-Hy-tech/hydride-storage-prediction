"""L1 -- the raw sources, their declared schemas, and what a valid row is.

Three CSV files are loaded here, each with its own column names and conventions::

    hydride_data.csv            1279 x  6   the curated dataset
    hydride_prefeaturizing.csv  1279 x  6   the same rows with the target replaced by log1p
    ML-HYDPARK_v0.0.5.csv        772 x 13   the upstream ML-HydPARK release

Validation belongs here so that no later layer has to defend against a malformed row. A
loader either returns a frame every column of which matches its declared schema, or it
raises :class:`SchemaViolation` naming the offending rows. There is no third outcome and
no silent coercion.

**Why the formula strings are parsed at load time.** ``CBFV.composition.parse_formula``
validates nothing, which was measured against the installed version rather than assumed:

    ``Xx2``       -> ``{'Xx': 2.0}``     an element that does not exist
    ``Mg0``       -> ``{}``              an empty composition
    ``Mg-1``      -> ``{'Mg': -1.0}``    a negative amount
    ``Hf2Cu (M)`` -> ``{..., 'M': 1.0}`` a parenthesised annotation read as an element

Downstream, ``generate_features`` drops the unknown-element row into its ``skipped``
list -- which the archival ``extract_features_cbfv.py`` never inspected -- and dies on the
empty one with ``ValueError: zero-size array to reduction operation maximum``, a message
that names neither the row nor the file. :func:`parse_formula` here is the same grammar
with the checks CBFV omits, so a bad composition is a named failure at the door rather
than a silent disappearance or an opaque crash three stages later.

**This module normalises nothing.** 34 formula strings in ``hydride_data.csv`` carry
trailing whitespace and 9 carry an internal space; both parse correctly and both are left
exactly as they are. Stripping them here would silently move the unique-formula count from
1149 to 1142 and pre-empt the canonical composition key, which is card #87's to define and
to reconcile. A loader that quietly repairs its input is a loader that hides the repair.

**The HyStor spreadsheet is not loaded, and card #86 decided on 2026-09-12 that it stays that
way.** ``HyStor_27_7_24 (1).xlsx`` is a single sheet of 1283 rows over six columns, and
``hydride_data.csv`` is its downstream -- not a fourth independent source -- and nothing in
the repository has ever read it. Reading it needs ``openpyxl``, which is in neither
``environment.lock.yml`` nor the machine interpreter, and adding a package invalidates the
lock file.

Be careful with "the same six columns", which this docstring used to say and which invites a
wrong inference. The columns are the same *fields*, but the CSV is a **renormalisation** of
the sheet rather than a copy of it: the sheet writes ``CaNi5`` and ``CaAl1.8B.2 (M)`` where
the CSV writes ``Ca1Ni5`` and ``Ca1Al1.8B0.2``, and only 117 of roughly 1,180 composition
strings match literally. So a loader here would not be a cheap second reader of the same
rows; it would be a divergent view that nothing reconciles. #86 measured that with stdlib
``zipfile`` and recorded it; #89 owns the provenance question it raises.

Card #9.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from hydms.config import Columns
from hydms.config import load as load_config
from hydms.data.target import model_space_name

__all__ = [
    "ELEMENT_SYMBOLS",
    "ColumnSpec",
    "FormulaError",
    "SchemaViolation",
    "SourceSchema",
    "hydride_data_schema",
    "load_hydride_data",
    "load_ml_hydpark",
    "load_prefeaturized",
    "ml_hydpark_schema",
    "parse_formula",
    "prefeaturized_schema",
    "validate",
]

# A failure that names two hundred rows is a failure nobody reads to the end. The total is
# always reported; the listing is truncated. Same convention as `hydms/qa/detectors.py`.
_MAX_NAMED = 8

#: Every chemical element symbol, Z = 1..118. A composition may name nothing else.
#:
#: The 22-feature contract (card #19) and the element property tables (card #16) must cover
#: at least the 55 elements this dataset actually uses; that is their assertion to make, not
#: this one's. What belongs here is only the question a loader can answer: is this a symbol
#: at all?
ELEMENT_SYMBOLS: frozenset[str] = frozenset(
    """
    H  He Li Be B  C  N  O  F  Ne Na Mg Al Si P  S  Cl Ar K  Ca
    Sc Ti V  Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y  Zr
    Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I  Xe Cs Ba La Ce Pr Nd
    Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W  Re Os Ir Pt Au Hg
    Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U  Np Pu Am Cm Bk Cf Es Fm
    Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og
    """.split()
)

_SYMBOL = re.compile(r"[A-Z][a-z]*")
_AMOUNT = re.compile(r"\d+(?:\.\d*)?|\.\d+")

_KINDS = ("string", "formula", "integer", "number")


class FormulaError(ValueError):
    """A composition string is not a formula this project will accept.

    Distinct from :class:`SchemaViolation` so a caller parsing one formula gets a precise
    error, while :func:`validate` aggregates many of them into one report.
    """


class SchemaViolation(ValueError):
    """A frame does not match its declared schema.

    The message lists **every** problem found, not the first, and names the offending rows
    for each -- ``docs/QA-PROTOCOL.md`` section 4.6: an assertion that reads ``assert False``
    costs the next person an hour. Reloading after each fix, one problem at a time, costs
    them the same hour in instalments.
    """


# --------------------------------------------------------------------------------------
# Formulae
# --------------------------------------------------------------------------------------


def _read_amount(text: str, start: int) -> tuple[int, float]:
    """Read the stoichiometric amount at ``start``, defaulting to 1.0 when absent.

    Whitespace between a symbol and its amount is skipped, because the data contains it:
    ``'Zr21.5V10...Sn0.3Al 0.4'`` means Al 0.4, and CBFV reads it the same way. Returns
    ``start`` unmoved when there is no number, so the caller's own whitespace handling
    stays in charge.
    """
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    match = _AMOUNT.match(text, index)
    if match is None:
        return start, 1.0
    return match.end(), float(match.group())


def parse_formula(formula: str) -> dict[str, float]:
    """Parse a composition string into ``{element: amount}``, sorted by symbol.

    The grammar is CBFV's -- element symbols with optional decimal amounts, arbitrarily
    nested parenthesised groups with an optional multiplier, whitespace ignored -- plus the
    three checks CBFV does not make: the symbol must be a real element, every amount must
    be strictly positive, and the result must not be empty.

    Amounts are returned exactly as written, unnormalised. Deciding that ``Mg1Al1`` and
    ``Mg0.5Al0.5`` are the same material is the canonical key's job (card #87); this
    function only reports what the string says.

    Raises:
        FormulaError: naming the formula and where in it the problem is.
    """
    if not isinstance(formula, str):
        raise FormulaError(
            f"a formula must be a string, got {type(formula).__name__}: {formula!r}"
        )

    stack: list[dict[str, float]] = [{}]
    index = 0
    while index < len(formula):
        character = formula[index]

        if character.isspace():
            index += 1
            continue

        if character == "(":
            stack.append({})
            index += 1
            continue

        if character == ")":
            if len(stack) == 1:
                raise FormulaError(
                    f"{formula!r} closes a group at position {index} that was never opened"
                )
            index, factor = _read_amount(formula, index + 1)
            group = stack.pop()
            if not group:
                raise FormulaError(f"{formula!r} contains a group that names no elements")
            if factor <= 0.0:
                raise FormulaError(
                    f"{formula!r} multiplies a group by {factor:g}; amounts must be positive"
                )
            for symbol, amount in group.items():
                stack[-1][symbol] = stack[-1].get(symbol, 0.0) + amount * factor
            continue

        match = _SYMBOL.match(formula, index)
        if match is None:
            raise FormulaError(
                f"{formula!r} has an unexpected character {character!r} at position {index}"
            )
        symbol = match.group()
        if symbol not in ELEMENT_SYMBOLS:
            raise FormulaError(f"{formula!r} names {symbol!r}, which is not a chemical element")
        index, amount = _read_amount(formula, match.end())
        if amount <= 0.0:
            raise FormulaError(
                f"{formula!r} gives {symbol} an amount of {amount:g}; amounts must be positive"
            )
        stack[-1][symbol] = stack[-1].get(symbol, 0.0) + amount

    if len(stack) != 1:
        raise FormulaError(f"{formula!r} leaves {len(stack) - 1} group(s) unclosed")
    composition = stack[0]
    if not composition:
        raise FormulaError(f"{formula!r} names no elements")
    return {symbol: composition[symbol] for symbol in sorted(composition)}


# --------------------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnSpec:
    """What one column must contain.

    Args:
        name: The column heading, exactly as it appears in the file.
        kind: ``"string"``, ``"formula"``, ``"integer"`` or ``"number"``.
        nullable: Whether an empty cell is legitimate. Default is that it is not, so a
            column that is silently allowed to go missing has to say so out loud.
        minimum: Inclusive lower bound, numeric kinds only.
        maximum: Inclusive upper bound, numeric kinds only.
        allowed: The complete set of permitted values, string kinds only. A value outside
            it is a violation rather than a pass-through: ``Alloy_class`` is what
            leave-one-alloy-class-out validation folds on (AC-6), so an eleventh class
            arriving unannounced changes the fold structure and must be a human decision.
        unique: Whether duplicate values are a violation.
    """

    name: str
    kind: str
    nullable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    allowed: tuple[str, ...] | None = None
    unique: bool = False

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(f"column {self.name!r}: kind {self.kind!r} is not one of {_KINDS}")
        if self.allowed is not None and self.kind not in ("string", "formula"):
            raise ValueError(f"column {self.name!r}: `allowed` applies to string kinds only")
        if (self.minimum is not None or self.maximum is not None) and self.kind not in (
            "integer",
            "number",
        ):
            raise ValueError(f"column {self.name!r}: bounds apply to numeric kinds only")


@dataclass(frozen=True)
class SourceSchema:
    """The declared shape of one raw file.

    ``expected_rows`` is asserted, not assumed. A file that has quietly lost rows -- to a
    re-export, a partial download, a spreadsheet saved over -- is the failure mode that
    makes every downstream number wrong while every downstream test still passes.
    """

    name: str
    filename: str
    columns: tuple[ColumnSpec, ...]
    expected_rows: int
    allow_extra_columns: bool = False

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(spec.name for spec in self.columns)


# Measured against the files in `data/raw/`, which are read-only input. Card #9's
# done-criteria name the two row counts.
HYDRIDE_DATA_ROWS = 1279
PREFEATURIZED_ROWS = 1279
ML_HYDPARK_ROWS = 772

# The ten classes present in `hydride_data.csv`. `HEA`, `LEA` and `MEA` are the high-,
# low- and medium-entropy alloy families the curated set adds over ML-HydPARK.
HYDRIDE_ALLOY_CLASSES = ("A2B", "AB", "AB2", "AB5", "HEA", "LEA", "MEA", "MIC", "Mg", "SS")

# ML-HydPARK splits AB2 into its two Laves polytypes and carries no entropy-alloy families,
# so its class vocabulary is neither a subset nor a superset of the curated one. Card #87
# is where the two are reconciled onto the canonical key.
ML_HYDPARK_MATERIAL_CLASSES = (
    "A2B",
    "AB",
    "AB2",
    "AB2(C14)",
    "AB2(C15)",
    "AB5",
    "MIC",
    "Mg",
    "SS",
)

# The three provenance tags in `Dataset`.
HYDRIDE_DATASETS = ("Extracted", "HydPark", "atomic_per")

# Physical bounds, deliberately loose. They ask "is this a temperature and a weight
# percent at all?", not "is this in the range the model was trained on" -- that second
# question is the refusal path's (card #77) and its numbers live in `pipeline.yaml` under
# `domain`. A schema that encoded the training span would reject any new data by design.
_MAX_WEIGHT_PERCENT = 100.0
_MAX_TEMPERATURE_K = 5000.0


def hydride_data_schema(columns: Columns | None = None) -> SourceSchema:
    """The schema of ``hydride_data.csv`` -- the curated dataset.

    Column names come from ``pipeline.yaml`` so they are spelled once in the project; they
    contain spaces, a percent sign and parentheses, and the archival scripts re-spelled
    them at every use.
    """
    names = columns if columns is not None else load_config().columns
    return SourceSchema(
        name="hydride_data",
        filename="hydride_data.csv",
        expected_rows=HYDRIDE_DATA_ROWS,
        columns=(
            ColumnSpec(names.formula, "formula"),
            ColumnSpec(names.alloy_class, "string", allowed=HYDRIDE_ALLOY_CLASSES),
            ColumnSpec(names.dataset, "string", allowed=HYDRIDE_DATASETS),
            ColumnSpec(names.target, "number", minimum=0.0, maximum=_MAX_WEIGHT_PERCENT),
            ColumnSpec(names.temperature, "integer", minimum=0.0, maximum=_MAX_TEMPERATURE_K),
            ColumnSpec(names.citation, "string"),
        ),
    )


def prefeaturized_schema(columns: Columns | None = None) -> SourceSchema:
    """The schema of ``hydride_prefeaturizing.csv``.

    The same rows as ``hydride_data.csv`` with ``H2_W% (max)`` replaced by its ``log1p``.
    The transform is :mod:`hydms.data.target`'s to own and to invert; this schema only
    records that the column is a non-negative number, which ``log1p`` of a non-negative
    target must be, and takes its heading from
    :func:`~hydms.data.target.model_space_name` so the ``log_`` contract is spelled once.
    """
    names = columns if columns is not None else load_config().columns
    return SourceSchema(
        name="hydride_prefeaturizing",
        filename="hydride_prefeaturizing.csv",
        expected_rows=PREFEATURIZED_ROWS,
        columns=(
            ColumnSpec(names.formula, "formula"),
            ColumnSpec(names.alloy_class, "string", allowed=HYDRIDE_ALLOY_CLASSES),
            ColumnSpec(names.dataset, "string", allowed=HYDRIDE_DATASETS),
            ColumnSpec(names.temperature, "integer", minimum=0.0, maximum=_MAX_TEMPERATURE_K),
            ColumnSpec(names.citation, "string"),
            ColumnSpec(model_space_name(names.target), "number", minimum=0.0),
        ),
    )


def ml_hydpark_schema() -> SourceSchema:
    """The schema of ``ML-HYDPARK_v0.0.5.csv``.

    Two leading counters, ``Unnamed: 0`` and ``index``, are the exporter's own row numbers
    written into the file. They are declared rather than dropped: this module validates, it
    does not tidy, and a consumer selects the columns it needs.

    Most measurement columns are sparse -- 360 rows have no temperature, 399 no reference --
    which is why they are nullable here. Only the two counters and the composition are
    structural.
    """
    return SourceSchema(
        name="ml_hydpark",
        filename="ML-HYDPARK_v0.0.5.csv",
        expected_rows=ML_HYDPARK_ROWS,
        columns=(
            ColumnSpec("Unnamed: 0", "integer", minimum=0.0),
            ColumnSpec("index", "integer", minimum=0.0),
            ColumnSpec("Material_Class", "string", nullable=True,
                       allowed=ML_HYDPARK_MATERIAL_CLASSES),
            ColumnSpec("Composition_Formula", "formula"),
            ColumnSpec("Hydrogen_Weight_Percent", "number", nullable=True,
                       minimum=0.0, maximum=_MAX_WEIGHT_PERCENT),
            ColumnSpec("Heat_of_Formation_kJperMolH2", "number", nullable=True),
            ColumnSpec("Temperature(K)", "number", nullable=True,
                       minimum=0.0, maximum=_MAX_TEMPERATURE_K),
            ColumnSpec("Pressure_Atmospheres_Absolute", "number", nullable=True, minimum=0.0),
            ColumnSpec("Entropy_of_Formation_JperMolH2perK", "number", nullable=True),
            ColumnSpec("Equilibrium_Pressure_25C", "number", nullable=True, minimum=0.0),
            ColumnSpec("LnEquilibrium_Pressure_25C", "number", nullable=True),
            ColumnSpec("HtoM", "number", nullable=True, minimum=0.0),
            ColumnSpec("Reference", "string", nullable=True),
        ),
    )


# --------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------


def _check_value(value: Any, spec: ColumnSpec) -> str | None:
    """Why ``value`` is not admissible under ``spec``, or ``None`` if it is."""
    if spec.kind in ("string", "formula"):
        if not isinstance(value, str):
            return f"expected a string, got {type(value).__name__}"
        if spec.allowed is not None and value not in spec.allowed:
            return f"is not one of {', '.join(spec.allowed)}"
        if spec.kind == "formula":
            try:
                parse_formula(value)
            except FormulaError as exc:
                return str(exc)
        return None

    if isinstance(value, bool) or not pd.api.types.is_number(value):
        return f"expected a number, got {type(value).__name__}"
    number = float(value)
    if not math.isfinite(number):
        return "is not finite"
    if spec.kind == "integer" and not number.is_integer():
        return "is not a whole number"
    if spec.minimum is not None and number < spec.minimum:
        return f"is below the minimum of {spec.minimum:g}"
    if spec.maximum is not None and number > spec.maximum:
        return f"is above the maximum of {spec.maximum:g}"
    return None


def _named(pairs: list[tuple[Any, str]]) -> str:
    """Render offending rows, truncated, with the total always stated."""
    shown = ", ".join(f"row {label} {detail}" for label, detail in pairs[:_MAX_NAMED])
    if len(pairs) > _MAX_NAMED:
        shown = f"{shown}, and {len(pairs) - _MAX_NAMED} more"
    return f"{len(pairs)} row(s): {shown}"


def validate(frame: pd.DataFrame, schema: SourceSchema, source: str | None = None) -> pd.DataFrame:
    """Check ``frame`` against ``schema`` and return it unchanged.

    Nothing is coerced, filled, stripped or reordered. The frame that comes back is the
    frame that went in; what changes is that it is now known to match its schema.

    Args:
        frame: The frame to check.
        schema: The declared shape it must match.
        source: What to call it in an error message. Defaults to ``schema.name``.

    Raises:
        SchemaViolation: listing every problem found, each with its offending rows named.
    """
    where = source if source is not None else schema.name
    problems: list[str] = []

    present = list(frame.columns)
    missing = [name for name in schema.column_names if name not in present]
    if missing:
        problems.append(f"missing column(s): {', '.join(repr(name) for name in missing)}")
    if not schema.allow_extra_columns:
        unexpected = [name for name in present if name not in schema.column_names]
        if unexpected:
            problems.append(
                f"unexpected column(s): {', '.join(repr(name) for name in unexpected)}"
            )

    if len(frame) != schema.expected_rows:
        problems.append(
            f"expected {schema.expected_rows} rows, found {len(frame)}. A source that has "
            f"changed size is a decision, not a detail: update the schema deliberately"
        )

    for spec in schema.columns:
        if spec.name in missing:
            continue
        series = frame[spec.name]

        empty = series.isna()
        if not spec.nullable and bool(empty.any()):
            blanks = [(label, "is empty") for label in series.index[empty]]
            problems.append(f"column {spec.name!r} is not nullable but {_named(blanks)}")

        offenders: list[tuple[Any, str]] = []
        for label, value in series[~empty].items():
            reason = _check_value(value, spec)
            if reason is not None:
                offenders.append((label, f"({value!r}) {reason}"))
        if offenders:
            problems.append(f"column {spec.name!r} ({spec.kind}): {_named(offenders)}")

        if spec.unique:
            duplicated = series.duplicated(keep=False) & ~empty
            if bool(duplicated.any()):
                repeats = [(label, f"({value!r}) is not unique")
                           for label, value in series[duplicated].items()]
                problems.append(f"column {spec.name!r} must be unique but {_named(repeats)}")

    if problems:
        listing = "\n  - ".join(problems)
        raise SchemaViolation(f"{where} does not match its schema:\n  - {listing}")
    return frame


# --------------------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------------------


def _load(schema: SourceSchema, path: Path | None) -> pd.DataFrame:
    """Read the file this schema describes and return it validated."""
    resolved = Path(path) if path is not None else load_config().paths.raw / schema.filename
    if not resolved.is_file():
        raise FileNotFoundError(
            f"{schema.name}: {resolved} does not exist. Raw data lives under the `paths.raw` "
            f"directory in hydms/config/pipeline.yaml"
        )
    return validate(pd.read_csv(resolved), schema, source=str(resolved))


def load_hydride_data(path: Path | None = None) -> pd.DataFrame:
    """Load ``hydride_data.csv``: 1279 rows, 6 columns, the curated dataset.

    Columns: ``Composition``, ``Alloy_class``, ``Dataset``, ``H2_W% (max)``,
    ``temperature(K)``, ``Citation``. Formula strings are returned exactly as stored,
    stray whitespace included -- see this module's docstring.
    """
    return _load(hydride_data_schema(), path)


def load_prefeaturized(path: Path | None = None) -> pd.DataFrame:
    """Load ``hydride_prefeaturizing.csv``: the same 1279 rows, target in log space."""
    return _load(prefeaturized_schema(), path)


def load_ml_hydpark(path: Path | None = None) -> pd.DataFrame:
    """Load ``ML-HYDPARK_v0.0.5.csv``: 772 rows, 13 columns, the upstream release."""
    return _load(ml_hydpark_schema(), path)
