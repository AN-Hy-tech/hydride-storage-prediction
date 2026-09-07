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

``domain.py``
    The applicability-domain ceiling -- and the finding that it is not a chemical distance.
    Per-class transfer does not correlate with how isolated a family is, so the ceiling is a
    **capacity** level: the highest weight percent more than one alloy class reaches in
    training. Four signals, five rejection codes, and the physical ceiling of a composition
    as arithmetic rather than as a fit.

``novelty.py``
    Element Mover's Distance to the nearest known alloy, and the alloy it is a distance to.
    AC-7's reporting obligation: the number rides on every verdict, admitted or not. Its
    ceiling is the corpus's own widest internal gap, computed rather than chosen, and it is
    **novelty evidence and never the applicability domain** -- #48 measured that a composition
    distance does not explain where the model fails to transfer.

The filtering is never done here. :meth:`~hydms.screens.protocol.Verdicts.select` is how a
caller asks for the shortlist, afterwards and explicitly, and #48's ceiling and #49's
distance join the table as further screens rather than as further filters.

Card #44.
"""

# `domain` and `novelty` are deliberately NOT imported below. Both are runnable entry points
# -- `python -m hydms.screens.domain --emit` and `python -m hydms.screens.novelty --emit`
# re-measure their committed references -- and `-m` on a module the package `__init__` has
# already imported executes it twice, once under its own name and once as `__main__`, which
# Python warns about. `hydms/surrogate/__init__.py` makes the same exclusion for `evaluate`
# for the same reason. `novelty` has a second reason: it reaches ElMD, which is the optional
# `novelty` extra, so importing `hydms.screens` must not require it. Reach for them as
# `from hydms.screens.domain import applicability_domain` and
# `from hydms.screens.novelty import novelty_screen`.

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
