"""L4 -- how chemically far a candidate is from everything already known.

PRD 4.3 link 5 asks that "novel" be a number rather than an assertion, and AC-7 makes the
number a **reporting obligation**: no candidate is published without an ElMD distance and an
interval width beside it. This module owns the distance and the alloy it is a distance *to*.

What the metric is, exactly
---------------------------

Element Mover's Distance is the 1-Wasserstein distance between two compositions read as
distributions over the **modified Pettifor** ordering of the elements -- a chemical scale, so
a substitution between neighbours costs less than a substitution across the table. ElMD's
default metric is ``mod_petti``, and on that metric its answer is a closed form
(``ElMD/ElMD.py``, ``simple_emd``)::

    d(a, b) = sum(abs(cumsum(a - b)))

over the 103-slot Pettifor vector of atomic fractions. That single line is what makes the
card's batching requirement satisfiable: see :func:`distances` below.

**This screen is novelty evidence, not the applicability domain**, and the distinction is
measured rather than stylistic. Card #48 tested whether a composition distance explains where
the model fails to transfer and it does not -- per-class leave-one-class-out R2 against
per-class isolation is Spearman **-0.2727** in element-fraction space and **-0.2848** in the
model's own fourteen-feature space (n = 10, p 0.43 and 0.45), *inverted at the ends*, since
the two least isolated families score among the best. The feature-space figure is the one that
binds here: a CatBoost fit reads fourteen numbers, so no metric over a space it never reads
can be the mechanism behind its failures. The applicability domain is therefore a **capacity**
level and lives in :mod:`hydms.screens.domain`; this module must never be quoted as one.
:class:`~hydms.delivery.contract.Novelty` carries ``metric`` for the same reason.

The threshold, derived
----------------------

The card's fourth box requires a declared rejection code, so this screen needs a distance past
which it refuses. It cannot be calibrated against the transfer curve -- #48 is what establishes
that there is no curve -- so it is calibrated against the **corpus's own internal spread**, and
it is computed rather than chosen.

Measure, for every distinct training composition, its distance to the nearest *other* training
composition. That distribution is what "a variation on something known" means on this corpus:

    p50   0.1758      p90   0.8752      p99    3.1532
    p75   0.4000      p95   1.3619      max   11.7320

The maximum is :data:`NoveltyReference.ceiling`. Past it, a candidate is farther from
everything known than the loneliest known alloy is from its own nearest neighbour -- which is
the sentence the card asked for, read along the only axis the evidence supports. It is set by
one composition, ``Li0.94Pd1`` (nearest ``Ce1Ni1``, at 11.7320), and the reference names it so
a reader can see exactly what holds the bound up. Drop that row and the level falls to 5.1333;
the emitter recomputes it either way, so new data moves the threshold instead of silently
invalidating a constant.

**The measured consequence, stated rather than hidden: it rejects 0 of the 385 held-out rows.**
That is the intended behaviour and not a screen that fails to work. The corpus is chemically
homogeneous -- the most novel held-out row, ``Ca1Al1.8B0.2``, sits at 6.5333 against a metric
whose span is 102.0 -- and the card warned in as many words that "a distance threshold fitted
to look busy on this data will be fitted to noise". A screen calibrated to this corpus should
almost never fire on data resembling it; it fires on the genuinely different chemistry an
optimiser proposes, which is the case AC-7 exists for. The number rides on every verdict either
way, which is the part AC-7 actually asks for.

Batched, and what the other shape costs
---------------------------------------

The card requires the distances be batched, "a per-candidate loop over the training set would
be too slow". Measured, that claim is true but for a smaller factor than it sounds, and the
honest numbers are these rather than the ones a cold timer reports:

    scipy ``cdist`` over cumulative vectors    ~37 M pairs/s, flat from 1e3 to 1e5 candidates
    ``ElMD.elmd()`` in a warm loop             1.37 us/pair -- a **46x** slower path
    ``ElMD(formula)`` construction             48.6 us/formula

So 780 training compositions against 100,000 candidates is **2.2 s** batched and about 100 s
pairwise. The construction cost is the one that actually bites, and it is why this module
parses each **distinct** formula once per batch rather than once per comparison: re-parsing
inside the loop would put 48.6 us on every one of the 78 million pairs.

A note for whoever times this next: a cold ``ElMD.elmd()`` measures ~3.5 ms/pair, and that is
numba compiling ``simple_emd``, not the metric. Warm it before you believe a ratio.

The broadcast form ``abs(cC[:, None, :] - cT[None, :, :]).sum(2)`` is correct to 2.8e-13 and
**23x slower** than ``cdist`` while allocating ``n x m x 103`` floats; :func:`distances` uses
``cdist`` and chunks the candidate axis so peak memory is bounded by the chunk rather than by
the batch.

What ElMD does when it cannot read a formula
--------------------------------------------

It does not raise, and it fails in **two** ways rather than one.

*Total loss.* ``ElMD("NotAnElement")``, ``ElMD("Xx2")`` and ``ElMD("")`` all return an object
whose ratio vector sums to **zero**, and a zero vector has a perfectly finite distance to every
training alloy -- so an unparseable candidate would otherwise receive a confident number
computed from nothing. :func:`vectors` checks the normalisation of every parsed composition, so
this one is caught by arithmetic.

*Partial loss, which is the dangerous one.* ``_dictify`` drops an unrecognised symbol and keeps
the rest, so ``LaNi5Xx2`` parses to ``{La: 1, Ni: 5}`` and renormalises to a **valid**
distribution that no sum check can distinguish from a real one: the candidate is admitted at
distance zero from ``LaNi5``, naming it as the nearest alloy. A typo is answered as a known
material. :func:`_vector` therefore reads every string a second time with
:func:`~hydms.data.load.parse_formula` -- this project's own grammar, which refuses an unknown
symbol by name -- and requires the two parsers to name the same elements.

Either way an unreadable formula is :data:`~hydms.screens.protocol.INDETERMINATE` -- a
**rejection**, fail-closed, like every other guard rail in this layer. Neither guard trips on
anything real: the two parsers agree on all 1,149 distinct curated formulas and on all 780
reference compositions. Arbitrary candidates, and hand-entered ones, are the reason they are
there.

**And the refusal says which of the two happened.** The reason on the verdict row is the one
:func:`_vector` produced, not a sentence written at the call site: ``parse_formula`` names the
offending symbol -- ``'LaNi5Xx2' names 'Xx', which is not a chemical element`` -- and that is
what a reader who typed the formula can act on. A single shared line saying the candidate
"parses to an empty formula" would describe ``LaNi5Xx2``, which parses to ``LaNi5``, with the
very mistake the cross-check exists to catch.

Card #49.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

import numpy as np
import pandas as pd

from hydms.config import Config
from hydms.config import load as load_config
from hydms.data.load import FormulaError, parse_formula
from hydms.screens.protocol import (
    ADMITTED,
    INDETERMINATE,
    ScreenError,
    verdict_table,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from numpy.typing import NDArray

__all__ = [
    "BEYOND_KNOWN_CHEMISTRY",
    "DISTANCE_COLUMN",
    "METRIC",
    "MOD_PETTI",
    "NEAREST_COLUMN",
    "PETTI_SLOTS",
    "REFERENCE_FILE",
    "ElementMoversDistance",
    "NoveltyReference",
    "distances",
    "emit",
    "novelty_screen",
    "vectors",
]

#: The candidate is farther from every known alloy than the loneliest known alloy is from its
#: own nearest neighbour. A statement about **chemistry**, never about the applicability
#: domain -- :mod:`hydms.screens.domain` owns that and #48 measured why they are different.
BEYOND_KNOWN_CHEMISTRY = "beyond-known-chemistry"

#: The evidence columns this screen adds to the verdict table, reaching the composite frame as
#: ``novelty.distance`` and ``novelty.nearest``. They are the two fields
#: :class:`~hydms.delivery.contract.Novelty` needs, spelled the same way, so #76 carries them
#: across without a rename.
DISTANCE_COLUMN = "distance"
NEAREST_COLUMN = "nearest"

#: What measured it. Recorded on the result rather than assumed, because a distance in a
#: result must be readable as novelty evidence and not as a domain verdict.
METRIC = "ElMD"

#: ElMD's default metric, and the only one with a closed form. Named because the closed form
#: in :func:`distances` is *only* valid for it: every other metric routes through the network
#: simplex over a full cost matrix, which does not reduce to a cumulative L1.
MOD_PETTI = "mod_petti"

#: Length of the modified-Pettifor ratio vector ElMD builds. Asserted rather than assumed --
#: a version that changed it would silently change every distance in this project.
PETTI_SLOTS = 103

#: The measured reference, shipped inside the package. The refusal path must work in a
#: container that has neither the curated CSVs nor a fitted model, which is the same reason
#: ``screens/domain-reference.json`` ships. Regenerate with
#: ``python -m hydms.screens.novelty --emit``.
REFERENCE_FILE = Path(__file__).with_name("novelty-reference.json")

_TOLERANCE = 1e-9


def _named(items: Iterable[object]) -> str:
    listed = sorted(map(repr, items))
    if len(listed) <= 8:
        return ", ".join(listed)
    return f"{', '.join(listed[:8])}, ... ({len(listed) - 8} more)"


def _elmd_class() -> Any:
    """Import ElMD, or say what is missing and how to get it.

    Imported here rather than at module scope so that importing this module -- which
    ``hydms.screens`` does not do, but a reader exploring the package might -- does not
    require the optional extra. Unlike MAPIE, ElMD **is** on the prediction path: a candidate
    formula has to be parsed onto the Pettifor scale before any distance exists, so the
    ``novelty`` extra is installed in CI rather than skipped.
    """
    try:
        from ElMD import ElMD
    except ImportError as error:  # pragma: no cover - exercised by the import test
        raise ScreenError(
            "the novelty screen needs ElMD, which is the `novelty` extra: "
            "`pip install -e \".[novelty]\"`. It is GPL-3.0, which is why this project is."
        ) from error
    return ElMD


def vectors(formulas: Sequence[str]) -> tuple[NDArray[np.float64], dict[int, str]]:
    """Parse formulas onto the modified-Pettifor scale, one row each.

    Each **distinct** string is parsed once and its row reused, because parsing is 48.6 us and
    dominates everything else this module does.

    **The normalisation is done here rather than read off ``ratio_vector``, and that is a bug
    fix, not a preference.** ElMD's ``_fuse`` builds its composition dict by iterating
    ``set(mol1) | set(mol2)``, so the *insertion order* of the elements follows the hashes of
    their symbols -- which Python randomises per process. ``_normalise_composition`` then
    divides by ``sum(composition.values())``, summed in that order, so a formula of three or
    more elements normalises to a **one-ulp different** vector in two different processes.
    Measured on the training corpus: 76 of 780 compositions moved by 2.2e-16 between runs, and
    every one of them had three elements or more. The consequence is not the 1e-16 -- it is
    that ``--emit`` was not reproducible and a committed reference could not be asserted
    byte-identical to what the code produces.

    Summing the parsed counts in **sorted symbol order** removes it at the source, so both the
    committed reference and a live candidate's distance are the same in every process. ElMD's
    own ``_gen_ratio_vector`` already sorts when it *places* the fractions; only the total was
    order-dependent. ``tests/screens/test_novelty.py`` pins this against ``ratio_vector`` to
    1e-12, so the deterministic path stays ElMD's metric rather than becoming our own.

    Args:
        formulas: The formula strings, in the order the rows should come back.

    Returns:
        ``(matrix, unreadable)`` -- an ``(n, 103)`` array of atomic fractions, and a mapping
        from each position that is not a composition to the sentence saying why. An unreadable
        row is left as **zeros**, which is what ElMD itself returns; it is the caller's job to
        refuse it rather than measure it. The cause is carried rather than recomputed because
        the three ways a string can fail are different facts, and a verdict that gives the
        wrong one is a reason nobody can act on.

    Raises:
        ScreenError: if ElMD is absent, or if it places an element outside the 103 slots this
            module is written against.
    """
    elmd = _elmd_class()
    cache: dict[str, tuple[NDArray[np.float64], str]] = {}
    matrix = np.zeros((len(formulas), PETTI_SLOTS), dtype=np.float64)
    unreadable: dict[int, str] = {}
    for position, formula in enumerate(formulas):
        text = "" if formula is None else str(formula)
        if text not in cache:
            cache[text] = _vector(elmd, text)
        row, cause = cache[text]
        matrix[position] = row
        if cause:
            unreadable[position] = cause
    return matrix, unreadable


def _vector(elmd: Any, formula: str) -> tuple[NDArray[np.float64], str]:
    """One formula's Pettifor vector, normalised deterministically, and why it is not one.

    ElMD does not raise on an unparseable formula -- ``ElMD("Xx2")`` parses to an empty
    composition whose distance to everything is finite and meaningless -- so "is this a
    composition at all" is answered here and returned rather than assumed.

    **A formula ElMD reads only *partly* is the sharper half of the same defect, and the
    sum-to-one check below cannot see it.** ``_dictify`` drops a symbol it does not recognise
    instead of raising, so ``LaNi5Xx2`` parses to ``{La: 1, Ni: 5}`` and renormalises to a
    perfectly valid distribution: the candidate would be admitted at distance **zero from
    LaNi5**, a typo answered as a known alloy, with a named nearest neighbour to make it look
    measured. Total loss is loud and partial loss is silent, which is the wrong way round.

    So the string is read a second time by :func:`~hydms.data.load.parse_formula` -- this
    project's own grammar, which refuses an unknown symbol by name -- and the two parsers must
    agree on *which elements are present*. They are independent readings of the same string,
    so a disagreement means there is no composition both can vouch for, and the formula is
    unreadable. Measured across every formula this project holds -- the 780 reference
    compositions and all 1,149 distinct curated strings -- the two agree everywhere, so the
    cross-check refuses nothing real. It is checked first because it is the cheap half:
    rejecting here skips the 48.6 us ``ElMD(formula)`` construction entirely.

    One string both parsers read the same way is worth knowing about: ``"NaN"`` is sodium and
    nitrogen to each of them, so a missing value written out as text is a *valid* formula and
    no guard here can catch it. Missing values are the caller's to keep out of the column.

    **The cause travels with the refusal**, because the three ways a string fails here are not
    the same fact and a reader acting on the verdict needs to know which one happened.
    ``parse_formula`` already names the offending symbol -- ``'LaNi5Xx2' names 'Xx', which is
    not a chemical element`` -- and that sentence is worth far more to whoever typed it than
    the shape of ElMD's internal failure.

    Args:
        elmd: The ``ElMD`` class, passed in so the import is resolved once per batch.
        formula: The candidate string, exactly as it arrived.

    Returns:
        ``(row, cause)`` -- the atomic-fraction row, and the empty string when it is one.
        A non-empty ``cause`` is a sentence naming why the string is not a composition; the
        row is then all zeros and must not be measured.
    """
    row = np.zeros(PETTI_SLOTS, dtype=np.float64)
    try:
        ours = parse_formula(formula)
    except FormulaError as error:
        return row, (
            f"{error}. ElMD does not raise on it -- it drops the symbols it cannot read and "
            f"measures whatever is left, if anything -- so it is refused here rather than "
            f"answered as some other alloy."
        )
    parsed = elmd(formula, metric=MOD_PETTI)
    # `composition` is the parsed, *un*-normalised element counts. Its keys are always in
    # ElMD's lookup: `_dictify` silently drops a symbol it does not recognise, which is the
    # same defect from the other side and is what makes an unreadable formula empty.
    counts = dict(parsed.composition)
    symbols = sorted(counts)
    total = sum(float(counts[symbol]) for symbol in symbols)
    if not symbols or not np.isfinite(total) or total <= 0.0:
        return row, (
            f"ElMD reads no composition at all in {formula!r}: it returns an empty formula "
            f"rather than raising, and a zero vector has a finite, meaningless distance to "
            f"every known alloy."
        )
    if symbols != sorted(ours):
        return row, (
            f"the two parsers disagree about {formula!r}: this project's grammar names "
            f"{_named(sorted(ours))} and ElMD names {_named(symbols)}. Two readings that do "
            f"not agree on which elements are present cannot both be a composition."
        )
    for symbol in symbols:
        slot = parsed.petti_lookup[symbol]
        if not isinstance(slot, int) or not 0 <= slot < PETTI_SLOTS:
            raise ScreenError(
                f"ElMD places {symbol!r} at modified-Pettifor slot {slot!r}; this module is "
                f"written against {PETTI_SLOTS} slots and every distance in the project "
                f"depends on that shape. Check the installed ElMD against docs/LIBRARY-APIS.md."
            )
        row[slot] = float(counts[symbol]) / total
    if abs(row.sum() - 1.0) > _TOLERANCE:
        return np.zeros(PETTI_SLOTS, dtype=np.float64), (
            f"the parsed fractions of {formula!r} sum to {row.sum():.6g} rather than one, so "
            f"whatever ElMD read is not a composition."
        )
    return row, ""


def distances(
    candidates: NDArray[np.float64],
    known: NDArray[np.float64],
    *,
    chunk: int = 4096,
) -> tuple[NDArray[np.float64], NDArray[np.intp]]:
    """Nearest known composition for every candidate, batched.

    Implements ElMD's ``mod_petti`` metric directly -- ``sum(abs(cumsum(a - b)))`` is the L1
    distance between the two **cumulative** vectors, so a whole batch is one ``cdist`` call
    rather than a Python loop over pairs. ``tests/screens/test_novelty.py`` pins the identity
    against ElMD itself; agreement is to 3.6e-15 over the curated corpus.

    Args:
        candidates: ``(n, 103)`` atomic-fraction rows.
        known: ``(m, 103)`` atomic-fraction rows -- the training compositions.
        chunk: How many candidates to score at once. Bounds peak memory at
            ``chunk x m`` floats, so a million-candidate batch costs no more here than a
            thousand-candidate one.

    Returns:
        ``(distance, index)`` -- the distance to the nearest known composition and which one,
        as a position into ``known``.
    """
    from scipy.spatial.distance import cdist

    if known.ndim != 2 or not len(known):
        raise ScreenError("the novelty reference holds no compositions to be distant from.")
    if candidates.ndim != 2 or candidates.shape[1] != known.shape[1]:
        raise ScreenError(
            f"candidate vectors are {candidates.shape} against reference {known.shape}; both "
            f"must be on the same Pettifor scale."
        )
    if chunk < 1:
        raise ScreenError(f"chunk must be at least one candidate; got {chunk}.")

    cumulative_known = np.cumsum(known, axis=1)
    distance = np.empty(len(candidates), dtype=np.float64)
    index = np.empty(len(candidates), dtype=np.intp)
    for start in range(0, len(candidates), chunk):
        block = np.cumsum(candidates[start : start + chunk], axis=1)
        pairwise = cdist(block, cumulative_known, "cityblock")
        index[start : start + chunk] = pairwise.argmin(axis=1)
        distance[start : start + chunk] = pairwise.min(axis=1)
    return distance, index


# --------------------------------------------------------------------------------------
# The measured reference
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class NoveltyReference:
    """The known chemistry a candidate is measured against, and the bound it may not pass.

    Attributes:
        formulas: One formula per distinct **canonical composition** in the training split,
            in a deterministic order. Distinct compositions rather than rows, because a
            distance to a duplicate is the same distance and #87's key is what decides that
            two spellings are one material.
        petti: The matching atomic-fraction rows, ``(len(formulas), 103)``. Stored rather
            than re-parsed so that an ElMD upgrade cannot move a committed distance without
            a test noticing.
        ceiling: The largest distance from a training composition to the nearest *other*
            training composition -- the corpus's own internal spread. Past it a candidate is
            :data:`BEYOND_KNOWN_CHEMISTRY`.
        loneliest: The composition that sets ``ceiling``, and ``loneliest_nearest`` is what
            it is that far from. Named because a bound held up by one row should say so.
    """

    formulas: tuple[str, ...]
    petti: NDArray[np.float64]
    ceiling: float
    loneliest: str
    loneliest_nearest: str

    def __post_init__(self) -> None:
        if not self.formulas:
            raise ScreenError("a novelty reference with no known compositions refuses nothing.")
        if self.petti.shape != (len(self.formulas), PETTI_SLOTS):
            raise ScreenError(
                f"the reference has {len(self.formulas)} formula(s) and a "
                f"{self.petti.shape} matrix; they describe the same compositions."
            )
        if not np.isfinite(self.ceiling) or self.ceiling <= 0.0:
            raise ScreenError(
                f"the novelty ceiling is {self.ceiling}; it is the widest gap the corpus "
                f"holds internally and must be a positive number."
            )
        # Every row is one composition's atomic fractions. A row that is not a distribution
        # still yields a finite distance to everything, so a corrupted reference would move
        # every number this module reports without any of them looking wrong.
        sums = self.petti.sum(axis=1)
        off = int(np.abs(sums - 1.0).argmax())
        if abs(sums[off] - 1.0) > _TOLERANCE:
            raise ScreenError(
                f"the reference row for {self.formulas[off]!r} sums to {sums[off]:.6g}; every "
                f"row holds one composition's atomic fractions and sums to one."
            )

    def to_json(self) -> str:
        """The reference as the committed file, sparse and deterministic.

        Sparse because a composition touches two to five of the 103 slots: written densely
        the file is 80,000 numbers and unreadable, and written sparsely it is a few thousand
        and a reader can check a row by eye.
        """
        payload = {
            "metric": MOD_PETTI,
            "slots": PETTI_SLOTS,
            "ceiling": self.ceiling,
            "loneliest": self.loneliest,
            "loneliest_nearest": self.loneliest_nearest,
            "compositions": [
                {
                    "formula": formula,
                    "petti": {
                        str(slot): float(self.petti[position, slot])
                        for slot in np.flatnonzero(self.petti[position])
                    },
                }
                for position, formula in enumerate(self.formulas)
            ],
        }
        return json.dumps(payload, indent=2, sort_keys=False) + "\n"

    @classmethod
    def from_json(cls, text: str) -> NoveltyReference:
        """Rebuild one, refusing a file this module was not written against."""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ScreenError(f"the novelty reference is not JSON: {error}") from error
        missing = [
            key
            for key in ("metric", "slots", "ceiling", "loneliest", "compositions")
            if key not in payload
        ]
        if missing:
            raise ScreenError(f"the novelty reference is missing {_named(missing)}.")
        if payload["metric"] != MOD_PETTI or int(payload["slots"]) != PETTI_SLOTS:
            raise ScreenError(
                f"the novelty reference was measured on {payload['metric']!r} over "
                f"{payload['slots']} slots; this module reads {MOD_PETTI!r} over "
                f"{PETTI_SLOTS}. A distance from one is not a distance from the other."
            )
        entries = payload["compositions"]
        matrix = np.zeros((len(entries), PETTI_SLOTS), dtype=np.float64)
        formulas = []
        for position, entry in enumerate(entries):
            formula = str(entry["formula"])
            formulas.append(formula)
            # Read rather than trusted. A slot outside the scale is an `IndexError` and a
            # *negative* one is worse -- numpy wraps it onto the far end of the Pettifor
            # ordering, so a hand-edited or older-format file would quietly relabel an
            # element instead of failing. Both are the file's fault and both are ScreenError,
            # because this is the boundary where an unreadable reference must become a
            # refusal rather than a traceback from inside numpy.
            for slot, fraction in entry["petti"].items():
                try:
                    column, value = int(slot), float(fraction)
                except (TypeError, ValueError) as error:
                    raise ScreenError(
                        f"the novelty reference gives {formula!r} the slot/fraction pair "
                        f"({slot!r}: {fraction!r}), which is not a number."
                    ) from error
                if not 0 <= column < PETTI_SLOTS:
                    raise ScreenError(
                        f"the novelty reference places part of {formula!r} at "
                        f"modified-Pettifor slot {column}; the scale has {PETTI_SLOTS} slots "
                        f"and a distance measured off it is not a distance."
                    )
                if not np.isfinite(value) or value <= 0.0:
                    raise ScreenError(
                        f"the novelty reference gives {formula!r} an atomic fraction of "
                        f"{value} at slot {column}; fractions are positive and finite."
                    )
                matrix[position, column] = value
        try:
            ceiling = float(payload["ceiling"])
        except (TypeError, ValueError) as error:
            raise ScreenError(
                f"the novelty ceiling in the reference is {payload['ceiling']!r}, "
                f"which is not a number."
            ) from error
        return cls(
            formulas=tuple(formulas),
            petti=matrix,
            ceiling=ceiling,
            loneliest=str(payload["loneliest"]),
            loneliest_nearest=str(payload.get("loneliest_nearest", "")),
        )

    @classmethod
    def packaged(cls) -> NoveltyReference:
        """The committed reference. What every screen built without one reads."""
        try:
            text = REFERENCE_FILE.read_text(encoding="utf-8")
        except OSError as error:
            raise ScreenError(
                f"the novelty reference {REFERENCE_FILE} is missing or unreadable. "
                f"Regenerate it with `python -m hydms.screens.novelty --emit`."
            ) from error
        return cls.from_json(text)

    @classmethod
    def measured(cls, formulas: Sequence[str]) -> NoveltyReference:
        """Derive one from a set of known formulas. See :func:`emit` for the real caller.

        ``ceiling`` is the maximum over compositions of the distance to the nearest *other*
        composition -- computed here rather than typed, so new data moves it.
        """
        ordered = tuple(sorted(dict.fromkeys(str(formula) for formula in formulas)))
        if len(ordered) < 2:
            raise ScreenError(
                f"the novelty ceiling is the widest gap *between* known compositions and "
                f"{len(ordered)} composition(s) have no gaps. Give the training split."
            )
        matrix, unreadable = vectors(ordered)
        if unreadable:
            first = next(iter(unreadable.values()))
            raise ScreenError(
                f"ElMD could not read {len(unreadable)} of the known formulas: "
                f"{_named(ordered[position] for position in unreadable)}. The first of them: "
                f"{first} The reference is what everything else is measured against; it may "
                f"not contain a composition that is not one."
            )
        separation, nearest = _self_distances(matrix)
        worst = int(separation.argmax())
        return cls(
            formulas=ordered,
            petti=matrix,
            ceiling=float(separation[worst]),
            loneliest=ordered[worst],
            loneliest_nearest=ordered[int(nearest[worst])],
        )


def _self_distances(
    matrix: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.intp]]:
    """Each composition's distance to the nearest *other* one, and which one that is."""
    from scipy.spatial.distance import pdist, squareform

    cumulative = np.cumsum(matrix, axis=1)
    full = squareform(pdist(cumulative, "cityblock"))
    np.fill_diagonal(full, np.inf)
    return full.min(axis=1), full.argmin(axis=1)


# --------------------------------------------------------------------------------------
# The screen
# --------------------------------------------------------------------------------------


def _number(value: float) -> str:
    """A distance as it should read in a sentence: 11.732, not 11.731999999999999."""
    return f"{value:.4g}"


@dataclass(frozen=True)
class ElementMoversDistance:
    """Measure every candidate's chemical distance to the nearest known alloy.

    Every candidate gets a ``distance`` and a ``nearest`` on its verdict row whether it passed
    or not -- that is AC-7's reporting obligation, and it is why they ride on the verdict frame
    rather than on a second return value. A parallel API would put the number and the verdict
    on two paths that can disagree; :func:`~hydms.screens.protocol.apply_screens` carries them
    into the composite table as ``novelty.distance`` and ``novelty.nearest``.

    Attributes:
        reference: The known chemistry, and the ceiling it implies.
        column: Which candidate column holds the formula. Defaults to ``columns.formula``.
        name: The screen's name and its column prefix.
    """

    reference: NoveltyReference
    column: str
    name: str = "novelty"

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.column.strip():
            raise ScreenError("a novelty screen needs a name and a formula column to read.")

    @property
    def reasons(self) -> tuple[str, ...]:
        """Two codes: past the corpus's internal spread, and a formula ElMD cannot read."""
        return (BEYOND_KNOWN_CHEMISTRY, INDETERMINATE)

    @property
    def ceiling(self) -> float:
        """The distance past which this screen refuses. See the module docstring."""
        return self.reference.ceiling

    def verdict(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """A distance, the alloy it is a distance to, and whether that is still chemistry.

        Raises:
            ScreenError: if ``column`` is absent. That is a statement about the batch rather
                than about any candidate in it, so refusing every row with an identical
                reason would report a caller's mistake as a property of the candidates.
        """
        if self.column not in candidates.columns:
            raise ScreenError(
                f"novelty screen {self.name!r} reads {self.column!r}, which the candidates do "
                f"not have; they have {_named(candidates.columns)}."
            )
        index = candidates.index
        if not len(index):
            empty = verdict_table(True, ADMITTED, "", index=index)
            empty[DISTANCE_COLUMN] = pd.Series(dtype=float)
            empty[NEAREST_COLUMN] = pd.Series(dtype=object)
            return empty

        formulas = candidates[self.column].tolist()
        matrix, unreadable = vectors(formulas)
        distance, nearest = distances(matrix, self.reference.petti)

        readable = np.ones(len(index), dtype=bool)
        readable[list(unreadable)] = False
        # A distance measured from a composition ElMD could not read is finite and
        # meaningless; it must not reach the table as though it were a measurement.
        distance = np.where(readable, distance, np.nan)
        names = np.array(
            [self.reference.formulas[position] for position in nearest], dtype=object
        )
        names[~readable] = ""

        beyond = readable & (distance > self.ceiling)
        passed = readable & ~beyond
        code = np.where(passed, ADMITTED, np.where(readable, BEYOND_KNOWN_CHEMISTRY, INDETERMINATE))
        reason = np.full(
            len(index),
            f"within the corpus's own spread: no known alloy is more than "
            f"{_number(self.ceiling)} from its nearest neighbour.",
            dtype=object,
        )
        for position in np.flatnonzero(beyond):
            reason[position] = (
                f"{_number(float(distance[position]))} from the nearest known alloy "
                f"({names[position]}) on the ElMD modified-Pettifor scale, past the "
                f"{_number(self.ceiling)} that separates the corpus's loneliest member "
                f"({self.reference.loneliest}) from its own nearest neighbour. This is a "
                f"statement about chemistry, not about the applicability domain."
            )
        # The cause comes from `vectors`, not from a sentence written here, because the
        # three ways a string fails are different facts. Saying "it parses to an empty
        # formula" about `LaNi5Xx2` -- which parses to `LaNi5` -- would describe the refusal
        # with the very mistake the cross-check exists to catch.
        for position, cause in unreadable.items():
            reason[position] = (
                f"{cause} There is no distance to report, and a screen that cannot judge "
                f"does not admit."
            )

        table = verdict_table(passed, code, reason, index=index)
        table[DISTANCE_COLUMN] = distance
        table[NEAREST_COLUMN] = names
        return table


def novelty_screen(
    cfg: Config | None = None, *, reference: NoveltyReference | None = None
) -> ElementMoversDistance:
    """The novelty screen over the committed reference, reading the configured formula column.

    Args:
        cfg: Loaded configuration; the default loads it.
        reference: Override the packaged reference. For tests and for a caller who has just
            re-measured one; production reads what shipped.
    """
    config = cfg if cfg is not None else load_config()
    return ElementMoversDistance(
        reference=reference if reference is not None else NoveltyReference.packaged(),
        column=config.columns.formula,
    )


def emit(cfg: Config | None = None) -> NoveltyReference:
    """Measure the reference from the curated data's **training** split. The slow half.

    Training rows only, and distinct canonical compositions rather than rows: a candidate is
    novel relative to what the model *learned from*, so a validation or test alloy is not
    known chemistry for this purpose. :func:`~hydms.data.canonical.group_keys` decides that two
    spellings are one material -- called rather than re-derived, because #87 owns that identity
    and ``Ce1Mg12``/``Mg12Ce1`` is the reason it exists.
    """
    from hydms.data.canonical import group_keys
    from hydms.surrogate.model import ModelSettings, capacity_matrix
    from hydms.surrogate.scaler import TRAIN

    config = cfg if cfg is not None else load_config()
    frame, split = capacity_matrix(config, settings=ModelSettings.from_config(config))
    training = frame.loc[split == TRAIN]
    keys = group_keys(training)
    formulas = training[config.columns.formula].astype(str)
    # One formula per canonical composition, chosen by sorting rather than by row order, so
    # the emitted file does not depend on how the frame happened to arrive.
    chosen: Mapping[str, str] = (
        pd.DataFrame({"key": keys.to_numpy(), "formula": formulas.to_numpy()})
        .sort_values("formula")
        .groupby("key", sort=True)["formula"]
        .first()
        .to_dict()
    )
    return NoveltyReference.measured(sorted(chosen.values()))


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """``--emit`` rewrites the committed reference; no argument prints what it holds."""
    stream = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(
        prog="python -m hydms.screens.novelty",
        description="The novelty reference: measure it, or show it.",
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help=f"re-measure from the curated data and rewrite {REFERENCE_FILE.name}",
    )
    args = parser.parse_args(argv)

    reference = emit() if args.emit else NoveltyReference.packaged()
    if args.emit:
        REFERENCE_FILE.write_text(reference.to_json(), encoding="utf-8")
        print(f"wrote {REFERENCE_FILE}", file=stream)
    print(
        f"{len(reference.formulas)} known composition(s) on the {MOD_PETTI} scale.\n"
        f"Ceiling {_number(reference.ceiling)}: the gap between {reference.loneliest} and "
        f"{reference.loneliest_nearest}, the widest the corpus holds internally.\n"
        f"A candidate past it is {BEYOND_KNOWN_CHEMISTRY} -- chemistry, never the "
        f"applicability domain (#48).",
        file=stream,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - the command line
    raise SystemExit(main())
