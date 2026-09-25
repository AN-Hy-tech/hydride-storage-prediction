"""L6 -- the five charts, as specifications rather than pixels.

A chart in this project is a **description** of what is drawn: axes with units, series with
their intervals, thresholds with their labels, panels locked to a shared scale. Rendering it
is :mod:`hydms.figures.render`'s job and is deliberately thin.

**Why the split.** Every promise card #81 makes is a property of the description, not of the
image: that an estimate never appears without its band, that an axis carries its unit, that
the honest panel sits at the same scale as the optimistic one, that a threshold is labelled
rather than coloured. Those are checkable by a test that imports nothing but this module --
which is the point, because the alternative is a guarantee that can only be checked where a
plotting library is installed, and the CI lane's install list decides that. A rendered figure
is then a smoke test of the drawing code, and no promise rests on it.

**Why the guards raise instead of coercing.** A chart that silently clipped a band to fit its
axis would be the exact failure this card exists to prevent -- a wide interval made to look
narrow. So :class:`Panel` refuses a series its axis cannot hold, and the builders widen the
axis instead. The axis moves; the data never does.

The five, and the false belief each one makes harder to hold:

=============================  ===============================================================
:func:`prediction_band`        that a number rendered alone is a number known to that precision
:func:`domain_strip`           that "the model answered" means "the model was asked something
                               it can answer"
:func:`temperature_sweep`      that support is uniform across the trained range
:func:`nearest_neighbours`     that a prediction far from any known alloy is evidence
:func:`parity`                 that a random-split score transfers to a new alloy family
=============================  ===============================================================

Card #81.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from hydms.delivery.contract import UNIT, PredictionResult
from hydms.figures.palette import NEUTRAL, SLOTS, STATUS
from hydms.screens.domain import DomainReference

__all__ = [
    "CATEGORICAL",
    "MEASURED",
    "PREDICTED",
    "QUANTITATIVE",
    "Axis",
    "Band",
    "Figure",
    "FigureError",
    "Marker",
    "Neighbour",
    "Panel",
    "ParityPoint",
    "Series",
    "TemperatureSupport",
    "domain_strip",
    "nearest_neighbours",
    "parity",
    "prediction_band",
    "temperature_sweep",
]

#: An axis carrying a number. It must name its unit -- card #81's last box, made structural.
QUANTITATIVE = "quantitative"

#: An axis carrying named positions. It must *not* name a unit: "this candidate" is not in
#: weight percent, and a unit there would be read as one.
CATEGORICAL = "categorical"

#: A series of observed values. It may carry an interval; it is not required to.
MEASURED = "measured"

#: A series the model produced. It **must** carry its interval, or it cannot be constructed.
PREDICTED = "predicted"

#: What a series' marks are, which is :attr:`Series.origin` and deliberately **not** called its
#: *reading*. "Reading" is already load-bearing in this project and means something else: which
#: evidence set a number was computed over -- the procedure score, the artifact score and the
#: transfer score are three readings of one model (``CONTEXT.md``, *What a number is about*), and
#: ``reports/model/evaluation-metrics.csv`` carries a column of that name. :func:`parity` uses the
#: word in *that* sense, for the protocols it draws side by side. A field here meaning
#: measured-versus-predicted would have put two senses of one word in one module.
_ORIGINS = (MEASURED, PREDICTED)
_MARKS = ("point", "dot", "line", "step", "bar", "rug")


class FigureError(ValueError):
    """A chart cannot be described, or describes something that would mislead.

    A ``ValueError``, like :class:`~hydms.delivery.contract.ContractError` and
    :class:`~hydms.screens.protocol.ScreenError`. Every raise names the field and what was
    wrong with it.
    """


def _finite(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise FigureError(f"{what} must be a number, not {type(value).__name__}.")
    number = float(value)
    if not math.isfinite(number):
        raise FigureError(
            f"{what} is {number}. A non-finite coordinate is not plottable, and a library "
            f"that drops it silently would draw a shorter series than the data holds."
        )
    return number


def _numbers(values: Iterable[object], what: str) -> tuple[float, ...]:
    return tuple(_finite(value, f"{what}[{position}]") for position, value in enumerate(values))


def _text(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FigureError(f"{what} is blank; a reader gets this string.")
    return value


def _number(value: float) -> str:
    """A quantity as it should read in a caption: 5.19, not 5.190000000000001."""
    return f"{value:g}"


# --------------------------------------------------------------------------------------
# The pieces
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Axis:
    """One axis, its bounds, and -- when it carries a number -- its unit.

    Attributes:
        label: What the axis measures, in words.
        kind: :data:`QUANTITATIVE` or :data:`CATEGORICAL`.
        unit: Required on a quantitative axis, forbidden on a categorical one.
        lower: The low bound. Derived on a categorical axis.
        upper: The high bound. Derived on a categorical axis.
        categories: The named positions, on a categorical axis only. Position *i* is at
            ``float(i)``.
        anchored: Why these bounds are fixed rather than fitted to the series, in words --
            empty when they *are* fitted. This is where "the axis may not rescale to hide a
            wide interval" is written down: a builder that anchors an axis says here what it
            anchored it to, and :func:`prediction_band` and :func:`temperature_sweep` are
            required by their own tests to have said something.
    """

    label: str
    kind: str = QUANTITATIVE
    unit: str = ""
    lower: float = 0.0
    upper: float = 1.0
    categories: tuple[str, ...] = ()
    anchored: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", _text(self.label, "an axis label"))
        if self.kind not in (QUANTITATIVE, CATEGORICAL):
            raise FigureError(
                f"an axis is {QUANTITATIVE!r} or {CATEGORICAL!r}, not {self.kind!r}."
            )
        object.__setattr__(self, "categories", tuple(self.categories))
        if self.kind == QUANTITATIVE:
            if not isinstance(self.unit, str) or not self.unit.strip():
                raise FigureError(
                    f"the {self.label!r} axis carries numbers and names no unit. Every axis "
                    f"carries its unit (card #81): a capacity axis labelled only 'capacity' "
                    f"is read in whatever unit the reader already had in mind, and this "
                    f"project's is a *material* weight percent, not a system one."
                )
            if self.categories:
                raise FigureError(
                    f"the {self.label!r} axis is quantitative and names categories; a "
                    f"position is either a number or a name."
                )
            object.__setattr__(self, "lower", _finite(self.lower, "an axis lower bound"))
            object.__setattr__(self, "upper", _finite(self.upper, "an axis upper bound"))
            if not self.upper > self.lower:
                raise FigureError(
                    f"the {self.label!r} axis spans {_number(self.lower)} to "
                    f"{_number(self.upper)}; an axis whose bounds meet or invert draws every "
                    f"value on top of every other."
                )
        else:
            if self.unit:
                raise FigureError(
                    f"the {self.label!r} axis is categorical and names the unit "
                    f"{self.unit!r}. A name has no unit, and one printed beside it would be "
                    f"read as the series'."
                )
            if not self.categories:
                raise FigureError(
                    f"the {self.label!r} axis is categorical and names no categories, so "
                    f"nothing on it has a position."
                )
            for position, name in enumerate(self.categories):
                _text(name, f"category {position}")
            object.__setattr__(self, "lower", -0.5)
            object.__setattr__(self, "upper", len(self.categories) - 0.5)
        if self.anchored and not self.anchored.strip():
            raise FigureError(f"the {self.label!r} axis claims an anchor and gives no reason.")

    @property
    def title(self) -> str:
        """The axis as it is printed: ``'capacity (wt%)'``, or just the label."""
        return f"{self.label} ({self.unit})" if self.unit else self.label

    def contains(self, value: float) -> bool:
        """Whether ``value`` lies on this axis."""
        return self.lower <= value <= self.upper


@dataclass(frozen=True)
class Band:
    """An interval per point, and the nominal level it targets.

    ``upper < lower`` is refused, matching
    :class:`~hydms.delivery.contract.Interval`: a band whose width is negative is not a band.

    **Nothing here requires the estimate to sit inside its own band, and that is deliberate.**
    A multiquantile fit can cross -- ``quantile_metrics`` measures it at 23% of rows on
    extrapolation candidates, and ``hydms/surrogate/conformal.py`` states that CQR cannot
    repair one. What the delivery layer should *say* about a crossed band is card #94's
    question. A chart that quietly re-ordered the heads to look tidy would answer it wrongly
    and invisibly, so this type draws what it was given.

    Attributes:
        lower: The lower head per point.
        upper: The upper head per point.
        level: The nominal coverage, strictly between 0 and 1. Nominal, not measured -- what
            the band is worth on held-out data is gate AC-3's to say.
    """

    lower: tuple[float, ...]
    upper: tuple[float, ...]
    level: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "lower", _numbers(self.lower, "a band's lower head"))
        object.__setattr__(self, "upper", _numbers(self.upper, "a band's upper head"))
        if len(self.lower) != len(self.upper):
            raise FigureError(
                f"a band has {len(self.lower)} lower head(s) and {len(self.upper)} upper; "
                f"they describe the same points."
            )
        if not self.lower:
            raise FigureError("a band with no points bounds nothing.")
        for position, (low, high) in enumerate(zip(self.lower, self.upper, strict=True)):
            if high < low:
                raise FigureError(
                    f"the band at point {position} runs {_number(low)} to {_number(high)}, "
                    f"so its width is negative. Quantile crossing is a real defect and it is "
                    f"counted; a band that reports it as an interval is not one."
                )
        object.__setattr__(self, "level", _finite(self.level, "a band's nominal level"))
        if not 0.0 < self.level < 1.0:
            raise FigureError(
                f"a band's nominal level is {_number(self.level)}; it is a probability and "
                f"lies strictly between 0 and 1."
            )

    @property
    def widths(self) -> tuple[float, ...]:
        """``upper - lower`` per point, computed so it cannot disagree with the heads."""
        return tuple(high - low for low, high in zip(self.lower, self.upper, strict=True))

    def __len__(self) -> int:
        return len(self.lower)


@dataclass(frozen=True)
class Series:
    """One entity's marks, and -- if the model produced them -- the interval around each.

    **A predicted series cannot be constructed without a band.** That is card #81's last box
    as a type rather than a review note, and it is the same move
    :class:`~hydms.delivery.contract.PredictionResult` makes one layer down: there is no way
    to describe a chart that shows a point estimate alone.

    Attributes:
        name: What this series is, as the legend prints it.
        origin: :data:`MEASURED` or :data:`PREDICTED` -- where the marks came from. Not called a
            *reading*: see :data:`_ORIGINS` for the word this project already spends on something
            else.
        mark: How it is drawn -- one of ``point, dot, line, step, bar, rug``.
        x: Positions on the panel's x axis. On a categorical axis these are ``0.0, 1.0, ...``.
        y: Positions on the y axis.
        slot: The categorical colour slot, ``1..SLOTS``. Colour follows the entity, so a
            panel never gives two series the same slot and a filter never repaints one.
        band: The interval per point. Required when ``reading`` is :data:`PREDICTED`.
        band_axis: Which axis the band's heads are read on -- ``'y'`` for the usual upright
            chart, ``'x'`` where the quantity runs horizontally (the strip in
            :func:`domain_strip` does). Named rather than assumed, because a band silently
            measured against the wrong axis is drawn at a plausible size and nothing looks
            wrong.
        labels: Direct labels, one per point; ``''`` for a point that carries none. A slot the
            active theme puts below 3:1 contrast must carry them -- :class:`Panel` checks.
        widths: Per-mark extent along x, for the ``bar`` mark only. Given because a histogram
            over **unequal** bins drawn with equal bars misreads its own data -- the eye reads
            area, so a 100 K bin drawn the width of a 50 K one doubles its apparent density.
            Empty means "one width, chosen by the renderer", which is right only where the
            bins are equal.
    """

    name: str
    origin: str
    mark: str
    x: tuple[float, ...]
    y: tuple[float, ...]
    slot: int = 1
    band: Band | None = None
    band_axis: str = "y"
    labels: tuple[str, ...] = ()
    widths: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "a series name"))
        if self.origin not in _ORIGINS:
            raise FigureError(
                f"series {self.name!r} has origin {self.origin!r}; it is one of "
                f"{', '.join(map(repr, _ORIGINS))}. Which one decides whether an interval is "
                f"optional, so it is not a label."
            )
        if self.mark not in _MARKS:
            raise FigureError(
                f"series {self.name!r} is drawn as {self.mark!r}; the marks are "
                f"{', '.join(map(repr, _MARKS))}."
            )
        object.__setattr__(self, "x", _numbers(self.x, f"series {self.name!r} x"))
        object.__setattr__(self, "y", _numbers(self.y, f"series {self.name!r} y"))
        if len(self.x) != len(self.y):
            raise FigureError(
                f"series {self.name!r} has {len(self.x)} x value(s) and {len(self.y)} y; "
                f"they are the same points."
            )
        if not self.x:
            raise FigureError(f"series {self.name!r} has no points.")
        if not isinstance(self.slot, int) or isinstance(self.slot, bool):
            raise FigureError(f"series {self.name!r} names slot {self.slot!r}, not an int.")
        if not 1 <= self.slot <= SLOTS:
            raise FigureError(
                f"series {self.name!r} asks for colour slot {self.slot}; the validated "
                f"palette has {SLOTS}. A fourth entity is a facet or an 'other'."
            )
        if self.origin == PREDICTED and self.band is None:
            raise FigureError(
                f"series {self.name!r} is a prediction drawn without its interval. A tree "
                f"ensemble extrapolates as a constant, so outside the training hull it "
                f"returns a plausible flat value and the band is what makes that visible "
                f"(risk R1). No chart in this project shows a point estimate alone."
            )
        if self.band is not None and len(self.band) != len(self.y):
            raise FigureError(
                f"series {self.name!r} has {len(self.y)} point(s) and a band over "
                f"{len(self.band)}; an interval belongs to the estimate it surrounds."
            )
        if self.band_axis not in ("x", "y"):
            raise FigureError(
                f"series {self.name!r} reads its band on axis {self.band_axis!r}; it is 'x' "
                f"or 'y'."
            )
        object.__setattr__(self, "labels", tuple(self.labels))
        if self.labels and len(self.labels) != len(self.y):
            raise FigureError(
                f"series {self.name!r} has {len(self.y)} point(s) and {len(self.labels)} "
                f"label(s); a direct label names one mark."
            )
        object.__setattr__(self, "widths", _numbers(self.widths, f"series {self.name!r} width"))
        if self.widths:
            if self.mark != "bar":
                raise FigureError(
                    f"series {self.name!r} is drawn as {self.mark!r} and gives per-mark "
                    f"widths; only a bar has a width to give."
                )
            if len(self.widths) != len(self.x):
                raise FigureError(
                    f"series {self.name!r} has {len(self.x)} bar(s) and {len(self.widths)} "
                    f"width(s)."
                )
            if any(width <= 0.0 for width in self.widths):
                raise FigureError(
                    f"series {self.name!r} has a bar of zero or negative width."
                )

    @property
    def labelled(self) -> bool:
        """Whether at least one point carries a visible direct label."""
        return any(text.strip() for text in self.labels)


@dataclass(frozen=True)
class Marker:
    """A threshold drawn across a panel, with the sentence that says what it is.

    ``label`` cannot be blank. A status colour never carries meaning alone -- two of the four
    sit below 3:1 on the light surface by design, and the label is the mitigation -- so the
    type refuses the version of this that would rely on hue.

    Attributes:
        label: What the line is, printed beside it.
        value: Where it sits.
        axis: ``'x'`` or ``'y'`` -- which axis ``value`` is read on.
        status: A role from :data:`~hydms.figures.palette.STATUS`, or
            :data:`~hydms.figures.palette.NEUTRAL` for a measured bound that judges nothing.
        note: An optional second sentence, for a caption or a tooltip.
    """

    label: str
    value: float
    axis: str
    status: str = NEUTRAL
    note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", _text(self.label, "a marker label"))
        object.__setattr__(self, "value", _finite(self.value, f"marker {self.label!r}"))
        if self.axis not in ("x", "y"):
            raise FigureError(
                f"marker {self.label!r} is read on axis {self.axis!r}; it is 'x' or 'y'."
            )
        if self.status != NEUTRAL and self.status not in STATUS:
            raise FigureError(
                f"marker {self.label!r} claims status {self.status!r}; the roles are "
                f"{', '.join(sorted(STATUS))} and {NEUTRAL!r}."
            )


@dataclass(frozen=True)
class Panel:
    """One set of axes and everything drawn on them.

    The guard that matters: **every value must lie on the axis that carries it.** A series or
    a marker the axis cannot hold is refused rather than clipped, so a builder that finds a
    band running past its axis widens the axis. That is the mechanism behind "a wide interval
    must *look* wide": the data sets the frame, never the other way round.

    Attributes:
        title: The panel's own heading. In a one-panel figure it may repeat the figure title.
        x: The x axis.
        y: The y axis.
        series: What is drawn, in draw order.
        markers: Thresholds across the panel.
        identity: Draw the ``y = x`` diagonal. Only meaningful where both axes carry the same
            quantity in the same unit, which is checked.
        note: One sentence under the panel.
    """

    title: str
    x: Axis
    y: Axis
    series: tuple[Series, ...]
    markers: tuple[Marker, ...] = ()
    identity: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "a panel title"))
        for axis, which in ((self.x, "x"), (self.y, "y")):
            if not isinstance(axis, Axis):
                raise FigureError(
                    f"panel {self.title!r} has {type(axis).__name__} as its {which} axis."
                )
        object.__setattr__(self, "series", tuple(self.series))
        object.__setattr__(self, "markers", tuple(self.markers))
        if not self.series:
            raise FigureError(f"panel {self.title!r} draws nothing.")

        seen: dict[int, str] = {}
        names: set[str] = set()
        for item in self.series:
            if not isinstance(item, Series):
                raise FigureError(
                    f"panel {self.title!r} carries {type(item).__name__} where a series "
                    f"belongs."
                )
            if item.slot in seen:
                raise FigureError(
                    f"panel {self.title!r} gives slot {item.slot} to both {seen[item.slot]!r} "
                    f"and {item.name!r}. Colour follows the entity, so two entities never "
                    f"share one."
                )
            seen[item.slot] = item.name
            if item.name in names:
                raise FigureError(
                    f"panel {self.title!r} draws two series called {item.name!r}; a legend "
                    f"built from these would name one of them twice."
                )
            names.add(item.name)
            self._fits(item)
        for marker in self.markers:
            if not isinstance(marker, Marker):
                raise FigureError(
                    f"panel {self.title!r} carries {type(marker).__name__} where a marker "
                    f"belongs."
                )
            axis = self.x if marker.axis == "x" else self.y
            if not axis.contains(marker.value):
                raise FigureError(
                    f"panel {self.title!r} puts marker {marker.label!r} at "
                    f"{_number(marker.value)}, off the {axis.label!r} axis "
                    f"({_number(axis.lower)} to {_number(axis.upper)}). A threshold drawn "
                    f"past the edge is a threshold the reader never sees; widen the axis."
                )
        if self.identity and (
            self.x.kind != QUANTITATIVE
            or self.y.kind != QUANTITATIVE
            or self.x.unit != self.y.unit
        ):
            raise FigureError(
                f"panel {self.title!r} asks for the y = x diagonal across "
                f"{self.x.title!r} and {self.y.title!r}. The identity line only means "
                f"something where both axes carry the same quantity in the same unit."
            )

    def _fits(self, item: Series) -> None:
        """Refuse a series the axes cannot hold, naming the first value that does not fit."""
        for axis, values, which in ((self.x, item.x, "x"), (self.y, item.y, "y")):
            for position, value in enumerate(values):
                if not axis.contains(value):
                    raise FigureError(
                        f"panel {self.title!r} draws {item.name!r} at {which}="
                        f"{_number(value)} (point {position}), off the {axis.label!r} axis "
                        f"({_number(axis.lower)} to {_number(axis.upper)}). Nothing here "
                        f"clips: widen the axis or drop the point deliberately."
                    )
        if item.band is None:
            return
        axis = self.x if item.band_axis == "x" else self.y
        for position, (low, high) in enumerate(
            zip(item.band.lower, item.band.upper, strict=True)
        ):
            for value, edge in ((low, "lower"), (high, "upper")):
                if not axis.contains(value):
                    raise FigureError(
                        f"panel {self.title!r} draws {item.name!r}'s {edge} head at "
                        f"{_number(value)} (point {position}), off the {axis.label!r} axis "
                        f"({_number(axis.lower)} to {_number(axis.upper)}). An axis that "
                        f"cuts a band is an axis that makes a wide interval look narrow."
                    )

    def relief(self, theme_name: str) -> tuple[str, ...]:
        """Series that need a direct label in this theme and do not have one.

        The skill's relief rule is not dismissable: a slot below 3:1 against its own surface
        carries visible labels or a table view. This reports which series break it; the
        figure-level test refuses any that do.
        """
        from hydms.figures.palette import theme as get_theme

        active = get_theme(theme_name)
        return tuple(
            item.name
            for item in self.series
            if active.relief_required(item.slot) and not item.labelled
        )

    @property
    def legend(self) -> bool:
        """Whether a legend box is required: always, for two or more series."""
        return len(self.series) >= 2


@dataclass(frozen=True)
class Figure:
    """One or more panels, a title, a caption, and the axes they hold in common.

    ``shared`` is the whole reason this type exists. Naming ``'y'`` there makes every panel's
    y axis **equal**, checked -- which is how "the leave-one-alloy-class-out version beside it
    at the same scale" stops being a review note. Two panels that disagree about their scale
    cannot be assembled into a figure that claims they agree.

    Attributes:
        name: A slug, for a filename and for a test to address.
        title: The heading.
        panels: The panels, left to right.
        caption: One or more sentences under the whole figure. Never blank: a chart in this
            project says in words what it is showing, because the number alone is what every
            one of these charts exists to qualify.
        shared: Axis names locked across panels -- any of ``'x'``, ``'y'``.
        layout: ``'row'`` (side by side) or ``'column'`` (stacked). A column must share
            ``'x'``: stacking is itself the claim that the panels line up, so two stacked
            panels on different x scales make that claim and it is not true. In a column the
            first panel is the subject and the ones beneath it are the evidence for it, which
            is what the renderer's height ratios say.
    """

    name: str
    title: str
    panels: tuple[Panel, ...]
    caption: str
    shared: tuple[str, ...] = field(default_factory=tuple)
    layout: str = "row"

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "a figure name"))
        object.__setattr__(self, "title", _text(self.title, "a figure title"))
        object.__setattr__(self, "caption", _text(self.caption, "a figure caption"))
        object.__setattr__(self, "panels", tuple(self.panels))
        object.__setattr__(self, "shared", tuple(self.shared))
        if not self.panels:
            raise FigureError(f"figure {self.name!r} has no panels.")
        if self.layout not in ("row", "column"):
            raise FigureError(
                f"figure {self.name!r} is laid out {self.layout!r}; it is 'row' or 'column'."
            )
        if self.layout == "column" and "x" not in self.shared:
            raise FigureError(
                f"figure {self.name!r} stacks its panels and does not share an x axis. "
                f"Stacking is itself the claim that the panels line up; a column on two x "
                f"scales makes that claim without it being true."
            )
        for panel in self.panels:
            if not isinstance(panel, Panel):
                raise FigureError(
                    f"figure {self.name!r} carries {type(panel).__name__} where a panel "
                    f"belongs."
                )
        for which in self.shared:
            if which not in ("x", "y"):
                raise FigureError(
                    f"figure {self.name!r} shares axis {which!r}; there are 'x' and 'y'."
                )
            first = getattr(self.panels[0], which)
            for panel in self.panels[1:]:
                if getattr(panel, which) != first:
                    raise FigureError(
                        f"figure {self.name!r} declares a shared {which} axis and panel "
                        f"{panel.title!r} disagrees with {self.panels[0].title!r}: "
                        f"{getattr(panel, which).title!r} "
                        f"({_number(getattr(panel, which).lower)} to "
                        f"{_number(getattr(panel, which).upper)}) against {first.title!r} "
                        f"({_number(first.lower)} to {_number(first.upper)}). Panels read "
                        f"side by side are compared by eye; a different scale in each is the "
                        f"comparison quietly withdrawn."
                    )

    def relief(self, theme_name: str) -> tuple[str, ...]:
        """Every series across every panel that breaks the relief rule in this theme."""
        return tuple(name for panel in self.panels for name in panel.relief(theme_name))


# --------------------------------------------------------------------------------------
# What the builders read
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TemperatureSupport:
    """How many training rows back each part of the temperature range -- measured, not recalled.

    The card this type serves says "only 39 test rows sit above 500 K". That number is
    :file:`REPORT.md`'s, over the archival pipeline's 247-row test split, and it does not
    describe the evidence this project now has: the committed out-of-fold table
    (``reports/model/model-out-of-fold.csv``) scores **893** rows and **130** of them sit
    above 500 K. The proportion is close -- 15.8% then, 14.6% now -- so the *claim* the card
    makes survives intact and only its number was inherited. Which is exactly why this type
    takes counts rather than carrying a constant: a chart whose thinning claim is typed in is
    a chart that keeps being right about the wrong split.

    Attributes:
        edges: Bin edges, ascending, length ``len(counts) + 1``.
        counts: Rows falling in each bin.
        source: What was counted, in words -- it is printed in the caption.
    """

    edges: tuple[float, ...]
    counts: tuple[int, ...]
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "edges", _numbers(self.edges, "a support edge"))
        object.__setattr__(self, "counts", tuple(int(count) for count in self.counts))
        object.__setattr__(self, "source", _text(self.source, "a support source"))
        if len(self.edges) != len(self.counts) + 1:
            raise FigureError(
                f"support has {len(self.edges)} edge(s) around {len(self.counts)} bin(s); a "
                f"bin is bounded on both sides."
            )
        if not self.counts:
            raise FigureError("support with no bins says nothing about coverage.")
        pairs = zip(self.edges[:-1], self.edges[1:], strict=True)
        if any(later <= earlier for earlier, later in pairs):
            raise FigureError(
                f"the support edges are not ascending: {', '.join(map(_number, self.edges))}."
            )
        if any(count < 0 for count in self.counts):
            raise FigureError("a support bin holds a non-negative number of rows.")

    @classmethod
    def measured(
        cls,
        temperatures: Sequence[float],
        *,
        edges: Sequence[float],
        source: str,
    ) -> TemperatureSupport:
        """Count ``temperatures`` into ``edges``. Bins are half-open, the last one closed."""
        bounds = _numbers(edges, "a support edge")
        values = _numbers(temperatures, "a temperature")
        counts = [0] * (len(bounds) - 1)
        for value in values:
            for position in range(len(counts)):
                low, high = bounds[position], bounds[position + 1]
                last = position == len(counts) - 1
                if low <= value < high or (last and value == high):
                    counts[position] += 1
                    break
        return cls(edges=bounds, counts=tuple(counts), source=source)

    @property
    def rows(self) -> int:
        """Every row counted."""
        return sum(self.counts)

    def above(self, temperature: float) -> int:
        """Rows in every bin whose lower edge is at or above ``temperature``.

        Bin-aligned on purpose: it reports what the drawn bars show, so the caption and the
        chart cannot disagree about the same threshold.
        """
        limit = _finite(temperature, "a support threshold")
        return sum(
            count
            for position, count in enumerate(self.counts)
            if self.edges[position] >= limit
        )

    @property
    def widths(self) -> tuple[float, ...]:
        """Each bin's extent, so unequal bins draw unequal. See :attr:`Series.widths`."""
        return tuple(
            high - low for low, high in zip(self.edges[:-1], self.edges[1:], strict=True)
        )

    @property
    def midpoints(self) -> tuple[float, ...]:
        """The centre of each bin, where its bar is drawn."""
        return tuple(
            (low + high) / 2.0
            for low, high in zip(self.edges[:-1], self.edges[1:], strict=True)
        )


@dataclass(frozen=True)
class Neighbour:
    """A training alloy near the candidate, and what was actually *measured* on it.

    ``capacity`` is a measurement, not a prediction -- that is the whole value of the chart it
    feeds -- so it is drawn as a :data:`MEASURED` series and needs no band. ``temperature_k``
    rides along because a capacity without its temperature is not comparable to one at another
    temperature, and the caption says so.
    """

    formula: str
    distance: float
    capacity: float
    temperature_k: float
    alloy_class: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "formula", _text(self.formula, "a neighbour's formula"))
        object.__setattr__(self, "distance", _finite(self.distance, "a neighbour's distance"))
        object.__setattr__(self, "capacity", _finite(self.capacity, "a neighbour's capacity"))
        object.__setattr__(
            self, "temperature_k", _finite(self.temperature_k, "a neighbour's temperature")
        )
        if self.distance < 0.0:
            raise FigureError(
                f"neighbour {self.formula!r} is at distance {_number(self.distance)}; a "
                f"distance is non-negative."
            )


@dataclass(frozen=True)
class ParityPoint:
    """One row's measurement against what the model said about it, with that row's band."""

    measured: float
    predicted: float
    lower: float
    upper: float

    def __post_init__(self) -> None:
        for name in ("measured", "predicted", "lower", "upper"):
            object.__setattr__(
                self, name, _finite(getattr(self, name), f"a parity point's {name}")
            )


# --------------------------------------------------------------------------------------
# Shared shaping
# --------------------------------------------------------------------------------------

#: How far past the data an anchored axis is padded, as a fraction of its span. Small, and the
#: same everywhere, so no chart can buy itself a flattering frame.
_PAD = 0.04


def _span(values: Sequence[float], *, pad: float = _PAD) -> tuple[float, float]:
    """A padded span that holds every value, never degenerate."""
    low, high = min(values), max(values)
    if high == low:
        reach = abs(high) * _PAD or 1.0
        return low - reach, high + reach
    reach = (high - low) * pad
    return low - reach, high + reach


def _capacity_axis(
    values: Sequence[float], *, anchored: str, floor: float = 0.0
) -> Axis:
    """The capacity axis, anchored to something wider than the series wherever it can be.

    ``floor`` pulls the bottom to zero on a ratio scale, so two candidates drawn on two
    different pages are read against the same origin; a band reaching below zero still widens
    it, because hiding that is what :class:`~hydms.delivery.contract.Interval` refuses to do
    one layer down.
    """
    low, high = _span((*values, floor))
    return Axis(
        label="capacity",
        unit=UNIT,
        lower=min(low, floor),
        upper=high,
        anchored=anchored,
    )


def _reference(reference: DomainReference | None) -> DomainReference:
    return reference if reference is not None else DomainReference.packaged()


def _verdict_sentence(result: PredictionResult) -> str:
    """The domain verdict as a caption clause -- admitted or not, always with its reason."""
    state = "admitted" if result.domain.admitted else f"refused ({result.domain.code})"
    return f"Applicability: {state} -- {result.domain.reason}."


# --------------------------------------------------------------------------------------
# 1. The prediction band
# --------------------------------------------------------------------------------------


def prediction_band(
    result: PredictionResult, *, reference: DomainReference | None = None
) -> Figure:
    """The estimate drawn inside its conformal interval, against the trained capacity range.

    The y axis is **anchored to the trained range**, not fitted to the band. That is the one
    decision the whole chart is for: an axis fitted to a band makes every band fill its panel,
    so a 0.2 wt% interval and a 3 wt% interval are drawn identically and the reader learns
    nothing. Anchored, a wide interval covers most of the frame and a narrow one does not. The
    axis widens only when the band runs past the trained range -- which is itself the signal,
    and is never hidden by clipping.

    The width is stated numerically in the caption as well as drawn, because a band is read as
    a shape and a shape is not a quantity.

    Args:
        result: The answer to draw. It carries its own interval and verdict by construction.
        reference: The measured training facts. Defaults to the committed reference.
    """
    ref = _reference(reference)
    interval = result.interval
    bounds = (interval.lower, interval.upper, ref.trained_min, ref.trained_max, result.capacity)
    y = _capacity_axis(
        bounds,
        anchored=(
            f"the trained capacity range {_number(ref.trained_min)}-"
            f"{_number(ref.trained_max)} {UNIT} over {ref.rows} rows, widened only where "
            f"this band runs past it, so a wide interval looks wide"
        ),
    )
    x = Axis(label="candidate", kind=CATEGORICAL, categories=(result.request.formula,))
    estimate = Series(
        name=f"{result.request.formula} at {_number(result.request.temperature_k)} K",
        origin=PREDICTED,
        mark="point",
        x=(0.0,),
        y=(result.capacity,),
        slot=1,
        band=Band(lower=(interval.lower,), upper=(interval.upper,), level=interval.level),
        labels=(f"{result.capacity:.2f} {UNIT}",),
    )
    markers = [
        Marker(
            label=f"highest trained capacity, {_number(ref.trained_max)} {UNIT}",
            value=ref.trained_max,
            axis="y",
            status=NEUTRAL,
            note="a gradient-boosted tree cannot predict above it",
        ),
        Marker(
            label=f"cross-family evidence ends, {_number(ref.cross_family_max)} {UNIT}",
            value=ref.cross_family_max,
            axis="y",
            status="warning",
            note=(
                f"above it the corpus holds {ref.sole_family} alone -- {ref.rows_above} of "
                f"{ref.rows} rows -- and #30 measured that family as untransferable"
            ),
        ),
    ]
    panel = Panel(
        title=f"{result.request.formula} at {_number(result.request.temperature_k)} K",
        x=x,
        y=y,
        series=(estimate,),
        markers=tuple(marker for marker in markers if y.contains(marker.value)),
        note=f"artifact {result.model_version}",
    )
    return Figure(
        name="prediction-band",
        title="Predicted capacity, inside its interval",
        panels=(panel,),
        caption=(
            f"{result.capacity:.2f} {UNIT}, in a {_number(interval.level * 100)}% nominal "
            f"band from {interval.lower:.2f} to {interval.upper:.2f} {UNIT} -- a width of "
            f"{interval.width:.2f} {UNIT}. The level is nominal, not measured coverage. "
            f"{_verdict_sentence(result)} This is a *material* weight percent and comparing "
            f"it to a DOE system target is a two-step overstatement (PRD 4.4)."
        ),
    )


# --------------------------------------------------------------------------------------
# 2. The domain strip
# --------------------------------------------------------------------------------------


def domain_strip(
    result: PredictionResult,
    *,
    training: Sequence[float],
    reference: DomainReference | None = None,
    physical_ceiling: float | None = None,
) -> Figure:
    """Where this candidate sits against the capacities the model was actually trained on.

    Two lanes on one capacity axis: every training row as a rug, and the candidate's band on
    a lane of its own. The thresholds are drawn as labelled rules -- the highest trained capacity,
    the level above which only one family has evidence, and, where it was computed, this
    composition's own physical ceiling.

    The belief it attacks is the one an answer alone cannot: that the model having *answered*
    means the question was inside what it can defend. The verdict sentence is in the caption
    and the rules are on the axis, so an answer sitting past one of them is visible rather
    than inferable.

    Args:
        result: The answer to place.
        training: Measured capacities of the training rows, for the rug.
        reference: The measured training facts. Defaults to the committed reference.
        physical_ceiling: This composition's ``wt%_max`` from
            :func:`~hydms.screens.domain.capacity_ceiling`, or ``None`` where it could not be
            computed -- an unparseable formula, an element with no mass. ``None`` is drawn as
            an absent rule and said so in the caption, never as an unbounded one.
    """
    ref = _reference(reference)
    rows = _numbers(training, "a training capacity")
    if not rows:
        raise FigureError(
            "the domain strip draws the candidate against the training distribution and was "
            "given no training rows. A strip with one mark on it says the candidate is "
            "somewhere, which is what the chart exists to improve on."
        )
    interval = result.interval
    reach = [
        *rows,
        interval.lower,
        interval.upper,
        result.capacity,
        ref.trained_min,
        ref.trained_max,
        ref.cross_family_max,
    ]
    if physical_ceiling is not None:
        reach.append(_finite(physical_ceiling, "the physical ceiling"))
    x = _capacity_axis(
        reach,
        anchored=(
            f"every one of the {len(rows)} training capacities, this candidate's band, and "
            f"every rule drawn on it -- so a candidate past a rule is drawn past it"
        ),
    )
    y = Axis(
        label="lane",
        kind=CATEGORICAL,
        categories=(f"training rows (n = {len(rows)})", "this candidate"),
    )
    rug = Series(
        name=f"training rows (n = {len(rows)})",
        origin=MEASURED,
        mark="rug",
        x=rows,
        y=(0.0,) * len(rows),
        slot=2,
    )
    candidate = Series(
        name=result.request.formula,
        origin=PREDICTED,
        mark="point",
        x=(result.capacity,),
        y=(1.0,),
        slot=1,
        band=Band(lower=(interval.lower,), upper=(interval.upper,), level=interval.level),
        band_axis="x",
        labels=(f"{result.capacity:.2f} {UNIT}",),
    )
    markers = [
        Marker(
            label=f"highest trained, {_number(ref.trained_max)} {UNIT}",
            value=ref.trained_max,
            axis="x",
            status=NEUTRAL,
        ),
        Marker(
            label=f"cross-family evidence ends, {_number(ref.cross_family_max)} {UNIT}",
            value=ref.cross_family_max,
            axis="x",
            status="warning",
            note=(
                f"{ref.rows_above} of {ref.rows} training rows sit above it and every one is "
                f"{ref.sole_family}"
            ),
        ),
    ]
    if physical_ceiling is not None:
        markers.append(
            Marker(
                label=f"physical ceiling, {float(physical_ceiling):.2f} {UNIT}",
                value=float(physical_ceiling),
                axis="x",
                status="serious",
                note="the richest binary hydride stoichiometry this composition could reach",
            )
        )
    ceiling_clause = (
        f"Its own physical ceiling is {float(physical_ceiling):.2f} {UNIT}."
        if physical_ceiling is not None
        else "Its physical ceiling could not be computed from the formula, so no rule is drawn."
    )
    panel = Panel(
        title="Against the training distribution",
        x=x,
        y=y,
        series=(rug, candidate),
        markers=tuple(marker for marker in markers if x.contains(marker.value)),
        note=f"artifact {result.model_version}",
    )
    return Figure(
        name="domain-strip",
        title="Where this composition sits",
        panels=(panel,),
        caption=(
            f"The model was trained between {_number(ref.trained_min)} and "
            f"{_number(ref.trained_max)} {UNIT}; above "
            f"{_number(ref.cross_family_max)} {UNIT} only {ref.sole_family} rows exist "
            f"({ref.rows_above} of {ref.rows}). {ceiling_clause} {_verdict_sentence(result)}"
        ),
    )


# --------------------------------------------------------------------------------------
# 3. The temperature sweep
# --------------------------------------------------------------------------------------


def temperature_sweep(
    results: Sequence[PredictionResult],
    *,
    support: TemperatureSupport,
    thinning_above: float = 500.0,
) -> Figure:
    """Predicted capacity across the temperature range, over the support that backs it.

    Two panels on **one shared x axis**: the prediction with its band, and beneath it the
    number of training rows behind each part of the range. Not a second y scale on the same
    panel -- a dual axis is the one chart form this project never draws -- and not a footnote
    either, because a footnote is what the reader skips at exactly the temperature where the
    curve is least supported.

    Args:
        results: One answer per temperature, in any order; they are sorted here. Every one
            must be the same composition, which is checked -- a sweep assembled from two
            materials is a chart of nothing.
        support: Measured training rows per temperature bin. Measured, never recalled: see
            :class:`TemperatureSupport`.
        thinning_above: The temperature the caption reports the thinning at. Bin-aligned by
            :meth:`TemperatureSupport.above`, so the sentence matches the bars.
    """
    if not results:
        raise FigureError("a temperature sweep needs at least one answer; none were given.")
    formulas = {answer.request.formula for answer in results}
    if len(formulas) != 1:
        raise FigureError(
            f"a sweep draws one composition across temperatures and was given "
            f"{len(formulas)}: {', '.join(sorted(map(repr, formulas)))}."
        )
    levels = {answer.interval.level for answer in results}
    if len(levels) != 1:
        raise FigureError(
            f"the answers in this sweep target {len(levels)} different nominal levels "
            f"({', '.join(_number(level) for level in sorted(levels))}); one band cannot "
            f"carry two."
        )
    ordered = sorted(results, key=lambda answer: answer.request.temperature_k)
    formula = ordered[0].request.formula
    temperatures = tuple(answer.request.temperature_k for answer in ordered)
    capacities = tuple(answer.capacity for answer in ordered)
    band = Band(
        lower=tuple(answer.interval.lower for answer in ordered),
        upper=tuple(answer.interval.upper for answer in ordered),
        level=ordered[0].interval.level,
    )

    low = min(support.edges[0], min(temperatures))
    high = max(support.edges[-1], max(temperatures))
    reach = (high - low) * _PAD
    x = Axis(
        label="temperature",
        unit="K",
        lower=low - reach,
        upper=high + reach,
        anchored=(
            "the trained temperature range and every bin of the support beneath it, so the "
            "curve and the counts under it are read on one scale"
        ),
    )
    y = _capacity_axis(
        capacities + band.lower + band.upper,
        anchored="zero and the whole band, so a widening interval widens on the page",
    )
    curve = Series(
        name=formula,
        origin=PREDICTED,
        mark="line",
        x=temperatures,
        y=capacities,
        slot=1,
        band=band,
    )
    counts = Series(
        name=support.source,
        origin=MEASURED,
        mark="bar",
        x=support.midpoints,
        y=tuple(float(count) for count in support.counts),
        slot=2,
        widths=support.widths,
    )
    above = support.above(thinning_above)
    rows = Axis(
        label="training rows",
        unit="rows",
        lower=0.0,
        upper=max(support.counts) * (1.0 + _PAD) + 1.0,
        anchored="zero, so an empty bin reads as empty rather than as a short bar",
    )
    return Figure(
        name="temperature-sweep",
        title=f"{formula} across the trained temperature range",
        panels=(
            Panel(
                title="Predicted capacity",
                x=x,
                y=y,
                series=(curve,),
                note=f"artifact {ordered[0].model_version}",
            ),
            Panel(
                title="Training rows behind the curve above",
                x=x,
                y=rows,
                series=(counts,),
                markers=(
                    Marker(
                        label=f"{_number(thinning_above)} K",
                        value=thinning_above,
                        axis="x",
                        status="warning",
                        note=f"{above} of {support.rows} rows sit above it",
                    ),
                ) if x.contains(thinning_above) else (),
            ),
        ),
        shared=("x",),
        layout="column",
        caption=(
            f"Coverage inside the trained range is not uniform: {above} of {support.rows} "
            f"{support.source} sit above {_number(thinning_above)} K "
            f"({above / support.rows:.1%}). The band is the "
            f"{_number(band.level * 100)}% nominal interval; the temperature window is an "
            f"outer bound and says nothing about how well supported any point inside it is."
        ),
    )


# --------------------------------------------------------------------------------------
# 4. The nearest neighbours
# --------------------------------------------------------------------------------------


def nearest_neighbours(
    result: PredictionResult,
    neighbours: Sequence[Neighbour],
    *,
    novelty_ceiling: float | None = None,
) -> Figure:
    """The nearest training alloys by ElMD, with what was *measured* on them.

    The prediction sits at its own distance from the corpus; the neighbours sit at theirs,
    carrying measurements rather than predictions. A candidate whose nearest known chemistry
    is far away, or whose neighbours were measured nowhere near the predicted capacity, is
    visible here and nowhere else.

    Args:
        result: The answer, which must carry a novelty measurement -- a distance chart cannot
            be drawn from an answer that did not measure one.
        neighbours: The k closest training alloys. Sorted here by distance.
        novelty_ceiling: The corpus's own internal spread, past which a candidate is beyond
            known chemistry (:class:`~hydms.screens.novelty.NoveltyReference`), or ``None``.
    """
    if result.novelty is None:
        raise FigureError(
            "this answer states that novelty was not measured, so there is no distance to "
            "draw it at. 'Not measured' is a stated absence and must not become a zero: zero "
            "means the candidate *is* a training alloy."
        )
    if not neighbours:
        raise FigureError(
            "a neighbours chart with no neighbours in it asserts that the candidate has no "
            "near chemistry, which is a different claim and one this chart cannot make."
        )
    ordered = sorted(neighbours, key=lambda item: item.distance)
    distances = tuple(item.distance for item in ordered)
    capacities = tuple(item.capacity for item in ordered)
    interval = result.interval
    here = result.novelty.distance

    edges = [*distances, here, 0.0]
    if novelty_ceiling is not None:
        edges.append(_finite(novelty_ceiling, "the novelty ceiling"))
    x = Axis(
        label="distance to this candidate",
        unit=result.novelty.metric,
        lower=0.0,
        upper=max(edges) * (1.0 + _PAD) + (0.01 if max(edges) == 0.0 else 0.0),
        anchored="zero, because zero means 'this is a training alloy' and must be on the page",
    )
    y = _capacity_axis(
        (*capacities, result.capacity, interval.lower, interval.upper),
        anchored="zero and every measured neighbour, so the prediction is read against them",
    )
    known = Series(
        name="measured training alloys",
        origin=MEASURED,
        mark="dot",
        x=distances,
        y=capacities,
        slot=2,
        labels=tuple(
            f"{item.formula} @ {_number(item.temperature_k)} K" for item in ordered
        ),
    )
    candidate = Series(
        name=f"{result.request.formula} (predicted)",
        origin=PREDICTED,
        mark="point",
        x=(here,),
        y=(result.capacity,),
        slot=1,
        band=Band(lower=(interval.lower,), upper=(interval.upper,), level=interval.level),
        labels=(f"{result.capacity:.2f} {UNIT}",),
    )
    markers = []
    if novelty_ceiling is not None and x.contains(float(novelty_ceiling)):
        markers.append(
            Marker(
                label=(
                    f"beyond known chemistry, {float(novelty_ceiling):.3f} "
                    f"{result.novelty.metric}"
                ),
                value=float(novelty_ceiling),
                axis="x",
                status="serious",
                note="the widest gap the training corpus holds internally",
            )
        )
    temperatures = {item.temperature_k for item in ordered}
    spread = (
        f"at one temperature, {_number(next(iter(temperatures)))} K"
        if len(temperatures) == 1
        else (
            f"at their own temperatures, {_number(min(temperatures))}-"
            f"{_number(max(temperatures))} K"
        )
    )
    return Figure(
        name="nearest-neighbours",
        title=f"The {len(ordered)} nearest known alloys",
        panels=(
            Panel(
                title=f"{result.request.formula} against its nearest chemistry",
                x=x,
                y=y,
                series=(known, candidate),
                markers=tuple(markers),
                note=f"artifact {result.model_version}",
            ),
        ),
        caption=(
            f"Nearest known alloy {result.novelty.nearest} at "
            f"{result.novelty.distance:.3f} {result.novelty.metric}. The neighbours' "
            f"capacities are measured values, {spread}, while the candidate is predicted at "
            f"{_number(result.request.temperature_k)} K -- capacity depends on temperature, "
            f"so a neighbour measured elsewhere is near chemistry rather than a comparable "
            f"number."
        ),
    )


# --------------------------------------------------------------------------------------
# 5. The parity plot
# --------------------------------------------------------------------------------------


def parity(readings: Mapping[str, Sequence[ParityPoint]], *, level: float) -> Figure:
    """Predicted against measured, one panel per protocol, locked to one scale.

    **At least two readings are required, and that is the chart.** A parity plot of a single
    protocol is the optimistic number on its own page, which is the belief card #81 names in
    its own narrative: "it puts the optimistic number and the honest number on one page". A
    builder that could produce the single-panel version would eventually be called that way.

    ``shared=('x', 'y')`` makes the scales equal by construction rather than by care, so the
    two clouds are comparable by eye -- which is the only way anyone reads a pair of scatter
    panels.

    Args:
        readings: Protocol name -> its scored rows. Panels appear in the mapping's order, so
            the caller decides which is read first.
        level: The nominal level of the bands, shared across readings.

    Raises:
        FigureError: with one reading. The message names what is missing, because the case
            that reached it first was a real gap in the evidence: ``hydms.surrogate.loco``
            wrote per-class metrics and no per-row predictions, so the leave-one-alloy-class-out
            panel could not be drawn. Since card #98 it writes ``loco-out-of-fold.csv``. A
            probe writes the same file, so whether it is a *result* is ``loco-run.csv``'s
            ``probe`` column, not the file's presence.
    """
    named = dict(readings)
    if len(named) < 2:
        have = ", ".join(map(repr, named)) or "nothing"
        raise FigureError(
            f"a parity figure carries at least two readings and was given {len(named)} "
            f"({have}). One protocol on its own page is the optimistic number presented "
            f"alone; the honest one belongs beside it at the same scale. If the second "
            f"reading is leave-one-alloy-class-out, its rows are "
            f"`reports/loco/loco-out-of-fold.csv`, written by "
            f"`python -m hydms.surrogate.loco --target capacity` (card #98) -- and a result "
            f"only when `loco-run.csv` beside it records `probe` false."
        )
    for name, points in named.items():
        _text(name, "a reading name")
        if not points:
            raise FigureError(f"reading {name!r} scored no rows, so its panel would be empty.")

    reach: list[float] = []
    for points in named.values():
        for point in points:
            reach.extend((point.measured, point.predicted, point.lower, point.upper))
    low, high = _span([*reach, 0.0])
    low = min(low, 0.0)
    anchored = (
        "the union of every reading, so the honest panel and the optimistic one are the same "
        "size and the same shape"
    )

    def axis(label: str) -> Axis:
        return Axis(label=label, unit=UNIT, lower=low, upper=high, anchored=anchored)

    x = axis("measured capacity")
    y = axis("predicted capacity")

    panels = []
    for name, points in named.items():
        rows = list(points)
        panels.append(
            Panel(
                title=f"{name} (n = {len(rows)})",
                x=x,
                y=y,
                series=(
                    Series(
                        name=name,
                        origin=PREDICTED,
                        mark="dot",
                        x=tuple(point.measured for point in rows),
                        y=tuple(point.predicted for point in rows),
                        slot=1,
                        band=Band(
                            lower=tuple(point.lower for point in rows),
                            upper=tuple(point.upper for point in rows),
                            level=level,
                        ),
                    ),
                ),
                identity=True,
            )
        )
    return Figure(
        name="parity",
        title="Predicted against measured, by protocol",
        panels=tuple(panels),
        # Declared, not merely true. Every panel is built from the same two Axis objects here,
        # so the scales already agree -- but `shared` is what makes them *checked*, and a
        # later edit that gave one panel its own axis would then go red rather than quietly
        # withdrawing the comparison the figure exists to make.
        shared=("x", "y"),
        caption=(
            f"Every point carries its {_number(level * 100)}% nominal interval, so the "
            f"scatter is not read as a set of exact predictions. Both panels share one scale "
            f"by construction; a protocol that holds out a whole alloy family is a different "
            f"question from one that holds out rows, and the gap between the panels is the "
            f"answer to it (AC-6)."
        ),
    )
