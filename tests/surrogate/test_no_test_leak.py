"""The test split is named by every fit and read by none of them -- leaks L1 and L5.

``Catboostmodel.py:604-606``::

    combined_pool = Pool(combined_X_scaled, combined_y, weight=weights_combined)
    test_pool = Pool(X_test_scaled, y_test)
    final_model.fit(combined_pool, eval_set=test_pool, early_stopping_rounds=5000)

and then ``:684-686`` reports that same pool as held out, under a plot legend reading "Test
RMSE" at ``:612``. ``:576-582`` is the same arrangement inside every cross-validation fold.

The card asks for "a test asserting the test split is never referenced during training", and
there are two ways to assert it that are worth having side by side.

**By identity.** Every fit declares the rows it will be scored against, and
:func:`~hydms.qa.detectors.assert_early_stopping_is_honest` compares that declaration to the
eval set before a tree is grown. That is what makes the archival call unwritable rather than
merely discouraged, and most of this file checks it.

**By value.** Identity checks catch a fit that names the wrong rows. They do not catch a fit
that reads the right rows for the wrong reason -- a stray ``to_model_space(frame[target])``
over the whole frame on the way past. So the fits below are handed a frame whose scored rows
are **NaN in every column a fit could read**, and are expected to succeed. A fit that so much
as transformed the target of a row it does not own would raise instead.

Card #26's runnable check::

    python -m hydms.surrogate.train --target capacity
    python -m pytest tests/surrogate/test_no_test_leak.py -q
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")
pytest.importorskip("catboost", reason="the model being fitted is CatBoost's")

import pandas as pd  # noqa: E402
from hydms.qa import LeakDetected  # noqa: E402
from hydms.surrogate.model import (  # noqa: E402
    ModelError,
    ModelSettings,
    final_fit,
    fit_quantile_model,
)

TARGET = "H2_W% (max)"
TEMPERATURE = "temperature(K)"
FORMULA = "Composition"

#: Twenty iterations of a three-deep tree. Nothing here is a claim about the model; every
#: assertion in this file is about which rows a fit touched.
CHEAP = {"iterations": 20, "depth": 3, "learning_rate": 0.3}


def _settings(**overrides: object) -> ModelSettings:
    return ModelSettings(
        quantiles=(0.1, 0.5, 0.9),
        early_stopping_rounds=5,
        optuna_trials=1,
        stopping_folds=5,
        seed=42,
        features=("avg_atomic_mass", TEMPERATURE),
        screen_labels=False,
        target=TARGET,
        temperature=TEMPERATURE,
        **overrides,  # type: ignore[arg-type]
    )


def _frame(rows: int = 60, *, poison: list[str] | None = None) -> pd.DataFrame:
    """A small record-and-matrix frame, optionally with some rows made unreadable.

    ``poison`` names labels whose every numeric column becomes ``NaN``. A fit that owns none
    of them must not notice: ``to_model_space`` refuses a NaN by design
    (``hydms.data.target``), so a fit that transformed the whole frame's target would raise
    ``TargetError`` and this file would go red.
    """
    rng = np.random.default_rng(0)
    labels = [f"row-{i}" for i in range(rows)]
    mass = rng.uniform(20.0, 140.0, size=rows)
    frame = pd.DataFrame(
        {
            FORMULA: [f"La1Ni{i % 7 + 1}" for i in range(rows)],
            TEMPERATURE: rng.uniform(250.0, 600.0, size=rows),
            "avg_atomic_mass": mass,
            TARGET: 0.02 * mass + rng.normal(scale=0.2, size=rows) + 1.0,
        },
        index=labels,
    )
    for label in poison or ():
        frame.loc[label, [TEMPERATURE, "avg_atomic_mass", TARGET]] = np.nan
    return frame


# --------------------------------------------------------------------------------------
# By identity
# --------------------------------------------------------------------------------------


def test_the_archival_call_raises_before_a_tree_is_grown() -> None:
    """`eval_set=test_pool`, reintroduced against the real fit. This is the demonstration."""
    frame = _frame()
    scored = list(frame.index[40:])
    with pytest.raises(LeakDetected) as exc:
        fit_quantile_model(
            frame,
            train=list(frame.index[:40]),
            eval_on=scored,
            scored_on=scored,
            where="final fit",
            params=CHEAP,
            settings=_settings(),
        )
    assert "leaks L1 and L5" in str(exc.value)
    assert "20 of 20 scored rows" in str(exc.value)


def test_a_single_shared_row_is_still_a_leak() -> None:
    """Half the test set is not half a leak; the whole validation split or nothing."""
    frame = _frame()
    scored = list(frame.index[45:])
    with pytest.raises(LeakDetected, match="1 of 15 scored rows"):
        fit_quantile_model(
            frame,
            train=list(frame.index[:40]),
            eval_on=[*frame.index[40:45], scored[0]],
            scored_on=scored,
            where="outer-0",
            params=CHEAP,
            settings=_settings(),
        )


def test_an_empty_eval_set_raises_here_rather_than_inside_catboost() -> None:
    """CatBoost refuses this at fit time; the point is that it refuses here first.

    The library's own message is `To employ param {'use_best_model': True} provide non-empty
    'eval_set'` -- verified against catboost 1.2.8 -- which arrives after the pools are built.
    This one arrives before anything is read, and says which leak it is.
    """
    frame = _frame()
    with pytest.raises(LeakDetected, match="empty eval_set"):
        fit_quantile_model(
            frame,
            train=list(frame.index[:40]),
            eval_on=[],
            scored_on=list(frame.index[40:]),
            where="final fit",
            params=CHEAP,
            settings=_settings(),
        )


def test_fitting_on_the_scored_rows_is_refused_as_a_caller_error() -> None:
    """Cruder than L1, and not L1: a `ModelError`, so a raised `LeakDetected` always means L1."""
    frame = _frame()
    with pytest.raises(ModelError, match="also being fitted on"):
        fit_quantile_model(
            frame,
            train=list(frame.index[:50]),
            eval_on=list(frame.index[55:]),
            scored_on=list(frame.index[45:55]),
            where="outer-0",
            params=CHEAP,
            settings=_settings(),
        )


def test_growing_on_the_eval_set_is_refused_too() -> None:
    """Early stopping that watches rows the trees are growing on never fires.

    Not in the leak inventory, and refused anyway: a fit like this reports a validation loss
    that falls monotonically, keeps its last iteration, and reads afterwards as a model that
    happened not to overfit. It is the failure that makes an honest eval set look unnecessary.
    """
    frame = _frame()
    with pytest.raises(ModelError, match="both fitted on and in the eval set"):
        fit_quantile_model(
            frame,
            train=list(frame.index[:50]),
            eval_on=list(frame.index[45:50]),
            scored_on=list(frame.index[50:]),
            where="outer-0",
            params=CHEAP,
            settings=_settings(),
        )


def test_an_honest_fit_records_the_three_row_sets_it_was_given() -> None:
    """The record is what the L1 and L5 sentinels read, so it must be the rows, exactly."""
    frame = _frame()
    train, evaluate, scored = (
        list(frame.index[:40]),
        list(frame.index[40:50]),
        list(frame.index[50:]),
    )
    model = fit_quantile_model(
        frame,
        train=train,
        eval_on=evaluate,
        scored_on=scored,
        where="outer-0",
        params=CHEAP,
        settings=_settings(),
    )
    assert list(model.record.fitted) == train
    assert list(model.record.eval_on) == evaluate
    assert list(model.record.scored_on) == scored
    assert not set(model.record.eval_on) & set(model.record.scored_on)


# --------------------------------------------------------------------------------------
# By value
# --------------------------------------------------------------------------------------


def test_a_fit_succeeds_when_every_scored_row_is_unreadable() -> None:
    """The strongest form of "never referenced": the scored rows carry nothing readable.

    `to_model_space` refuses a NaN and names the row. So if any statement between this call
    and CatBoost transformed, scaled, weighted or even described the scored rows, this test
    raises `TargetError` rather than passing.
    """
    scored = [f"row-{i}" for i in range(50, 60)]
    frame = _frame(poison=scored)
    model = fit_quantile_model(
        frame,
        train=[f"row-{i}" for i in range(40)],
        eval_on=[f"row-{i}" for i in range(40, 50)],
        scored_on=scored,
        where="outer-0",
        params=CHEAP,
        settings=_settings(),
    )
    predicted = model.predict(frame.loc[[f"row-{i}" for i in range(40)]])
    assert np.isfinite(predicted.to_numpy()).all()


def test_the_deployed_fit_stops_on_val_and_never_reads_test() -> None:
    """`final_fit` is the L1 site, and this is the whole of what it must be true of.

    The test rows are poisoned, so the fit cannot have read them; the assertions then check
    that it named them anyway -- because a fit that quietly stopped naming the test split
    would satisfy the poison and leave nothing for the honesty check to compare against.
    """
    scored = [f"row-{i}" for i in range(48, 60)]
    frame = _frame(poison=scored)
    split = pd.Series("train", index=frame.index)
    split.loc[[f"row-{i}" for i in range(40, 48)]] = "val"
    split.loc[scored] = "test"

    model = final_fit(frame, split, params=CHEAP, settings=_settings())

    assert set(model.record.eval_on) == set(frame.index[split == "val"])
    assert set(model.record.scored_on) == set(scored)
    assert not set(model.record.fitted) & set(scored)
    assert not set(model.record.eval_on) & set(scored)


def test_the_deployed_fit_refuses_a_split_that_holds_nothing_out() -> None:
    """A split with no `val` has no honest eval set, and the failure says which split is missing."""
    frame = _frame()
    with pytest.raises(ModelError, match="'test', 'val'"):
        final_fit(frame, pd.Series("train", index=frame.index), params=CHEAP, settings=_settings())
