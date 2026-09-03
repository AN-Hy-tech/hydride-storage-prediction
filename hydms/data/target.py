"""L1 -- the modelled target is ``log1p(wt%)``, and this is the only module that knows it.

Every number the surrogate produces lives in one of two spaces, and nothing in the file, the
column heading or the type says which. ``REPORT.md`` section 7.3 already records what that
costs: the published SHAP attributions are in log space and were read as weight percent. The
archival pipeline spread the pairing over four scripts -- ``log_transform_target.py:35``
applies it, ``benchmark_model_selection.py:946-949`` inverts it, ``Catboostmodel.py`` inverts
it again -- so there was no single place to be right.

Here there is one. :func:`to_model_space` and :func:`to_wt_pct` are the entry points, and a
named ``Series`` carries its space in its name: ``H2_W% (max)`` in, ``log_H2_W% (max)`` out,
and back again. A column whose values are in log space and whose heading says weight percent
cannot be produced by this module.

**The transform is ``log1p``, and that is measured rather than inferred.** Against
``hydride_prefeaturizing.csv``'s ``log_H2_W% (max)`` over all 1279 rows::

    log1p(y)        max |difference|  4.44e-16      <- this one
    log(y)                            2.40e+00
    log1p(10 * y)                     2.19e+00
    log(10 * y)                       2.17e+00

So the inverse is ``expm1``, and the published column is a fixture with a known answer to
hold the round trip to.

**The column is a fixture, never a source.** ``hydride_prefeaturizing.csv`` is row-for-row
aligned with ``hydride_data.csv`` -- verified elementwise on formula and temperature for all
1279 rows -- but *only* positionally: ``(Composition, temperature(K))`` is not unique on
either file (1279 rows, 1272 distinct pairs, card #10), so there is no key to join it on.
Reading the column across would be leak **L9** in a new place. :func:`to_model_space`
recomputes it.

**Nothing here is bit-exact, and no test may assert that it is.** Three separate reasons,
each measured on the real data:

  - The published column was written by ``DataFrame.to_csv`` and read back through decimal
    text. It differs from ``log1p`` of the target by up to 4.44e-16 -- one ulp -- on 274 of
    1279 rows against NumPy's ``log1p`` and 413 against the standard library's.
  - ``math.log1p`` and ``numpy.log1p`` are not the same implementation. They differ by at
    most 1.11e-16, again one ulp, on this data. This module uses the standard library's,
    because NumPy cannot be imported under ``hydms/`` until the descriptor layer solves the
    stub problem (``pyproject.toml``, ``[tool.mypy]``); since every caller comes through
    here, one implementation is used everywhere and AC-1's bit-for-bit reproducibility is
    unaffected.
  - ``expm1(log1p(y))`` returns ``y`` exactly on 794 of 1279 rows and is within 2.7e-15
    absolute (3.8e-16 relative) on the rest.

A tolerance of 1e-12 is comfortably above all three and comfortably below anything that
could matter to a weight percent measured to two decimal places.

**Which published metric is in which space.** Read off the archival code, not off the prose:

    ============================  ==========  ===================================================
    ``REPORT.md``                 Space       Where
    ============================  ==========  ===================================================
    section 2.4 skew / kurtosis   both        the table's own two columns are before and after
    section 4.2 CV R2 mean+-std   **log**     ``cross_validate(pipe, X_train, y_train,
                                              scoring='r2')`` at ``benchmark:1093``; ``y_train``
                                              is the log target and nothing back-transforms it
    section 4.2 Val / Test R2,    wt%         ``evaluate_model(..., 'orig')`` applies ``expm1``
    RMSE, MAE                                 to both sides first, ``benchmark:946-949``
    section 4.3 bootstrap CI      wt%         ``bootstrap_ci(y_val_original, expm1(y_val_pred),
                                              ...)`` at ``benchmark:1194-1196``
    section 6.1 SHAP, PDP         **log**     stated in the report; also leak L11, since both
                                              are computed on ``X_test``
    ============================  ==========  ===================================================

The two log-space rows are why the section 4.2 table cannot be read across: its
"Overfitting" column is defined in the report's own footnote as ``CV_R2_mean - Val_R2_orig``,
which subtracts a weight-percent number from a log-space one. (The code does not do that --
``benchmark:1120`` computes ``train_r2_orig - val_r2_orig``, both in weight percent -- so the
footnote misdescribes the column it annotates. Recorded as a disagreement on card #89.)

Card #11.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import pandas as pd

__all__ = [
    "MODEL_SPACE_PREFIX",
    "MODEL_SPACE_RANGE",
    "ROUND_TRIP_TOLERANCE",
    "WT_PCT_RANGE",
    "TargetError",
    "model_space_name",
    "to_model_space",
    "to_wt_pct",
]

# A failure that names two hundred rows is a failure nobody reads to the end. The total is
# always reported; the listing is truncated. Same convention as `hydms/data/load.py`,
# `hydms/data/canonical.py`, `hydms/data/merge.py` and `hydms/qa/detectors.py`.
_MAX_NAMED = 8

#: What a column heading gains when its values move into model space. ``H2_W% (max)``
#: becomes ``log_H2_W% (max)``, which is the name ``hydride_prefeaturizing.csv`` already
#: uses -- ``hydms.data.load.prefeaturized_schema`` declares it through
#: :func:`model_space_name` so the contract is spelled once.
MODEL_SPACE_PREFIX = "log_"

#: The tightest tolerance any comparison of two target vectors may use. Derived in this
#: module's docstring from three separate one-ulp effects; asserted in
#: ``tests/data/test_target.py``, which measures each of them rather than trusting this
#: number.
ROUND_TRIP_TOLERANCE = 1e-12

#: The span of ``H2_W% (max)`` over all 1279 rows of ``hydride_data.csv``, and its image
#: under :func:`to_model_space`. The round-trip property test covers this range; the
#: refusal path's *trained* domain is a different question and lives in ``pipeline.yaml``.
#:
#: The lower bound is the standard library's ``log1p(0.1)``. NumPy's is
#: ``0.09531017980432493``, one ulp above -- the same one-ulp gap this module's docstring
#: measures over the whole column, showing up in a constant. Written out here because a
#: literal is where it is checkable.
WT_PCT_RANGE = (0.1, 7.19)
MODEL_SPACE_RANGE = (0.09531017980432487, 2.1029138978649784)


class TargetError(ValueError):
    """A value cannot be moved between the two target spaces, and the message says why.

    A ``ValueError``, like :class:`~hydms.data.load.SchemaViolation`,
    :class:`~hydms.data.merge.MergeError` and
    :class:`~hydms.data.canonical.CanonicalisationError`: a guard refusing, not a detector
    reporting that a guard failed.
    """


def model_space_name(name: str) -> str:
    """The model-space heading for a weight-percent column.

    ``hydms.data.load.prefeaturized_schema`` declares ``hydride_prefeaturizing.csv``'s
    target column through this function, so the contract is spelled once rather than as an
    f-string in each module that needs it.

    Args:
        name: A weight-percent column heading.

    Returns:
        The heading with :data:`MODEL_SPACE_PREFIX` applied.

    Raises:
        TargetError: The heading is already in model space. ``log_log_H2_W% (max)`` is what
            a double transform looks like from the outside, and it is the mistake
            ``REPORT.md`` section 7.3 records.
    """
    if name.startswith(MODEL_SPACE_PREFIX):
        raise TargetError(
            f"{name!r} is already a model-space column name. Applying the transform twice "
            f"is the mistake REPORT.md section 7.3 records; call to_wt_pct first if you "
            f"meant to go back."
        )
    return f"{MODEL_SPACE_PREFIX}{name}"


def _model_space_label(name: object) -> object:
    """:func:`model_space_name` over a ``Series`` name, which may be ``None`` or a tuple."""
    return model_space_name(name) if isinstance(name, str) else name


def _wt_pct_label(name: object) -> object:
    """The weight-percent heading for a model-space column. Never refuses.

    A model value need not have arrived from a column at all -- a surrogate's prediction is
    named after nothing -- so an unprefixed name is passed through rather than rejected.
    """
    if isinstance(name, str) and name.startswith(MODEL_SPACE_PREFIX):
        return name[len(MODEL_SPACE_PREFIX) :]
    return name


def _usable(value: Any, floor: float | None) -> str | None:
    """Why ``value`` cannot be transformed, or ``None`` if it can."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{value!r} is not a number"
    if math.isnan(number):
        return "is missing (NaN)"
    if math.isinf(number):
        return f"is {number}"
    if floor is not None and number < floor:
        return f"is {number!r}, below {floor!r}"
    return None


def _refuse(problems: Iterable[tuple[object, str]], *, total: int, direction: str) -> None:
    """Raise naming every offending row, not the first. A column is fixed once."""
    listed = list(problems)
    if not listed:
        return
    shown = "\n  - ".join(f"row {label}: {detail}" for label, detail in listed[:_MAX_NAMED])
    more = f"\n  - and {len(listed) - _MAX_NAMED} more" if len(listed) > _MAX_NAMED else ""
    raise TargetError(
        f"{len(listed)} of {total} value(s) cannot be moved {direction}:\n  - {shown}{more}"
    )


def _apply(
    values: float | pd.Series,
    *,
    transform: Any,
    floor: float | None,
    rename: Any,
    direction: str,
) -> Any:
    """One pass to validate, one to transform. Shared by both directions."""
    if isinstance(values, pd.Series):
        problems = [
            (label, complaint)
            for label, value in values.items()
            if (complaint := _usable(value, floor)) is not None
        ]
        _refuse(problems, total=len(values), direction=direction)
        return values.map(transform).rename(rename(values.name))

    complaint = _usable(values, floor)
    if complaint is not None:
        raise TargetError(f"a target value cannot be moved {direction}: {values!r} {complaint}")
    return transform(float(values))


def _expm1(value: float) -> float:
    """``math.expm1`` with the overflow turned into this module's own failure."""
    try:
        return math.expm1(value)
    except OverflowError as exc:
        raise TargetError(
            f"{value!r} overflows on the way back to weight percent: expm1 of it exceeds the "
            f"largest float. The published target spans {WT_PCT_RANGE[0]}-{WT_PCT_RANGE[1]} "
            f"wt%, so a model-space value this large is a broken model, not a prediction."
        ) from exc


def to_model_space(wt_pct: float | pd.Series) -> Any:
    """Weight percent to the space the surrogate is fitted in: ``log1p``.

    ::

        to_model_space(7.19)      ==  2.1029138978649784
        to_model_space(series)    ==  a Series named log_<the input's name>

    Args:
        wt_pct: A hydrogen capacity in weight percent, or a ``Series`` of them.

    Returns:
        The same shape in model space. A named ``Series`` is renamed by
        :func:`model_space_name`, so the space is visible in any frame it lands in.

    Raises:
        TargetError: A value is missing, infinite, not a number, or negative -- a negative
            weight percent is not a measurement, and ``log1p`` below -1 is undefined, so the
            floor is 0 rather than -1. Every offending row is named, not the first.
    """
    return _apply(
        wt_pct,
        transform=math.log1p,
        floor=0.0,
        rename=_model_space_label,
        direction="into model space",
    )


def to_wt_pct(model_value: float | pd.Series) -> Any:
    """Model space back to weight percent: ``expm1``.

    **A negative result is returned, not clipped.** ``expm1`` of a negative model value is a
    negative weight percent, which is unphysical -- and a quantile head's lower band can
    produce one near the bottom of the range. Clipping it here would erase the only signal
    that the model has left the region it can defend, and that judgement belongs to the
    refusal path (card #77) and the applicability domain (card #48), which see the interval
    and the domain verdict as well as the point. This module reports the arithmetic.

    Args:
        model_value: A value in model space, or a ``Series`` of them.

    Returns:
        The same shape in weight percent. A ``Series`` named ``log_x`` comes back named
        ``x``; any other name is passed through, since a prediction is named after nothing.

    Raises:
        TargetError: A value is missing, infinite, not a number, or so large that ``expm1``
            overflows.
    """
    return _apply(
        model_value,
        transform=_expm1,
        floor=None,
        rename=_wt_pct_label,
        direction="back to weight percent",
    )
