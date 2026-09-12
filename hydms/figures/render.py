"""L6 -- drawing a :class:`~hydms.figures.charts.Figure`, in matplotlib, in one theme.

Deliberately thin, and deliberately the only part of this layer that imports a plotting
library. Every promise card #81 makes lives in :mod:`hydms.figures.charts` as a guard on the
description, so nothing here is load-bearing: this module turns a description that already
satisfies those promises into pixels, and a bug in it is a bug about appearance.

**matplotlib is imported inside the function, not at module scope.** The import is the only
reason the ``figures`` extra exists, and a page or a test that only builds descriptions must
not pay for it -- the same shape as :mod:`hydms.surrogate.conformal`'s MAPIE import, for the
same reason.

The renderer is under CI rather than optional-and-skipped. That is a decision, not an
oversight: an extra CI does not install is a guarantee nobody checks, and the cheapest way to
keep this one honest was to name ``figures`` in the workflow's install line.

Card #81.
"""

from __future__ import annotations

import textwrap
from itertools import pairwise
from typing import Any

from hydms.figures.charts import CATEGORICAL, PREDICTED, Axis, Figure, Panel, Series
from hydms.figures.palette import Theme
from hydms.figures.palette import theme as get_theme

__all__ = ["render", "save"]

#: Width in inches per panel, and the figure height. One place, so a two-panel figure is twice
#: as wide rather than half as tall -- panels compared side by side must not be squashed.
_PANEL_WIDTH = 5.2
_HEIGHT = 4.0

_MARKER_DASH = (0, (4, 3))


def render(figure: Figure, *, theme: str = "light") -> Any:
    """Draw ``figure`` and return the matplotlib ``Figure``.

    Args:
        figure: The description to draw.
        theme: ``'light'`` or ``'dark'``.

    Raises:
        ValueError: if any series in ``figure`` breaks the relief rule in this theme -- a slot
            below 3:1 contrast against the surface with no visible direct label. The rule is
            not dismissable, so the renderer refuses rather than drawing an unreadable mark.
    """
    import matplotlib

    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt

    active = get_theme(theme)
    unlabelled = figure.relief(theme)
    if unlabelled:
        raise ValueError(
            f"figure {figure.name!r} draws {', '.join(map(repr, unlabelled))} in a slot that "
            f"sits below 3:1 contrast on the {theme} surface with no direct label. The relief "
            f"rule is not dismissable: label the series or move it to another slot."
        )

    count = len(figure.panels)
    if figure.layout == "column":
        fig, axes = plt.subplots(
            count,
            1,
            figsize=(_PANEL_WIDTH * 1.7, _HEIGHT * (1.0 + 0.45 * (count - 1))),
            squeeze=False,
            sharex=True,
            # The first panel is the subject; what is stacked under it is the evidence for
            # it, and evidence gets less height than the claim it supports.
            gridspec_kw={"height_ratios": [2.0] + [1.0] * (count - 1)},
        )
        drawn = [row[0] for row in axes]
    else:
        fig, axes = plt.subplots(
            1, count, figsize=(_PANEL_WIDTH * count, _HEIGHT), squeeze=False
        )
        drawn = list(axes[0])
    fig.patch.set_facecolor(active.plane)
    for position, (panel, ax) in enumerate(zip(figure.panels, drawn, strict=True)):
        # Stacked panels share one x axis, so only the bottom one names it. Repeating the
        # label above a set of hidden ticks reads as a second, separate scale.
        _panel(
            panel,
            ax,
            active,
            x_label=figure.layout != "column" or position == count - 1,
        )
    fig.suptitle(figure.title, color=active.ink, fontsize=12, ha="left", x=0.02)
    # matplotlib's own `wrap=True` measures against the axes, not the figure, and runs off
    # a wide one. Wrapping to a column derived from the figure width keeps the caption inside
    # the page at every panel count.
    fig.text(
        0.02,
        0.01,
        textwrap.fill(figure.caption, width=int(fig.get_figwidth() * 17)),
        color=active.ink_secondary,
        fontsize=7.5,
        va="bottom",
    )
    fig.tight_layout(rect=(0.0, 0.10, 1.0, 0.94))
    return fig


def save(figure: Figure, path: Any, *, theme: str = "light", dpi: int = 200) -> Any:
    """Render and write to ``path``, closing the matplotlib figure afterwards."""
    import matplotlib.pyplot as plt

    drawn = render(figure, theme=theme)
    drawn.savefig(path, dpi=dpi, facecolor=drawn.get_facecolor())
    plt.close(drawn)
    return path


def _panel(panel: Panel, ax: Any, active: Theme, *, x_label: bool = True) -> None:
    ax.set_facecolor(active.surface)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(active.axis)
        ax.spines[spine].set_linewidth(1.0)
    ax.grid(True, color=active.grid, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=active.muted, labelsize=8)

    for item in panel.series:
        _series(item, ax, active, panel)
    for marker in panel.markers:
        colour = active.status(marker.status)
        if marker.axis == "x":
            ax.axvline(marker.value, color=colour, linewidth=1.5, linestyle=_MARKER_DASH)
            ax.annotate(
                marker.label,
                xy=(marker.value, 1.0),
                xycoords=("data", "axes fraction"),
                xytext=(3, -10),
                textcoords="offset points",
                color=active.ink_secondary,
                fontsize=7,
                rotation=90,
                va="top",
            )
        else:
            ax.axhline(marker.value, color=colour, linewidth=1.5, linestyle=_MARKER_DASH)
            ax.annotate(
                marker.label,
                xy=(0.01, marker.value),
                xycoords=("axes fraction", "data"),
                xytext=(0, 3),
                textcoords="offset points",
                color=active.ink_secondary,
                fontsize=7,
            )
    if panel.identity:
        low = max(panel.x.lower, panel.y.lower)
        high = min(panel.x.upper, panel.y.upper)
        ax.plot(
            [low, high],
            [low, high],
            color=active.muted,
            linewidth=1.0,
            linestyle=_MARKER_DASH,
            zorder=1,
        )

    _axis(panel.x, ax, active, which="x", label=x_label)
    _axis(panel.y, ax, active, which="y")
    ax.set_title(panel.title, color=active.ink, fontsize=10, loc="left")
    if panel.note:
        ax.annotate(
            panel.note,
            xy=(1.0, 1.0),
            xycoords="axes fraction",
            xytext=(-2, 4),
            textcoords="offset points",
            color=active.muted,
            fontsize=7,
            ha="right",
        )
    if panel.legend:
        legend = ax.legend(loc="best", fontsize=7, frameon=False)
        for text in legend.get_texts():
            text.set_color(active.ink_secondary)


def _series(item: Series, ax: Any, active: Theme, panel: Panel) -> None:
    colour = active.slot(item.slot)
    if item.band is not None:
        if item.band_axis == "y" and item.mark in ("line", "step"):
            ax.fill_between(
                item.x,
                item.band.lower,
                item.band.upper,
                color=colour,
                alpha=active.band,
                linewidth=0,
                zorder=2,
            )
        elif item.mark == "point":
            # A filled span, not a whisker. A handful of estimates is the case where the
            # interval has room to be a *shape*, and a shape is what makes a wide band read as
            # wide at a glance; a thin capped line reads as a tick mark whatever its length.
            _span_fill(item, ax, colour, active, panel)
        elif item.band_axis == "y":
            ax.errorbar(
                item.x,
                item.y,
                yerr=_errors(item.y, item.band.lower, item.band.upper),
                fmt="none",
                ecolor=colour,
                elinewidth=1.0,
                capsize=2.0,
                alpha=0.55,
                zorder=2,
            )
        else:
            ax.errorbar(
                item.x,
                item.y,
                xerr=_errors(item.x, item.band.lower, item.band.upper),
                fmt="none",
                ecolor=colour,
                elinewidth=2.0,
                capsize=3.0,
                alpha=0.75,
                zorder=2,
            )

    label = f"{item.name} ({item.band.level:.0%} band)" if item.band else item.name
    if item.mark == "line":
        ax.plot(item.x, item.y, color=colour, linewidth=2.0, label=label, zorder=3)
    elif item.mark == "step":
        ax.step(item.x, item.y, color=colour, linewidth=2.0, where="mid", label=label, zorder=3)
    elif item.mark == "bar":
        width = [value * 0.92 for value in item.widths] if item.widths else _bar_width(item.x)
        ax.bar(
            item.x,
            item.y,
            width=width,
            color=colour,
            edgecolor=active.surface,
            linewidth=1.5,
            label=label,
            zorder=3,
        )
    elif item.mark == "rug":
        ax.scatter(
            item.x,
            item.y,
            marker="|",
            s=180,
            color=colour,
            alpha=0.35,
            linewidths=1.0,
            label=label,
            zorder=3,
        )
    else:
        size = 110 if item.mark == "point" else 26
        alpha = 1.0 if item.mark == "point" else 0.6
        ax.scatter(
            item.x,
            item.y,
            s=size,
            color=colour,
            edgecolors=active.surface,
            linewidths=2.0 if item.mark == "point" else 0.0,
            alpha=alpha,
            label=label,
            zorder=4 if item.origin == PREDICTED else 3,
        )

    # A label on a point whose band runs horizontally is pushed straight up: at (6, 6) it
    # lands on the band's own cap and, in the strip, on a threshold's rotated label.
    offset = (0, 14) if item.band is not None and item.band_axis == "x" else (6, 6)
    for x, y, text in zip(item.x, item.y, item.labels or ("",) * len(item.x), strict=True):
        if text.strip():
            ax.annotate(
                text,
                xy=(x, y),
                xytext=offset,
                textcoords="offset points",
                color=active.ink_secondary,
                fontsize=7,
                zorder=5,
            )


def _span_fill(
    item: Series, ax: Any, colour: str, active: Theme, panel: Panel
) -> None:
    """Draw a point series' band as a filled span across the axis it is read on.

    The span's thickness is measured on the *other* axis, so it is taken from that axis rather
    than fixed: 0.34 lane-widths on a categorical axis, and a small fraction of the range on a
    quantitative one. A constant in data units looks right on the one chart it was tuned for
    and becomes a rectangle covering a third of the panel on the next.
    """
    assert item.band is not None
    across = panel.x if item.band_axis == "y" else panel.y
    thickness = (
        0.34 if across.kind == CATEGORICAL else (across.upper - across.lower) * 0.035
    )
    for position, (low, high) in enumerate(
        zip(item.band.lower, item.band.upper, strict=True)
    ):
        extent = max(0.0, high - low)
        if item.band_axis == "y":
            ax.bar(
                item.x[position],
                extent,
                bottom=low,
                width=thickness,
                color=colour,
                alpha=active.band,
                linewidth=0,
                zorder=2,
            )
        else:
            ax.barh(
                item.y[position],
                extent,
                left=low,
                height=thickness,
                color=colour,
                alpha=active.band,
                linewidth=0,
                zorder=2,
            )


def _errors(centres: tuple[float, ...], lower: tuple[float, ...], upper: tuple[float, ...]) -> Any:
    """Half-widths either side of each centre, clamped at zero.

    A crossed band -- a head on the wrong side of the estimate -- is drawn as a zero arm on
    that side rather than as a negative one, which matplotlib refuses outright. It is not
    hidden: the caller's own caption reports the width it was given, and what the delivery
    layer should *say* about a crossed band is card #94's question.
    """
    return [
        [max(0.0, centre - low) for centre, low in zip(centres, lower, strict=True)],
        [max(0.0, high - centre) for centre, high in zip(centres, upper, strict=True)],
    ]


def _bar_width(positions: tuple[float, ...]) -> float:
    """A bar width leaving the 2px-equivalent gap between neighbours."""
    if len(positions) < 2:
        return 1.0
    gaps = [later - earlier for earlier, later in pairwise(positions)]
    return min(gaps) * 0.82


def _axis(axis: Axis, ax: Any, active: Theme, *, which: str, label: bool = True) -> None:
    if which == "x":
        ax.set_xlim(axis.lower, axis.upper)
        if label:
            ax.set_xlabel(axis.title, color=active.muted, fontsize=8)
        if axis.kind == CATEGORICAL:
            ax.set_xticks(range(len(axis.categories)), axis.categories)
    else:
        ax.set_ylim(axis.lower, axis.upper)
        ax.set_ylabel(axis.title, color=active.muted, fontsize=8)
        if axis.kind == CATEGORICAL:
            ax.set_yticks(range(len(axis.categories)), axis.categories)
