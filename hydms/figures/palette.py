"""L6 -- the two themes every chart in this project is drawn in, and why these hexes.

A palette is the one part of a chart that is **computable rather than tasteful**, so it is
computed: the values below were chosen by running the `dataviz` skill's validator, not by
eye, and the numbers it reported are recorded here as constants a test pins.

**The command that produced them**, run 2026-09-12 against the reference ramps::

    node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a" --mode light --pairs all
    node scripts/validate_palette.js "#3987e5,#d95926,#199e70" --mode dark  --pairs all

Both reported ``ALL CHECKS PASS``. The reported separations are :data:`CVD_SEPARATION` and
:data:`NORMAL_SEPARATION`; the light surface raised one ``WARN``, recorded as
:data:`NEEDS_RELIEF`.

**Why three slots and not eight.** The reference palette's full eight clear the *adjacent*
pairlist only. Charts in this project are scatter and dot plots -- forms where any two series
can land beside each other -- so the **all-pairs** list governs, and only the first three
slots clear it in both modes. That is not a limitation to work around: a chart here never
carries more than two entities (a candidate and the evidence it is read against), and a third
is the outer bound, not the target. Past three the answer is a facet, which :class:`Figure`
already has.

**What a test can and cannot check here.** ``tests/test_figures.py`` pins every hex and every
recorded number. That cannot tell anyone the palette is safe -- the simulation that decides
that lives in the validator, in another language, outside this repository. What it does is
make any change to a hex or a claim fail, which forces the command above to be re-run rather
than the number re-typed. The check is real; its subject is drift, not colour science.

Card #81.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

__all__ = [
    "CVD_SEPARATION",
    "DARK",
    "LIGHT",
    "NEEDS_RELIEF",
    "NORMAL_SEPARATION",
    "SLOTS",
    "STATUS",
    "THEMES",
    "Theme",
    "theme",
]

#: How many categorical slots a panel may draw from. See the module docstring: three is what
#: clears the all-pairs gate in both modes, and it is an upper bound rather than a budget.
SLOTS = 3

#: Worst all-pairs CVD separation the validator reported, OKLab x100, deutan. The gate is 8.
CVD_SEPARATION: Mapping[str, float] = {"light": 9.2, "dark": 9.4}

#: Worst all-pairs normal-vision separation the validator reported. The hard floor is 15.
NORMAL_SEPARATION: Mapping[str, float] = {"light": 24.0, "dark": 20.9}

#: Slots whose contrast against their own surface falls below 3:1, by theme name. The skill's
#: **relief rule** applies to these and is not dismissable: wherever one is used it carries a
#: visible direct label, so the mark is never the only thing identifying the series.
#: :meth:`Theme.relief_required` is what a panel asks, and :class:`~hydms.figures.charts.Panel`
#: enforces the answer.
NEEDS_RELIEF: Mapping[str, tuple[int, ...]] = {"light": (3,), "dark": ()}

#: The four status roles, fixed across both themes and never themed. They are deliberately not
#: categorical slots: a status colour must never impersonate a series. Every one of them
#: reaches a chart as a colour **and** a label -- :class:`~hydms.figures.charts.Marker` refuses
#: a blank one -- because two of the four sit below 3:1 on the light surface by design and the
#: label is the mitigation.
STATUS: Mapping[str, str] = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

#: What a marker that carries no judgement is drawn in -- a measured bound, not a warning.
NEUTRAL = "neutral"


class PaletteError(ValueError):
    """A theme was asked for something it does not have.

    A ``ValueError``, like every other layer guard in this project.
    """


@dataclass(frozen=True)
class Theme:
    """One mode's complete drawing vocabulary: surface, ink, grid, series, status.

    Dark is **selected**, not derived. The three series hexes below are the same three hues
    re-stepped for the dark surface and validated as their own set; flipping the light values
    programmatically is the thing this dataclass exists to make impossible, because an
    automatic flip passes no gate at all.

    Attributes:
        name: ``'light'`` or ``'dark'``.
        surface: The chart surface the validator measured contrast against.
        plane: The page behind the surface.
        ink: Primary text.
        ink_secondary: Captions and notes.
        muted: Axis labels and tick text.
        grid: The hairline grid.
        axis: The baseline and axis rules.
        series: The categorical slots, in fixed order. Slot *n* is ``series[n - 1]``; they are
            assigned in order and never cycled.
        band: Opacity a prediction band is filled at. One number, here, so a wide band cannot
            be made to look narrow by a page choosing its own.
    """

    name: str
    surface: str
    plane: str
    ink: str
    ink_secondary: str
    muted: str
    grid: str
    axis: str
    series: tuple[str, ...]
    band: float = 0.18

    def __post_init__(self) -> None:
        if len(self.series) != SLOTS:
            raise PaletteError(
                f"theme {self.name!r} carries {len(self.series)} series slot(s); the "
                f"validated set is {SLOTS}. A slot nobody validated is a slot nobody "
                f"measured against the others."
            )
        if not 0.0 < self.band < 1.0:
            raise PaletteError(
                f"theme {self.name!r} fills bands at {self.band}; that is an opacity and lies "
                f"strictly between 0 and 1. At 0 the interval is invisible, which is the one "
                f"thing every chart here exists to prevent."
            )

    def slot(self, number: int) -> str:
        """The hex for categorical slot ``number``, counting from 1.

        Raises:
            PaletteError: outside ``1..SLOTS``. Loud rather than wrapping: a fourth series
                folded back onto slot 1 is two entities in one colour, and nothing downstream
                could tell.
        """
        if not isinstance(number, int) or isinstance(number, bool):
            raise PaletteError(f"a slot is numbered by an int, not {type(number).__name__}.")
        if not 1 <= number <= SLOTS:
            raise PaletteError(
                f"slot {number} does not exist; this palette validated {SLOTS}. A fourth "
                f"entity is a facet or an 'other', never a generated hue."
            )
        return self.series[number - 1]

    def status(self, role: str) -> str:
        """The hex for a status role, or the muted ink for :data:`NEUTRAL`."""
        if role == NEUTRAL:
            return self.muted
        try:
            return STATUS[role]
        except KeyError:
            raise PaletteError(
                f"{role!r} is not a status role; they are "
                f"{', '.join(sorted(STATUS))} and {NEUTRAL!r}. A series colour standing in "
                f"for a status is exactly the impersonation the reserved palette prevents."
            ) from None

    def relief_required(self, number: int) -> bool:
        """Whether slot ``number`` must carry a visible direct label in this theme.

        True where the slot's contrast against :attr:`surface` is below 3:1. The validator
        decides this, not the caller; :data:`NEEDS_RELIEF` records what it decided.
        """
        return number in NEEDS_RELIEF[self.name]


LIGHT = Theme(
    name="light",
    surface="#fcfcfb",
    plane="#f9f9f7",
    ink="#0b0b0b",
    ink_secondary="#52514e",
    muted="#898781",
    grid="#e1e0d9",
    axis="#c3c2b7",
    series=("#2a78d6", "#eb6834", "#1baf7a"),
)

DARK = Theme(
    name="dark",
    surface="#1a1a19",
    plane="#0d0d0d",
    ink="#ffffff",
    ink_secondary="#c3c2b7",
    muted="#898781",
    grid="#2c2c2a",
    axis="#383835",
    series=("#3987e5", "#d95926", "#199e70"),
)

#: Both themes by name. Every chart is drawn from one of these two and nothing else.
THEMES: Mapping[str, Theme] = {LIGHT.name: LIGHT, DARK.name: DARK}


def theme(name: str = "light") -> Theme:
    """The theme called ``name``.

    Raises:
        PaletteError: for any other name. There is no automatic third mode: a theme that was
            not stepped for its own surface and validated against it is not a theme.
    """
    try:
        return THEMES[name]
    except KeyError:
        raise PaletteError(
            f"there is no {name!r} theme; this project draws in "
            f"{' and '.join(sorted(THEMES))}. Each was stepped for its own surface and "
            f"validated against it, so a third mode is a validator run, not a lookup."
        ) from None
