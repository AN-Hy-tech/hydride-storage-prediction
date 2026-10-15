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

``evaluate.py``
    What the model is worth, with an interval on every number and a name on every claim.
    **Imported from directly, not re-exported below** -- see the note under this docstring.
    Bootstraps over **canonical compositions** rather than rows, reports both scales, and
    labels each row with which of the two readings it is -- the out-of-fold one, a claim about
    the *procedure*, or the artifact one, a claim about *a model*. It also owns SHAP and
    partial dependence, which run on the deployed fit's training rows and never on a held-out
    split (leak L11). It fits nothing: ``python -m hydms.surrogate.evaluate`` reads the tables
    the training run left behind.

``loco.py``
    Leave-one-alloy-class-out, which is ``validation.py``'s protocol with
    :func:`~hydms.surrogate.validation.leave_one_class_out` passed as the outer cut and
    nothing else changed -- so the extrapolation number and the random-split one come from one
    scoring path rather than two that agree until they do not. What the module adds is the
    reporting layer AC-6 is really about: every class published with the support its score
    rests on, a class whose R2 is *undefined* named as such rather than dropped, and the
    random-split figure carried into the same row so neither can be published alone. A command
    only: ``python -m hydms.surrogate.loco``, about 4.7 h, with ``--budget`` to cost it first
    and ``--emit`` to rebuild the write-up from the tables.

``predict.py``
    The layer's public face, and the only thing outside it a caller should need:
    :func:`~hydms.surrogate.predict.predict` takes formulas and temperatures and returns a
    calibrated interval per candidate, with ``lcb`` as a first-class column so that no caller
    can accidentally rank on the median. Everything above -- the booster, the scaler, the
    constant -- is hidden behind it, and the version that answered is pinned and gate-checked.
"""

# `evaluate` is deliberately NOT imported below, and it is the only library module here that
# is not. It is also a runnable entry point -- `python -m hydms.surrogate.evaluate`, which is
# card #29's runnable check -- and `-m` on a module the package `__init__` has already imported
# executes it twice, once under its own name and once as `__main__`. Python warns about it:
# "found in sys.modules after import of package 'hydms.surrogate' ... this may result in
# unpredictable behaviour". `train`, `calibrate` and `select` avoid it by being commands only;
# `evaluate` is both, so the import is what gives way. Reach for it as
# `from hydms.surrogate.evaluate import ...`.
#
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
from .deploy import (
    DEPLOYED,
    DeployedFit,
    deployed_fit,
    deployed_params,
    save_deployed,
)
from .model import (
    FIXED,
    MODEL_PAYLOAD,
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
    model_from,
    quantile_metrics,
    sample_weights,
    screened_rows,
    stopping_slice,
)
from .predict import (
    INTERVAL_WIDTH,
    LOWER_BOUND,
    PredictionError,
    Surrogate,
    load_surrogate,
    predict,
    surrogate_from,
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
    "DEPLOYED",
    "FIXED",
    "HELD_OUT_SPLITS",
    "INTERVAL_WIDTH",
    "LOWER_BOUND",
    "MODEL_PAYLOAD",
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
    "DeployedFit",
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
    "PredictionError",
    "QuantileModel",
    "ScalerError",
    "ScoringTask",
    "ScreenedRows",
    "Selection",
    "SelectionError",
    "SelectionSettings",
    "Stage",
    "Surrogate",
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
    "deployed_fit",
    "deployed_params",
    "final_fit",
    "fit_conformal",
    "fit_quantile_model",
    "fit_scaler",
    "grouped_folds",
    "leave_one_class_out",
    "load_surrogate",
    "loss_function",
    "model_from",
    "nested_scores",
    "per_fold_intervals",
    "placeholder_exposure",
    "predict",
    "quantile_metrics",
    "row_cost",
    "sample_weights",
    "save_deployed",
    "scaler_from",
    "screened_rows",
    "select_across_folds",
    "select_features",
    "selected_names",
    "stopping_slice",
    "surrogate_from",
]
