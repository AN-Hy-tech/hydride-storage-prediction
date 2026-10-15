"""L4 -- the simplest admissibility rule there is: a number inside a closed interval.

A window is where the screen contract earns its keep at the smallest possible scale, and it
is the shape ``docs/QA-PROTOCOL.md`` names for this layer -- *boundary cases on each window
are covered, both sides*. #48's applicability-domain ceiling and #49's novelty distance are
the same idea with a harder threshold behind them; this module is the one where the
threshold is already known and the whole card is the verdict.

Three decisions worth stating rather than reading out of the arithmetic:

**The interval is closed.** 195 K and 773 K are measured rows of ``hydride_data.csv``, not
theoretical limits, so a candidate sitting exactly on one of them is inside the range the
model was trained on. A half-open window would refuse a real training temperature.

**A value it cannot read is a rejection, not a pass.** A missing or non-finite value gets
:data:`~hydms.screens.protocol.INDETERMINATE` and ``passed=False``. A guard rail that cannot
evaluate a candidate must not admit it -- the failure mode of the other choice is a
candidate reaching the shortlist *because* the rule meant to stop it broke.

*Which door reaches that sentence, decided on card #77.*
:class:`~hydms.delivery.contract.PredictionRequest` runs ``temperature_k`` through a finite
check and raises, so **no single prediction can produce this code**: a caller cannot express
the question. That is deliberate and it is structural rather than preferred -- a
:class:`~hydms.delivery.contract.Refusal` carries the request it declines, so an input that
cannot build a request cannot be carried by the refusal describing it, and the transport
answers 422 instead (#78). The sentence is still reachable, through the other door: a curated
frame with a missing value in this column -- the training data, #84's uploaded CSV -- gets it
verbatim. So it is not dead vocabulary, and ``docs/REFUSALS.md`` names the door per row rather
than leaving a reader to assume the one they came in by. Gate HG-2 measures both doors and
requires their union to be the declared vocabulary exactly.

**A missing column raises instead.** That is not a fact about one candidate, it is the wrong
frame: refusing every row with an identical reason would report a caller's mistake as a
property of the candidates.

**The temperature window is an outer bound and nothing more.** It says a candidate is not
being asked about at 1200 K. It does *not* say the model is trustworthy at 760 K: coverage
inside the range is badly uneven -- only 130 of 893 out-of-fold rows sit above 500 K, as
:class:`~hydms.figures.TemperatureSupport` measures them -- which is exactly why
the learned applicability domain (#48) exists and why this screen must never be quoted as
one. ``hydms/config/pipeline.yaml`` says the same thing where the two numbers are set.

Card #44.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from hydms.config import Config
from hydms.config import load as load_config
from hydms.screens.protocol import (
    ADMITTED,
    INDETERMINATE,
    ScreenError,
    verdict_table,
)

__all__ = ["OUTSIDE_WINDOW", "Window", "temperature_window"]

#: The candidate's value is a number and it is outside the interval. Distinct from
#: :data:`~hydms.screens.protocol.INDETERMINATE`, which is "there was no number to compare".
OUTSIDE_WINDOW = "outside-window"


def _number(value: float) -> str:
    """A bound or a value as it should read in a sentence: 773, not 773.0; 313.5 stays."""
    return f"{value:g}"


@dataclass(frozen=True)
class Window:
    """Admit a candidate when ``column`` lies within ``[low, high]``.

    Attributes:
        name: The screen's name, and the prefix of its columns in the verdict table.
        column: The candidate column to read. Named rather than assumed, so the caller's
            spelling -- ``temperature(K)`` comes from the raw file and carries its unit in
            its name -- stays in config instead of being repeated here.
        low: Inclusive lower bound.
        high: Inclusive upper bound.
        units: For the reason strings only. ``"K"``.
        quantity: What the interval *is*, as a noun phrase for the reason strings: "the
            trained temperature range". A reason that reads as a sentence is the deliverable
            of this layer, not a nicety.
    """

    name: str
    column: str
    low: float
    high: float
    units: str = ""
    quantity: str = "window"

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.column.strip():
            raise ScreenError("a window needs a name and a column to read.")
        if not np.isfinite(self.low) or not np.isfinite(self.high):
            raise ScreenError(
                f"window {self.name!r} has non-finite bounds ({self.low}, {self.high}); a "
                f"bound that is not a number cannot reject anything."
            )
        if self.low > self.high:
            raise ScreenError(
                f"window {self.name!r} is empty: low={self.low} is above high={self.high}. "
                f"It would refuse every candidate, and the reason would say the opposite of "
                f"what happened."
            )

    @property
    def reasons(self) -> tuple[str, ...]:
        """Two codes: outside the interval, and no number to compare."""
        return (OUTSIDE_WINDOW, INDETERMINATE)

    @property
    def span(self) -> str:
        """The interval as it appears in every reason this screen writes."""
        units = f" {self.units}" if self.units else ""
        return f"{self.quantity} {_number(self.low)}-{_number(self.high)}{units}"

    def verdict(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """A verdict per candidate: inside, outside, or unreadable.

        Raises:
            ScreenError: if ``column`` is absent from the frame or is not numeric. Both are
                statements about the batch rather than about any candidate in it.
        """
        if self.column not in candidates.columns:
            raise ScreenError(
                f"window {self.name!r} reads {self.column!r}, which the candidates do not "
                f"have. They have: {', '.join(map(repr, candidates.columns))}."
            )
        column = candidates[self.column]
        if not pd.api.types.is_numeric_dtype(column) or pd.api.types.is_bool_dtype(column):
            raise ScreenError(
                f"window {self.name!r} reads {self.column!r}, which is {column.dtype}. A "
                f"window compares numbers; coerce the column before screening rather than "
                f"letting a comparison decide what a string means."
            )

        values = column.to_numpy(dtype="float64", copy=True, na_value=np.nan)
        readable = np.isfinite(values)
        inside = readable & (values >= self.low) & (values <= self.high)

        # Only the rejected rows get per-row text. Formatting one string per candidate is the
        # expensive part of a large batch, and every admitted row says the same thing anyway.
        reason = pd.Series(f"inside {self.span}", index=candidates.index, dtype=object)
        outside = readable & ~inside
        if outside.any():
            reason.loc[outside] = [
                f"{self.column} = {_number(value)}"
                f"{' ' + self.units if self.units else ''} is "
                f"{'below' if value < self.low else 'above'} {self.span}"
                for value in values[outside]
            ]
        if not readable.all():
            reason.loc[~readable] = (
                f"{self.column} is missing or not a finite number, so {self.span} could not "
                f"be applied -- and a rule that could not run does not admit"
            )

        code = np.where(inside, ADMITTED, np.where(readable, OUTSIDE_WINDOW, INDETERMINATE))
        return verdict_table(inside, code, reason, index=candidates.index)


def temperature_window(cfg: Config | None = None) -> Window:
    """The trained temperature range, from config -- the outer bound of the refusal path.

    195-773 K is the measured span of ``temperature(K)`` across all 1,279 rows. Both bounds
    and the column name come from ``hydms/config/pipeline.yaml``, so tightening the range is
    a config change and not a code change (the same property #48's ceiling is required to
    have).

    This is the *outer* bound. See the module docstring: uniform coverage inside it is not
    claimed and must not be inferred.
    """
    config = cfg if cfg is not None else load_config()
    return Window(
        name="temperature",
        column=config.columns.temperature,
        low=config.domain.temperature_min_k,
        high=config.domain.temperature_max_k,
        units="K",
        quantity="the trained temperature range",
    )
