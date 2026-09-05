"""Which artifact version a gate scores, and how it gets hold of it.

Two gates -- AC-3 and AC-4 -- have to answer a question *about a trained model*, and both meet
the same circle at the door. :func:`~hydms.surrogate.predict.load_surrogate` refuses a version
whose gate run is unestablished, and the first thing ever recorded against a freshly-saved
version is a gate run. So a gate cannot reach the version it exists to certify through the
promoted-artifact door, and the two gates would otherwise each have grown their own way round
it.

**The way round, decided on card #33.** The bundle is loaded here with ``require_gates=False``
-- the door :mod:`hydms.artifacts.store` documents for "the card that has just written a
version and wants it back" -- and the :class:`~hydms.surrogate.predict.Surrogate` is then built
by :func:`~hydms.surrogate.predict.surrogate_from`, which is the *same code*
``load_surrogate`` runs once it holds a bundle. So the only line of the delivery path a gate
skips is the gate check whose input the gate is producing, and everything AC-4 exists to catch
-- a refit scaler, a reordered feature matrix -- is downstream of it and exercised in full.
``load_surrogate`` grew no parameter and lost no guarantee; a test in
``tests/gates/test_artifact.py`` pins that it still refuses this very version.

**Which version.** The promoted one when there is one, and otherwise the newest on disk. That
order is the one the phase actually walks: before card #34 promotes anything the only candidate
*is* the newest, and after it promotes, a gate that scored some older version would be
certifying a model nobody ships. The choice is reported in every result, because "coverage is
0.79" is not evidence until it says of what.

Cards #31 and #33.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from hydms.config import Config

__all__ = ["Candidate", "candidate", "matrix"]


@dataclass(frozen=True)
class Candidate:
    """The version a gate is scoring, loaded, with the reason it was chosen.

    Attributes:
        surrogate: The prediction path, pinned to this version.
        bundle: The loaded artifact, for a gate that needs the payloads themselves --
            AC-4 compares the delivery path against the training-time one and therefore needs
            both sides.
        promoted: Whether ``current.json`` points here. ``False`` means this version is a
            candidate for promotion and nothing more, which is what card #34's own run looks
            like and is not a defect.
    """

    surrogate: Any
    bundle: Any
    promoted: bool

    @property
    def version(self) -> str:
        return str(self.bundle.version)

    @property
    def provenance(self) -> str:
        """One clause naming what answered, for the result message."""
        return (
            f"{self.version} (promoted)"
            if self.promoted
            else f"{self.version} (the newest version on disk; nothing is promoted yet)"
        )


class NoCandidate(LookupError):
    """No artifact version is available to score. Carries the message a gate should skip with."""


def candidate(cfg: Config, *, store: Path | None = None) -> Candidate:
    """The version under certification, loaded and ready to predict from.

    Args:
        cfg: The loaded configuration -- the only thing a gate's ``check`` receives.
        store: The artifacts directory. Defaults to ``cfg.paths.artifacts``.

    Returns:
        A :class:`Candidate`.

    Raises:
        NoCandidate: the store holds no version with a manifest. A gate turns this into a
            ``SKIPPED`` carrying the message, because a criterion nobody could answer is not a
            criterion anybody established.
        GatesIncomplete: never -- the bundle is loaded with ``require_gates=False`` on purpose.
        PayloadCorrupt, ModelError, ConformalError, PredictionError: the version is on disk and
            broken, which is a red gate rather than an absent one, so these propagate and the
            harness records them as ``ERRORED``.
    """
    from hydms import artifacts
    from hydms.surrogate.predict import surrogate_from

    root = Path(store) if store is not None else cfg.paths.artifacts
    known = artifacts.versions(store=root)
    if not known:
        raise NoCandidate(
            f"no artifact version in {root}, so there is no model to score. Build and persist "
            f"the deployed fit with `python -m hydms.surrogate.calibrate --target capacity "
            f"--save` (about two minutes from reports/model/model-chosen.csv), or download "
            f"one from the slow lane. A gate over no artifact is not a pass."
        )
    pinned = artifacts.current(store=root)
    resolved = pinned if pinned is not None else known[-1]
    bundle = artifacts.load(resolved, store=root, require_gates=False)
    return Candidate(
        surrogate=surrogate_from(bundle),
        bundle=bundle,
        promoted=pinned == resolved,
    )


def matrix(cfg: Config) -> tuple[pd.DataFrame, pd.Series]:
    """The record-and-features frame and card #13's split, as the fit itself saw them.

    :func:`~hydms.surrogate.model.capacity_matrix` and nothing else, so a gate scores the rows
    the model was fitted over rather than a second assembly of them -- the duplication AC-4
    exists to catch, arriving in the checker instead of the code.
    """
    from hydms.surrogate.model import capacity_matrix

    return capacity_matrix(cfg)
