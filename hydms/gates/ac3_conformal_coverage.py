"""AC-3 -- conformal interval coverage matches its nominal level.

PRD section 10.3: empirical coverage on the held-out test set is within a few points of
nominal. The nominal level is the one the *artifact's own correction* records, so this gate
cannot be made to pass by editing a configuration file after the fit.

It is the load-bearing check for risk R1: ranking uses the lower confidence bound, and a bound
whose coverage is unverified makes every ranked list downstream meaningless.

What this gate reads, and why it is allowed to
----------------------------------------------

The **test split**, which no other stage in this project touches. ``hydms.surrogate.calibrate``
deliberately reports coverage on the calibration rows only, and says so, because a command that
printed the test number beside a knob would invite the knob to be turned until it looked good --
leak L2 in new clothes. AC-3 is the one place the test split is read, it is read once, and
nothing downstream of it adjusts anything.

Three numbers, not one
----------------------

A boolean would hide the finding. The result carries:

  - **calibrated coverage**, the criterion itself;
  - **raw coverage** -- the same model's heads with the correction *not* applied, on the same
    rows. Card #26's probe measured the raw band at 64.4 % against a nominal 80 %, in every
    fold, and that gap is the entire reason card #27 exists. Reporting both here is what turns
    "the gate is green" into "the calibration bought this much, on data nobody fitted on";
  - **the binomial standard error** at this test-set size, because coverage is a mean of
    Bernoulli draws and a reader has to be able to tell a miscalibrated band from a small
    sample. At 254 test rows and a nominal 0.80 that error is about 0.025, so the tolerance
    below is two of them and no tighter tolerance would be honest at this ``n``.

The tolerance is here and not in ``pipeline.yaml``
--------------------------------------------------

Same reasoning as :data:`hydms.gates.ac2_featuriser_parity.TOLERANCE`. Every other threshold in
this project is a modelling choice a re-measurement may move; this one is the definition of the
criterion, and a gate whose bar can be widened by editing a config file is not a gate. The
*nominal level* is configuration -- ``conformal.confidence_level`` -- and it is read from the
artifact rather than the file, so that a version calibrated for an 80 % band is scored against
80 % even if the file has since been changed.

Which version it scores
-----------------------

:func:`hydms.gates._artifact.candidate` -- the promoted one when there is one, otherwise the
newest on disk, loaded with ``require_gates=False`` because this gate's own output is what
would establish them. Card #33 owns that decision and :mod:`hydms.gates._artifact` carries it.

Owned by card #31.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

from hydms.config import Config

from ._artifact import NoCandidate, candidate, matrix
from ._core import Gate, GateResult, Speed

__all__ = ["GATE", "TOLERANCE"]

#: How far measured coverage may sit from nominal. Two binomial standard errors at the size of
#: this project's test split, which is the smallest bar that does not fail on sampling noise
#: alone -- see the module docstring. "A few points" is the PRD's phrase; this is the number.
TOLERANCE: Final = 0.05

#: The split whose rows this gate scores. Named rather than spelled at the use site, because
#: reading any other one would make the criterion mean something else entirely.
HELD_OUT: Final = "test"


def _standard_error(level: float, n: int) -> float:
    """The binomial standard error of a coverage estimate over ``n`` independent rows.

    An upper bound on the precision available here, not a correction: the test rows are
    grouped by composition, so the effective sample size is a little below ``n`` and the true
    error is a little above this. Reported so that a near-miss can be read for what it is.
    """
    return math.sqrt(level * (1.0 - level) / n) if n else float("nan")


@dataclass(frozen=True)
class ConformalCoverage:
    """The gate. Every number it reports is measured in this call."""

    name: str = "AC-3"
    title: str = "Conformal coverage matches nominal"
    card: int = 31
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        try:
            scored = candidate(cfg)
        except NoCandidate as absent:
            return GateResult.skip(self.name, str(absent))

        surrogate = scored.surrogate
        nominal = surrogate.confidence_level

        frame, split = matrix(cfg)
        rows = frame.index[split == HELD_OUT]
        if not len(rows):
            return GateResult.fail(
                self.name,
                f"the split assigns no row to {HELD_OUT!r}, so this gate would have measured "
                f"coverage over nothing. It holds {sorted(split.unique())}.",
                measured="0 rows",
                threshold=f"nominal {nominal:g}",
            )

        held = frame.loc[rows]
        truth = held[cfg.columns.target].to_numpy(dtype="float64")
        calibrated = surrogate.predict(held[cfg.columns.formula], held[cfg.columns.temperature])

        lower_name, upper_name = _band(surrogate)
        measured = _coverage(truth, calibrated[lower_name], calibrated[upper_name])
        width = float((calibrated[upper_name] - calibrated[lower_name]).mean())

        raw = _raw_heads(scored.bundle, held)
        raw_coverage = _coverage(truth, raw[lower_name], raw[upper_name])
        raw_width = float((raw[upper_name] - raw[lower_name]).mean())

        gap = abs(measured - nominal)
        error = _standard_error(nominal, len(rows))
        configured = cfg.conformal.confidence_level
        drift = (
            ""
            if math.isclose(configured, nominal, rel_tol=0.0, abs_tol=1e-12)
            else (
                f"\nNote: pipeline.yaml now says conformal.confidence_level={configured:g}, "
                f"but {scored.version} was calibrated for {nominal:g} and is scored against "
                f"its own level. The file changed after the fit; re-calibrate before "
                f"promoting, or the band does not mean what the file says."
            )
        )

        evidence = (
            f"{scored.provenance}, {len(rows)} held-out row(s) in {HELD_OUT!r}. "
            f"Calibrated: coverage {measured:.4f}, mean width {width:.4f} wt%. "
            f"Raw (the same heads, correction not applied): coverage {raw_coverage:.4f}, "
            f"mean width {raw_width:.4f} wt% -- the gap card #27 exists to close, measured "
            f"here on rows nothing was fitted or calibrated on. Binomial standard error at "
            f"this n and this nominal: {error:.4f}, so the {TOLERANCE:g} tolerance is about "
            f"two of them.{drift}"
        )

        if gap > TOLERANCE:
            return GateResult.fail(
                self.name,
                f"coverage is {measured:.4f} against a nominal {nominal:g} -- off by "
                f"{gap:.4f}, more than the {TOLERANCE:g} this criterion allows. "
                f"{'Over' if measured > nominal else 'Under'}-covering: the band is "
                f"{'wider' if measured > nominal else 'narrower'} than it claims, and the "
                f"lower confidence bound every ranked list is sorted on means "
                f"{measured:.1%} where it says {nominal:.0%} (risk R1). {evidence}",
                measured=measured,
                threshold=nominal,
            )

        return GateResult.ok(
            self.name,
            f"coverage is {measured:.4f} against a nominal {nominal:g}, off by {gap:.4f} of "
            f"an allowed {TOLERANCE:g}. {evidence}",
            measured=measured,
            threshold=nominal,
        )


def _band(surrogate: object) -> tuple[str, str]:
    """The names of the outer two heads, taken from the correction that widened them.

    Not positional. ``describe()`` is the public statement of which head the calibration
    treated as lower and which as upper, and looking them up by name is what keeps a band whose
    quantiles are not in ascending order from being scored back to front -- the same rule
    :func:`hydms.surrogate.predict._with_bound_and_width` follows one layer down.
    """
    described = surrogate.describe().iloc[0]  # type: ignore[attr-defined]
    return str(described["lower_head"]), str(described["upper_head"])


def _coverage(truth: np.ndarray, lower: pd.Series, upper: pd.Series) -> float:
    """The share of observations the band contains, inclusive at both ends."""
    low = lower.to_numpy(dtype="float64")
    high = upper.to_numpy(dtype="float64")
    return float(np.mean((truth >= low) & (truth <= high)))


def _raw_heads(bundle: object, held: pd.DataFrame) -> pd.DataFrame:
    """The same model's heads in weight percent with **no** correction applied.

    Reached through the stored payload rather than through the surrogate, because the surrogate
    deliberately has no way to hand out an uncalibrated number -- that is the whole of card
    #28's information hiding, and this gate is not going to make a hole in it to fetch a
    diagnostic. What the gate certifies still comes from :meth:`Surrogate.predict`.
    """
    from hydms.surrogate.model import model_from

    return model_from(bundle).predict(held)


GATE: Gate = ConformalCoverage()
