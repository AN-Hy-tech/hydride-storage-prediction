"""L3 -- the scaling transform is fitted once, on the training split, and travels with the model.

``Catboostmodel.py:507-511`` does the right thing and then loses it::

    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    ...
    joblib.dump(scaler, os.path.join(optimized_models_dir, 'scaler.pkl'))

The fit is on train alone, which is correct. What is wrong is everything around it: the file
lands beside the script with no manifest, nothing records which matrix or which rows produced
it, and the audit found no such file on disk at all. So Architecture A's "load the fitted
scaler, do not refit" had nothing to load, and the only way to reproduce a scaled candidate
was to re-run the fit -- on whatever data happened to be at hand. Memo 4.3 practical check 2
names that a *silent correctness bug*: a scaler re-derived from candidates centres them on
themselves, so a batch of ten candidates and the same ten inside a batch of a thousand get
different numbers, and neither raises.

Three decisions worth stating rather than reading out of the arithmetic.

**What is persisted is the fitted transform, not the estimator.** ``RobustScaler`` performs
the fit -- the definition of "robust" stays scikit-learn's, not ours -- and
:func:`fit_scaler` keeps its result: the feature names, the medians and the IQRs.
:class:`FittedScaler` is then a value, and three things follow that do not follow from
pickling the estimator. There is no ``fit`` anywhere inside it to reach, so "never refit" is
structural rather than a convention. The stored artifact carries no scikit-learn pickle, so a
scikit-learn upgrade cannot change what a saved ``v1`` does -- which is the failure AC-1
exists to detect. And the numbers are legible in ``describe()`` and in a review.

Nothing is given up for it: ``(x - centre) / scale`` in NumPy is **bit-identical** to
``RobustScaler.transform`` over all 1,278 x 21 values of the real training matrix, measured,
and ``tests/surrogate/test_scaler.py`` re-measures it rather than trusting this sentence.

**A scaler cannot be fitted without being told which rows are training rows.**
:func:`fit_scaler` takes the whole matrix *and* the split assignment from
:func:`hydms.data.splits.assign_splits`, and selects the training rows itself. It refuses a
split with nothing held out. A caller can still defeat that by handing it a split that calls
everything ``train``, but they cannot do it by accident, and the result records
``fitted_rows`` against ``held_out_rows`` so the artifact says which happened.

**A candidate batch is transformed by name, never by position.** Measured on scikit-learn
1.6.1: ``RobustScaler`` fitted on a ``DataFrame`` raises on a reordered one -- but accepts a
bare ``ndarray`` with nothing but a ``UserWarning``, and ``fit_transform`` returns an
``ndarray``, so the column names are gone one line after the fit. A permuted matrix through
that door returns plausible, wrong numbers, which is precisely the failure gate AC-4 exists
to catch. :meth:`FittedScaler.transform` therefore takes a ``DataFrame``, requires exactly
the fitted column set, selects it in fitting order, and returns a ``DataFrame``. Whatever
order the caller had, the model downstream is handed the order the model was fitted on.

**One feature has a zero IQR on the training split.** ``avg_is_alkaline``: the median-centred
column is constant, so ``RobustScaler`` substitutes a scale of 1.0 and the scaled column is
all zeros. That is not this module's to fix -- ``selection.variance_threshold`` in
``pipeline.yaml`` is 0.001 and card #24 owns the filter -- but a scale of exactly 1.0 is
indistinguishable from an IQR that genuinely equals 1.0 once the fit is over, so the names
are recorded in :attr:`FittedScaler.degenerate` at fit time, where they are still knowable.

Card #23.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NoReturn

import numpy as np
import pandas as pd

from hydms.data.metadata import refuse_non_features
from hydms.data.splits import SPLIT_NAMES

__all__ = [
    "QUANTILE_RANGE",
    "SCALER_PAYLOAD",
    "FittedScaler",
    "ScalerError",
    "fit_scaler",
    "scaler_from",
]

# A failure that names two hundred columns is a failure nobody reads to the end. The total is
# always reported; the listing is truncated. Same convention as `hydms/data/metadata.py`,
# `hydms/data/target.py` and `hydms/descriptors/featurize.py`.
_MAX_NAMED = 8

#: The payload key the fitted scaler is saved under, so ``artifacts/v{N}/scaler.joblib`` is
#: spelled once rather than at every call site. :func:`scaler_from` reads it back.
SCALER_PAYLOAD = "scaler"

#: ``RobustScaler``'s own default, written out rather than left implicit. The centre is the
#: median and the scale is the span between these two percentiles; ``Catboostmodel.py:507``
#: took the default, so this reproduces the published fit. It is passed explicitly because a
#: library default that changes underneath a pinned artifact is the shape of an AC-1 failure.
QUANTILE_RANGE = (25.0, 75.0)

#: The split a scaler is fitted on. Named here because "train" appearing as a bare string in
#: the surrogate layer is how it comes to mean something slightly different in two places;
#: the list of splits is :data:`hydms.data.splits.SPLIT_NAMES`.
TRAIN = "train"


class ScalerError(ValueError):
    """The scaler cannot be fitted, or is being asked to transform the wrong matrix.

    A ``ValueError``, like :class:`~hydms.data.metadata.MetadataError`,
    :class:`~hydms.data.splits.SplitError` and :class:`~hydms.data.target.TargetError`
    across the layers below: a guard refusing, naming what it refused.
    """


def _named(items: Iterable[object]) -> str:
    """Render offenders for a message: sorted, truncated, and counted."""
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


@dataclass(frozen=True)
class FittedScaler:
    """A fitted robust scaling transform, with no way to fit it again.

    Constructed only by :func:`fit_scaler` and read back only by :func:`scaler_from`. It is
    the object stored as ``scaler`` in an artifact version, so its fields are also its
    provenance: a reader of ``artifacts/v{N}/`` can see which split it was fitted on and how
    many rows were withheld from that fit.

    Attributes:
        feature_names: The columns it scales, in the order it was fitted on. This is the
            order :meth:`transform` returns, whatever order the caller supplied.
        centre: The median of each feature over the fitting rows.
        scale: The inter-percentile span of each feature over the fitting rows, with a zero
            span replaced by 1.0 exactly as ``RobustScaler`` does. See
            :attr:`degenerate` -- after the fit, a 1.0 here is ambiguous.
        fitted_on: The split name the fit used: ``"train"``.
        fitted_rows: How many rows that was.
        held_out_rows: How many rows of the matrix were *not* used. Zero is refused at fit
            time; it is recorded so an artifact states the ratio rather than implying it.
        quantile_range: The percentiles that defined :attr:`scale`.
        degenerate: The features whose span was zero over the fitting rows, captured while
            it is still distinguishable from a span of exactly 1.0.
    """

    feature_names: tuple[str, ...]
    centre: tuple[float, ...]
    scale: tuple[float, ...]
    fitted_on: str
    fitted_rows: int
    held_out_rows: int
    quantile_range: tuple[float, float]
    degenerate: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.feature_names:
            raise ScalerError("a scaler over no features scales nothing.")
        repeated = sorted({n for n in self.feature_names if self.feature_names.count(n) > 1})
        if repeated:
            raise ScalerError(
                f"feature name(s) {_named(repeated)} appear more than once. A repeated name "
                f"makes the centre and scale of that column ambiguous."
            )
        widths = {len(self.feature_names), len(self.centre), len(self.scale)}
        if len(widths) != 1:
            raise ScalerError(
                f"a scaler needs one centre and one scale per feature: "
                f"{len(self.feature_names)} name(s), {len(self.centre)} centre(s), "
                f"{len(self.scale)} scale(s)."
            )
        for label, values in (("centre", self.centre), ("scale", self.scale)):
            bad = [
                name
                for name, value in zip(self.feature_names, values, strict=True)
                if not np.isfinite(value)
            ]
            if bad:
                raise ScalerError(
                    f"the {label} of feature(s) {_named(bad)} is not a finite number, so "
                    f"every candidate would scale to NaN and nothing would raise."
                )
        zero = [name for name, value in zip(self.feature_names, self.scale, strict=True) if value == 0.0]
        if zero:
            raise ScalerError(
                f"feature(s) {_named(zero)} have a scale of zero, which divides by zero. A "
                f"zero span is substituted with 1.0 at fit time and recorded in "
                f"`degenerate`; a zero reaching here means it was constructed by hand."
            )
        if self.fitted_rows <= 0:
            raise ScalerError(
                f"a scaler fitted on {self.fitted_rows} row(s) has no statistics to hold."
            )
        unknown = set(self.degenerate) - set(self.feature_names)
        if unknown:
            raise ScalerError(
                f"degenerate feature(s) {_named(unknown)} are not features of this scaler."
            )

    def __len__(self) -> int:
        """How many features it scales."""
        return len(self.feature_names)

    def __contains__(self, name: object) -> bool:
        return name in self.feature_names

    # ----------------------------------------------------------------------------------
    # The one thing it does
    # ----------------------------------------------------------------------------------

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """Scale a batch, by name, in fitting order.

        The columns must be exactly :attr:`feature_names` -- no more, no fewer. That check is
        strictly stronger than :func:`~hydms.data.metadata.refuse_non_features`, which
        therefore runs at fit time rather than here: a set equal to the fitted features
        cannot contain the target or the alloy class. It also means this method reads no
        configuration, which keeps it off the hot path of a candidate sweep.

        Args:
            features: The matrix to scale, on any index, with the fitted columns in any
                order. Not an ``ndarray``: scikit-learn accepts one with a ``UserWarning``
                and cannot then tell a permuted matrix from a correct one, which is the
                door this signature closes.

        Returns:
            ``(len(features), len(self))`` of ``float64``, columns in **fitting** order, on
            the caller's index. The input is never modified.

        Raises:
            ScalerError: if it is not a ``DataFrame``, if the column set is not the fitted
                one, or if any value is not finite. Every offending name is listed.
        """
        if not isinstance(features, pd.DataFrame):
            raise ScalerError(
                f"a scaler transforms a DataFrame, not a {type(features).__name__}. An "
                f"array carries no column names, so a permutation of the fitted order "
                f"would scale each column by another column's statistics and return "
                f"plausible, wrong numbers -- which is the failure gate AC-4 exists for."
            )

        fitted = set(self.feature_names)
        present = set(features.columns)
        missing = fitted - present
        extra = present - fitted
        if missing or extra:
            parts = []
            if missing:
                parts.append(f"{len(missing)} missing: {_named(missing)}")
            if extra:
                parts.append(f"{len(extra)} unexpected: {_named(extra)}")
            raise ScalerError(
                f"this scaler was fitted on {len(self)} feature(s) and the batch has "
                f"{len(features.columns)}; {'; '.join(parts)}. A scaler is fitted with a "
                f"model and a feature set together -- a batch built to a different set "
                f"needs the artifact version that was trained on it."
            )
        if features.columns.has_duplicates:
            repeated = sorted(features.columns[features.columns.duplicated()])
            raise ScalerError(
                f"the batch repeats column(s) {_named(repeated)}; selecting one by name "
                f"would return several, and which of them was scaled would depend on "
                f"column order."
            )

        values = features.loc[:, list(self.feature_names)].to_numpy(dtype=float, copy=True)
        finite = np.isfinite(values)
        if not finite.all():
            columns = [
                name
                for position, name in enumerate(self.feature_names)
                if not finite[:, position].all()
            ]
            rows = features.index[~finite.all(axis=1)]
            raise ScalerError(
                f"{len(rows)} of {len(features)} row(s) carry a value that is not finite, "
                f"in column(s) {_named(columns)}: row(s) {_named(rows)}. A NaN scales to a "
                f"NaN and reaches the model as a missing value it was never trained to "
                f"read; the featuriser refuses such rows rather than filling them "
                f"(hydms.descriptors.featurize)."
            )

        scaled = (values - np.asarray(self.centre)) / np.asarray(self.scale)
        return pd.DataFrame(scaled, index=features.index, columns=list(self.feature_names))

    # ----------------------------------------------------------------------------------
    # The things it refuses to do
    # ----------------------------------------------------------------------------------

    def fit(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Always raises. A fitted scaler is a value, and refitting it is the leak."""
        self._refuse("fit")

    def fit_transform(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Always raises -- the scikit-learn shortcut, and the one that hides a refit."""
        self._refuse("fit_transform")

    def partial_fit(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Always raises. Updating the statistics from candidates is the same defect."""
        self._refuse("partial_fit")

    def _refuse(self, method: str) -> NoReturn:
        raise ScalerError(
            f"{method}() does not exist on a fitted scaler, deliberately. This transform was "
            f"fitted on {self.fitted_rows} {self.fitted_on} row(s) and belongs to the model "
            f"stored beside it; re-deriving it from candidates centres them on themselves, "
            f"so the same candidate scores differently depending on what else was in its "
            f"batch, and nothing raises. Fit a new one with hydms.surrogate.fit_scaler() "
            f"only as part of training a new artifact version."
        )

    # ----------------------------------------------------------------------------------
    # Reading it
    # ----------------------------------------------------------------------------------

    def describe(self) -> pd.DataFrame:
        """One row per feature: its centre, its scale, and whether its span was zero.

        For the model card (#83) and for a person reading an artifact directory. The
        statistics are the whole of what this object is, so there is nothing to hide behind
        a summary.
        """
        return pd.DataFrame(
            {
                "centre": list(self.centre),
                "scale": list(self.scale),
                "degenerate": [name in self.degenerate for name in self.feature_names],
            },
            index=pd.Index(list(self.feature_names), name="feature"),
        )


def fit_scaler(
    features: pd.DataFrame,
    split: pd.Series,
    *,
    on: str = TRAIN,
    quantile_range: tuple[float, float] = QUANTILE_RANGE,
) -> FittedScaler:
    """Fit the scaling transform on one split of a feature matrix.

    The split is a *parameter*, not something derived here: it is
    :func:`hydms.data.splits.assign_splits`' output, whose grouping guarantee (leak L8) is
    the reason a training row and a held-out row are different rows at all. Deriving one
    inside this layer would put the same protocol in two places.

    Args:
        features: The whole feature matrix -- every split, not a pre-filtered subset. Its
            columns must be features and nothing else
            (:func:`~hydms.data.metadata.refuse_non_features`).
        split: Which split each row belongs to, indexed exactly as ``features`` is, label for
            label and in the same order. A positional pairing here is leak L9 in a new place.
        on: The split to fit on. ``"train"``, and the argument exists so the value is visible
            in a call rather than assumed.
        quantile_range: The percentiles defining the scale, defaulting to
            :data:`QUANTILE_RANGE`.

    Returns:
        A :class:`FittedScaler` over ``features.columns``, in that order.

    Raises:
        ScalerError: if the split does not line up with the matrix, names an unknown split,
            selects no rows, or holds nothing out; if a column is not numeric; or if a value
            in the fitting rows is not finite.
        MetadataError: if the matrix carries the target, the alloy class or any other
            non-feature column.
    """
    if not isinstance(features, pd.DataFrame):
        raise ScalerError(
            f"a scaler is fitted on a DataFrame, not a {type(features).__name__}; the "
            f"column names are what it stores."
        )
    if on not in SPLIT_NAMES:
        raise ScalerError(
            f"{on!r} is not a split. The splits are {', '.join(SPLIT_NAMES)} "
            f"(hydms.data.splits.SPLIT_NAMES)."
        )
    refuse_non_features(features)

    if len(split) != len(features) or not split.index.equals(features.index):
        raise ScalerError(
            f"the split assignment does not line up with the matrix: {len(split)} label(s) "
            f"against {len(features)} row(s), and the indexes are "
            f"{'in a different order' if len(split) == len(features) else 'different lengths'}"
            f". They are paired by label, never by position -- a positional pairing after a "
            f"row was dropped upstream is leak L9 (merge_datasets.py:46)."
        )
    if features.columns.has_duplicates:
        repeated = sorted(features.columns[features.columns.duplicated()])
        raise ScalerError(
            f"the matrix repeats column(s) {_named(repeated)}. `temperature(K)` is both a "
            f"raw column and a feature, and a positional concat returns it twice -- join "
            f"through hydms.data.metadata.with_features, which refuses that."
        )

    fitting = split == on
    fitted_rows = int(fitting.sum())
    held_out_rows = int(len(features) - fitted_rows)
    if fitted_rows == 0:
        counts = split.value_counts().to_dict()
        raise ScalerError(
            f"no row is assigned to {on!r}, so there is nothing to fit on. The split holds "
            f"{counts}."
        )
    if held_out_rows == 0:
        raise ScalerError(
            f"every one of {len(features)} row(s) is assigned to {on!r}, so this fit would "
            f"see the whole matrix. A scaler fitted on the held-out rows centres them on "
            f"themselves, and the leak is invisible afterwards -- pass the full matrix with "
            f"assign_splits()' output, not a pre-filtered training subset."
        )

    training = features.loc[fitting]
    non_numeric = [
        name for name in training.columns if not pd.api.types.is_numeric_dtype(training[name])
    ]
    if non_numeric:
        raise ScalerError(
            f"column(s) {_named(non_numeric)} are not numeric, so they have no median to "
            f"centre on. A feature matrix is float64 throughout "
            f"(hydms.descriptors.contract.assert_contract)."
        )

    values = training.to_numpy(dtype=float, copy=True)
    if not np.isfinite(values).all():
        finite = np.isfinite(values)
        columns = [
            name
            for position, name in enumerate(training.columns)
            if not finite[:, position].all()
        ]
        raise ScalerError(
            f"the {on} rows carry values that are not finite, in column(s) "
            f"{_named(columns)}. A median over NaN is NaN, and every candidate would then "
            f"scale to NaN without an error."
        )

    scaler = _robust_scaler(quantile_range).fit(values)
    centre = tuple(float(value) for value in scaler.center_)
    # `RobustScaler` substitutes 1.0 for a zero span (`_handle_zeros_in_scale`), so a scale of
    # exactly 1.0 is ambiguous the moment the fit is over. The span is recomputed here from
    # the same percentiles to tell the two apart while it is still possible.
    low, high = np.percentile(values, quantile_range, axis=0)
    degenerate = tuple(
        name for name, span in zip(training.columns, high - low, strict=True) if float(span) == 0.0
    )
    return FittedScaler(
        feature_names=tuple(str(name) for name in features.columns),
        centre=centre,
        scale=tuple(float(value) for value in scaler.scale_),
        fitted_on=on,
        fitted_rows=fitted_rows,
        held_out_rows=held_out_rows,
        quantile_range=(float(quantile_range[0]), float(quantile_range[1])),
        degenerate=degenerate,
    )


def _robust_scaler(quantile_range: tuple[float, float]) -> Any:
    """``RobustScaler`` with the percentiles pinned, imported lazily.

    Deferred so that ``import hydms.surrogate`` -- and therefore ``hydms.gates list`` and the
    board scripts -- stays answerable on an interpreter with no scientific stack, the same
    reason :func:`hydms.data.splits._sklearn` defers its imports.
    """
    try:
        from sklearn.preprocessing import RobustScaler
    except ImportError as exc:  # pragma: no cover -- exercised only on a bare interpreter
        raise ScalerError(
            "the fit is scikit-learn's RobustScaler and it is not importable here. It is a "
            "core dependency; see docs/ENVIRONMENT.md."
        ) from exc
    return RobustScaler(quantile_range=quantile_range)


def scaler_from(bundle: Any, *, name: str = SCALER_PAYLOAD) -> FittedScaler:
    """The fitted scaler held in a loaded artifact version, checked against its manifest.

    The load path of the card, and the reason it is one line rather than
    ``bundle[SCALER_PAYLOAD]``: three things can be wrong with a stored payload and none of
    them shows up until a prediction is already a number.

      - **It is not a fitted scaler.** A version written before this card holds a bare
        ``RobustScaler``, which has a ``fit`` and accepts an ``ndarray``.
      - **It scales a feature the featuriser cannot build.** The scaler's columns must be
        among the manifest's feature contract. They may be *fewer* -- selection (#24) is
        expected to narrow them -- but a name outside the contract means the artifact was
        assembled from two different runs.
      - **The payload is absent**, which reads as a ``KeyError`` naming what the version
        does hold.

    Args:
        bundle: A loaded :class:`~hydms.artifacts.store.Artifacts`.
        name: The payload key. :data:`SCALER_PAYLOAD` unless a version stored several.

    Returns:
        The stored :class:`FittedScaler`.

    Raises:
        ScalerError: the payload is not a :class:`FittedScaler`, or it scales a column the
            version's feature contract does not declare.
        KeyError: the version holds no such payload.
    """
    scaler = bundle[name]
    if not isinstance(scaler, FittedScaler):
        raise ScalerError(
            f"payload {name!r} of {getattr(bundle, 'version', 'this version')} is a "
            f"{type(scaler).__name__}, not a FittedScaler. A raw scikit-learn estimator has "
            f"a fit() and accepts an unnamed array, which is what this type exists to "
            f"prevent; re-train the version through hydms.surrogate.fit_scaler()."
        )
    declared = _declared_features(bundle)
    if declared is not None:
        outside = [name_ for name_ in scaler.feature_names if name_ not in declared]
        if outside:
            raise ScalerError(
                f"the stored scaler scales {len(outside)} column(s) the version's feature "
                f"contract does not declare: {_named(outside)}. The featuriser cannot build "
                f"them, so this scaler and this manifest came from different runs."
            )
    return scaler


def _declared_features(bundle: Any) -> frozenset[str] | None:
    """The feature names the bundle's manifest records, or ``None`` if it records none.

    ``None`` rather than an empty set, and rather than raising: :func:`scaler_from` is also
    how a test or a person inspects a hand-built bundle, and "this object has no manifest" is
    not a finding about the scaler.
    """
    names: Sequence[str] | None = getattr(bundle, "feature_names", None)
    if names is None:
        manifest = getattr(bundle, "manifest", None)
        contract = getattr(manifest, "contract", None)
        if isinstance(contract, Mapping):
            features = contract.get("features")
            if isinstance(features, Sequence):
                names = [
                    str(entry["name"])
                    for entry in features
                    if isinstance(entry, Mapping) and "name" in entry
                ]
    if not names:
        return None
    return frozenset(str(name) for name in names)
