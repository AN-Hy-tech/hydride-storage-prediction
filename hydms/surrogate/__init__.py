"""L3 — model choice, the fit-once scaler, quantile regression and conformal calibration.

Emits prediction intervals, never bare point estimates: ranking downstream uses the
lower confidence bound, which is what stops the optimiser exploiting extrapolation.

``scaler.py``
    The scaling transform, and the fact that it belongs to the trained model rather than to
    the batch in front of it. :func:`~hydms.surrogate.scaler.fit_scaler` fits it on one split
    of a matrix and returns a :class:`~hydms.surrogate.scaler.FittedScaler`, which has a
    ``transform`` and no ``fit``; it is stored as the ``scaler`` payload of an artifact
    version and read back with :func:`~hydms.surrogate.scaler.scaler_from`.

``validation.py``
    The project's only fold generator, and the nested protocol every score is produced
    through. Folds group on the canonical composition (leak L7) and the reported score comes
    from an outer fold the hyperparameter search never saw (leak L4), recorded as a
    :class:`~hydms.qa.detectors.SelectionRecord` per model compared.
"""

from .scaler import (
    QUANTILE_RANGE,
    SCALER_PAYLOAD,
    FittedScaler,
    ScalerError,
    fit_scaler,
    scaler_from,
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
    "Contender",
    "Evaluation",
    "FittedScaler",
    "Fold",
    "FoldSet",
    "FoldSpace",
    "ScalerError",
    "ScoringTask",
    "TuningTask",
    "ValidationError",
    "fit_scaler",
    "grouped_folds",
    "leave_one_class_out",
    "nested_scores",
    "scaler_from",
]
