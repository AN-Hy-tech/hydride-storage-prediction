"""L1 -- the columns that are the record, not the model's input.

``extract_features_cbfv.py:19-21`` is one line::

    object_cols = df_raw.select_dtypes(include='object').columns
    cols_to_drop = [col for col in object_cols if col != 'Composition']
    df_raw = df_raw.drop(columns=cols_to_drop)

It deletes ``Alloy_class``, ``Dataset`` and ``Citation`` because they are not numbers, which
is locally reasonable and globally fatal: leave-one-alloy-class-out validation (AC-6) is the
PRD's most important validation number, and after this line there is nothing to fold on.
There is no trace of the class anywhere downstream in the repository. That is leak **L13**.

The lesson is not "keep object columns". It is that a table entering featurisation holds
three different kinds of column and the code had a word for only one of them:

  - **Identifiers** -- ``Composition``, and the canonical key derived from it. The featuriser
    reads the formula; neither is a feature.
  - **The record** -- ``Alloy_class``, ``Dataset``, ``Citation``. Nothing computes with them
    and everything downstream needs them: the class for AC-6 folds and the applicability
    domain, the provenance columns for the Chapter 1 revision.
  - **The target** -- ``H2_W% (max)`` and its model-space twin. Carried beside the features
    for exactly as long as it takes to fit, and never *inside* them.

:func:`metadata_columns` names what must survive featurisation, which is what the L13
sentinel is handed. :func:`non_feature_columns` names what must never be inside the feature
matrix, which is the same list plus the target in both spaces -- because the one column
whose presence in ``X`` would be worse than L13 is the thing the model is predicting.

**The class is joined on the canonical key, never the formula string.** ``Ce1Mg12`` is
labelled ``MIC`` and ``Mg12Ce1`` is labelled ``Mg``; they are one material. Joining per
string keeps both answers and hands a leave-one-class-out fold two labels for one
composition. :func:`with_metadata` therefore goes through
:func:`hydms.data.canonical.alloy_classes`, which reconciles by
:data:`~hydms.data.canonical.ALLOY_CLASS_PRECEDENCE` -- card #87 decided that and this module
consumes the decision rather than making a second one.

**What reconciliation does to the distribution.** Measured over all 1279 rows: no row is lost
and no class disappears, 13 rows change label, and the movement is entirely into the
structural families and out of the residual ones::

    AB5  196 -> 196      Mg   148 -> 148      SS   103 -> 103
    AB2  368 -> 371      HEA   77 ->  77      MIC  132 -> 127
    AB    90 ->  90      MEA  110 -> 109
    A2B   27 ->  32      LEA   28 ->  26

``Mg2Ni1`` moving from ``Mg`` to ``A2B`` is the textbook A2B compound being called by its
structure, and ``Ti0.8Zr0.2Mn1Cr1`` moving from ``MEA`` to ``AB2`` is a C14 Laves phase that
also happens to have four principal elements. Both spellings were correct; AC-6 needs a
partition, so one wins.

**AC-6 is feasible on this partition**, which is worth stating because it is the reason the
card exists. Counted as *compositions* rather than rows -- folds group on the canonical key
(#88), so rows are not the unit -- the smallest class is ``A2B`` with 24 and ``LEA`` with 26,
out of 1115. Ten held-out folds, none of them empty, none of them a single material.

**No eleventh label, and no ``UNKNOWN``.** The card asked for missing classes to be labelled
``UNKNOWN`` rather than dropped. Measured, ``Alloy_class`` is complete on all 1279 rows, so
nothing in the curated data needs it -- and an eleventh label is not free: it changes the fold
structure of AC-6 and would be a fold of rows whose only shared property is that nobody
labelled them. So a missing class **refuses** here, at the door, exactly as
``ColumnSpec.allowed`` refuses an unrecognised one in :mod:`hydms.data.load`. If a future
source arrives with gaps, that is a decision to make deliberately, and both the closed set in
:mod:`hydms.data.load` and :data:`~hydms.data.canonical.ALLOY_CLASS_PRECEDENCE` have to learn
the word in the same commit.

Card #12.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pandas as pd

from hydms.config import Columns
from hydms.config import load as load_config
from hydms.data.canonical import ALLOY_CLASS_PRECEDENCE, alloy_classes, group_keys
from hydms.data.target import model_space_name

__all__ = [
    "CANONICAL_KEY_COLUMN",
    "MetadataError",
    "class_distribution",
    "metadata_columns",
    "non_feature_columns",
    "refuse_non_features",
    "with_metadata",
]

# A failure that names two hundred rows is a failure nobody reads to the end. The total is
# always reported; the listing is truncated. Same convention as `hydms/data/load.py`,
# `hydms/data/canonical.py`, `hydms/data/merge.py` and `hydms/data/target.py`.
_MAX_NAMED = 8

#: The column :func:`with_metadata` attaches. Named here rather than spelled in each
#: consumer; :func:`hydms.data.canonical.group_keys` already returns a ``Series`` with this
#: name, and the two must not drift.
CANONICAL_KEY_COLUMN = "canonical_key"


class MetadataError(ValueError):
    """Metadata is missing where it is needed, or present where it must not be.

    A ``ValueError``, like :class:`~hydms.data.load.SchemaViolation`,
    :class:`~hydms.data.merge.MergeError`,
    :class:`~hydms.data.canonical.CanonicalisationError` and
    :class:`~hydms.data.target.TargetError`: a guard refusing, not a detector reporting that
    a guard failed. The detector for the same defect is
    :func:`hydms.qa.detectors.assert_metadata_survives`, and it reports rather than refuses
    because gate HG-1 has to be able to say *how* the pipeline lost a column.
    """


def _named(items: Iterable[object]) -> str:
    """Render offenders for a message: sorted, truncated, and counted."""
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


def metadata_columns(columns: Columns | None = None) -> tuple[str, ...]:
    """The columns a featuriser must carry through, in the order they appear in the file.

    This is the list handed to :func:`hydms.qa.detectors.assert_metadata_survives` -- the L13
    sentinel's ``live`` check, which card #12 wires once ``hydms.descriptors.featurize``
    exists. It does **not** include the target: a stage is entitled to drop the target (the
    surrogate is handed ``X`` and ``y`` separately), and asserting that it survives would go
    red on correct code.

    Args:
        columns: Column names, defaulting to ``pipeline.yaml``'s.

    Returns:
        ``Composition``, ``Alloy_class``, ``Dataset``, ``Citation``, ``canonical_key``.
    """
    names = columns if columns is not None else load_config().columns
    return (
        names.formula,
        names.alloy_class,
        names.dataset,
        names.citation,
        CANONICAL_KEY_COLUMN,
    )


def non_feature_columns(columns: Columns | None = None) -> tuple[str, ...]:
    """Every column that must never appear in the feature matrix.

    :func:`metadata_columns` plus the target in both spaces. The target is the reason this
    function exists separately: a featuriser dropping ``Alloy_class`` costs AC-6, while a
    feature matrix *containing* ``H2_W% (max)`` costs everything at once, and the second
    failure looks like an excellent model rather than like a bug.

    Args:
        columns: Column names, defaulting to ``pipeline.yaml``'s.

    Returns:
        The metadata columns, then ``H2_W% (max)`` and ``log_H2_W% (max)``.
    """
    names = columns if columns is not None else load_config().columns
    return (*metadata_columns(names), names.target, model_space_name(names.target))


def refuse_non_features(features: pd.DataFrame, columns: Columns | None = None) -> None:
    """Refuse a feature matrix carrying anything from :func:`non_feature_columns`.

    Called by whatever hands a matrix to a model -- the scaler (#23), selection (#24), the
    surrogate (#26). It is deliberately a check on the *matrix* rather than on the featuriser:
    a column can arrive in ``X`` from a join, a ``concat`` or a ``reset_index`` long after
    featurisation, and the place to catch it is the last one before the fit.

    Args:
        features: The matrix about to be handed to a model.
        columns: Column names, defaulting to ``pipeline.yaml``'s.

    Raises:
        MetadataError: naming every offending column, and saying which kind each is.
    """
    names = columns if columns is not None else load_config().columns
    target_names = (names.target, model_space_name(names.target))
    present = [name for name in non_feature_columns(names) if name in features.columns]
    if not present:
        return
    targets = [name for name in present if name in target_names]
    detail = (
        f" {_named(targets)} is the target itself, so a model fitted on this matrix would "
        f"be predicting its own input."
        if targets
        else ""
    )
    raise MetadataError(
        f"the feature matrix carries {len(present)} column(s) that are not features: "
        f"{_named(present)}.{detail} Metadata travels beside the matrix, never inside it "
        f"(hydms.data.metadata)."
    )


def with_metadata(
    frame: pd.DataFrame,
    *,
    formula_column: str | None = None,
    class_column: str | None = None,
    aliases: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """The frame with its canonical key attached and its ``Alloy_class`` reconciled.

    The one place the raw table becomes the table the rest of the pipeline uses. Two
    guarantees, both asserted rather than assumed:

      - **Every row survives, with its own index label.** Reconciliation relabels; it never
        drops, merges or reorders. 1279 rows in, 1279 rows out.
      - **Two rows describing one material carry one label.** That is the whole point --
        a fold that holds out a class must hold out every row of it -- and it is what
        joining on the formula string cannot give.

    Args:
        frame: A table with a formula column and a class column, e.g. the output of
            :func:`hydms.data.load.load_hydride_data`.
        formula_column: Defaults to ``columns.formula``.
        class_column: Defaults to ``columns.alloy_class``.
        aliases: Applied to each label before reconciliation, for a source whose vocabulary
            is not the curated one -- :data:`~hydms.data.canonical.ML_HYDPARK_CLASS_ALIASES`
            is the one that exists.

    Returns:
        A copy of ``frame`` with :data:`CANONICAL_KEY_COLUMN` added and ``Alloy_class``
        replaced by the reconciled label. The input is not mutated.

    Raises:
        CanonicalisationError: A row cannot be keyed, a class is missing, or a label is
            outside the ten the curated file declares. A missing class refuses here rather
            than becoming an eleventh class -- see this module's docstring.
        MetadataError: The reconciliation lost or gained a row, which cannot happen and is
            asserted because the cost of it happening silently is every fold in AC-6.
    """
    names = load_config().columns
    label = class_column if class_column is not None else names.alloy_class

    keys = group_keys(frame, formula_column)
    reconciled = alloy_classes(
        frame,
        formula_column=formula_column,
        class_column=class_column,
        aliases=aliases,
    )
    if len(reconciled) != len(frame) or not reconciled.index.equals(frame.index):
        raise MetadataError(
            f"reconciling {label!r} changed the row set: {len(frame)} row(s) in, "
            f"{len(reconciled)} out. Reconciliation relabels and must never drop, merge or "
            f"reorder -- every fold in AC-6 depends on it."
        )

    out = frame.copy()
    out[CANONICAL_KEY_COLUMN] = keys
    out[label] = reconciled
    return out


def class_distribution(
    frame: pd.DataFrame,
    *,
    formula_column: str | None = None,
    class_column: str | None = None,
    aliases: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """What reconciliation did to each class, in rows and in compositions.

    The evidence behind "no rows lost and no class emptied", and the table the Chapter 1
    revision (#37) reports. ``compositions`` is the column AC-6 actually cares about: folds
    group on the canonical key (#88), so a class with many rows over few materials is a
    smaller fold than it looks.

    Args:
        frame: A table with a formula column and a class column.
        formula_column: Defaults to ``columns.formula``.
        class_column: Defaults to ``columns.alloy_class``.
        aliases: As :func:`with_metadata`.

    Returns:
        One row per class in :data:`~hydms.data.canonical.ALLOY_CLASS_PRECEDENCE` order, with
        ``raw`` (rows as the file labelled them), ``reconciled`` (rows after precedence),
        ``delta`` and ``compositions`` (distinct canonical keys after reconciliation). Classes
        absent from ``frame`` are omitted; a class that reconciliation emptied would show
        ``reconciled`` 0 rather than disappearing.
    """
    names = load_config().columns
    label = class_column if class_column is not None else names.alloy_class

    resolved = with_metadata(
        frame,
        formula_column=formula_column,
        class_column=class_column,
        aliases=aliases,
    )
    raw_counts = frame[label].value_counts()
    new_counts = resolved[label].value_counts()
    compositions = (
        resolved[[CANONICAL_KEY_COLUMN, label]].drop_duplicates()[label].value_counts()
    )

    seen = set(raw_counts.index) | set(new_counts.index)
    order = [name for name in ALLOY_CLASS_PRECEDENCE if name in seen]
    records: list[dict[str, Any]] = [
        {
            label: name,
            "raw": int(raw_counts.get(name, 0)),
            "reconciled": int(new_counts.get(name, 0)),
            "delta": int(new_counts.get(name, 0)) - int(raw_counts.get(name, 0)),
            "compositions": int(compositions.get(name, 0)),
        }
        for name in order
    ]
    return pd.DataFrame.from_records(records).set_index(label)
