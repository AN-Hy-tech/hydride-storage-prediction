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

``conformal.py``
    What turns three raw quantile heads into an interval that means its own number. MAPIE's
    conformalized quantile regression estimates one constant on rows carved out of ``train``
    by :func:`~hydms.surrogate.conformal.calibration_slice`, and what is *stored* is that
    number rather than the calibrator -- so MAPIE is a fit-time dependency and the prediction
    path never imports it. ``python -m hydms.surrogate.calibrate`` is the runnable entry
    point.

``model.py``
    The capacity model and its quantile heads. A fit cannot be made without naming the rows
    it will be *scored* against, and that is the first thing checked (leaks L1 and L5); the
    sample weights are sliced free of the target before anything reads them (leak L12).
    :func:`~hydms.surrogate.model.capacity_contender` is this model as a contender for the
    protocol above; ``python -m hydms.surrogate.train`` is the runnable entry point.
"""

# `SENTINEL_BUDGET` and `sentinel_settings` are deliberately NOT re-exported below. Two
# modules own one each -- `selection` reduces Boruta's iterations, `model` reduces the search
# space -- and a package-level name would have to pick one of them silently. Import them from
# the module whose budget you mean.

from .comparison import (
    Comparison,
    ComparisonError,
    Placeholder,
    placeholder_exposure,
    row_cost,
)
from .conformal import (
    CONFORMAL_PAYLOAD,
    PARITY_TOLERANCE,
    SYMMETRIC,
    ConformalError,
    FittedConformal,
    calibrated_heads,
    calibration_groups,
    calibration_slice,
    compare_metrics,
    conformal_from,
    fit_conformal,
)
from .model import (
    FIXED,
    SEARCH_SPACE,
    Configuration,
    FitLog,
    FitRecord,
    Hyperparameter,
    ModelError,
    ModelSettings,
    QuantileModel,
    ScreenedRows,
    capacity_contender,
    capacity_matrix,
    column_names,
    final_fit,
    fit_quantile_model,
    loss_function,
    quantile_metrics,
    sample_weights,
    screened_rows,
    stopping_slice,
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
    STAGE_NAMES,
    FoldSelection,
    Selection,
    SelectionError,
    SelectionSettings,
    Stage,
    select_across_folds,
    select_features,
    selected_names,
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
    "CONFORMAL_PAYLOAD",
    "FIXED",
    "HELD_OUT_SPLITS",
    "OUTER_FOLDS",
    "PARITY_TOLERANCE",
    "QUANTILE_RANGE",
    "SCALER_PAYLOAD",
    "SEARCH_SPACE",
    "STAGE_NAMES",
    "SYMMETRIC",
    "Comparison",
    "ComparisonError",
    "Configuration",
    "ConformalError",
    "Contender",
    "Evaluation",
    "FitLog",
    "FitRecord",
    "FittedConformal",
    "FittedScaler",
    "Fold",
    "FoldSelection",
    "FoldSet",
    "FoldSpace",
    "Hyperparameter",
    "ModelError",
    "ModelSettings",
    "Placeholder",
    "QuantileModel",
    "ScalerError",
    "ScoringTask",
    "ScreenedRows",
    "Selection",
    "SelectionError",
    "SelectionSettings",
    "Stage",
    "TuningTask",
    "ValidationError",
    "calibrated_heads",
    "calibration_groups",
    "calibration_slice",
    "capacity_contender",
    "capacity_matrix",
    "column_names",
    "compare_metrics",
    "conformal_from",
    "final_fit",
    "fit_conformal",
    "fit_quantile_model",
    "fit_scaler",
    "grouped_folds",
    "leave_one_class_out",
    "loss_function",
    "nested_scores",
    "placeholder_exposure",
    "quantile_metrics",
    "row_cost",
    "sample_weights",
    "scaler_from",
    "screened_rows",
    "select_across_folds",
    "select_features",
    "selected_names",
    "stopping_slice",
]
