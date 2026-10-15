"""L2 -- formulae and temperatures in, the 22-column feature matrix out.

Card #20. This is the descriptor layer's entire public surface. Everything the layer knows --
which tables the properties come from, how a statistic is weighted, whether a composite is
formed before or after the statistic, what the columns are called and what order they are in
-- is behind :func:`featurize`, and a caller that has a list of candidate formulae needs none
of it::

    X = featurize(["LaNi5", "TiFe"], 298.0)     # (2, 22), float64, contract order

One call, not one call per formula. Architectures A and B both evaluate candidates in batches
and the memo's practical check 3 warns explicitly against a per-formula loop, so the batch is
the unit here: the formulae are parsed once, the element property lookups are resolved once
per (table, property) rather than once per row, and the arithmetic runs over the whole batch
in :mod:`hydms.descriptors.stats`. A composition's features do not depend on what it was
batched with -- that is asserted as arithmetic, not as a shape, because the layer's tightest
numerical property depends on it (#17: the reduction runs down the leading axis, and a batch
of one and a batch of ten thousand must agree exactly). Measured by card #22 over ten thousand
**distinct** candidates: **0.245 s**, or 41,000 formulae per second, of which a quarter is
:func:`~hydms.data.load.parse_formula` and the rest is numpy. The curated set less europium is
1,278 rows in **0.026 s**. Those figures replace the ones this docstring carried until #22:
they were measured over a batch of ten thousand *repeats of four formulae*, which answered the
computability verdict from a memo nine thousand nine hundred and ninety-six times out of ten
thousand and was thirteen times slower per distinct composition than the layer actually is.
``docs/BENCHMARKS.md`` has the table, the machine and the batch-size curve.

**No file is read and no file is written.** The old pipeline's descriptor stage was a script
that read a CSV and wrote another one, which is how the training set acquired a feature matrix
whose producer is not in the repository (``jarvis_filtered_features.csv``, PHASE-H-RUNBOOK
1). A function that takes formulae and returns a frame cannot leave an orphan behind.

Refuse, never fill
------------------

**A composition this project cannot featurise is refused, with the blocking element named.**
Seven of the 22 features are not computable for every composition (#19): the citable Oliynyk
edition leaves ``gordy_en`` blank for 21 of the 55 elements in the dataset, and all six JARVIS
features are unavailable for europium. :meth:`~hydms.descriptors.contract.FeatureContract.
computability` is asked **before** a row is built, never after -- because the alternative is a
NaN in a feature matrix, and a NaN is one median-fill away from a number that looks like a
measurement. Measured over the 1,279 curated rows with the shipped tables, **266 are
refused**: 265 for ``dev_Gordy_electonegativity`` alone, and one -- ``Eu1Ni5``, row 516 -- for
seven features at once.

That is a large refusal and it is deliberate. Softening it is not this module's call: it is
feature selection's, and #24/#25 have the counts. A caller who wants those rows drops the
features that block them, and the same verdict says which::

    keep = [f for f in formulas if contract.computability(parse_formula(f)).complete]
    X = featurize(keep, kelvin[keep], contract=contract)

Without ``dev_Gordy_electonegativity`` the remaining 21 features cover **1,278 of the 1,279
rows** -- everything but the europium one. That is the trade, in one number, for whoever
re-runs selection.

**The published composite column is read, never derived.** Five of the six JARVIS features are
composites, and they are *columns* of the JARVIS table rather than anything CBFV synthesises
(#16), so the statistic is taken over the published column. That is what CBFV reads and
therefore what parity means (#21). It is a rule and not a preference because eleven of that
table's 156 composite columns are **not** the arithmetic their names claim (#18), so
:func:`~hydms.descriptors.composites.require_self_consistent` is run over the properties this
call is about to featurise -- once per table per call, and it raises naming the column and the
element rather than returning a descriptor that is zero for two elements and right for the
other 101. It is not free: card #22 measured it at **5 ms**, which is 2% of a ten-thousand
candidate batch and **57% of a batch of one**. That is the per-call floor, and it is another
reason the batch is the unit here.

Labels, not positions
---------------------

The returned frame carries **the caller's own index**. Hand it a ``Series`` and the features
come back on that Series' labels; hand it a list and they come back on a ``RangeIndex``. This
is not a convenience: the metadata that must travel beside the matrix -- ``Alloy_class`` above
all, which AC-6 cannot be computed without -- is re-attached to it afterwards, and the way
that goes wrong is a positional ``concat`` after a row is dropped somewhere upstream. That is
leak L9, and it is in this repository (``merge_datasets.py:46``). So a label is carried
through wherever one was given, duplicated labels are refused because they would make the
re-attachment ambiguous, and a ``temperature`` Series whose index disagrees with the formulae's
is refused rather than zipped by position.

Nothing is dropped, ever. An unparseable formula, a hole, a non-finite temperature: each
raises, listing **every** offender with its label, because a featuriser that returns fewer
rows than it was given is how a feature matrix comes to be joined to the wrong compositions.

The parser is this project's
-----------------------------

:func:`hydms.data.load.parse_formula`, not ``pymatgen.core.Composition``. The card that opened
this module named pymatgen, and that line predates #9, which built the validated grammar this
project uses -- periodic-table membership, strictly positive amounts, a non-empty result --
and asserted it at parity with CBFV over all 1,279 + 772 formulae. #87 then built the canonical
composition key on that same function. A third parser would give the project three ideas of
what a formula is, and the differences would surface as compositions that featurise but cannot
be keyed, which is the shape of leak L8. (pymatgen is not in ``environment.lock.yml`` either.)

The tables are an argument
--------------------------

:func:`featurize` reads the shipped, cited tables by default and a caller featurising for real
should never pass anything else. The parameter exists for gate AC-2, whose whole meaning
depends on it: the published Oliynyk table is a *revised* edition of the one CBFV ships and
eight of the thirteen properties differ, so "our featuriser reproduces CBFV" is a claim about
the code only when both are handed the same numbers (#16). The gate supplies CBFV's copy as
test input -- it is unlicensed and must never become package data -- and the verdict from
:meth:`~hydms.descriptors.contract.FeatureContract.computability` is computed against whatever
was supplied, so it stays a statement about the numbers actually used.

A supplied table must spell its properties the way the contract does (``gordy_en``, not
``Gordy_electonegativity``); :data:`~hydms.descriptors.contract.PUBLISHED_SPELLING` is the map,
and :meth:`~hydms.descriptors.element_data.PropertyTable.of` builds the table.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from types import MappingProxyType
from typing import Any

import numpy as np
import pandas as pd

from hydms.data.load import FormulaError, parse_formula
from hydms.descriptors.composites import require_self_consistent
from hydms.descriptors.contract import (
    CONTRACT,
    Computability,
    FeatureContract,
    assert_contract,
)
from hydms.descriptors.element_data import TABLES, PropertyTable, load_table
from hydms.descriptors.stats import Statistics, statistics

__all__ = [
    "FeaturisationError",
    "featurize",
]

# A failure naming two hundred rows is a failure nobody reads to the end. The total is always
# reported; the listing is truncated. Same convention as the rest of the layer.
_MAX_NAMED = 8


class FeaturisationError(ValueError):
    """A batch cannot be featurised, and the message says which rows and why.

    A ``ValueError`` for the same reason as
    :class:`~hydms.descriptors.contract.ContractError`,
    :class:`~hydms.descriptors.stats.CompositionError` and
    :class:`~hydms.data.load.FormulaError`: the caller passed something the layer does not
    admit, rather than losing a race or a file handle.

    Spelled with an ``s`` to match :class:`~hydms.data.canonical.CanonicalisationError` and the
    rest of the project's prose. The *module* is ``featurize`` because that is the name the
    L13 sentinel already points at and the name CBFV gave the operation; the two spellings sit
    side by side deliberately rather than by accident.

    Attributes:
        rows: Each offending row's own sentence, by the caller's label, in batch order --
            **as data**, so a caller screening many candidates can refuse exactly those rows
            and answer the rest (card #84). Empty when the defect belongs to the batch rather
            than to a row: a repeated label, temperatures that do not line up, an unknown
            table. A row's sentence names its formula and says what is wrong with it; it does
            not name the label or the batch, because it is written for the one row it
            describes. The message is still the whole account, every offender listed.
    """

    def __init__(self, message: str, rows: Mapping[Any, str] | None = None) -> None:
        super().__init__(message)
        self.rows: Mapping[Any, str] = MappingProxyType(dict(rows or {}))


def _named(items: Iterable[object]) -> str:
    """Render offenders for a message: in the order given, truncated, and counted."""
    listed = [str(item) for item in items]
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


def _rows(formulas: Sequence[str] | pd.Series) -> tuple[pd.Index, list[str]]:
    """The batch's labels and its formula strings.

    A ``Series`` keeps its index; anything else gets a ``RangeIndex``, so a caller who never
    had labels is not given imaginary ones.
    """
    if isinstance(formulas, str):
        raise FeaturisationError(
            f"featurize() takes a batch of formulae, not one string: {formulas!r} would be "
            f"iterated character by character. Pass [{formulas!r}] -- a single composition is "
            f"a batch of one."
        )
    if isinstance(formulas, pd.Series):
        labels, strings = pd.Index(formulas.index), list(formulas)
    else:
        strings = list(formulas)
        labels = pd.RangeIndex(len(strings))
    if labels.has_duplicates:
        repeated = labels[labels.duplicated()].unique()
        raise FeaturisationError(
            f"the batch's index repeats {len(repeated)} label(s): "
            f"{_named(repr(label) for label in repeated)}. The "
            f"feature matrix is returned on this index and the row metadata -- Alloy_class "
            f"above all -- is re-attached to it by label, which a repeated label makes "
            f"ambiguous. Reset the index before featurising."
        )
    return labels, strings


def _temperatures(temperatures: Any, labels: pd.Index) -> np.ndarray:
    """The temperature column as ``float64``, aligned with ``labels``.

    The cast is the point (#19): ``temperature(K)`` is ``int64`` in the raw file, every
    committed value is integral, and a candidate evaluated at 313.5 K would truncate to 313 in
    silence. ``assert_contract`` refuses the integer column by name, so this is not optional.

    A scalar is broadcast over the batch, which is the common call when a whole generation of
    candidates is being evaluated at one temperature.

    What is *not* checked here is the range. Whether 900 K is a temperature this model may be
    asked about is the applicability domain's question (#48) and the refusal path's answer
    (#77); a featuriser that also policed the domain would give the same fact two owners.
    """
    if isinstance(temperatures, pd.Series):
        if not pd.Index(temperatures.index).equals(labels):
            raise FeaturisationError(
                "the temperatures are a Series whose index does not match the formulae's, so "
                "pairing them would be positional -- which is leak L9's shape exactly "
                "(merge_datasets.py:46). Pass both columns from the same frame, or pass "
                "numpy.asarray(temperatures) to say positional alignment is what you meant."
            )
        temperatures = temperatures.to_numpy()

    try:
        kelvin = np.asarray(temperatures, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise FeaturisationError(
            f"the temperatures are not numbers: {error}. temperature(K) is a feature column "
            f"like any other and it is float64 in the contract."
        ) from error

    if kelvin.ndim == 0:
        kelvin = np.full(len(labels), float(kelvin), dtype=np.float64)
    if kelvin.ndim != 1 or kelvin.size != len(labels):
        raise FeaturisationError(
            f"{len(labels)} formula(e) and {kelvin.size} temperature(s) of shape "
            f"{kelvin.shape}: a temperature is needed for every row, because it is one of the "
            f"22 features. A scalar is broadcast over the batch; anything else must line up."
        )
    if kelvin.size and not np.all(np.isfinite(kelvin)):
        bad = np.flatnonzero(~np.isfinite(kelvin))
        raise FeaturisationError(
            f"{bad.size} temperature(s) are not finite, at label(s) "
            f"{_named(repr(label) for label in labels[bad])}. A NaN here is a NaN in the "
            f"matrix, and a "
            f"median-fill downstream would turn it into something that looks like a reading."
        )
    return kelvin


def _sources(
    declared: FeatureContract, tables: Mapping[str, PropertyTable] | None
) -> dict[str, PropertyTable]:
    """The property table behind each name the contract uses, shipped unless supplied."""
    supplied = dict(tables) if tables else {}
    unknown = sorted(name for name in supplied if name not in TABLES)
    if unknown:
        raise FeaturisationError(
            f"no such element property table: {_named(unknown)}. This project reimplements "
            f"exactly two, {' and '.join(repr(t) for t in TABLES)} (card #8)."
        )
    needed = sorted({spec.table for spec in declared if spec.table is not None})
    return {
        name: supplied[name] if name in supplied else load_table(name) for name in needed
    }


def _audit_composites(declared: FeatureContract, sources: Mapping[str, PropertyTable]) -> None:
    """Refuse to featurise from a composite column that is not its own arithmetic (#18)."""
    for name, table in sources.items():
        props = sorted({spec.prop for spec in declared if spec.table == name and spec.prop})
        require_self_consistent(table, props)


def _parse(
    strings: Sequence[str], labels: pd.Index
) -> tuple[list[dict[str, float] | None], dict[int, str]]:
    """Every formula parsed, and the parser's own sentence for each one that would not parse.

    Returns ``(parsed, failures)``: ``parsed`` is aligned with ``strings``, holding ``None``
    where a formula failed, and ``failures`` maps each failed *position* to its sentence. It
    does not raise, so :func:`featurize` can ask the contract about the rows that did parse
    and refuse the batch **once**, naming every offender of both kinds -- a caller that drops
    the offenders and asks again must not discover a second list of them on the retry.
    """
    parsed: list[dict[str, float] | None] = []
    failures: dict[int, str] = {}
    for position, formula in enumerate(strings):
        try:
            parsed.append(parse_formula(formula))
        except FormulaError as error:
            parsed.append(None)
            failures[position] = str(error)
    return parsed, failures


def _require_computable(
    declared: FeatureContract,
    parsed: Sequence[dict[str, float] | None],
    strings: Sequence[str],
    sources: Mapping[str, PropertyTable],
) -> dict[int, str]:
    """Ask the contract before building a row: each parsed row that cannot be built, and why.

    Rows that did not parse (``None``) are skipped -- they are already refused, for a reason
    that comes first. The verdict is per *element set* -- the amounts cannot make a hole -- so
    it is computed once and reused. The curated data's 1,279 rows carry 1,115 distinct
    compositions and **464** distinct element sets, so the memo is worth having even before a
    candidate generator starts handing over ten thousand variations on the same alloy.
    """
    verdicts: dict[tuple[str, ...], Computability] = {}
    refused: dict[int, str] = {}
    for position, composition in enumerate(parsed):
        if composition is None:
            continue
        elements = tuple(composition)
        verdict = verdicts.get(elements)
        if verdict is None:
            verdict = declared.computability(elements, tables=sources)
            verdicts[elements] = verdict
        if not verdict.complete:
            refused[position] = f"{strings[position]}: {verdict.reason}"
    return refused


def _refuse(
    declared: FeatureContract,
    labels: pd.Index,
    strings: Sequence[str],
    unparsed: Mapping[int, str],
    holes: Mapping[int, str],
) -> None:
    """Raise one :class:`FeaturisationError` for every offender of both kinds, if there are any.

    Two things are built from the same findings. The **message** is the batch's account, as
    it always was: each offender prefixed by its label, and the reason nothing was returned.
    The **rows** are each offender's own sentence, written for that one row and naming no
    label and no batch -- so a delivery path that answers N candidates at once can refuse
    exactly the rows that failed, with the same words it would give each of them alone.
    """
    if not unparsed and not holes:
        return
    parts: list[str] = []
    if unparsed:
        parts.append(
            f"{len(unparsed)} of {len(strings)} formula(e) could not be parsed: "
            f"{_named(f'[{labels[p]!r}] {s}' for p, s in unparsed.items())}. Nothing was "
            f"featurised -- a batch that silently returns fewer rows than it was given is how "
            f"a feature matrix comes to be attached to the wrong compositions."
        )
    if holes:
        parts.append(
            f"{len(holes)} of {len(strings)} composition(s) cannot produce all "
            f"{len(declared)} features from the tables given: "
            f"{_named(f'[{labels[p]!r}] {s}' for p, s in holes.items())}. These rows are "
            f"refused rather than filled: a hole in a published table is not a number, and a "
            f"NaN here would be indistinguishable from a measurement two stages later. To "
            f"featurise them, pass a contract without the blocking features -- "
            f"FeatureContract.from_names() builds one -- which is the trade cards #24 and #25 "
            f"own."
        )
    rows = {
        position: f"the formula could not be parsed: {sentence.rstrip('.')}."
        for position, sentence in unparsed.items()
    }
    rows.update(
        (
            position,
            f"{sentence}. A hole in a published element table is refused rather than filled, "
            f"because a filled hole is a number nobody measured.",
        )
        for position, sentence in holes.items()
    )
    raise FeaturisationError(
        " ".join(parts), rows={labels[position]: rows[position] for position in sorted(rows)}
    )


def _pack(parsed: Sequence[dict[str, float]]) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    """The batch as ``(weights, codes, universe)``.

    ``weights`` and ``codes`` are ``(n_compositions, max_arity)``. A weight of exactly ``0.0``
    is padding, which :func:`~hydms.descriptors.stats.statistics` masks; the matching code
    points at the universe's one-past-the-end slot, which every property vector fills with
    ``nan`` so that a padded slot cannot be mistaken for a value.

    Element symbols are interned to integers once, so a property vector for the whole batch is
    a fancy-index rather than one dict lookup per element per row per property. That is the
    difference between a batched featuriser and a loop wearing one's clothes.
    """
    universe = tuple(sorted({element for row in parsed for element in row}))
    code_of = {element: index for index, element in enumerate(universe)}
    padding = len(universe)
    width = max(len(row) for row in parsed)

    weights = np.zeros((len(parsed), width), dtype=np.float64)
    codes = np.full((len(parsed), width), padding, dtype=np.intp)
    for row, composition in enumerate(parsed):
        for column, (element, amount) in enumerate(composition.items()):
            weights[row, column] = amount
            codes[row, column] = code_of[element]
    return weights, codes, universe


def _values(
    table: PropertyTable, prop: str, universe: Sequence[str], codes: np.ndarray
) -> np.ndarray:
    """One property, laid out like ``codes``, with ``nan`` in the padded slots.

    ``PropertyTable.value`` raises on a hole rather than returning one, so this cannot
    silently fill; :func:`_require_computable` has already established that it will not have
    to, for every element the batch uses.
    """
    lookup = np.empty(len(universe) + 1, dtype=np.float64)
    for index, element in enumerate(universe):
        lookup[index] = table.value(element, prop)
    lookup[len(universe)] = np.nan
    values: np.ndarray = lookup[codes]
    return values


def _empty(declared: FeatureContract, labels: pd.Index) -> pd.DataFrame:
    """The contract's columns with no rows.

    An empty batch is not an error -- a screen that rejects every candidate in a generation
    hands one over -- and returning the right columns keeps the caller's next step honest
    instead of making it special-case a shape.
    """
    frame = pd.DataFrame(
        {name: np.empty(0, dtype=np.float64) for name in declared.names}, index=labels
    )
    assert_contract(frame, declared)
    return frame


def featurize(
    formulas: Sequence[str] | pd.Series,
    temperatures: float | Sequence[float] | np.ndarray | pd.Series,
    *,
    contract: FeatureContract | None = None,
    tables: Mapping[str, PropertyTable] | None = None,
) -> pd.DataFrame:
    """Model-ready features for a batch of candidate compositions.

    Args:
        formulas: The compositions, as strings. A ``Series`` keeps its index; any other
            sequence is labelled by position. A bare ``str`` is refused rather than iterated
            character by character.
        temperatures: One kelvin value per formula, or a scalar to be used for all of them.
            Cast to ``float64``: the raw column is ``int64`` and 313.5 K must not become 313.
        contract: What to build, defaulting to the published 22
            (:data:`~hydms.descriptors.contract.CONTRACT`). Pass a narrower one --
            :meth:`~hydms.descriptors.contract.FeatureContract.from_names` builds it -- to
            featurise compositions the full 22 cannot cover.
        tables: The element property tables to read, by name, defaulting to the shipped cited
            ones. See the module docstring: this exists for gate AC-2 and for nothing else,
            and a supplied table must use the contract's property spellings.

    Returns:
        ``(len(formulas), len(contract))`` of ``float64``, columns in contract order, on the
        caller's index. It satisfies
        :func:`~hydms.descriptors.contract.assert_contract` -- which is asserted here rather
        than promised, because "by construction" is a claim a rewrite can quietly break.

    Raises:
        FeaturisationError: if a formula will not parse, if a composition cannot produce every
            feature, if the temperatures do not line up or are not finite, or if the index
            repeats a label. Every offending row is named, and nothing is dropped.
        CompositeError: if a composite column the contract asks for is not the arithmetic its
            name claims (:func:`~hydms.descriptors.composites.require_self_consistent`).
        ContractError: from the closing check, if the assembled frame is somehow not what the
            contract declares. Unreached; it is the guard that keeps the claim true.
    """
    declared = contract if contract is not None else CONTRACT
    labels, strings = _rows(formulas)
    kelvin = _temperatures(temperatures, labels)

    sources = _sources(declared, tables)
    _audit_composites(declared, sources)

    if not strings:
        return _empty(declared, labels)

    parsed, unparsed = _parse(strings, labels)
    holes = _require_computable(declared, parsed, strings, sources)
    _refuse(declared, labels, strings, unparsed, holes)

    weights, codes, universe = _pack([row for row in parsed if row is not None])
    computed: dict[tuple[str, str], Statistics] = {}
    built: dict[str, np.ndarray] = {}
    for spec in declared:
        table, prop, statistic = spec.table, spec.prop, spec.statistic
        if table is None or prop is None or statistic is None:
            # The passthrough, and the only column no table produces. `FeatureSpec` is
            # all-or-none, so this is `spec.is_passthrough` written so mypy can see it.
            built[spec.name] = kelvin
            continue
        # One `Statistics` per (table, property), not per feature: four of the 19 properties
        # are read by two features each, and the arithmetic is the expensive half.
        key = (table, prop)
        if key not in computed:
            computed[key] = statistics(weights, _values(sources[table], prop, universe, codes))
        built[spec.name] = computed[key][statistic]

    frame = pd.DataFrame(built, index=labels, columns=list(declared.names))
    assert_contract(frame, declared)
    return frame
