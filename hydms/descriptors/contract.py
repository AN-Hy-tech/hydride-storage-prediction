"""The 22 features: their names, their order, their dtype, and where each one is computable.

Card #19. This module is the single source of truth for what a feature matrix *is*. The
featuriser (#20) builds columns from it, the scaler (#23) and the surrogate (#26) are handed
matrices checked against it, and the artifact manifest (#4) records it so a stored model
carries what it expects rather than trusting the caller to remember.

Nothing here computes a number. :mod:`hydms.descriptors.element_data` owns the tables and
:mod:`hydms.descriptors.stats` owns the arithmetic; this module owns the *names* and the
question those two cannot answer between them -- **for which compositions does each name
mean anything at all?**

**A feature is a statistic of a property of a table.** Twenty-one of the 22 are
``f"{statistic}_{property}"``: five statistics (:data:`~hydms.descriptors.stats.STATISTICS`)
over the 19 distinct element properties the selected set needs, 13 from ``oliynyk`` and 6
from ``jarvis``. The twenty-second, ``temperature(K)``, is not a descriptor at all -- it is
the raw input column carried through, and it is classified separately rather than attributed
to a table (:doc:`FEATURE_PROVENANCE`, card #8).

That rule is what makes the contract *regenerable* rather than hand-maintained. When card
#25 re-runs selection and the set becomes some other N, :meth:`FeatureContract.from_names`
rebuilds the whole contract from the selected names, because the name carries its own
provenance. Measured: the rule is injective over everything either table could ever offer --
5 statistics x 537 properties gives 2,685 names and 2,685 distinct ones, no collision -- and
the two tables share **no** property name, so a name identifies its table without ambiguity.
Three JARVIS properties do begin with a statistic's spelling (``avg_ion_rad``,
``max_oxid_s``, ``min_oxid_s``), which is why the split is on the *first* underscore and not
on any of the five prefixes.

**Two vocabularies, one alias map.** The published feature names quote CBFV's spelling of
the Oliynyk columns -- ``dev_Pauling_Electronegativity``, ``dev_Gordy_electonegativity``
(the typo is in the source table) -- while the committed table uses the 2024 publication's
own headers, ``pauling_en`` and ``gordy_en``. :data:`PUBLISHED_SPELLING` maps ours to
theirs for exactly the 13 Oliynyk properties in play, and is the identity everywhere else:
the JARVIS half already agrees, because CBFV's ``jarvis.csv`` *is* NIST's file. The map is
asserted against CBFV's own header in ``tests/descriptors/test_contract.py`` rather than
trusted, using the reference table #16 committed for gate AC-2.

Order and dtype
---------------

**The declared order is REPORT.md 3.2's, and it is a declaration rather than a recovery.**
The order the published model was actually *trained* in was ``selected_cols_final`` -- the
survivors of Boruta and iterative VIF, in the order CBFV emitted them
(``Boruta_FeatEng.py:112``) -- and that order is nowhere in this repository.
``Machine_Model/data/processed_data/`` was never committed, and every committed listing of
the 22 is sorted by something else: ``feature_selection_report.csv`` by SHAP descending,
``feature_importance.csv`` alphabetically, ``feature_target_pearson_corr.csv`` by
correlation. So this module *chooses* the SHAP-descending order, because that is the one a
reader of the thesis has seen. What protects AC-4 is not that the order matches history --
it cannot be known to -- but that exactly one place declares it.

**Every column is ``float64``, including ``temperature(K)``, which arrives as ``int64``.**
The raw column is integer-valued in all 1,279 rows and both loader schemas declare it
``integer`` (:func:`hydms.data.load.hydride_data_schema`). It is cast here anyway, for a
reason that is not tidiness: the applicability domain this project ships is a continuous
bound (``temperature_min_k: 195.0`` in ``pipeline.yaml``), a scaler returns floats, and a
candidate evaluated at 313.5 K silently truncates to 313 in an integer column. One dtype for
the whole matrix also makes :func:`assert_contract` a check rather than a lookup table.

Where the 22 are computable, and where they are not
---------------------------------------------------

The card that opened this module said **two** of the 22 cannot be computed everywhere.
Counted per column against the citable sources over all 1,279 curated rows, it is **seven**:

=====================================  =========  ==============  =====================
feature                                blocked by rows uncomputable compositions
=====================================  =========  ==============  =====================
``dev_Gordy_electonegativity``         21 elements 266 of 1,279   236 of 1,115
``avg_polzbl_divi_atom_mass``          Eu          1              1
``dev_atom_mass_mult_therm_cond``      Eu          1              1
``avg_is_alkaline``                    Eu          1              1
``dev_bp_divi_atom_mass``              Eu          1              1
``range_first_ion_en_mult_X``          Eu          1              1
``dev_voro_coord_divi_mol_vol``        Eu          1              1
=====================================  =========  ==============  =====================

The card was not wrong about the *causes* -- it named both -- only about the count, because
all six JARVIS features fail on one element and it counted them as one. As a contract they
are six columns, and a caller asking "can I build this matrix?" needs six answers.

**The single europium row is ``Eu1Ni5``, row 516.** NIST marks 434 of europium's 438 JARVIS
properties ``-9999``; the four real ones are ``X``, ``Z``, ``atom_mass`` and ``atom_rad``,
and none of the six selected features is computable from those. CBFV, handed the same row,
drops europium from its index and substitutes an all-zero property vector -- which is why
gate AC-2 must exclude the row rather than compare against it (#21).

**The Gordy hole belongs to the citable edition, not to CBFV.** Lee et al. 2024 leave
``gordy_en`` blank for 21 of the 55 elements this dataset uses -- Ce, Dy, Er, Eu, Gd, Hf, Ho,
Ir, Lu, Nd, Os, Pr, Pt, Re, Sm, Ta, Tb, Th, Tm, U, W -- while CBFV's older copy supplies a
value for **all twenty-one** of them (measured against ``cbfv_oliynyk_reference.csv``:
Ce 4.5734, Hf 6.3704, Pr 4.6395, ...). So the published model trained on a real Gordy number
for every row, and the hole is something the reimplementation *acquires* by citing its
sources properly. Two consequences, both belonging to other cards and boxed there: gate AC-2
does not see this at all, because it is run against CBFV's table where no hole exists (#21);
and the choice between dropping 266 rows and dropping the feature is feature selection's to
make with these numbers in hand (#24, #25).

The loss is not spread evenly, and the card's guess at its shape was the wrong pair of
families. Rows affected, by reconciled alloy class::

    AB5   91 of 196  (46.4%)      SS    19 of 103  (18.4%)
    MIC   54 of 127  (42.5%)      MEA   12 of 109  (11.0%)
    HEA   20 of  77  (26.0%)      A2B    3 of  32  ( 9.4%)
    AB    22 of  90  (24.4%)      AB2   34 of 371  ( 9.2%)
    Mg    11 of 148  ( 7.4%)      LEA    0 of  26  ( 0.0%)

The card expected "most of the AB5 and AB2 chemistry". AB2 is the *second least* affected
class at 9.2%, and AB5 loses under half its rows. The pair that actually carries the loss is
AB5 and MIC. On the second source, ML-HYDPARK's 772 formulae, the same seven features cost
128 rows (16.6%), all of them Gordy except the one europium row.

**A hole is not a number and this module will not pretend otherwise.**
:meth:`FeatureContract.computability` answers per composition, before anything is computed,
and returns the blocking element and the reason. That is the whole point of the card: the
alternative -- letting the featuriser produce a NaN and a median-fill turn it back into
something that looks like a measurement -- is the mechanism that put a europium row computed
as though europium had zero mass into the published feature matrix.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from typing import Any, Final

import pandas as pd

from hydms.descriptors.element_data import TABLES, PropertyTable, load_table
from hydms.descriptors.stats import STATISTICS

__all__ = [
    "CONTRACT",
    "DTYPE",
    "PUBLISHED_SPELLING",
    "Computability",
    "ContractError",
    "FeatureContract",
    "FeatureSpec",
    "Hole",
    "assert_contract",
]

#: Every feature column, without exception. See the module docstring's "Order and dtype":
#: ``temperature(K)`` arrives as ``int64`` and is cast, because a candidate at 313.5 K must
#: not become 313.
DTYPE: Final = "float64"

#: Our property name -> the spelling the published feature names use. The identity for
#: everything absent from this map, which is the whole JARVIS half: CBFV's ``jarvis.csv`` is
#: NIST's own file and needs no translation. Verified against CBFV's header in
#: ``tests/descriptors/test_contract.py``; the ``electonegativity`` misspelling is the source
#: table's and is reproduced deliberately.
PUBLISHED_SPELLING: Final[Mapping[str, str]] = {
    "zunger_radii_sum": "Zunger_radii_sum",
    "pauling_en": "Pauling_Electronegativity",
    "valence_d": "valence_d",
    "specific_heat_j_g_k": "specific_heat_(J/g_K)_",
    "gilman_no_of_valence_electrons": "gilmor_number_of_valence_electron",
    "covalent_radius": "Covalent_Radius",
    "mulliken_en": "Mulliken_EN",
    "heat_of_vaporization_kj_mol": "heat_of_vaporization_(kJ/mol)_",
    "gordy_en": "Gordy_electonegativity",
    "mendeleev_number": "Mendeleev_Number",
    "density_g_ml": "Density_(g/mL)",
    "atomic_weight": "Atomic_Weight",
    "unfilled_s": "Number_of_unfilled_s_valence_electrons",
}

#: The raw input column carried into the matrix by ``extend_features=True``. No table
#: produces it, every table's output contains it, and it is the one feature that is always
#: computable because it is not computed.
PASSTHROUGH: Final = "temperature(K)"

# A failure naming two hundred things is a failure nobody reads to the end. Same convention
# as `hydms/data/load.py`, `hydms/data/metadata.py` and the rest of the data layer.
_MAX_NAMED = 8

# The two spellings of "this table cannot give you that number", kept apart because they are
# different problems: the first is usually a typo or an element nobody tabulated, the second
# is a blank cell in a real publication and is nobody's mistake.
_ABSENT = "the table has no such element"
_EMPTY = "the published table leaves the cell empty"


class ContractError(ValueError):
    """A feature matrix, a name or a manifest does not match the contract.

    A ``ValueError`` for the same reason as
    :class:`~hydms.descriptors.element_data.ElementDataError`,
    :class:`~hydms.descriptors.stats.CompositionError` and
    :class:`~hydms.data.metadata.MetadataError`: the caller passed something the contract
    does not admit, rather than losing a race or a file handle.
    """


def _named(items: Iterable[object]) -> str:
    """Render offenders for a message: in the order given, truncated, and counted."""
    listed = [str(item) for item in items]
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


def _servable_in(table: PropertyTable, prop: str) -> frozenset[str]:
    """Every element ``table`` can supply ``prop`` for.

    Membership answers both failure modes at once -- an element the table has never heard of
    and an element whose cell is empty are both simply absent from the set -- so the caller
    needs one lookup rather than a try/except.
    """
    return frozenset(e for e in table.elements if table.has(e, prop))


@cache
def _servable(table: str, prop: str) -> frozenset[str]:
    """:func:`_servable_in` for a shipped table, cached.

    Cached per (table, property) because :meth:`FeatureContract.computability` is called once
    per candidate composition and the shipped tables never change at runtime. A table passed
    in by a caller cannot be cached -- :class:`~hydms.descriptors.element_data.PropertyTable`
    holds a dict and is unhashable -- so that path recomputes, which is affordable because
    the only caller is a gate that runs once.
    """
    return _servable_in(load_table(table), prop)


@dataclass(frozen=True)
class FeatureSpec:
    """One column: what it is called, and what it is made of.

    Frozen, like every other description of a published artifact in this layer. A caller able
    to edit a spec in place could make a stored model's manifest disagree with the matrix the
    featuriser builds, which is the exact failure the contract exists to prevent.
    """

    #: The published name, e.g. ``dev_Pauling_Electronegativity``. This is the identity: it
    #: is what REPORT.md quotes, what the manifest stores and what the matrix column is
    #: called.
    name: str
    #: One of :data:`~hydms.descriptors.stats.STATISTICS`, or ``None`` for the passthrough.
    statistic: str | None
    #: ``"oliynyk"`` or ``"jarvis"``, or ``None`` for the passthrough.
    table: str | None
    #: The property name **as the committed table spells it**, not as the feature name does.
    prop: str | None

    def __post_init__(self) -> None:
        parts = (self.statistic, self.table, self.prop)
        if (None in parts) != all(part is None for part in parts):
            raise ContractError(
                f"{self.name!r} is half a descriptor: statistic={self.statistic!r}, "
                f"table={self.table!r}, property={self.prop!r}. A feature is either a "
                f"statistic of a property of a table or a passthrough, never in between."
            )
        if self.statistic is not None and self.statistic not in STATISTICS:
            raise ContractError(
                f"{self.name!r} names statistic {self.statistic!r}, which "
                f"hydms.descriptors.stats does not implement. The five are "
                f"{', '.join(STATISTICS)}; CBFV's `mode` is deliberately absent."
            )
        if self.table is not None and self.table not in TABLES:
            raise ContractError(
                f"{self.name!r} names table {self.table!r}. This project reimplements "
                f"exactly two, {' and '.join(repr(t) for t in TABLES)} (card #8)."
            )

    @property
    def is_passthrough(self) -> bool:
        """Whether this column is carried from the raw input rather than computed.

        Exactly one of the 22 is: ``temperature(K)``. It is the only feature that is always
        computable, because nothing looks it up.
        """
        return self.table is None

    @classmethod
    def of(cls, statistic: str, table: str, prop: str) -> FeatureSpec:
        """A descriptor spec, with its published name built by the naming rule.

        The rule is ``f"{statistic}_{PUBLISHED_SPELLING.get(prop, prop)}"`` and it is what
        makes the contract regenerable: card #25 selects names, not hand-written specs.
        """
        return cls(
            name=f"{statistic}_{PUBLISHED_SPELLING.get(prop, prop)}",
            statistic=statistic,
            table=table,
            prop=prop,
        )

    @classmethod
    def passthrough(cls, name: str = PASSTHROUGH) -> FeatureSpec:
        """The raw-input column, attributed to no table."""
        return cls(name=name, statistic=None, table=None, prop=None)


@dataclass(frozen=True)
class Hole:
    """One reason one feature cannot be computed for one composition.

    Carries the *element* rather than only the feature, because that is what a caller can
    act on: ``dev_Gordy_electonegativity is unavailable`` is a dead end, while
    ``Ce has no gordy_en in oliynyk`` names a substitution to consider and a table to check.
    """

    feature: str
    element: str
    table: str
    prop: str
    #: :data:`_ABSENT` or :data:`_EMPTY` -- which of the two ways the table fails.
    reason: str

    def __str__(self) -> str:
        return f"{self.feature} needs {self.prop}[{self.element}]: {self.reason} ({self.table})"


@dataclass(frozen=True)
class Computability:
    """Which of the contract's features this composition can actually produce.

    The verdict card #19 exists to deliver, and the reason it is a verdict rather than a
    boolean: a caller that only learns *that* a composition is unusable will drop it
    silently, which is the behaviour the screens layer forbids (card #44) and the refusal
    path requires an explanation for (card #77).
    """

    #: The element symbols the verdict was computed over, sorted.
    elements: tuple[str, ...]
    #: Feature names that can be computed, in contract order.
    available: tuple[str, ...]
    #: Every (feature, element) pair that fails, in contract order then element order. One
    #: feature blocked by three elements appears three times; :attr:`unavailable` is the
    #: deduplicated view.
    holes: tuple[Hole, ...]

    @property
    def complete(self) -> bool:
        """Whether every feature in the contract can be computed for this composition."""
        return not self.holes

    @property
    def unavailable(self) -> tuple[str, ...]:
        """The blocked feature names, deduplicated, in contract order."""
        return tuple(dict.fromkeys(hole.feature for hole in self.holes))

    @property
    def reason(self) -> str:
        """One sentence a refusal can quote verbatim, or a statement that nothing is wrong."""
        if self.complete:
            return (
                f"all {len(self.available)} features are computable for "
                f"{''.join(self.elements)}"
            )
        blocked = sorted({hole.element for hole in self.holes})
        return (
            f"{len(self.unavailable)} of {len(self.available) + len(self.unavailable)} "
            f"features cannot be computed for {''.join(self.elements)}: "
            f"{_named(self.unavailable)}. Blocking element(s): {_named(blocked)}. "
            f"{_named(str(hole) for hole in self.holes)}"
        )


@dataclass(frozen=True)
class FeatureContract:
    """The feature names, their order and their dtype -- declared once, for everybody.

    Frozen and ordered. ``features`` is a tuple because the order *is* the contract: a model
    trained on one order and fed another produces plausible, wrong numbers, which is the
    silent failure AC-4 exists to catch.
    """

    features: tuple[FeatureSpec, ...]

    def __post_init__(self) -> None:
        if not self.features:
            raise ContractError(
                "a feature contract with no features cannot be a contract; it would accept "
                "every matrix, including an empty one."
            )
        names = [spec.name for spec in self.features]
        duplicated = [name for name in dict.fromkeys(names) if names.count(name) > 1]
        if duplicated:
            raise ContractError(
                f"{len(duplicated)} feature name(s) appear more than once: "
                f"{_named(duplicated)}. A name is a column, and pandas will happily give a "
                f"frame two columns with one name."
            )

    def __len__(self) -> int:
        return len(self.features)

    def __iter__(self) -> Iterator[FeatureSpec]:
        return iter(self.features)

    def __contains__(self, name: object) -> bool:
        return any(spec.name == name for spec in self.features)

    def __getitem__(self, name: str) -> FeatureSpec:
        """``contract["avg_valence_d"]`` -- the spec behind a column name.

        Raises:
            KeyError: naming the contract's size, because the usual cause is a name from a
                different selection round rather than a typo.
        """
        for spec in self.features:
            if spec.name == name:
                return spec
        raise KeyError(
            f"{name!r} is not in this contract, which declares {len(self.features)} "
            f"feature(s). If it came from a different selection round, rebuild the contract "
            f"with FeatureContract.from_names() rather than editing this one."
        )

    @property
    def names(self) -> tuple[str, ...]:
        """The column names, in contract order. What a matrix's columns must equal."""
        return tuple(spec.name for spec in self.features)

    @property
    def digest(self) -> str:
        """A stable fingerprint of the names, their order and their dtype.

        What a stored model records so it can refuse a matrix built by a different contract
        without carrying the whole list around. Order-sensitive by construction: two
        contracts over the same names in different orders have different digests, which is
        the point.
        """
        payload = "\n".join(f"{spec.name}\t{DTYPE}" for spec in self.features)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def computability(
        self,
        composition: Iterable[str],
        tables: Mapping[str, PropertyTable] | None = None,
    ) -> Computability:
        """Which features this composition can produce, and why the rest cannot.

        Called *before* featurisation, per candidate. The amounts are irrelevant -- a hole is
        per element per property -- so a ``dict`` from
        :func:`hydms.data.load.parse_formula` may be passed directly and its keys are used.

        Args:
            composition: The element symbols, or any mapping keyed by them.
            tables: The tables to answer *against*, by name. Defaults to the shipped, cited
                ones, which is what a caller featurising for real wants. The exception is
                gate AC-2 (card #21), which is required to run against CBFV's copy of the
                Oliynyk table: that copy supplies ``gordy_en`` for all 21 elements the
                citable 2024 edition leaves blank, so a verdict computed against the shipped
                table would refuse 266 of the 1,279 rows the gate exists to compare.
                :func:`hydms.descriptors.featurize.featurize` forwards whatever it was given,
                so the verdict is always about the numbers actually used.

        Returns:
            Computability: the verdict, with a blocking element and a reason per failure.

        Raises:
            ContractError: if the composition is empty. There is no honest verdict for a
                composition with no elements, and returning "everything is computable"
                would be the dishonest one.
        """
        elements = tuple(sorted(set(composition)))
        if not elements:
            raise ContractError(
                "an empty composition has no computability verdict: every feature would be "
                "vacuously available. hydms.data.load.parse_formula refuses these at the "
                "door and hydms.descriptors.stats.statistics raises on them too."
            )

        supplied = dict(tables) if tables else {}
        available: list[str] = []
        holes: list[Hole] = []
        for spec in self.features:
            if spec.table is None or spec.prop is None:
                available.append(spec.name)
                continue
            source = supplied.get(spec.table)
            servable = (
                _servable(spec.table, spec.prop)
                if source is None
                else _servable_in(source, spec.prop)
            )
            blocking = [element for element in elements if element not in servable]
            if not blocking:
                available.append(spec.name)
                continue
            known = (load_table(spec.table) if source is None else source).elements
            holes.extend(
                Hole(
                    feature=spec.name,
                    element=element,
                    table=spec.table,
                    prop=spec.prop,
                    reason=_EMPTY if element in known else _ABSENT,
                )
                for element in blocking
            )
        return Computability(
            elements=elements, available=tuple(available), holes=tuple(holes)
        )

    def as_manifest(self) -> dict[str, Any]:
        """The contract as JSON-safe data, for card #4's artifact manifest.

        Returns:
            ``{"features": [{"name", "statistic", "table", "property", "dtype"}, ...],
            "digest": ...}``. The passthrough's ``statistic``, ``table`` and ``property`` are
            ``None``, which JSON writes as ``null`` and :meth:`from_manifest` reads back.
        """
        return {
            "features": [
                {
                    "name": spec.name,
                    "statistic": spec.statistic,
                    "table": spec.table,
                    "property": spec.prop,
                    "dtype": DTYPE,
                }
                for spec in self.features
            ],
            "digest": self.digest,
        }

    @classmethod
    def from_manifest(cls, payload: Mapping[str, Any]) -> FeatureContract:
        """Rebuild a contract from :meth:`as_manifest`, checking the digest.

        Args:
            payload: What :meth:`as_manifest` produced, after a round trip through JSON.

        Returns:
            FeatureContract: equal to the one that produced ``payload``.

        Raises:
            ContractError: if the payload is malformed, or if the rebuilt contract's digest
                does not match the recorded one -- which means the stored names, their order
                or their dtype were edited after the model was fitted.
        """
        entries = payload.get("features")
        if not isinstance(entries, list):
            raise ContractError(
                f"a contract manifest needs a 'features' list; got "
                f"{type(entries).__name__}. Keys present: {_named(sorted(payload))}."
            )
        features = []
        for index, entry in enumerate(entries):
            missing = [key for key in ("name", "statistic", "table", "property")
                       if key not in entry]
            if missing:
                raise ContractError(
                    f"feature {index} of the manifest is missing {_named(missing)}. "
                    f"A manifest entry is what FeatureContract.as_manifest() writes."
                )
            features.append(
                FeatureSpec(
                    name=entry["name"],
                    statistic=entry["statistic"],
                    table=entry["table"],
                    prop=entry["property"],
                )
            )
        contract = cls(features=tuple(features))
        recorded = payload.get("digest")
        if recorded is not None and recorded != contract.digest:
            raise ContractError(
                f"the manifest's digest {recorded!r} does not match the contract it "
                f"describes ({contract.digest!r}). The recorded names, their order or their "
                f"dtype were changed after the model was fitted, and a model fed a matrix "
                f"built to a different contract returns plausible, wrong numbers."
            )
        return contract

    @classmethod
    def from_names(cls, names: Iterable[str]) -> FeatureContract:
        """Rebuild the contract from a list of feature names, resolving each to its table.

        This is what card #25 calls after re-running selection: the contract is *regenerated*
        rather than hand-edited, because the name carries its own provenance. Resolution is
        unambiguous -- the two tables share no property name, and the naming rule is
        injective over every property either of them offers.

        Args:
            names: Feature names in the order the matrix will carry them.

        Returns:
            FeatureContract: with each descriptor resolved to (statistic, table, property).

        Raises:
            ContractError: naming every unresolvable feature at once, and saying which half
                of the name failed. Resolving them one exception at a time across a
                twenty-column selection is how a session gets spent.
        """
        wanted = list(names)
        inverse = {published: ours for ours, published in PUBLISHED_SPELLING.items()}
        properties = {table: set(load_table(table).properties) for table in TABLES}

        features: list[FeatureSpec] = []
        failures: list[str] = []
        for name in wanted:
            if name == PASSTHROUGH:
                features.append(FeatureSpec.passthrough(name))
                continue
            statistic, _, published = name.partition("_")
            if statistic not in STATISTICS or not published:
                failures.append(
                    f"{name!r} does not begin with one of {', '.join(STATISTICS)}"
                )
                continue
            prop = inverse.get(published, published)
            table = next((t for t in TABLES if prop in properties[t]), None)
            if table is None:
                failures.append(f"{name!r} names property {prop!r}, which is in neither table")
                continue
            features.append(FeatureSpec(name=name, statistic=statistic, table=table, prop=prop))

        if failures:
            raise ContractError(
                f"{len(failures)} of {len(wanted)} feature name(s) could not be resolved to "
                f"a table: {_named(failures)}. A feature name is "
                f"'<statistic>_<property>', with the property spelled as the published "
                f"features spell it (hydms.descriptors.contract.PUBLISHED_SPELLING); "
                f"{PASSTHROUGH!r} is the one name that is not a descriptor."
            )
        return cls(features=tuple(features))


#: The 22 published features, in REPORT.md 3.2's SHAP-descending order. Written as literal
#: (statistic, table, property) triples rather than resolved from the tables, so importing
#: this module reads no files; ``test_contract.py`` asserts that
#: ``FeatureContract.from_names(CONTRACT.names)`` reproduces it exactly, which is the
#: regeneration path card #25 will use.
CONTRACT: Final[FeatureContract] = FeatureContract(
    features=(
        FeatureSpec.of("avg", "jarvis", "polzbl_divi_atom_mass"),
        FeatureSpec.of("dev", "oliynyk", "zunger_radii_sum"),
        FeatureSpec.of("dev", "oliynyk", "pauling_en"),
        FeatureSpec.of("avg", "oliynyk", "valence_d"),
        FeatureSpec.of("dev", "jarvis", "atom_mass_mult_therm_cond"),
        FeatureSpec.of("avg", "jarvis", "is_alkaline"),
        FeatureSpec.of("dev", "jarvis", "bp_divi_atom_mass"),
        FeatureSpec.of("dev", "oliynyk", "specific_heat_j_g_k"),
        FeatureSpec.of("dev", "oliynyk", "gilman_no_of_valence_electrons"),
        FeatureSpec.of("dev", "oliynyk", "covalent_radius"),
        FeatureSpec.of("range", "oliynyk", "mulliken_en"),
        FeatureSpec.of("range", "oliynyk", "specific_heat_j_g_k"),
        FeatureSpec.of("range", "oliynyk", "heat_of_vaporization_kj_mol"),
        FeatureSpec.of("dev", "oliynyk", "gordy_en"),
        FeatureSpec.of("range", "jarvis", "first_ion_en_mult_X"),
        FeatureSpec.of("range", "oliynyk", "mendeleev_number"),
        FeatureSpec.of("range", "oliynyk", "density_g_ml"),
        FeatureSpec.of("dev", "jarvis", "voro_coord_divi_mol_vol"),
        FeatureSpec.of("dev", "oliynyk", "heat_of_vaporization_kj_mol"),
        FeatureSpec.of("range", "oliynyk", "atomic_weight"),
        FeatureSpec.passthrough(),
        FeatureSpec.of("avg", "oliynyk", "unfilled_s"),
    )
)


def assert_contract(frame: pd.DataFrame, contract: FeatureContract | None = None) -> None:
    """Refuse a feature matrix that is not exactly what the contract declares.

    Four failures, reported together rather than one exception at a time: missing columns,
    extra columns, the right columns in the wrong order, and the right columns with the wrong
    dtype. The third is the one this function exists for -- a matrix with all 22 columns in a
    different order is the failure that produces plausible, wrong numbers instead of an
    error, and it is what acceptance criterion AC-4 catches downstream.

    This checks the *matrix*, not the featuriser, for the same reason
    :func:`hydms.data.metadata.refuse_non_features` does: a column can be added, dropped or
    reordered by a join, a ``concat`` or a ``reset_index`` long after featurisation, and the
    place to catch it is the last one before the fit.

    Args:
        frame: The matrix about to be scaled, fitted or predicted on.
        contract: Defaults to :data:`CONTRACT`, the published 22.

    Raises:
        ContractError: naming every discrepancy. Metadata and target columns are reported as
            the extras they are, with a pointer to the guard that owns them.
    """
    declared = contract if contract is not None else CONTRACT
    columns = list(frame.columns)

    duplicated = [name for name in dict.fromkeys(columns) if columns.count(name) > 1]
    if duplicated:
        raise ContractError(
            f"the matrix has {len(duplicated)} duplicated column name(s): "
            f"{_named(duplicated)}. Every check below would then be ambiguous, because "
            f"frame[name] returns a frame rather than a column."
        )

    problems: list[str] = []
    missing = [name for name in declared.names if name not in columns]
    extra = [name for name in columns if name not in declared]
    if missing:
        problems.append(f"{len(missing)} missing: {_named(missing)}")
    if extra:
        problems.append(
            f"{len(extra)} not in the contract: {_named(extra)}. Metadata and the target "
            f"travel beside the matrix, never inside it -- "
            f"hydms.data.metadata.refuse_non_features is the guard for that"
        )
    if not missing and not extra and columns != list(declared.names):
        first = next(
            i
            for i, (got, want) in enumerate(zip(columns, declared.names, strict=True))
            if got != want
        )
        problems.append(
            f"the right {len(columns)} columns in the wrong order: position {first} is "
            f"{columns[first]!r} and the contract declares {declared.names[first]!r}. "
            f"A model trained on one order and fed another returns plausible, wrong numbers"
        )

    wrong = [
        f"{name} is {frame[name].dtype}"
        for name in declared.names
        if name in columns and str(frame[name].dtype) != DTYPE
    ]
    if wrong:
        problems.append(
            f"{len(wrong)} column(s) are not {DTYPE}: {_named(wrong)}. Every feature is "
            f"{DTYPE}, including {PASSTHROUGH!r}, which the raw file stores as an integer"
        )

    if problems:
        raise ContractError(
            f"the feature matrix does not match the {len(declared)}-feature contract "
            f"(digest {declared.digest[:12]}): " + "; ".join(problems) + "."
        )
