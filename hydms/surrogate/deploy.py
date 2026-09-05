"""The deployed fit: the one model this project ships, made in one place.

**Why this module exists.** Before it, two commands each built something they called "the
deployed fit" and the two were different models. ``hydms.surrogate.train`` grew one on every
screened training row and computed SHAP and partial dependence on it;
``hydms.surrogate.calibrate`` carved a calibration slice out of those same rows first, grew a
model on the remainder, and conformalised *that*. So the committed explainability tables
described a model with no band, and the committed conformal correction belonged to a model with
no explanation. Neither object was shippable, and nothing in the code said so: the drift was
between two files, which is where information leakage always hides.

There is now one definition. :func:`deployed_fit` performs the whole sequence -- screen, carve,
fit, calibrate -- and both commands call it. A caller cannot assemble three of the four steps,
which is the same guard :func:`~hydms.surrogate.validation.nested_scores` puts around the
cross-validation protocol and for the same reason: assembling it by hand is where leak L4 came
from.

**The order is not arbitrary and cannot be rearranged.** The calibration slice is carved
*before* the trees are grown, because a conformity score computed on a row the model was fitted
on is a residual the model has already minimised -- systematically too small, and a band that
under-covers exactly where it claims not to. Card #34's box says this in one line: the carve
comes first, and :func:`~hydms.surrogate.model.final_fit` does not do it.

**What this costs, stated because it is the number people get wrong.** The carve takes one fold
of ``model.calibration_folds`` out of the screened training rows, so the deployed model grows on
about four fifths of what the cross-validation's folds were cut from. That asymmetry is real and
:func:`~hydms.surrogate.calibrate._rows_table` publishes it beside the score rather than leaving
it to be inferred from two numbers in different files. It is the price of a calibrated band and
it is not a defect.

**Nothing here promotes anything.** :func:`save_deployed` writes an artifact version with no
gate report, which :func:`hydms.artifacts.store.save` documents as the honest state for a run
that has just fitted a model: the version cannot be promoted, and
:func:`~hydms.surrogate.predict.load_surrogate` refuses it, until a gate run is recorded against
it. Card #34 owns promotion; this module owns the object being promoted.

Cards #26, #27 and #34; the seam is card #34's box on the calibration carve.
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

import pandas as pd

from hydms.config import Config
from hydms.config import load as load_config
from hydms.data.splits import SPLIT_NAMES
from hydms.descriptors.contract import SELECTED
from hydms.surrogate.conformal import (
    CONFORMAL_PAYLOAD,
    FittedConformal,
    calibration_slice,
    fit_conformal,
)
from hydms.surrogate.model import (
    MODEL_PAYLOAD,
    PARAM_PREFIX,
    FitLog,
    ModelError,
    ModelSettings,
    QuantileModel,
    fit_quantile_model,
    screened_rows,
)
from hydms.surrogate.scaler import SCALER_PAYLOAD, TRAIN, FittedScaler, fit_scaler

__all__ = [
    "CHOSEN",
    "DEPLOYED",
    "DeployedFit",
    "deployed_fit",
    "deployed_params",
    "save_deployed",
]

#: Where the deployed configuration comes from when an earlier run left one. Written by
#: ``python -m hydms.surrogate.train``; absent on a clean checkout, in which case a fit uses
#: CatBoost's own defaults and whoever asked is told so.
CHOSEN = "model-chosen.csv"

#: The fit's name, as it appears in a :class:`~hydms.surrogate.model.FitRecord` and in every
#: failure message about it. Spelled once: the leak sentinels read records back by this name,
#: and a second spelling in a second module is how "the deployed fit" came to mean two
#: different models in the first place.
DEPLOYED = "final fit"


@dataclass(frozen=True)
class DeployedFit:
    """The shippable model and everything that has to travel with it.

    Immutable, and constructed only by :func:`deployed_fit`. Holding the four objects together
    is the point: a model without its correction cannot answer a prediction (gate HG-2), and a
    correction without the model it was calibrated against is a number with no referent.

    Attributes:
        model: The fitted booster, grown on :attr:`fitting`.
        conformal: The correction calibrated on :attr:`calibration`, rows the trees never saw.
        scaler: The fitted scaling transform. CatBoost is invariant to it -- see
            :mod:`hydms.surrogate.model`'s docstring -- and it is carried anyway because the
            downstream screens are not, and card #23 exists so that nothing refits one.
        fitting: The rows the trees grew on: screened training rows, minus the carve.
        calibration: The rows the correction was estimated from.
        screened_out: The rows CleanLab dropped, kept so the accounting adds up.
    """

    model: QuantileModel
    conformal: FittedConformal
    scaler: FittedScaler
    fitting: tuple[Hashable, ...]
    calibration: tuple[Hashable, ...]
    screened_out: tuple[Hashable, ...]

    @property
    def payloads(self) -> dict[str, Any]:
        """What an artifact version stores, under the keys the readers already agree on.

        The three names are :data:`~hydms.surrogate.model.MODEL_PAYLOAD`,
        :data:`~hydms.surrogate.conformal.CONFORMAL_PAYLOAD` and
        :data:`~hydms.surrogate.scaler.SCALER_PAYLOAD` -- each declared by the module that
        reads it back, so this mapping cannot name a key nothing loads.
        """
        return {
            MODEL_PAYLOAD: self.model,
            CONFORMAL_PAYLOAD: self.conformal,
            SCALER_PAYLOAD: self.scaler,
        }


def deployed_params(
    destination: Path, out: TextIO | None = None
) -> tuple[Mapping[str, Any] | None, str]:
    """The hyperparameters the deployed fit uses, from an earlier run's table if there is one.

    Here rather than in ``hydms.surrogate.calibrate`` because this module is the one definition
    of the deployed fit, and *which configuration it is fitted at* is part of that definition.
    Gate AC-1 has to fit the same model twice and needs the same answer this reading gives, and
    a second reader in the gate would be the drift this module was created to end.

    Chosen on an inner-fold objective, never on an outer score -- the reading
    :func:`hydms.surrogate.train._deployed` makes, and the reason it is a reading rather than a
    re-selection: picking a configuration by any number visible downstream would be selecting
    on the data the calibration is about to be certified against.

    Args:
        destination: The reports directory holding :data:`CHOSEN`.
        out: Where to narrate what was found. ``None`` says nothing, which is what a gate
            wants -- it puts the provenance in its own result instead.

    Returns:
        ``(params, provenance)``. ``params`` is ``None`` when no configuration is on disk,
        which means CatBoost's own defaults; ``provenance`` says which, in one clause.
    """

    def say(message: str) -> None:
        if out is not None:
            print(message, file=out)

    table = destination / CHOSEN
    if not table.exists():
        say(
            f"no deployed configuration on disk ({table} is absent), so this fit uses "
            f"CatBoost's own defaults. That is a smoke test of the calibration path, not the "
            f"deployed band -- run `python -m hydms.surrogate.train` first for that."
        )
        return None, "catboost defaults"
    chosen = pd.read_csv(table)
    if chosen.empty or "objective" not in chosen.columns:
        say(f"{table} records no configuration; using CatBoost's defaults.")
        return None, "catboost defaults"
    best = chosen.loc[chosen["objective"].idxmin()]
    # An allow-list, not a deny-list. Every hyperparameter column carries `PARAM_PREFIX`; the
    # rest of the table is bookkeeping -- `objective`, `trials`, `pruned`, `seconds`, and a
    # `features` **count**. Selecting by "not one of these six" fed that count to
    # `CatBoostRegressor(**params)` as `features=14`, and kept the prefix on the names besides.
    params = {
        str(name)[len(PARAM_PREFIX) :]: best[name]
        for name in chosen.columns
        if str(name).startswith(PARAM_PREFIX) and pd.notna(best[name])
    }
    if not params:
        say(
            f"{table} has no {PARAM_PREFIX!r} column, so it records no hyperparameters this "
            f"command can read; using CatBoost's defaults. That table was written by a "
            f"different version of `hydms.surrogate.train` than the one installed."
        )
        return None, "catboost defaults"
    where = str(best.get("fold", "?"))
    say(
        f"deployed configuration: the one {where!r} chose, on its inner-fold objective "
        f"{float(best['objective']):.5f}"
    )
    return params, f"{CHOSEN}:{where}"


def deployed_fit(
    frame: pd.DataFrame,
    split: pd.Series,
    *,
    params: Mapping[str, Any] | None = None,
    settings: ModelSettings | None = None,
    config: Config | None = None,
    target_column: str | None = None,
    log: FitLog | None = None,
) -> DeployedFit:
    """Screen, carve, fit, calibrate -- the whole deployed fit, in one call.

    The sequence, and why each step is where it is:

    1. **Screen** the training rows (:func:`~hydms.surrogate.model.screened_rows`). Declared as
       ``train`` to the screening stage, which is what entitles it to drop rows and what stops
       it touching anything else (leaks L3 and L10).
    2. **Carve** the calibration slice out of what survived
       (:func:`~hydms.surrogate.conformal.calibration_slice`). Grouped on the canonical
       composition, so a calibration row cannot share a material with a fitting row (leak L8).
    3. **Fit** on the remainder, stopping on ``val`` and naming ``test`` as the scored split.
       ``test`` is named and not read; that is what makes
       :func:`~hydms.qa.detectors.assert_early_stopping_is_honest` able to check leak L1 at
       all.
    4. **Calibrate** on the carved rows (:func:`~hydms.surrogate.conformal.fit_conformal`),
       which checks disjointness against the fit's own record rather than against an assumption
       about which slice the fit chose.

    Args:
        frame: The whole matrix, every split -- :func:`~hydms.surrogate.model.capacity_matrix`'s
            first return. A pre-filtered training subset is the one call this refuses, like
            :func:`~hydms.surrogate.model.final_fit` and
            :func:`~hydms.surrogate.scaler.fit_scaler`.
        split: Card #13's assignment, indexed as ``frame`` is.
        params: The hyperparameters. Both callers pass what the nested run chose, read from
            ``model-chosen.csv`` on an **inner**-fold objective -- never on an outer score,
            which is what keeps choosing a configuration from being leak L2 in a new place.
        settings: Defaults to :meth:`~hydms.surrogate.model.ModelSettings.from_config`.
        config: For ``model.calibration_folds`` and ``conformal.confidence_level``. Defaults to
            the packaged configuration.
        target_column: Defaults to ``columns.target``.
        log: A :class:`~hydms.surrogate.model.FitLog` to record the fit into.

    Returns:
        A :class:`DeployedFit`.

    Raises:
        ModelError: the split does not line up with the frame, or a split is empty.
        ValidationError: too few compositions to cut the calibration slice.
        ConformalError: the calibration is not honest -- see
            :func:`~hydms.surrogate.conformal.fit_conformal`.
        LeakDetected: a composition spans the calibration rows and the fit.
    """
    cfg = config if config is not None else load_config()
    active = settings if settings is not None else ModelSettings.from_config(cfg)

    if not split.index.equals(frame.index):
        raise ModelError(
            f"the split assignment is indexed differently from the matrix: {len(split)} "
            f"label(s) against {len(frame)}. It comes from assign_splits() on this frame."
        )
    rows = {name: list(frame.index[split == name]) for name in SPLIT_NAMES}
    empty = sorted(name for name, labels in rows.items() if not labels)
    if empty:
        raise ModelError(
            f"the split assigns no row to {', '.join(map(repr, empty))}; it holds "
            f"{', '.join(map(repr, split.unique()))}. The deployed fit needs all three: it "
            f"grows on {TRAIN!r} minus the calibration carve, stops on the validation split "
            f"and is reported on the test split."
        )

    target = target_column if target_column is not None else cfg.columns.target
    kept = screened_rows(frame, rows[TRAIN], settings=active, target_column=target)
    fitting, calibrating = calibration_slice(
        frame, kept.kept, settings=active, config=cfg
    )
    model = fit_quantile_model(
        frame,
        train=fitting,
        eval_on=rows["val"],
        scored_on=rows["test"],
        where=DEPLOYED,
        params=params,
        settings=active,
        target_column=target,
        removed=kept.removed,
        log=log,
    )
    conformal = fit_conformal(
        frame, model, calibrate_on=calibrating, config=cfg, target_column=target
    )
    scaler = fit_scaler(frame[list(active.features)], split, on=TRAIN)
    return DeployedFit(
        model=model,
        conformal=conformal,
        scaler=scaler,
        fitting=tuple(fitting),
        calibration=tuple(calibrating),
        screened_out=tuple(kept.removed),
    )


def save_deployed(
    fit: DeployedFit,
    *,
    settings: ModelSettings,
    contract: Any = SELECTED,
    notes: str = "",
    version: str | None = None,
    store: Path | None = None,
) -> Any:
    """Write the deployed fit into a new artifact version, with **no gate report**.

    The version this writes is deliberately unpromotable. ``gates=None`` is what
    :func:`hydms.artifacts.store.save` documents as honest for a run that has just fitted a
    model and has not yet been certified: :func:`hydms.artifacts.store.promote` refuses it and
    :func:`~hydms.surrogate.predict.load_surrogate` refuses it, because a version whose gates
    nobody has run is a version nobody has checked.

    **This is the seam, and it is where card #33 has a knot to untie.**
    ``load_surrogate`` never relaxes the gate requirement, not even for an explicitly named
    version -- so gate AC-4 cannot reach this version through the delivery path it is meant to
    certify. Reading it back needs
    :func:`hydms.artifacts.store.load` with ``require_gates=False``, which is the door the
    store opens for exactly this case. Whether AC-4 scores the version that way, or card #34
    writes a second version carrying the gate report, is card #33's and card #34's decision and
    is written down rather than guessed at here.

    Args:
        fit: What :func:`deployed_fit` returned.
        settings: The run's settings, for the seed the manifest records.
        contract: The feature contract to record. Defaults to
            :data:`~hydms.descriptors.contract.SELECTED`, which is what a model is fitted on
            from card #26 onward -- **not** the published 22, which stays gate AC-2's parity
            set.
        notes: One line for a human reading the promotion history.
        version: Override the assigned version. Defaults to the next free ``v<N>``.
        store: The artifacts directory. Defaults to the configured ``paths.artifacts``.

    Returns:
        The :class:`~hydms.artifacts.manifest.Manifest` written beside the payloads.

    Raises:
        ArtifactError: the version already exists -- an artifact version is written once.
    """
    from hydms.artifacts.store import save

    return save(
        fit.payloads,
        contract=contract,
        seeds={"pipeline": settings.seed},
        gates=None,
        notes=notes,
        version=version,
        store=store,
    )


def rows_table(fit: DeployedFit, split: pd.Series) -> pd.DataFrame:
    """The row accounting, including the cost the carve imposes -- stated, not hidden.

    The deployed model grows on the training rows *minus* the calibration slice, while the
    cross-validation that estimated its performance fitted on folds cut from all of them. Card
    #27 requires that asymmetry reported rather than left to be inferred from two numbers in
    different files, and card #34 requires it published beside the score.
    """
    train_rows = int((split == TRAIN).sum())
    record = fit.model.record
    return pd.DataFrame(
        [
            {
                "split_train": train_rows,
                "screened_out": len(fit.screened_out),
                "calibration": len(fit.calibration),
                "grown_on": len(record.fitted),
                "stopped_on": len(record.eval_on),
                "scored_on_named": len(record.scored_on),
                "grown_on_share_of_train": (
                    len(record.fitted) / train_rows if train_rows else float("nan")
                ),
            }
        ],
        index=pd.Index([DEPLOYED], name="fit"),
    )


def explain(fit: DeployedFit, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """SHAP and partial dependence for the deployed fit, on **its own training rows**.

    Leak L11: ``benchmark_model_selection.py:1375,1383,1394`` computed both on ``X_test``, which
    is what makes ``REPORT.md`` section 6.1 a test-set artefact. The rows handed over here are
    ``model.record.fitted`` -- the rows this fit actually grew on, read off the fit's own record
    rather than re-derived from the split. Re-deriving them would give the split's training
    rows, which is **not** the same set: screening drops some and the calibration carve takes
    another fifth, and an explanation averaged over rows the model never saw is a different
    object from the one section 6.1 claims to be.

    Raises:
        EvaluationError: from :func:`~hydms.surrogate.evaluate.shap_table`.
    """
    from hydms.surrogate.evaluate import EXPLAINABILITY, pdp_table, shap_table

    rows = frame.loc[list(fit.model.record.fitted)]
    return (
        shap_table(fit.model, rows, computed_on=EXPLAINABILITY),
        pdp_table(fit.model, rows, computed_on=EXPLAINABILITY),
    )
