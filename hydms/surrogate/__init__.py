"""L3 — model choice, the fit-once scaler, quantile regression and conformal calibration.

Emits prediction intervals, never bare point estimates: ranking downstream uses the
lower confidence bound, which is what stops the optimiser exploiting extrapolation.

``scaler.py``
    The scaling transform, and the fact that it belongs to the trained model rather than to
    the batch in front of it. :func:`~hydms.surrogate.scaler.fit_scaler` fits it on one split
    of a matrix and returns a :class:`~hydms.surrogate.scaler.FittedScaler`, which has a
    ``transform`` and no ``fit``; it is stored as the ``scaler`` payload of an artifact
    version and read back with :func:`~hydms.surrogate.scaler.scaler_from`.

``selection.py``
    The port of ``Boruta_FeatEng.py``'s three stages -- variance, Boruta, VIF -- run over the
    rows of one fold rather than over the whole training split (leak L6), and over rows
    :mod:`hydms.data.screening` has already judged. :func:`~hydms.surrogate.selection.select_across_folds`
    is the protocol shape; ``python -m hydms.surrogate.select`` is the runnable entry point.

``comparison.py``
    What the corrected selection changed, against the published 22 -- card #25's write-up,
    generated from the tables a slow-lane run left on disk rather than by fitting anything.
    :meth:`~hydms.surrogate.comparison.Comparison.read` assembles it and
    ``python -m hydms.surrogate.select --emit-comparison`` publishes it.

``validation.py``
    The project's only fold generator, and the nested protocol every score is produced
    through. Folds group on the canonical composition (leak L7) and the reported score comes
    from an outer fold the hyperparameter search never saw (leak L4), recorded as a
    :class:`~hydms.qa.detectors.SelectionRecord` per model compared.
"""

from .comparison import (
    Comparison,
    ComparisonError,
    Placeholder,
    placeholder_exposure,
    row_cost,
)
from .scaler import (
    QUANTILE_RANGE,
    SCALER_PAYLOAD,
    FittedScaler,
    ScalerError,
    fit_scaler,
    scaler_from,
)
from .selection import (
    SENTINEL_BUDGET,
    STAGE_NAMES,
    FoldSelection,
    Selection,
    SelectionError,
    SelectionSettings,
    Stage,
    select_across_folds,
    select_features,
    selected_names,
    sentinel_settings,
)
from .validation import (
    HELD_OUT_SPLITS,
    OUTER_FOLDS,
    Contender,
    Evaluation,
    Fold,
    FoldSet,
    FoldSpace,
    ScoringTask,
    TuningTask,
    ValidationError,
    grouped_folds,
    leave_one_class_out,
    nested_scores,
)

__all__ = [
    "HELD_OUT_SPLITS",
    "OUTER_FOLDS",
    "QUANTILE_RANGE",
    "SCALER_PAYLOAD",
    "SENTINEL_BUDGET",
    "STAGE_NAMES",
    "Comparison",
    "ComparisonError",
    "Contender",
    "Evaluation",
    "FittedScaler",
    "Fold",
    "FoldSelection",
    "FoldSet",
    "FoldSpace",
    "Placeholder",
    "ScalerError",
    "ScoringTask",
    "Selection",
    "SelectionError",
    "SelectionSettings",
    "Stage",
    "TuningTask",
    "ValidationError",
    "fit_scaler",
    "grouped_folds",
    "leave_one_class_out",
    "nested_scores",
    "placeholder_exposure",
    "row_cost",
    "scaler_from",
    "select_across_folds",
    "select_features",
    "selected_names",
    "sentinel_settings",
]
