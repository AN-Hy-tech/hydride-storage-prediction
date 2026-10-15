"""AC-4 -- known training alloys round-trip through the screening path.

PRD section 10.4: ten known training alloys fed through the screening path reproduce the
trained model's predictions on those same rows.

It exists for two silent failures that raise no error on their own -- a refit scaler and a
reordered feature matrix. Both produce numbers, and both produce the wrong ones.

The two paths, and what makes them different objects
-----------------------------------------------------

*The training path* holds a matrix. :func:`~hydms.surrogate.model.capacity_matrix` featurised
1,279 rows once, the fit grew on a subset of them, and scoring one of those rows means handing
the model a slice of that same matrix.

*The screening path* holds a string. :func:`~hydms.surrogate.predict.predict` takes a formula
and a temperature, featurises them from scratch through the contract the artifact's fitted
names imply, and predicts. That is the path every candidate the optimiser proposes will take,
and no row of the training matrix is anywhere near it.

They must produce the same number for a row that appears in both, and nothing else in the
project checks that they do. A scaler applied on one side and not the other, or a contract that
orders its columns differently from the fit, changes the answer and raises nothing.

Comparing like with like
------------------------

The card's box, which cost a session to get right: :func:`~hydms.surrogate.predict.predict`
returns the **calibrated** band, and the training-time heads
(:meth:`~hydms.surrogate.model.QuantileModel.predict`) are raw. Scoring all three columns
against ``model.predict`` would match on the median and fail on the outer two by the
transformed correction -- every time, on a pipeline that is working. So the reference side is
built with :func:`~hydms.surrogate.conformal.calibrated_heads`, which is exactly what
``predict`` calls once it has features. The difference between the two sides is then the
featurisation and nothing else, which is the difference this gate is about.

``lcb`` and ``interval_width`` are derived columns -- a duplicate of the lower head, and a
subtraction -- so they are not part of the round trip. A gate that compared them would be
checking arithmetic it had just performed itself.

Why the tolerance is 1e-12 and not 1e-9
----------------------------------------

Both sides featurise **the same formula string at the same temperature through the same
contract**, so this is not AC-2's situation, where two independent implementations accumulate
in different element orders. Here the inputs are identical and the arithmetic is the same code,
so the heads should agree bit for bit; the tolerance exists because this project compares no
float with ``==`` (six one-ulp effects are documented in ``tests/``), not because a real
disagreement is expected. **A failure at 1e-12 here is a finding, not a rounding residue.**

Owned by card #33.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from typing import Any, Final

import numpy as np
import pandas as pd

from hydms.config import Config

from ._artifact import NoCandidate, candidate, matrix
from ._core import Gate, GateResult, Speed

__all__ = ["GATE", "ROWS", "TOLERANCE"]

#: How many known alloys to round-trip. The PRD says ten; it is here rather than in
#: ``pipeline.yaml`` for the reason :data:`hydms.gates.ac2_featuriser_parity.TOLERANCE` gives.
ROWS: Final = 10

#: The agreement required between the two paths, in weight percent. See the module docstring:
#: the two sides run the same arithmetic on the same inputs, so this is a guard against
#: float equality rather than a budget for disagreement.
TOLERANCE: Final = 1e-12

#: A failure naming every row is a failure nobody reads to the end.
_MAX_NAMED = 6


@dataclass(frozen=True)
class Disagreement:
    """One cell where the two paths differ: which row, which column, and both numbers."""

    label: Hashable
    formula: str
    column: str
    screening: float
    training: float

    @property
    def gap(self) -> float:
        return abs(self.screening - self.training)

    def __str__(self) -> str:
        return (
            f"{self.formula} (row {self.label}) {self.column}: {self.gap:.4e} -- "
            f"screening={self.screening!r}, training={self.training!r}"
        )


@dataclass(frozen=True)
class KnownAlloyRoundTrip:
    """The gate. Every number it reports is measured in this call."""

    name: str = "AC-4"
    title: str = "Known alloys round-trip through predict()"
    card: int = 33
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        try:
            scored = candidate(cfg)
        except NoCandidate as absent:
            return GateResult.skip(self.name, str(absent))

        from hydms.surrogate.conformal import calibrated_heads, conformal_from
        from hydms.surrogate.model import column_names, model_from

        surrogate = scored.surrogate
        model = model_from(scored.bundle)
        conformal = conformal_from(scored.bundle)

        frame, _ = matrix(cfg)
        chosen = _spread(frame, model.record.fitted, cfg.columns.alloy_class, ROWS)
        if not chosen:
            return GateResult.fail(
                self.name,
                f"{scored.version}'s model records {len(model.record.fitted)} fitted row(s), "
                f"none of which is in the matrix this gate rebuilt. The artifact and the data "
                f"layer disagree about which rows exist, so no round trip is possible.",
                measured="0 rows",
                threshold=f"{ROWS} rows",
            )

        rows = frame.loc[list(chosen)]
        formulas = rows[cfg.columns.formula]
        heads = list(column_names(model.quantiles))

        screening = surrogate.predict(formulas, rows[cfg.columns.temperature])[heads]
        training = calibrated_heads(model, rows, conformal=conformal)[heads]

        # One array comparison rather than a lookup per cell: `predict` returns on the caller's
        # index and `calibrated_heads` on the frame's, both in `chosen` order and both sliced to
        # `heads`, so position i,j means the same row and head on either side.
        ours = screening.to_numpy(dtype="float64")
        theirs = training.to_numpy(dtype="float64")
        gaps = np.abs(ours - theirs)
        worst = float(gaps.max()) if gaps.size else 0.0
        spelled = [str(formula) for formula in formulas]
        off = [
            Disagreement(
                label=chosen[at_row],
                formula=spelled[at_row],
                column=heads[at_head],
                screening=float(ours[at_row, at_head]),
                training=float(theirs[at_row, at_head]),
            )
            for at_row, at_head in zip(*np.nonzero(gaps > TOLERANCE), strict=True)
        ]

        classes = sorted(set(rows[cfg.columns.alloy_class].astype(str)))
        provenance = (
            f"{scored.provenance}; {len(chosen)} row(s) the model actually grew on, across "
            f"{len(classes)} alloy class(es) ({', '.join(classes)}); "
            f"{len(surrogate.feature_names)} fitted feature(s); the band is the calibrated "
            f"one on both sides, so the correction is not what is being compared."
        )

        if off:
            return GateResult.fail(
                self.name,
                f"{len(off)} of {len(chosen) * len(heads)} predictions disagree between the "
                f"screening path and the training path by more than {TOLERANCE:g} wt%:\n"
                + "\n".join(f"  {d}" for d in sorted(off, key=lambda d: -d.gap)[:_MAX_NAMED])
                + f"\n{_features(surrogate, frame, formulas, rows[cfg.columns.temperature])}"
                + f"\n{provenance}",
                measured=worst,
                threshold=TOLERANCE,
            )

        return GateResult.ok(
            self.name,
            f"all {len(chosen) * len(heads)} predictions agree between the screening path and "
            f"the training path to {worst:.4e} wt%, inside {TOLERANCE:g}. Neither a refit "
            f"scaler nor a reordered feature matrix is present: both would move the median "
            f"head and neither raises. {provenance}",
            measured=worst,
            threshold=TOLERANCE,
        )


def _spread(
    frame: pd.DataFrame,
    fitted: Sequence[Hashable],
    alloy_class: str,
    wanted: int,
) -> tuple[Hashable, ...]:
    """``wanted`` rows the model grew on, taken from as many alloy classes as possible.

    Round-robin over the classes rather than the first ten labels, because the card asks for
    ten alloys "across different alloy classes" and the matrix is ordered by the source file --
    the first ten labels would very likely be one family, and a column-order bug that only
    bites a chemistry the batch happens not to contain is exactly the bug this gate is for.

    Deterministic and unseeded: classes in sorted order, rows within a class in frame order. A
    gate that sampled would report a different set on every run and a failure nobody could
    reproduce.
    """
    present = [label for label in fitted if label in frame.index]
    if not present:
        return ()
    by_class: dict[str, list[Hashable]] = {}
    for label, name in frame.loc[present, alloy_class].astype(str).items():
        by_class.setdefault(name, []).append(label)

    picked: list[Hashable] = []
    order = sorted(by_class)
    depth = 0
    while len(picked) < wanted and any(len(by_class[name]) > depth for name in order):
        for name in order:
            if len(picked) >= wanted:
                break
            if len(by_class[name]) > depth:
                picked.append(by_class[name][depth])
        depth += 1
    return tuple(picked)


def _features(
    surrogate: Any,
    frame: pd.DataFrame,
    formulas: pd.Series,
    temperatures: pd.Series,
) -> str:
    """Per-feature values from both paths, for the card's "diagnosable" box.

    Computed only on a failure, and it is the half of the failure that says *why*. A refit
    scaler moves every column by a constant factor; a reordered matrix moves the values between
    columns while the set of them stays the same. Those two look identical in the predictions
    and completely different here.
    """
    from hydms.descriptors.contract import FeatureContract
    from hydms.descriptors.featurize import featurize

    names = list(surrogate.feature_names)
    theirs = frame.loc[formulas.index, names]
    try:
        ours = featurize(formulas, temperatures, contract=FeatureContract.from_names(names))
    except Exception as error:  # a diagnostic must not replace the failure it explains
        return f"The features could not be re-featurised for comparison: {error!r}"

    gaps = {
        name: float(
            np.max(
                np.abs(
                    ours[name].to_numpy(dtype="float64")
                    - theirs[name].to_numpy(dtype="float64")
                )
            )
        )
        for name in names
    }
    moved = sorted((g, n) for n, g in gaps.items() if g > TOLERANCE)
    if not moved:
        return (
            f"Re-featurising these formulae through the artifact's own contract reproduces the "
            f"training matrix exactly (worst column {max(gaps.values()):.4e} over "
            f"{len(names)} of them), so the contract is not what disagrees. What is left is "
            f"downstream of it: the model payload, the correction, or something the prediction "
            f"path does to its features that this comparison does not repeat."
        )
    ordering = set(np.round(ours.to_numpy(dtype="float64"), 12).ravel()) == set(
        np.round(theirs.to_numpy(dtype="float64"), 12).ravel()
    )
    return (
        f"{len(moved)} of {len(names)} feature column(s) differ between the paths, worst "
        f"first: "
        + "; ".join(f"{name} {gap:.4e}" for gap, name in sorted(moved, reverse=True)[:_MAX_NAMED])
        + (
            ". The two matrices hold the same set of values, so this is a column ORDER "
            "disagreement, not a different computation."
            if ordering
            else ". The two matrices hold different values, so this is a different "
            "computation -- a refit or misapplied transform, not a reordering."
        )
    )


GATE: Gate = KnownAlloyRoundTrip()
