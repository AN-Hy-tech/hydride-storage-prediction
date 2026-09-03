"""L1 -- what makes two rows the same material.

``split_data.py:48,55`` groups on the **raw formula string** and asserts that no formula
spans two splits. That assertion passes. It is also not the property anyone wants: measured
on ``hydride_data.csv``, 1279 rows carry 1149 distinct formula strings and only **1115
distinct compositions**, and sixteen of those -- 35 rows -- land in more than one split under
the published seed. ``Ce1Mg12`` sits in test while ``Mg12Ce1`` sits in validation: the same
6.0 wt% at the same 598 K, written two ways. That is leak **L8**, and this module is the
identity that removes it.

Every selected feature is a composition statistic or the temperature (PRD section 2.3), so
two spellings of one composition have byte-identical feature vectors up to temperature. A
model that trains on one and is scored on the other is scored on its training data.

**The key is a pure function of one formula string.** That constraint decides the design.
Clustering the corpus with a tolerance would be the textbook answer to "when are two
compositions the same", and it is unavailable: a candidate alloy arriving at
``predict_capacity()`` has no corpus to be clustered against, and an identity that depends on
which other rows happen to be present is not an identity. So the key *rounds* -- and the
corpus-level property clustering would have given for free is asserted instead, by
:func:`separation`, over every formula in both raw files.

**Four significant digits on atomic fractions.** Measured over the 1784 distinct formula
strings in ``hydride_data.csv`` and ``ML-HYDPARK_v0.0.5.csv``:

    two formulae sharing a key differ by at most      3.46e-05  (9.9e-05 relative)
    two formulae with different keys differ by at least 1.01e-04 (6.45e-04 relative)

The resolution falls in that gap, so on this corpus rounding *is* clustering with a
tolerance: nothing was merged that a 1e-4 tolerance would have kept apart, and nothing was
split that it would have joined. Three or fewer digits closes the gap -- at three, the widest
pair sharing a key (3.10e-04) is **wider** than the closest pair not sharing one (1.98e-04),
which is the definition of a silent merge. Five or more digits reopens
``Ti0.2167V0.2167Nb0.2167Cr0.35`` against ``Ti0.216667V0.216667Nb0.216667Cr0.35``, which are
the same alloy typed to different precision, and gives 1116 compositions rather than the 1115
every document in this repository states. :func:`separation` is what will notice if new data
narrows the gap; it is asserted in ``tests/data/test_canonical.py``, not assumed here.

**Significant digits rather than decimal places**, which on this corpus group identically but
differ on one row. ``hydride_data.csv`` contains ``Mg0853Ni0.125La0.022`` -- a missing decimal
point, since 0.853 + 0.125 + 0.022 = 1.000 exactly -- which puts La at an atomic fraction of
2.58e-05. Rounded to four *decimal places* that element renders as ``La0``, a key asserting
that lanthanum is present at zero and one that :func:`~hydms.data.load.parse_formula` cannot
read back. Rounded to four significant digits it renders as ``La0.00002579``, and the key
stays a formula naming the same material. The row is a data defect either way and is boxed on
card #14.

**What the key is not.** It is not a row identity. Two rows may share a key legitimately --
the same material measured at two temperatures, or twice at one temperature by two groups.
Canonicalisation takes the distinct ``(key, temperature(K))`` pairs from 1272 to **1268**
over 1279 rows; four of the eleven repeats exist only because two spellings were merged. The
row identity is the spine's index label (``hydms/data/merge.py``); this is the *group* key,
which is what splits (#13) and cross-validation folds (#88) must group on.

**Alloy_class.** ``extract_features_cbfv.py:19-21`` drops every object column but
``Composition``, destroying the class and with it leave-one-alloy-class-out validation
(AC-6). That is leak **L13**. Re-joining it on the canonical key needs a decision rather than
a merge: **ten** canonical compositions carry more than one label, and
:data:`ALLOY_CLASS_PRECEDENCE` is the stated rule that resolves them. See
:func:`reconcile_class` for why precedence rather than a majority vote.

Card #87.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from itertools import combinations

import pandas as pd

from hydms.config import load as load_config
from hydms.data.load import FormulaError, parse_formula

__all__ = [
    "ALLOY_CLASS_PRECEDENCE",
    "ML_HYDPARK_CLASS_ALIASES",
    "SIGNIFICANT_DIGITS",
    "CanonicalisationError",
    "Collapse",
    "CollapseStage",
    "Separation",
    "alloy_class_table",
    "alloy_classes",
    "canonical_key",
    "collapse",
    "group_keys",
    "reconcile_class",
    "separation",
]

# A failure that names two hundred rows is a failure nobody reads to the end. The total is
# always reported; the listing is truncated. Same convention as `hydms/data/load.py`,
# `hydms/data/merge.py` and `hydms/qa/detectors.py`.
_MAX_NAMED = 8

#: Significant digits kept on each atomic fraction. The measurement that chose it, and the
#: measurement that would notice it becoming wrong, are in this module's docstring and in
#: :func:`separation`.
SIGNIFICANT_DIGITS = 4

# Fixed-point width used to render a rounded fraction. Positional notation on purpose: `%g`
# would emit `2.579e-05` for the trace element in `Mg0853Ni0.125La0.022`, and a key that
# `parse_formula` cannot read back is a key that has stopped being a formula. Twelve places
# holds four significant digits for any fraction down to 1e-9; below that `_render` refuses
# rather than emitting a zero amount.
_MAX_DECIMALS = 12


class CanonicalisationError(ValueError):
    """A composition cannot be given a canonical identity, and the message says why.

    A ``ValueError``, like :class:`~hydms.data.load.SchemaViolation` and
    :class:`~hydms.data.merge.MergeError`: this is a guard refusing, not a detector reporting
    that a guard failed.
    """


def _named(items: Iterable[object]) -> str:
    """Render offenders for a message: sorted, truncated, and counted."""
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


# --------------------------------------------------------------------------------------
# The key
# --------------------------------------------------------------------------------------


def _render(fraction: float, *, formula: str, symbol: str) -> str:
    """One atomic fraction, rounded to :data:`SIGNIFICANT_DIGITS` and written positionally.

    Trailing zeros are trimmed so that ``0.5`` is written once, not as ``0.5000`` in one key
    and ``0.5`` in another. The refusal at the end is unreachable on the current corpus --
    the smallest atomic fraction anywhere in either raw file is 2.58e-05 -- and is here
    because the alternative is a key containing an element at zero.
    """
    rounded = float(f"{fraction:.{SIGNIFICANT_DIGITS}g}")
    text = f"{rounded:.{_MAX_DECIMALS}f}".rstrip("0").rstrip(".")
    if text in ("", "0", "-0"):
        raise CanonicalisationError(
            f"{formula!r} puts {symbol} at an atomic fraction of {fraction:.3e}, which is "
            f"below the resolution of the canonical key ({SIGNIFICANT_DIGITS} significant "
            f"digits, {_MAX_DECIMALS} decimal places). A key naming an element at zero would "
            f"claim a composition nobody wrote."
        )
    return text


def canonical_key(formula: str) -> str:
    """The identity of the material ``formula`` describes.

    Two strings receive the same key when they name the same atomic fractions, whatever the
    element order, the overall scale, or the whitespace::

        canonical_key("Ce1Mg12")   == canonical_key("Mg12Ce1")     # element order
        canonical_key("Mg1Al1")    == canonical_key("Mg0.5Al0.5")  # scale
        canonical_key("Pr1Co5")    == canonical_key("Pr1Co5 ")     # whitespace
        canonical_key("La(Ni)5")   == canonical_key("LaNi5")       # grouping

    The result is itself a formula -- elements in symbol order, each with its atomic fraction
    -- so it round-trips through :func:`~hydms.data.load.parse_formula` and reads as
    chemistry rather than as a hash. ``LaNi5`` becomes ``La0.1667Ni0.8333``.

    **Case.** The grammar is :func:`~hydms.data.load.parse_formula`'s, which requires real
    element symbols, so ``mg12ce1`` is refused rather than repaired: ``co`` is ``Co`` or
    ``C`` and ``O`` and nothing here can tell which. What the key guarantees is the half that
    is decidable -- the *output* casing is the periodic table's, so two accepted spellings
    that differ only in the case of an amount-free suffix cannot produce two keys. Measured:
    no two of the 1149 formula strings in ``hydride_data.csv`` differ by case alone.

    **A key is a label, not an input.** Keying a key is not guaranteed to return it
    unchanged: rounded fractions no longer sum to exactly one, so re-normalising them can
    move a final digit, which it does for 185 of the 1784 formulae in the two raw files. It
    never moves one onto *another* material's key -- that is asserted in
    ``tests/data/test_canonical.py`` -- so a re-keyed key still names the same material; it
    is simply not the same string, and nothing should be grouping on a key it computed twice.
    Normalising by the largest amount instead would be a fixed point by construction, and was
    rejected: measured, it merges two compositions 3.15e-05 apart while separating two
    3.15e-06 apart, which is the silent merge this key exists to make impossible.

    Args:
        formula: A composition string.

    Returns:
        The canonical key: symbols in sorted order, each followed by its atomic fraction.

    Raises:
        FormulaError: The string is not a formula this project accepts -- an unknown element,
            a non-positive amount, an unbalanced group.
        CanonicalisationError: An element's atomic fraction is below the key's resolution.
    """
    amounts = parse_formula(formula)
    total = sum(amounts.values())
    return "".join(
        f"{symbol}{_render(amounts[symbol] / total, formula=formula, symbol=symbol)}"
        for symbol in sorted(amounts)
    )


def group_keys(frame: pd.DataFrame, column: str | None = None) -> pd.Series:
    """The canonical key of every row, aligned to ``frame``'s index.

    This is the seam. The split protocol (#13) groups on this, the cross-validation folds
    (#88) group on this, and the ``Alloy_class`` re-join below joins on this -- one function,
    so that "the same material" cannot come to mean three different things in three modules.

    Args:
        frame: Any table with a formula column.
        column: Which column holds the formula. Defaults to ``columns.formula`` from
            ``pipeline.yaml`` -- ``Composition``.

    Returns:
        A ``Series`` named ``canonical_key``, indexed exactly as ``frame`` is.

    Raises:
        CanonicalisationError: naming every row that could not be keyed, not the first. A
            frame is keyed once and fixed once.
    """
    name = column if column is not None else load_config().columns.formula
    if name not in frame.columns:
        raise CanonicalisationError(
            f"the frame has no column {name!r} to key on; it holds {_named(frame.columns)}"
        )

    keys: list[str] = []
    problems: list[tuple[object, str]] = []
    for label, value in frame[name].items():
        try:
            keys.append(canonical_key(value))
        except (FormulaError, CanonicalisationError) as exc:
            keys.append("")
            problems.append((label, str(exc)))

    if problems:
        listing = "\n  - ".join(f"row {label}: {detail}" for label, detail in problems[:_MAX_NAMED])
        more = (
            f"\n  - and {len(problems) - _MAX_NAMED} more"
            if len(problems) > _MAX_NAMED
            else ""
        )
        raise CanonicalisationError(
            f"{len(problems)} of {len(frame)} row(s) in column {name!r} could not be given a "
            f"canonical key:\n  - {listing}{more}"
        )

    return pd.Series(keys, index=frame.index, name="canonical_key")


# --------------------------------------------------------------------------------------
# The collapse, in three steps
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CollapseStage:
    """One normalisation step and what it merged.

    Attributes:
        name: ``"raw"``, ``"whitespace"``, ``"order"`` or ``"composition"``.
        description: What this step treats as the same thing.
        distinct: How many distinct forms survive it.
        merged: How many forms it removed relative to the step before.
    """

    name: str
    description: str
    distinct: int
    merged: int


@dataclass(frozen=True)
class Collapse:
    """The accounting of 1149 formula strings down to 1115 compositions.

    Reported per step rather than end to end, because a single number hides which
    normalisation did what -- and because the first step is the one a stray ``str.strip()``
    somewhere downstream could silently reproduce, leaving the other two undone and nobody
    any the wiser.
    """

    stages: tuple[CollapseStage, ...]

    @property
    def raw(self) -> int:
        return self.stages[0].distinct

    @property
    def compositions(self) -> int:
        return self.stages[-1].distinct

    def __str__(self) -> str:
        return " -> ".join(f"{stage.name} {stage.distinct}" for stage in self.stages)


def collapse(formulae: Iterable[str]) -> Collapse:
    """Account for the collapse from formula strings to compositions, step by step.

    On ``hydride_data.csv``'s 1279 rows::

        raw           1149   the string as stored
        whitespace    1142   34 strings carry a trailing space and 9 an internal one; 7 of
                             the padded forms already have an unpadded twin in the file
        order         1121   element order, and a symbol written twice, no longer matter
        composition   1115   overall scale no longer matters -- Mg1Al1 is Mg0.5Al0.5

    The ``order`` stage compares exact amounts and merges nothing that scaling would merge,
    so the two steps are separately visible. Both are needed: whitespace and order together
    still leave ``Mg1Al1`` and ``Mg0.5Al0.5`` as two materials.

    Args:
        formulae: The formula strings, in any order, with repeats allowed.

    Returns:
        The four stages, each with its distinct count and what it merged.
    """
    strings = list(formulae)
    stripped = ["".join(text.split()) for text in strings]
    parsed = [parse_formula(text) for text in strings]
    ordered = ["".join(f"{s}{amounts[s]!r}" for s in sorted(amounts)) for amounts in parsed]
    keys = [canonical_key(text) for text in strings]

    counts = [
        ("raw", "the string exactly as stored", len(set(strings))),
        ("whitespace", "leading, trailing and internal spaces removed", len(set(stripped))),
        ("order", "element order and repeated symbols resolved, amounts exact", len(set(ordered))),
        ("composition", f"atomic fractions to {SIGNIFICANT_DIGITS} significant digits", len(set(keys))),
    ]
    stages = tuple(
        CollapseStage(
            name=name,
            description=description,
            distinct=distinct,
            merged=(counts[position - 1][2] - distinct) if position else 0,
        )
        for position, (name, description, distinct) in enumerate(counts)
    )
    return Collapse(stages=stages)


# --------------------------------------------------------------------------------------
# The property clustering would have given for free
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Separation:
    """How close the key came to merging two materials that are not the same one.

    Attributes:
        keys: Distinct canonical keys over the formulae measured.
        widest_within_key: The largest difference in atomic fraction between two formulae
            that received the **same** key. Every one of these is a merge the key performed.
        widest_pair: The two formulae behind it.
        closest_between_keys: The smallest difference between two formulae that received
            **different** keys, over pairs naming the same elements -- two compositions with
            different element sets cannot share a key whatever their fractions.
        closest_pair: The two formulae behind it.
        comparisons: How many pairs were compared.

    ``safe`` is the property the card asks for: *canonicalisation never silently merges two
    genuinely different materials*. It holds when the widest merge is narrower than the
    closest thing left unmerged, because then no pair straddles the rounding boundary and the
    key behaves exactly like clustering at that tolerance.
    """

    keys: int
    widest_within_key: float
    widest_pair: tuple[str, str] | None
    closest_between_keys: float
    closest_pair: tuple[str, str] | None
    comparisons: int

    @property
    def safe(self) -> bool:
        return self.widest_within_key < self.closest_between_keys

    def __str__(self) -> str:
        return (
            f"{self.keys} keys, {self.comparisons} comparable pairs: merged at most "
            f"{self.widest_within_key:.3e} apart, separated at least "
            f"{self.closest_between_keys:.3e} apart"
        )


def _fractions(formula: str) -> dict[str, float]:
    amounts = parse_formula(formula)
    total = sum(amounts.values())
    return {symbol: amount / total for symbol, amount in amounts.items()}


def separation(formulae: Iterable[str]) -> Separation:
    """Measure how much room the key had, over a whole corpus.

    Rounding is a decision made one formula at a time, so it cannot know whether the value it
    rounded away was the only thing separating two materials. This is the check that knows:
    every pair of formulae naming the same elements is compared, and the two extremes are
    reported -- the widest gap the key merged, and the narrowest it did not.

    Pairs are compared only within an element set. Two compositions naming different elements
    produce different key strings whatever their fractions, so no rounding of theirs can
    merge them; comparing them would only report a distance that means nothing. That is also
    what keeps this cheap: 1784 formulae over 505 element sets is 8920 comparisons, not 1.6
    million.

    Args:
        formulae: Every formula string in the corpus. Repeats are ignored.

    Returns:
        The measurement, whose ``safe`` property is the assertion worth making.
    """
    distinct = list(dict.fromkeys(formulae))
    by_elements: dict[frozenset[str], list[str]] = {}
    fractions = {text: _fractions(text) for text in distinct}
    keys = {text: canonical_key(text) for text in distinct}
    for text in distinct:
        by_elements.setdefault(frozenset(fractions[text]), []).append(text)

    widest = 0.0
    widest_pair: tuple[str, str] | None = None
    closest = float("inf")
    closest_pair: tuple[str, str] | None = None
    comparisons = 0

    for group in by_elements.values():
        for left, right in combinations(group, 2):
            comparisons += 1
            here, there = fractions[left], fractions[right]
            distance = max(abs(here[symbol] - there[symbol]) for symbol in here)
            if keys[left] == keys[right]:
                if distance > widest:
                    widest, widest_pair = distance, (left, right)
            elif distance < closest:
                closest, closest_pair = distance, (left, right)

    return Separation(
        keys=len(set(keys.values())),
        widest_within_key=widest,
        widest_pair=widest_pair,
        closest_between_keys=closest,
        closest_pair=closest_pair,
        comparisons=comparisons,
    )


# --------------------------------------------------------------------------------------
# Alloy_class
# --------------------------------------------------------------------------------------

#: The ten classes of ``hydride_data.csv``, ordered by how specific a claim each one makes
#: about the material. Read left to right: when one composition carries two of these, the
#: leftmost wins.
#:
#: The vocabulary is not one axis. ``AB5``, ``AB2``, ``AB`` and ``A2B`` name a stoichiometric
#: family and with it a crystal-chemical one; ``Mg`` names a chemistry; ``HEA``, ``MEA`` and
#: ``LEA`` count principal elements; ``SS`` and ``MIC`` are what is left when none of the
#: others fits. So a row labelled ``AB2`` and a row labelled ``MEA`` are not contradicting
#: each other -- ``Ti0.8Zr0.2Mn1Cr1`` is a C14 Laves phase *and* a medium-entropy alloy, and
#: both spellings of it are correct. Leave-one-alloy-class-out validation (AC-6) needs a
#: partition, so one has to win, and the structural claim is the one that survives.
ALLOY_CLASS_PRECEDENCE: tuple[str, ...] = (
    "AB5",
    "AB2",
    "AB",
    "A2B",
    "Mg",
    "HEA",
    "MEA",
    "LEA",
    "SS",
    "MIC",
)

#: ML-HydPARK's ``Material_Class`` written in the curated vocabulary. The two closed sets are
#: **not nested**: ML-HydPARK splits ``AB2`` into its two Laves polytypes and carries no
#: entropy families, while ``hydride_data.csv`` carries HEA/LEA/MEA and does not distinguish
#: C14 from C15. Folding the polytypes together is the only mapping that does not invent a
#: distinction the curated file never made.
#:
#: This is a mapping, not a merge, and nothing here consumes it: ``Alloy_class`` is complete
#: on all 1279 curated rows, so the re-join needs no second source. It is declared because
#: the comparison is worth having on record -- of the 378 canonical keys the two files share,
#: 377 carry a ML-HydPARK class and **30 of those disagree** with the curated label after
#: aliasing. A cross-source join done casually would silently relabel one composition in
#: twelve.
ML_HYDPARK_CLASS_ALIASES: Mapping[str, str] = {"AB2(C14)": "AB2", "AB2(C15)": "AB2"}


def reconcile_class(labels: Iterable[str]) -> str:
    """The one class a composition belongs to, given every label its rows carry.

    Resolution is by :data:`ALLOY_CLASS_PRECEDENCE` alone -- **not** by majority vote. A
    majority counts measurements, and how many measurements a composition has is an artefact
    of which papers happened to report it: ``Mg2Ni1`` carries three ``Mg`` rows and one
    ``A2B`` row, and Mg2Ni is the textbook A2B compound. Half the conflicts are 1-1 or 2-2
    ties in any case, so a majority rule would need a precedence to break them and would then
    be two rules where one will do.

    Measured on the real data: precedence resolves all ten conflicting compositions to the
    label a metallurgist would give them, and 13 of 1279 rows change label.

    Args:
        labels: The labels the rows of one composition carry. Repeats are ignored.

    Returns:
        The winning label.

    Raises:
        CanonicalisationError: No labels, or a label outside the curated vocabulary. An
            eleventh class arriving unannounced changes the fold structure of AC-6 and must
            be a human decision -- the same reason ``ColumnSpec.allowed`` refuses one at the
            door.
    """
    seen = {str(label) for label in labels}
    if not seen:
        raise CanonicalisationError(
            "reconcile_class was given no labels. A composition with no class is a row that "
            "was dropped upstream, not a class of its own."
        )
    unknown = seen - set(ALLOY_CLASS_PRECEDENCE)
    if unknown:
        raise CanonicalisationError(
            f"{_named(unknown)} is not one of the {len(ALLOY_CLASS_PRECEDENCE)} classes in "
            f"hydride_data.csv ({', '.join(ALLOY_CLASS_PRECEDENCE)}). ML-HydPARK's "
            f"vocabulary maps onto this one through ML_HYDPARK_CLASS_ALIASES; anything else "
            f"is a decision about the fold structure of AC-6."
        )
    return min(seen, key=ALLOY_CLASS_PRECEDENCE.index)


def alloy_class_table(
    frame: pd.DataFrame,
    *,
    formula_column: str | None = None,
    class_column: str | None = None,
    aliases: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """One row per canonical composition: its class, and the evidence behind it.

    The re-join `extract_features_cbfv.py:19-21` made impossible, keyed on the composition
    rather than on the formula string -- joining on the string would hand ``Ce1Mg12`` and
    ``Mg12Ce1`` their class labels independently, which is leak L8 wearing a different hat.

    Every conflict is reported rather than resolved away. ``labels`` holds what the rows
    actually said, so the ten compositions where the sources disagree can be read off the
    table instead of taken on trust::

        table[table["conflicted"]][["Alloy_class", "labels", "rows"]]

    The resolved column is called ``Alloy_class`` whatever the source called its own, because
    after ``aliases`` every label is in the curated vocabulary and the column now means the
    curated thing. Reading ``Material_Class`` out of a frame and getting ``Alloy_class`` back
    is the rename being visible rather than assumed.

    Args:
        frame: A table with a formula column and a class column.
        formula_column: Defaults to ``columns.formula`` from ``pipeline.yaml`` --
            ``Composition``, or ``Composition_Formula`` for ML-HydPARK.
        class_column: Defaults to ``columns.alloy_class`` -- ``Alloy_class``, or
            ``Material_Class`` for ML-HydPARK.
        aliases: Applied to each label before reconciliation, for a source whose vocabulary
            is not the curated one. :data:`ML_HYDPARK_CLASS_ALIASES` is the one that exists.

    Returns:
        A frame indexed by canonical key with ``Alloy_class`` (the resolved label),
        ``labels`` (every distinct label seen, in precedence order, comma-separated),
        ``rows`` (how many rows the composition has) and ``conflicted`` (whether the sources
        disagreed).

    Raises:
        CanonicalisationError: A row cannot be keyed, a class is missing, or a label is
            outside the vocabulary.
    """
    names = load_config().columns
    label_column = class_column if class_column is not None else names.alloy_class
    if label_column not in frame.columns:
        raise CanonicalisationError(
            f"the frame has no class column {label_column!r}; it holds {_named(frame.columns)}"
        )

    keys = group_keys(frame, formula_column)
    raw_labels = frame[label_column]
    missing = raw_labels.isna()
    if bool(missing.any()):
        raise CanonicalisationError(
            f"{int(missing.sum())} row(s) have no {label_column!r}: "
            f"{_named(frame.index[missing])}. A row with no class refuses "
            f"here rather than becoming an eleventh class -- #12 settled that, and "
            f"hydms.data.metadata says why."
        )

    translate = dict(aliases) if aliases is not None else {}
    grouped: dict[str, list[str]] = {}
    for key, label in zip(keys, raw_labels, strict=True):
        text = str(label)
        grouped.setdefault(key, []).append(translate.get(text, text))

    records = []
    for key in sorted(grouped):
        labels = grouped[key]
        # `reconcile_class` first, because it is the one that validates the vocabulary.
        # Ordering `distinct` by `ALLOY_CLASS_PRECEDENCE.index` would otherwise raise a bare
        # `tuple.index(x): x not in tuple` on an unrecognised label -- a crash naming neither
        # the label nor the row, shadowing the refusal that exists two lines below. Found by
        # #12, whose settled answer for an unlabelled row is that it refuses at the door.
        resolved = reconcile_class(labels)
        distinct = sorted(set(labels), key=ALLOY_CLASS_PRECEDENCE.index)
        records.append(
            {
                "canonical_key": key,
                names.alloy_class: resolved,
                "labels": ", ".join(distinct),
                "rows": len(labels),
                "conflicted": len(distinct) > 1,
            }
        )
    return pd.DataFrame.from_records(records).set_index("canonical_key")


def alloy_classes(
    frame: pd.DataFrame,
    *,
    formula_column: str | None = None,
    class_column: str | None = None,
    aliases: Mapping[str, str] | None = None,
) -> pd.Series:
    """The reconciled class of every row, aligned to ``frame``'s index.

    What card #12 carries through featurisation as metadata, and what
    leave-one-alloy-class-out cross-validation (#30) folds on. Two rows describing the same
    composition are guaranteed to receive the same label here even when the file gave them
    different ones -- which is the whole point, since a fold that holds out a class must hold
    out every row of it. Measured on ``hydride_data.csv``: 13 of 1279 rows are relabelled,
    all of them inside the ten conflicting compositions.

    Takes the same arguments as :func:`alloy_class_table` and raises the same errors.
    """
    names = load_config().columns
    table = alloy_class_table(
        frame,
        formula_column=formula_column,
        class_column=class_column,
        aliases=aliases,
    )
    keys = group_keys(frame, formula_column)
    return keys.map(table[names.alloy_class]).rename(names.alloy_class)
