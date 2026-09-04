"""L4 — physics windows, the applicability-domain ceiling, novelty and cost.

A screen returns a verdict with a reason, never a silent drop. Admissibility is a
derived column, not a filter applied inside the evaluator.

``protocol.py``
    What a screen *is*: the :class:`~hydms.screens.protocol.Screen` protocol, the declared
    reason vocabulary, and :func:`~hydms.screens.protocol.apply_screens`, which runs every
    screen over the whole batch and assembles one verdict table. It is also the enforcement
    point — a screen that drops, adds or reorders a row, mutates the candidates, or emits a
    code it never declared is refused there, by name.

``window.py``
    The smallest real screen: a number inside a closed interval, with both boundaries
    admitted and a missing value refused.
    :func:`~hydms.screens.window.temperature_window` builds the trained-temperature bound
    from config.

The filtering is never done here. :meth:`~hydms.screens.protocol.Verdicts.select` is how a
caller asks for the shortlist, afterwards and explicitly, and #48's ceiling and #49's
distance join the table as further screens rather than as further filters.

Card #44.
"""

from .protocol import (
    ADMITTED,
    ADMITTED_COLUMN,
    INDETERMINATE,
    SEPARATOR,
    VERDICT_COLUMNS,
    Screen,
    ScreenError,
    Verdicts,
    apply_screens,
    verdict_table,
)
from .window import OUTSIDE_WINDOW, Window, temperature_window

__all__ = [
    "ADMITTED",
    "ADMITTED_COLUMN",
    "INDETERMINATE",
    "OUTSIDE_WINDOW",
    "SEPARATOR",
    "VERDICT_COLUMNS",
    "Screen",
    "ScreenError",
    "Verdicts",
    "Window",
    "apply_screens",
    "temperature_window",
    "verdict_table",
]
