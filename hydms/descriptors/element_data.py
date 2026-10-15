"""The numeric element properties, and where each one came from.

Card #16. This module owns two things and hides both: the tables themselves, and the
refusal that happens when a table has no value for something it is asked about.

**Why these tables and not CBFV's.** ``CBFV`` carries no licence at all -- ``spdx_id`` is
null on both GitHub and PyPI, which under default copyright means all rights reserved -- has
been unmaintained since 2022, and breaks under NumPy 2.x. It cannot be vendored into a
GPL-3.0 deliverable. The values here come instead from two publications that may be
redistributed, cited in ``data/SOURCES.md`` and turned into the committed CSVs by
``scripts/build_element_tables.py``, which is the audit trail between the two.

**The tables are not interchangeable with CBFV's, and that is deliberate.** The Oliynyk list
was revised for its 2024 publication: of the thirteen properties the 22 selected features
need, five agree with CBFV's copy exactly and eight do not, by as much as 10 in ``valence_d``
(Ga, Ge). ``SOURCES.md`` records every delta. The consequence for gate AC-2 is that parity
with CBFV is a claim about *this code*, not about these numbers: the featuriser must
reproduce CBFV to 1e-9 **given the same table**, which is why ``tests/descriptors/data/``
carries CBFV's values as a reference fixture rather than this package shipping them.

**A hole is not a zero, not a NaN, and not -9999.** The two publications spell "no value"
differently and both spellings arrive here as the same refusal:

* Oliynyk leaves the cell **empty** -- 421 of them. One matters: ``gordy_en`` is absent for 21
  of the 55 elements this dataset uses (Ce, Dy, Er, Eu, Gd, Hf, Ho, Ir, Lu, Nd, Os, Pr, Pt,
  Re, Sm, Ta, Tb, Th, Tm, U, W -- the rare earths that dominate AB5 hydrides), and
  ``dev_Gordy_electonegativity`` is one of the 22 selected features.
* JARVIS writes **-9999.0**, in 9130 of its 45114 cells. It is a sentinel, not a measurement,
  and a loader that took it at face value would hand the featuriser a number four orders below
  every real value in the column.

Every access raises on either. That is not defensive coding -- it is the specific failure this
card exists to prevent, and CBFV demonstrates it. Asked to featurise ``Eu1Ni5``, whose europium
is absent from CBFV's ``jarvis.csv`` entirely, CBFV substitutes an all-zero property vector,
emits a full row of plausible numbers, and mentions the formula only in a ``skipped`` list that
``extract_features_cbfv.py`` never read. The published feature matrix therefore contains one row
computed as though europium had zero mass, zero polarizability and zero boiling point. NIST's
file keeps the europium row and marks its properties -9999, so this layer cannot featurise that
composition either -- but it says so instead of inventing an answer, which is the whole
difference.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path
from typing import Final

import numpy as np

__all__ = [
    "TABLES",
    "ElementDataError",
    "PropertyTable",
    "load_table",
    "require_coverage",
]

#: The two tables the 22 selected features are drawn from, resolved empirically by the
#: provenance spike (card #8): 15 features from ``oliynyk``, 6 from ``jarvis``, and
#: ``temperature(K)``, which is a raw input column and no table's business.
TABLES: Final = ("oliynyk", "jarvis")

_DATA = Path(__file__).parent / "data"

#: What to print when a table is named in an error. Full citations are in ``SOURCES.md``;
#: these exist so a traceback says where the number was supposed to come from.
_CITATION: Final[dict[str, str]] = {
    "oliynyk": "Lee et al. 2024, Data in Brief 53, 110178 (CC BY 4.0)",
    "jarvis": "Choudhary et al. 2020, npj Comput. Mater. 6, 173 (NIST)",
}

#: Values that are a table's way of writing "no value", per table. Recognised at read time,
#: so a sentinel becomes a hole before anything can compute with it.
#:
#: JARVIS uses -9999.0 in 9130 of its 45114 cells. It is four orders below every genuine value
#: in every column that carries it, so this is not a threshold or a heuristic -- it is the
#: source's documented marker, matched exactly. Oliynyk uses an empty cell instead and needs
#: no sentinel; the empty string is handled by the reader for both.
_SENTINELS: Final[dict[str, frozenset[float]]] = {
    "oliynyk": frozenset(),
    "jarvis": frozenset({-9999.0}),
}


class ElementDataError(ValueError):
    """An element property was asked for and the table cannot honestly supply it.

    A ``ValueError``, like :class:`~hydms.data.load.SchemaViolation` and
    :class:`~hydms.data.target.TargetError`, because the caller passed something the data
    does not support rather than losing a race or a file handle.

    It is raised for three distinct situations, and the message says which: the table has no
    such property, the table has no such element, or the table has both and the cell is
    empty. The third is the one worth having a name for -- it is a *hole*, a value the
    publication does not provide, and it is the difference between this module and CBFV.
    """


@dataclass(frozen=True)
class PropertyTable:
    """One element-property table, read once and never mutated.

    Frozen because a table is a published artifact: a caller that could edit it in place
    could make the featuriser irreproducible without changing a line of committed data.
    """

    name: str
    citation: str
    properties: tuple[str, ...]
    #: element -> property -> value. A property absent from the inner mapping is a hole:
    #: the table has a column for it and the publication left the cell empty.
    _values: dict[str, dict[str, float]]

    @classmethod
    def of(
        cls, name: str, citation: str, values: Mapping[str, Mapping[str, float]]
    ) -> PropertyTable:
        """A table from an in-memory ``{element: {property: value}}`` mapping.

        The committed tables come from :func:`load_table` and nothing else should. This exists
        for the one caller that must featurise against a table it has *not* shipped: gate
        AC-2 (card #21) is required to compare against CBFV's copy of the Oliynyk table, which
        is test input and must never become package data, and
        :func:`hydms.descriptors.featurize.featurize` takes tables as an argument for that
        reason. Without this the caller would be constructing a frozen dataclass through its
        underscored field.

        A property is a column of the table if *any* element carries it, which is how a hole
        stays distinguishable from a typo: an element missing the property is a hole, and a
        property no element carries is not a column at all.
        """
        properties: dict[str, None] = {}
        for row in values.values():
            properties.update(dict.fromkeys(row))
        return cls(
            name=name,
            citation=citation,
            properties=tuple(properties),
            _values={element: dict(row) for element, row in values.items()},
        )

    @property
    def elements(self) -> frozenset[str]:
        return frozenset(self._values)

    def has(self, element: str, prop: str) -> bool:
        """Whether a real number can be produced, with no exception and no judgement."""
        return prop in self._values.get(element, {})

    @cached_property
    def _coverage(self) -> dict[str, frozenset[str]]:
        """property -> the elements carrying it, built once on first use.

        Derived, so caching it does not make this table any less frozen: the same values it
        was constructed with, arranged the other way round.
        """
        coverage: dict[str, set[str]] = {prop: set() for prop in self.properties}
        for element, row in self._values.items():
            for prop in row:
                coverage[prop].add(element)
        return {prop: frozenset(elements) for prop, elements in coverage.items()}

    def servable(self, prop: str) -> frozenset[str]:
        """Every element this table can supply ``prop`` for.

        Membership answers both failure modes at once -- an element the table has never heard
        of and an element whose cell is empty are both simply absent -- so a caller asking
        "can I compute this?" needs one lookup rather than a try/except.

        **It is memoised, and card #22 is why.** The set depends only on the table, and
        :meth:`~hydms.descriptors.contract.FeatureContract.computability` asks for it once per
        feature per *candidate composition*. Rebuilding it there cost **97% of the wall clock**
        of featurising ten thousand distinct compositions -- 13.8 million :meth:`has` calls for
        nineteen answers -- and it was invisible until a benchmark used candidates that were
        actually distinct. An unknown property returns the empty set rather than raising:
        nothing is servable from a column that does not exist, which is what the caller means.
        """
        return self._coverage.get(prop, frozenset())

    def value(self, element: str, prop: str) -> float:
        """One number, or an exception that says exactly what is missing.

        Never returns NaN. A caller that receives a float from this method may rely on it
        being a measurement.
        """
        if prop not in self.properties:
            raise ElementDataError(
                f"{self.name!r} has no property {prop!r}. It carries {len(self.properties)} "
                f"properties, from {self.citation}."
            )
        row = self._values.get(element)
        if row is None:
            raise ElementDataError(
                f"{self.name!r} has no element {element!r}. It covers {len(self._values)} "
                f"elements, from {self.citation}. A composition containing it cannot be "
                f"featurised from this table, and substituting zeros for it -- which is what "
                f"CBFV does -- would produce a number that looks like a measurement."
            )
        if prop not in row:
            raise ElementDataError(
                f"{self.name!r} has a {prop!r} column but no value for {element!r} in "
                f"{self.citation}: the cell is empty, or carries the table's missing-value "
                f"sentinel. This is a hole in the published table -- not a zero, not a NaN and "
                f"not -9999 -- and nothing downstream may treat it as any of them."
            )
        return row[prop]

    def vector(self, prop: str, elements: tuple[str, ...]) -> np.ndarray:
        """``prop`` for each element, in the order given.

        The array is what the composition statistics (card #17) average, deviate and range
        over. Every entry is a real number or the call raises: a partially-filled array
        would push the decision about holes into whichever statistic happened to see it
        first, which is precisely how ``avg_polzbl_divi_atom_mass`` came to be computed for
        a europium that CBFV had silently zeroed.
        """
        return np.array([self.value(e, prop) for e in elements], dtype=np.float64)


def _read(
    path: Path, sentinels: frozenset[float]
) -> tuple[tuple[str, ...], dict[str, dict[str, float]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        properties = tuple(header[1:])
        values: dict[str, dict[str, float]] = {}
        for row in reader:
            if not row:
                continue
            # A hole is simply not recorded, so `prop in row` is the whole test for "does this
            # table actually have this number". Both spellings collapse here -- an empty cell
            # and a sentinel value -- so no code past this point has to know the difference.
            kept: dict[str, float] = {}
            for prop, cell in zip(properties, row[1:], strict=True):
                if cell == "":
                    continue
                number = float(cell)
                if number in sentinels or math.isnan(number):
                    continue
                kept[prop] = number
            values[row[0]] = kept
    return properties, values


@cache
def load_table(name: str) -> PropertyTable:
    """Load one of :data:`TABLES` by name. Cached: the CSVs never change at runtime."""
    if name not in TABLES:
        raise ElementDataError(
            f"unknown element property table {name!r}. This project reimplements exactly "
            f"two, {' and '.join(repr(t) for t in TABLES)}, because those are the two the 22 "
            f"selected features come from (card #8)."
        )
    path = _DATA / f"{name}.csv"
    if not path.is_file():
        raise ElementDataError(
            f"{path} is missing. The committed tables are built from their cited sources by "
            f"scripts/build_element_tables.py; see hydms/descriptors/data/SOURCES.md."
        )
    properties, values = _read(path, _SENTINELS[name])
    return PropertyTable(
        name=name, citation=_CITATION[name], properties=properties, _values=values
    )


def require_coverage(
    table: str, elements: frozenset[str] | set[str], properties: tuple[str, ...] | list[str]
) -> None:
    """Raise unless ``table`` can supply every one of ``properties`` for every element.

    Called with the elements a dataset actually uses, this is the check that a table was
    validated against the right thing. The curated dataset uses **55** elements, not the 54
    that ``REPORT.md`` §2.3 and the PRD's dataset table both state -- counted from the parsed
    compositions of all 1279 rows, with seven appearing exactly once (N, Eu, Lu, Pb, Au, Os,
    Re). The disagreement is recorded on card #89. A table validated against 54 would pass
    while one element silently had no properties, which is the failure this function exists
    to make impossible, so callers derive the set rather than writing a number down.

    Every gap is reported, not just the first: finding them one exception at a time across a
    55-element table is how a session gets spent.
    """
    loaded = load_table(table)
    unknown = [p for p in properties if p not in loaded.properties]
    if unknown:
        raise ElementDataError(
            f"{table!r} has no such propert{'y' if len(unknown) == 1 else 'ies'}: "
            f"{', '.join(sorted(unknown))}."
        )

    absent = sorted(e for e in elements if e not in loaded.elements)
    holes = sorted(
        f"{prop}[{element}]"
        for prop in properties
        for element in sorted(elements)
        if element in loaded.elements and not loaded.has(element, prop)
    )
    if not absent and not holes:
        return

    parts = []
    if absent:
        parts.append(f"{len(absent)} element(s) absent from the table: {', '.join(absent)}")
    if holes:
        shown = ", ".join(holes[:10]) + (f" (+{len(holes) - 10} more)" if len(holes) > 10 else "")
        parts.append(f"{len(holes)} empty cell(s) in the published table: {shown}")
    raise ElementDataError(
        f"{table!r} ({loaded.citation}) cannot cover the requested "
        f"{len(elements)} element(s) x {len(properties)} propert(y/ies). " + "; ".join(parts)
    )
