"""How a per-element property becomes a per-composition number.

Card #17. Five statistics over a weighted composition -- ``avg``, ``dev``, ``range``,
``max`` and ``min``. This is the whole of what CBFV does mathematically; everything else
in the descriptor layer is table lookup (:mod:`hydms.descriptors.element_data`) and
naming (card #19).

The module is pure: arrays in, arrays out, no I/O, no table, no formula parsing. It does
not know what a property *is*, which is why the property axis belongs to the caller --
see "One property at a time" below.

Three things were measured against CBFV 1.1.0 rather than read off its source, over all
1,279 formulae of ``hydride_data.csv`` and every property of both tables. Each changed
what this module is.

**1. ``dev`` is not a standard deviation.** It is the *fraction-weighted mean absolute
deviation about the fraction-weighted mean*::

    avg = sum_i  f_i * p_i
    dev = sum_i  f_i * |p_i - avg|

Transcribing that arithmetic reproduces CBFV's ``dev`` column to **0.0** -- not to a
tolerance, exactly -- on every one of the 1,279 x 44 oliynyk cells and the 1,278 x 438
jarvis cells. The plausible rivals are nowhere near: a fraction-weighted population
standard deviation differs by up to **328.8**, an unweighted standard deviation by up to
**1172.2**, and an unweighted mean absolute deviation by up to **1094.9**. A reader who
assumes "dev" means "deviation" in the usual sense gets a different number in the third
significant figure, not in the twelfth.

**2. ``range``, ``max`` and ``min`` are unweighted.** They are taken over the *distinct
elements present*, with no reference to how much of each there is: ``range`` is
``max - min`` over the property values of the elements in the formula. A padded slot is
therefore not a value of 0 to be minimised over -- it is not there at all, and this
module masks it rather than zero-filling it.

**3. The reduction must run down the leading axis.** NumPy uses pairwise summation when
it reduces the fast axis, which reorders the additions; reducing the leading axis is a
plain sequential accumulation, and adding an exactly-zero padded term to a finite float
changes nothing at all. So the shape the arrays are reduced in decides whether this
module reproduces CBFV or merely approximates it:

===============================  ==========================  ==========================
reduction                        max |diff| vs CBFV, oliynyk  max |diff| vs CBFV, jarvis
===============================  ==========================  ==========================
``(n, k)`` over axis 1           1.364e-12                   2.794e-09
``(k, n)`` over axis 0           **0.0**                     **0.0**
===============================  ==========================  ==========================

The jarvis figure is the one that matters: **2.794e-09 is over gate AC-2's 1e-9
tolerance**, on ``bp_mult_mp``. Restricted to the nineteen properties the 22 selected
features actually need the naive form peaks at 2.274e-12 and would have passed -- which is
exactly why this is written down instead of discovered later by card #25 re-running
selection onto a property that had never been checked. The correct axis costs nothing, so
there is no trade to make: :func:`statistics` transposes to element-leading and reduces
there, whatever shape the caller hands it.

**4. A batch of one defeats 3, and only from eight elements up.** Transposed, a single
composition leaves the reduction axis *contiguous* after all, so numpy sums it pairwise --
and its contiguous sum switches from a plain loop to an eight-accumulator unrolled one at
exactly eight elements. Measured over 200 random compositions per arity: a lone composition
agrees with itself inside a batch **bit for bit up to arity 7**, and from **arity 8**
disagrees by up to **5.5e-12** on ``avg`` and ``dev``. Eleven of the 1,279 curated rows have
eight elements or more, and featurising one formula alone is exactly what the app (#82) and
AC-4's round-trip (#33) do. So :func:`statistics` duplicates a lone composition, reduces the
pair and discards the copy: the promise "a composition does not depend on what it was batched
with" then holds at every arity, which is the form the rest of the project relies on. Found by
card #20 through :func:`hydms.descriptors.featurize.featurize`; card #17's own test used arity
5 and could not have seen it.

**What is *not* exactly invariant.** ``docs/QA-PROTOCOL.md`` §L2 asks for permutation and
scale invariance, and neither holds to the bit -- in this module or in CBFV, for the same
reason. A sequential accumulation in a different element order rounds differently, and
rescaling the weights re-rounds the division that normalises them. Measured on the
committed tables, permuting the elements of every formula moves a statistic by up to
1.364e-12 (oliynyk) and 2.794e-09 (jarvis); multiplying every weight by 7 moves it by up
to 2.274e-12 and 3.725e-09. Those absolute numbers are magnitudes, not errors: one ulp at
jarvis's largest value, 2.15e7, *is* 3.7e-09. The invariance is real and is tested, but it
is tested as ``|a - b| <= atol + rtol * |b|`` with measured constants, never with ``==``.
Card #11 reached the same conclusion about the target transform from three unrelated
one-ulp effects.

**One property at a time.** :func:`statistics` takes ``(n_compositions, max_arity)``
weights and values of the same shape -- one property, a batch of compositions -- rather
than carrying a trailing property axis. That is not a simplification for its own sake: a
hole in the published table is per *property* per *element*
(``gordy_en`` is empty for 21 of the 55 elements this dataset uses, and every jarvis
property is a sentinel for europium), so a property axis inside this module would force
the caller to drop a whole composition because one of its nineteen properties has a hole,
or a whole property because one composition needs it. Keeping the axis outside leaves that
decision with card #19, where it belongs.

``mode`` -- CBFV's sixth statistic, the minimum property value among the elements tied for
the largest fraction -- is deliberately absent. No selected feature uses it, and an
unused statistic is one more thing card #21 would have to hold to 1e-9.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np

__all__ = [
    "STATISTICS",
    "CompositionError",
    "Statistics",
    "statistics",
]

#: CBFV's own prefixes, in CBFV's own order. A feature column is ``f"{prefix}_{property}"``,
#: so these strings are not a private vocabulary -- they are half of every feature name the
#: 22-feature contract (card #19) quotes, and :class:`Statistics` is indexable by them so a
#: caller can build the name and fetch the column with one string.
STATISTICS: Final = ("avg", "dev", "range", "max", "min")


class CompositionError(ValueError):
    """A batch of compositions cannot yield a statistic, and the message says why.

    A ``ValueError`` for the same reason as
    :class:`~hydms.descriptors.element_data.ElementDataError` and
    :class:`~hydms.data.load.SchemaViolation`: the caller passed something the arithmetic
    does not support, rather than losing a race or a file handle.

    Raised rather than returning ``nan`` for the empty composition, which is the failure
    this layer exists to remove. CBFV, handed one, dies inside a reduction with
    ``ValueError: zero-size array to reduction operation maximum`` -- a message naming
    neither the row nor the file -- and, handed an element it has no properties for,
    substitutes zeros and emits a full row of plausible numbers instead.
    """


@dataclass(frozen=True)
class Statistics:
    """The five statistics of one property over a batch of compositions.

    Every field is a ``(n_compositions,)`` float64 array, aligned with the rows of the
    ``weights`` that produced it. Field names are CBFV's prefixes verbatim, including the
    three that shadow builtins as attributes: the point is that ``f"{name}_{prop}"`` is
    the feature column name, so a caller that has the name can reach the column.

    Frozen because a statistic is a measurement of an input that has already been
    validated; a caller able to edit one in place could make a feature matrix disagree
    with the composition it was computed from.
    """

    avg: np.ndarray
    dev: np.ndarray
    range: np.ndarray
    max: np.ndarray
    min: np.ndarray

    def __getitem__(self, statistic: str) -> np.ndarray:
        """``stats["avg"]`` -- so the caller can index with the half of a feature name.

        Raises:
            KeyError: naming the five that exist. ``mode`` is the one people ask for; the
                module docstring says why it is absent.
        """
        if statistic not in STATISTICS:
            raise KeyError(
                f"{statistic!r} is not a composition statistic. This module implements "
                f"{', '.join(STATISTICS)}; CBFV's `mode` is deliberately not among them "
                f"because no selected feature uses it."
            )
        value: np.ndarray = getattr(self, statistic)
        return value


def statistics(weights: np.ndarray, values: np.ndarray) -> Statistics:
    """The five statistics of one element property over a batch of compositions.

    Args:
        weights: ``(n_compositions, max_arity)``. Element amounts, **unnormalised** -- they
            are divided by their row sum here, which is what makes the result invariant to
            rescaling a formula. A weight of exactly ``0.0`` means *this slot is padding*:
            the composition has fewer elements than the widest one in the batch. Padding
            is masked, never averaged in and never minimised over.
        values: the same shape. ``values[i, j]`` is the property of the element that
            ``weights[i, j]`` weighs, as
            :meth:`~hydms.descriptors.element_data.PropertyTable.vector` returns it.
            Padded slots are ignored entirely, so they may hold anything -- ``0.0``,
            ``nan``, whatever was convenient to pad with.

    Returns:
        Statistics: five ``(n_compositions,)`` arrays.

    Raises:
        CompositionError: if the two shapes disagree or are not two-dimensional; if any
            weight is negative; if a row is all padding, which is a composition with no
            elements; or if a *present* slot holds a non-finite value. The last is the
            important one -- a ``nan`` reaching the arithmetic would spread to ``avg`` and
            then to ``dev``, and a downstream median-fill would turn it back into
            something that looks like a measurement. That is precisely how the published
            feature matrix came to contain a row computed as though europium had zero
            mass (``hydms/descriptors/data/SOURCES.md``).
    """
    weights = np.asarray(weights, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)

    if weights.ndim != 2 or values.shape != weights.shape:
        raise CompositionError(
            f"weights and values must both be (n_compositions, max_arity) and the same "
            f"shape; got weights {weights.shape} and values {values.shape}. A single "
            f"composition is a batch of one -- pass weights[None, :]."
        )

    present = weights != 0.0
    if np.any(weights < 0.0):
        rows = np.flatnonzero(np.any(weights < 0.0, axis=1))
        raise CompositionError(
            f"{rows.size} composition(s) carry a negative element amount, first at row "
            f"{int(rows[0])}. CBFV accepts these -- `Mg-1` parses to {{'Mg': -1.0}} and is "
            f"normalised by the sum of absolute amounts -- and hydms.data.load.parse_formula "
            f"refuses them at the door. Nothing downstream of it should produce one."
        )
    empty = np.flatnonzero(~np.any(present, axis=1))
    if empty.size:
        raise CompositionError(
            f"{empty.size} composition(s) contain no elements at all, first at row "
            f"{int(empty[0])}: every weight in the row is zero, so there is nothing to "
            f"average. There is no honest statistic for an empty composition."
        )
    if not np.all(np.isfinite(values[present])):
        rows = np.flatnonzero(np.any(present & ~np.isfinite(values), axis=1))
        raise CompositionError(
            f"{rows.size} composition(s) carry a non-finite property value in a slot that "
            f"is not padding, first at row {int(rows[0])}. A hole in a published table is "
            f"not a number: PropertyTable.value() raises rather than handing one over, and "
            f"a nan arriving here would reach `avg`, then `dev`, and then look like a "
            f"measurement."
        )

    # A batch of one is the one shape the paragraph below does not survive: transposed, a
    # lone composition leaves the reduction axis contiguous, and numpy's contiguous sum
    # regroups the additions from eight elements up. Reducing a duplicated pair restores the
    # stride, and the copy is dropped at the end. See the module docstring's point 4; it is
    # worth 5.5e-12 on the eleven curated rows with eight elements or more, and it is what
    # makes a single-formula prediction agree with the training matrix.
    alone = weights.shape[0] == 1
    if alone:
        weights = np.repeat(weights, 2, axis=0)
        values = np.repeat(values, 2, axis=0)
        present = np.repeat(present, 2, axis=0)

    # Element-leading, contiguous. Everything below reduces over axis 0, which numpy
    # performs as a sequential accumulation rather than a pairwise one -- that is what
    # makes a padded exact zero cost nothing and the result bit-identical to CBFV's
    # per-composition loop. See the module docstring's table; it is worth 2.794e-09.
    weight = np.ascontiguousarray(weights.T)
    value = np.ascontiguousarray(values.T)
    here = np.ascontiguousarray(present.T)

    fraction = np.where(here, weight / weight.sum(axis=0), 0.0)
    # Padding is zeroed before it is weighted, so `nan` padding stays out of `0.0 * nan`.
    contribution = np.where(here, value, 0.0)

    avg = (fraction * contribution).sum(axis=0)
    dev = (fraction * np.abs(contribution - avg)).sum(axis=0)

    # Unweighted, and over the present elements only: +/-inf is the identity for these two
    # reductions, so padding cannot become the largest or the smallest value.
    largest = np.where(here, value, -np.inf).max(axis=0)
    smallest = np.where(here, value, np.inf).min(axis=0)

    if alone:
        avg, dev = avg[:1], dev[:1]
        largest, smallest = largest[:1], smallest[:1]

    return Statistics(
        avg=avg, dev=dev, range=largest - smallest, max=largest, min=smallest
    )
