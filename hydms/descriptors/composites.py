"""How two element properties combine into one derived property -- and who did the combining.

Card #18. Six of the 22 selected features are drawn from JARVIS and five of those name two
properties rather than one: ``avg_polzbl_divi_atom_mass``, ``dev_bp_divi_atom_mass``,
``dev_atom_mass_mult_therm_cond``, ``dev_voro_coord_divi_mol_vol``, ``range_first_ion_en_mult_X``.
The sixth, ``avg_is_alkaline``, is a plain column and is grouped with them only because all six
fail on the same element.

**Nothing here computes a feature.** :mod:`hydms.descriptors.element_data` owns the tables,
:mod:`hydms.descriptors.stats` owns the five statistics, and :mod:`hydms.descriptors.contract`
owns the names. This module owns the one question those three cannot answer between them --
*is the column called ``a_divi_b`` actually ``a`` divided by ``b``?* -- and the answer is: on the
committed JARVIS table, **for 145 of 156 columns yes, and for eleven no**.

The order the statistic and the composite are applied in
--------------------------------------------------------

**Statistic-of-composite.** The composite is a property *of an element*: the table publishes a
column for it, so the statistic is taken over that column exactly as it is taken over ``polzbl``
or ``bp``. Card #16 settled PRD risk **R3** that way -- by construction, from the source data,
not by experiment -- and card #8's note that the composites "appear in no table header" was
simply wrong.

The card asked for both orders behind a flag with the loser deleted before merge. They were
**measured instead of shipped**, which is cheaper and leaves more behind: no flag ever existed,
and the rejected order is pinned in ``tests/descriptors/test_composites.py`` as a negative test,
so a later "simplification" back to composite-of-statistic fails rather than silently changing
every one of these five features. The two orders are nowhere near each other. Against CBFV's own
output over the sixteen fixture formulae, statistic-of-composite agrees to at worst **9.1e-13**;
composite-of-statistic is wrong by between **1.8%** (``avg_first_ion_en_mult_X``) and a factor of
**65** (``dev_bp_divi_atom_mass``). Some of the disagreements are structural rather than merely
large: ``range(a) / range(b)`` and ``range(a) * range(b)`` are not ranges of anything, and on a
two-element composition ``dev_voro_coord_divi_mol_vol`` computed the wrong way is **exactly
zero**. This is a first-significant-figure difference, so no tolerance anywhere in the project
would have hidden it.

The grammar, and why a declarative spec is possible
---------------------------------------------------

``_divi_`` divides, ``_mult_`` multiplies, and the operands are themselves column names:
:data:`INFIXES` is the whole specification. That it can be a specification rather than a table of
special cases is a measured property of the source, not an assumption:

* 156 of JARVIS's 438 columns carry an infix; ``oliynyk`` carries **none**.
* **No** column name carries two infixes.
* **Every** one of the 156 splits into two names that are themselves columns of the same table.
* **No** column splits two ways -- so :func:`decompose` performs a parse, never a guess.

The one trap is that a *feature* name is not a *property* name.
``avg_polzbl_divi_atom_mass`` splits on its infix into ``avg_polzbl`` and ``atom_mass``, and the
first of those is not a column. :func:`decompose` refuses it rather than inventing a
decomposition; the statistic is stripped by :meth:`hydms.descriptors.contract.FeatureContract.
from_names`, which splits on the *first* underscore, and what reaches here is what is left.

Eleven columns are not what their names say
--------------------------------------------

For every element carrying the column and both operands, 145 of the 156 composites equal the
arithmetic of their parts **bit-exactly** -- not to a tolerance, to ``==``, on every element.
Eleven do not, and they are one family and two elements::

    X_mult_voro_coord, atom_mass_mult_voro_coord, atom_rad_mult_voro_coord,
    bp_mult_voro_coord, elec_aff_mult_voro_coord, first_ion_en_mult_voro_coord,
    hfus_mult_voro_coord, mol_vol_mult_voro_coord, ... (11 in all)

wrong on exactly **Cs and Gd**, where every one of them is ``0.0``. Both elements store
``voro_coord = 1.0``, and ``voro_coord_divi_mol_vol`` uses that 1.0 (Gd: ``1/19.9 =
0.05025125628140704``, the stored value). So the published file contradicts itself about two
elements: its ``_mult_voro_coord`` family was formed as though ``voro_coord`` were 0, and its
``_divi_`` column as though it were 1.

**Which is why the featuriser reads the published column and never a value it derives.** CBFV
reads the column, so the column is what parity means (#21). On the five selected composites the
two routes are the same double for all 82 elements that carry them -- the rule costs nothing
today. The eleven columns are what make it a rule rather than a preference, and
:func:`require_self_consistent` is how a caller finds out before training rather than after.

**``voro_coord = 1.0`` is a placeholder, and it reaches a selected feature.** Every other element
in the table has 3 to 12 (the histogram is 3.0-12.0 across 101 elements; only Cs and Gd sit at
1.0), and gadolinium is hcp with twelve nearest neighbours. Gd appears in **18 of the 1,279**
curated rows and ``dev_voro_coord_divi_mol_vol`` is one of the 22, so those rows carry a
descriptor built on a filler value. That is a limitation to state rather than a bug to fix here:
it is boxed on #83 (the model card's stated limits) and on #25, which owns whether the feature
survives re-selection.

**A hole in a part is a hole in the column, 156 times out of 156.** The table never carries a
number for a composite whose operands it does not have -- unlike CBFV, which substitutes zeros
for an element it lacks and emits a full row of plausible descriptors. So
:meth:`~hydms.descriptors.element_data.PropertyTable.has` on the composite is the whole test, and
europium -- whose JARVIS properties are all ``-9999`` -- is refused by the column just as it is by
its parts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from hydms.descriptors.element_data import ElementDataError, PropertyTable, load_table

__all__ = [
    "INFIXES",
    "SELF_CONSISTENCY_ATOL",
    "SELF_CONSISTENCY_RTOL",
    "Composite",
    "CompositeError",
    "Disagreement",
    "composite_properties",
    "decompose",
    "disagreements",
    "require_self_consistent",
]

#: The whole specification: the two infixes CBFV and JARVIS spell composites with, mapped to the
#: arithmetic they name. Not a private vocabulary -- ``_divi_`` and ``_mult_`` are inside five of
#: the 22 published feature names, so these strings are half of what card #19's contract quotes.
INFIXES: Final[dict[str, str]] = {"_divi_": "/", "_mult_": "*"}

#: Measured, not chosen. A composite column and the arithmetic of its parts are the *same double*
#: on every element of the committed table where they agree at all -- 145 of 156 columns, bit for
#: bit -- so this tolerance is headroom for a future table revision rounding its columns
#: differently, never a licence for observed error. The eleven columns that disagree are out by a
#: relative 1.0, twelve orders the other side of it.
SELF_CONSISTENCY_RTOL: Final = 1e-12
SELF_CONSISTENCY_ATOL: Final = 1e-12

# A failure naming two hundred things is a failure nobody reads to the end. Same convention as
# `hydms/descriptors/contract.py`, `hydms/data/load.py` and the rest of the project.
_MAX_NAMED = 8


class CompositeError(ValueError):
    """A name cannot be decomposed, or a column is not the arithmetic its name claims.

    A ``ValueError`` for the same reason as
    :class:`~hydms.descriptors.element_data.ElementDataError`,
    :class:`~hydms.descriptors.stats.CompositionError` and
    :class:`~hydms.descriptors.contract.ContractError`: the caller passed something the data does
    not admit, rather than losing a race or a file handle.
    """


@dataclass(frozen=True)
class Composite:
    """One derived column, and the two columns it is derived from.

    Frozen for the same reason :class:`~hydms.descriptors.element_data.PropertyTable` is: a
    decomposition that could be edited after the fact could make an audit agree with a column it
    never checked.
    """

    #: The composite column's own name, e.g. ``polzbl_divi_atom_mass``.
    name: str
    #: The left operand's column name, e.g. ``polzbl``.
    left: str
    #: ``"/"`` or ``"*"``, as :data:`INFIXES` maps it.
    operator: str
    #: The right operand's column name, e.g. ``atom_mass``.
    right: str

    def combine(self, left: float, right: float) -> float:
        """The number this composite's name says its parts produce.

        Raises:
            CompositeError: on division by zero. No element of the committed table has a zero
                denominator for any of the 156 composite columns, so this is a guard for a
                future table rather than a branch anything reaches today -- and it refuses
                instead of returning ``0.0`` or an infinity, because a quotient by zero is not
                a measurement and the whole descriptor layer exists to stop one being invented.
        """
        if self.operator == "*":
            return left * right
        if right == 0.0:
            raise CompositeError(
                f"{self.name!r} divides by {self.right!r}, which is 0.0 here. There is no "
                f"honest value for that quotient; a table that needs one has a hole spelled "
                f"as a zero."
            )
        return left / right


@dataclass(frozen=True)
class Disagreement:
    """One element at which a composite column is not the arithmetic of its parts."""

    composite: Composite
    element: str
    #: What the table publishes for the composite.
    published: float
    #: What its two operands say it should be.
    derived: float

    def __str__(self) -> str:
        return (
            f"{self.composite.name}[{self.element}]: the table says {self.published!r}, "
            f"{self.composite.left} {self.composite.operator} {self.composite.right} says "
            f"{self.derived!r}"
        )


def _table(table: str | PropertyTable) -> PropertyTable:
    return load_table(table) if isinstance(table, str) else table


def decompose(name: str, table: str | PropertyTable | None = None) -> Composite | None:
    """Split a *property* name into the two properties its name says it combines.

    Args:
        name: a property name, not a feature name. ``polzbl_divi_atom_mass``, never
            ``avg_polzbl_divi_atom_mass`` -- see the module docstring's "the one trap".
        table: the table the operands must be columns of. Supplying it is what turns a string
            split into a parse; without it, a name carrying two infixes cannot be resolved and
            is refused.

    Returns:
        The decomposition, or ``None`` if the name carries no infix and so names a plain column.

    Raises:
        CompositeError: if the name carries an infix but cannot be resolved -- because a table
            was given and no split lands on two of its columns (the usual cause is a feature
            name reaching here with its statistic still attached), or because more than one
            split is valid.
    """
    known = _table(table) if table is not None else None
    splits: list[Composite] = []
    for infix, operator in INFIXES.items():
        start = name.find(infix)
        while start != -1:
            left, right = name[:start], name[start + len(infix) :]
            if left and right:
                splits.append(Composite(name=name, left=left, operator=operator, right=right))
            start = name.find(infix, start + 1)

    if not splits:
        return None
    if known is not None:
        splits = [s for s in splits if s.left in known.properties and s.right in known.properties]
        if not splits:
            raise CompositeError(
                f"{name!r} carries a composite infix but no split of it lands on two "
                f"{known.name!r} columns. A feature name reaching here with its "
                f"statistic still attached is the usual cause: 'avg_polzbl_divi_atom_mass' "
                f"splits into 'avg_polzbl' and 'atom_mass', and the first is not a column. "
                f"Strip the statistic first -- FeatureContract.from_names splits on the first "
                f"underscore."
            )
    if len(splits) > 1:
        how = ", ".join(f"{s.left} {s.operator} {s.right}" for s in splits)
        raise CompositeError(
            f"{name!r} decomposes {len(splits)} ways ({how}) and this module will not guess "
            f"between them. No column of either committed table is ambiguous -- all 156 "
            f"composites split exactly one way -- so a name that is has come from somewhere "
            f"else."
        )
    return splits[0]


def composite_properties(table: str | PropertyTable) -> tuple[Composite, ...]:
    """Every column of ``table`` whose name says it is derived from two others.

    In table order, which is the file's order. 156 for ``jarvis`` and none at all for
    ``oliynyk``: composites are a JARVIS habit, and the five in the selected feature set are
    five of the 156 rather than anything CBFV synthesised.
    """
    known = _table(table)
    found = []
    for prop in known.properties:
        composite = decompose(prop, known)
        if composite is not None:
            found.append(composite)
    return tuple(found)


def disagreements(
    table: str | PropertyTable, names: tuple[str, ...] | list[str] | None = None
) -> tuple[Disagreement, ...]:
    """Where the table's own composite columns are not the arithmetic they are named for.

    Args:
        table: the table to audit.
        names: which composite columns to check. ``None`` audits every one of them; a caller
            that only cares about the columns it is about to featurise passes those. A name
            with no infix is skipped rather than refused, so the caller may pass a mixed list
            of the properties it needs.

    Returns:
        One :class:`Disagreement` per (column, element) pair that differs by more than
        :data:`SELF_CONSISTENCY_RTOL` / :data:`SELF_CONSISTENCY_ATOL`, in table order then
        element order. Empty is the answer for the five selected composites, and for 145 of the
        156 columns in ``jarvis``.

        An element is skipped when the table lacks the column or either operand for it: a hole
        is not a disagreement, and the table never carries a composite whose parts it lacks
        (measured, 156 columns out of 156).
    """
    known = _table(table)
    if names is None:
        checked = composite_properties(known)
    else:
        checked = tuple(c for c in (decompose(n, known) for n in names) if c is not None)

    found: list[Disagreement] = []
    for composite in checked:
        for element in sorted(known.elements):
            if not all(
                known.has(element, prop)
                for prop in (composite.name, composite.left, composite.right)
            ):
                continue
            published = known.value(element, composite.name)
            try:
                derived = composite.combine(
                    known.value(element, composite.left), known.value(element, composite.right)
                )
            except CompositeError:
                # A zero denominator is a defect of the parts, not evidence about the column.
                # Unreached on the committed tables; see `Composite.combine`.
                continue
            tolerance = SELF_CONSISTENCY_ATOL + SELF_CONSISTENCY_RTOL * abs(derived)
            if abs(published - derived) > tolerance:
                found.append(
                    Disagreement(
                        composite=composite,
                        element=element,
                        published=published,
                        derived=derived,
                    )
                )
    return tuple(found)


def require_self_consistent(
    table: str | PropertyTable, names: tuple[str, ...] | list[str]
) -> None:
    """Raise unless every composite among ``names`` is the arithmetic its name claims.

    The guard a caller runs before featurising with a composite it has not audited. It exists
    because eleven of JARVIS's columns are *not* their own arithmetic and one of them,
    ``atom_mass_mult_voro_coord``, is a plausible neighbour of a selected feature: a re-run of
    feature selection (#25) over a wider candidate pool can land on one, and the failure it
    would cause is a descriptor that is zero for two elements and correct for the other 101.

    Raises:
        CompositeError: naming the columns and the elements, at most
            eight of them, because a message listing two hundred is a message nobody reads.
        ElementDataError: if a name is not a column of the table at all -- raised by
            :class:`~hydms.descriptors.element_data.PropertyTable`, and left to it rather than
            re-spelled here.
    """
    known = _table(table)
    unknown = [n for n in names if n not in known.properties]
    if unknown:
        raise ElementDataError(
            f"{known.name!r} has no propert{'y' if len(unknown) == 1 else 'ies'}: "
            f"{', '.join(sorted(unknown))}."
        )
    found = disagreements(known, names)
    if found:
        shown = "; ".join(str(d) for d in found[:_MAX_NAMED])
        more = "" if len(found) <= _MAX_NAMED else f" (+{len(found) - _MAX_NAMED} more)"
        columns = sorted({d.composite.name for d in found})
        raise CompositeError(
            f"{len(columns)} composite column(s) of {known.name!r} are not the arithmetic "
            f"their names claim, at {len(found)} element(s): {shown}{more}. The published "
            f"column is what CBFV reads and therefore what parity means, so this is not "
            f"repaired here -- it is a reason not to featurise with the column."
        )
