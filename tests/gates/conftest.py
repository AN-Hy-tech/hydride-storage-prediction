"""Fixtures shared by the harness tests, the CLI tests and the two artifact-scoring gates.

Two things live here.

**``unwritten``** exists because of a mistake worth not repeating. Both harness files used the
literal name ``AC-2`` wherever they needed "a criterion nobody has written yet" -- so landing
card #21, the first real gate, turned four tests about *strictness* into tests about featuriser
parity, and they failed for a reason none of them was about. The registry knows which gates are
still :class:`~hydms.gates.Pending`; asking it costs nothing and the question stays the one the
test is actually asking.

**``deployed`` and ``pointed_at``** exist because gates AC-3 and AC-4 score a *trained artifact
over the real matrix*, and a synthetic one would not test them. A model fitted on invented
numbers cannot be round-tripped against
:func:`~hydms.surrogate.model.capacity_matrix`'s rows, which is the whole of AC-4's subject. So
the fixture builds the real deployed object -- the real 1,279-row matrix, the real split, the
real screen-carve-fit-calibrate sequence -- under :data:`CHEAP` hyperparameters and with
CleanLab off. What is faked is the *quality* of the fit, which is the one thing neither gate is
about: AC-4 asks whether two paths agree, AC-3 asks what a band's coverage is, and both are
questions about a model rather than about a good one.

Cards #5 (the harness), #21 (the first gate), #31 and #33 (the two that need an artifact).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from hydms.config import Config
from hydms.gates import Gate, Pending, registry

#: Eighty shallow trees at a fast learning rate. About a second, against the ~42 s a real
#: deployed fit costs -- and the tests below assert nothing about how well it predicts.
CHEAP: dict[str, Any] = {"iterations": 80, "depth": 4, "learning_rate": 0.3}


@pytest.fixture(scope="session")
def unwritten() -> tuple[Gate, ...]:
    """Every registered criterion whose check has not been written yet.

    Asserted non-empty: when the phase finishes there will be none, and these tests must
    disappear loudly -- onto a stub gate -- rather than quietly passing over nothing, which is
    the exact failure the harness they test exists to prevent.
    """
    pending = tuple(g for g in registry() if isinstance(g, Pending))
    assert pending, (
        "every registered gate is implemented -- move the harness's strictness tests onto a "
        "stub gate rather than letting them run over an empty selection"
    )
    return pending


@pytest.fixture(scope="session")
def deployed():
    """One cheap deployed fit over the real matrix: ``(cfg, settings, frame, split, fit)``.

    Session-scoped because it featurises 1,279 rows and fits a booster, and every test in the
    two gate files wants the same object. Not marked ``slow``: a test the fast lane deselects
    does not guard a gate the fast lane runs.
    """
    pytest.importorskip("catboost", reason="the deployed fit is CatBoost's")
    pytest.importorskip("mapie", reason="the band is MAPIE-calibrated; `pip install -e .[uq]`")
    from hydms.config import load
    from hydms.surrogate.deploy import deployed_fit
    from hydms.surrogate.model import ModelSettings, capacity_matrix

    cfg = load()
    # Screening off: CleanLab costs more than the fit does and drops rows for reasons neither
    # gate is asking about. The carve, which both gates *are* about, stays on.
    settings = replace(ModelSettings.from_config(cfg), screen_labels=False)
    frame, split = capacity_matrix(cfg, settings=settings)
    fit = deployed_fit(frame, split, params=CHEAP, settings=settings, config=cfg)
    return cfg, settings, frame, split, fit


@pytest.fixture
def pointed_at(tmp_path: Path):
    """A factory: save a :class:`~hydms.surrogate.deploy.DeployedFit`, get a ``Config`` for it.

    The returned configuration differs from the loaded one in exactly one field --
    ``paths.artifacts`` -- which is the only thing a gate's ``check(cfg)`` can be steered by,
    and steering it is how a test scores a version it built rather than whatever happens to sit
    in the developer's own ``artifacts/``.

    The version is written with **no gate report**, exactly as ``calibrate --save`` writes one.
    That is the state card #33's knot is about, so a fixture that wrote a green report would
    test the one situation these gates never meet.
    """

    def _point(fit: Any, cfg: Config, settings: Any, **kwargs: Any) -> Config:
        from hydms.surrogate.deploy import save_deployed

        save_deployed(fit, settings=settings, store=tmp_path, notes="test fixture", **kwargs)
        return replace(cfg, paths=replace(cfg.paths, artifacts=tmp_path))

    return _point


@pytest.fixture(autouse=True)
def _forget_loaded_surrogates():
    """The prediction path caches by ``(store, version)``; every test here writes a new store."""
    from hydms.surrogate.predict import clear_cache

    clear_cache()
    yield
    clear_cache()
