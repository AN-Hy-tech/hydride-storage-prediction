"""One served deployment for the delivery tests: a real fit, promoted, over a tiny corpus.

Shared because two files stand a service up over it -- ``test_api.py`` through FastAPI's
``TestClient`` (card #78) and ``test_app.py`` over a real socket (card #82) -- and a second copy
of a fit fixture is a second fit that can drift from the first. Moved here from
``test_api.py`` unchanged.

Every import that needs the scientific stack is inside the fixture, for the reason
``tests/conftest.py`` gives: collecting this file must not fail where the environment is not
built. A module that uses ``store`` does its own ``importorskip`` first.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

TARGET = "H2_W% (max)"
FORMULA = "Composition"
QUANTILES = (0.1, 0.5, 0.9)
CHEAP = {"iterations": 80, "depth": 4, "learning_rate": 0.3}


def _alloys() -> list[str]:
    """Forty AB5-family compositions near the corpus ElMD knows. See #76's fixture."""
    out: list[str] = []
    for cobalt in (0.0, 0.5, 1.0, 1.5, 2.0):
        for cerium in (0.0, 0.1, 0.2, 0.3):
            for nickel in (4.5, 5.0):
                lanthanum = 1.0 - cerium
                terms = [f"La{lanthanum:g}"]
                if cerium:
                    terms.append(f"Ce{cerium:g}")
                terms.append(f"Ni{nickel - cobalt:g}")
                if cobalt:
                    terms.append(f"Co{cobalt:g}")
                out.append("".join(terms))
    return out


def _frame(features_named: tuple[str, ...], rows: int = 400) -> Any:
    """The fixture corpus, featurised for real. A small target keeps answers under the ceiling."""
    import numpy as np
    import pandas as pd
    from hydms.descriptors.contract import PASSTHROUGH, FeatureContract
    from hydms.descriptors.featurize import featurize

    rng = np.random.default_rng(7)
    alloys = _alloys()
    labels = pd.Index([f"row-{i}" for i in range(rows)])
    formulas = pd.Series([alloys[i % len(alloys)] for i in range(rows)], index=labels)
    kelvin = rng.uniform(250.0, 600.0, size=rows)
    features = featurize(formulas, kelvin, contract=FeatureContract.from_names(features_named))
    target = (
        0.20 * features["avg_valence_d"]
        + 0.0005 * features[PASSTHROUGH]
        + rng.normal(scale=0.08, size=rows)
        + 0.45
    )
    return features.assign(**{FORMULA: formulas, TARGET: target})


@pytest.fixture(scope="module")
def store(tmp_path_factory) -> Path:
    """One promoted, gate-recorded version -- so `load_bundle` itself is the door under test."""
    pytest.importorskip("catboost", reason="the model behind predict() is CatBoost's")
    pytest.importorskip("mapie", reason="the band is MAPIE-calibrated; `pip install -e .[uq]`")
    import pandas as pd
    from hydms import artifacts
    from hydms.descriptors.contract import PASSTHROUGH, FeatureContract
    from hydms.gates._core import GateReport, GateResult
    from hydms.surrogate.conformal import CONFORMAL_PAYLOAD, calibration_slice, fit_conformal
    from hydms.surrogate.model import MODEL_PAYLOAD, ModelSettings, fit_quantile_model
    from hydms.surrogate.scaler import SCALER_PAYLOAD, fit_scaler

    features = ("avg_valence_d", "dev_Pauling_Electronegativity", PASSTHROUGH)
    frame = _frame(features)
    settings = ModelSettings(
        quantiles=QUANTILES,
        early_stopping_rounds=5,
        optuna_trials=1,
        stopping_folds=5,
        seed=42,
        features=features,
        screen_labels=False,
        target=TARGET,
        temperature=PASSTHROUGH,
    )
    train = list(frame.index[:280])
    val = list(frame.index[280:330])
    test = list(frame.index[330:])
    fitting, calibrating = calibration_slice(frame, train, settings=settings)
    model = fit_quantile_model(
        frame,
        train=fitting,
        eval_on=val,
        scored_on=test,
        where="final fit",
        params=CHEAP,
        settings=settings,
    )
    conformal = fit_conformal(frame, model, calibrate_on=calibrating)
    split = pd.Series("train", index=frame.index)
    split.loc[val] = "val"
    split.loc[test] = "test"
    scaler = fit_scaler(frame.loc[:, list(features)], split)

    directory = tmp_path_factory.mktemp("artifacts")
    artifacts.save(
        {MODEL_PAYLOAD: model, CONFORMAL_PAYLOAD: conformal, SCALER_PAYLOAD: scaler},
        contract=FeatureContract.from_names(model.feature_names),
        gates=GateReport(
            results=tuple(
                GateResult.ok(name, "established") for name in ("AC-2", "AC-3", "AC-4")
            ),
            selection="--all",
            strict=False,
            started_at="2026-09-12T00:00:00+00:00",
            duration_s=0.0,
        ),
        store=directory,
    )
    artifacts.promote("v1", store=directory)
    return directory
