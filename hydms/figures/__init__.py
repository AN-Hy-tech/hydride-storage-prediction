"""L6 -- the thesis figure set, built from a named artifact version.

Figures are generated from a promoted artifact rather than from whatever happens to
be in memory, so every figure in the thesis traces to a version.

**The five charts, and what each one refuses to let a reader believe** (card #81):

===============================  =============================================================
:func:`prediction_band`          that a number rendered alone is known to that precision
:func:`domain_strip`             that "the model answered" means the question was answerable
:func:`temperature_sweep`        that support is uniform across the trained range
:func:`nearest_neighbours`       that a prediction far from any known chemistry is evidence
:func:`parity`                   that a random-split score transfers to a new alloy family
===============================  =============================================================

They are built here, once, so the prediction page and the model card cannot draw the same
quantity two different ways -- which is the failure mode a per-page chart helper always
reaches eventually.

**A chart is a description before it is an image.** :mod:`hydms.figures.charts` builds
:class:`~hydms.figures.charts.Figure` objects and imports no plotting library;
:mod:`hydms.figures.render` turns one into matplotlib. Every guarantee the card asks for --
an estimate never drawn without its interval, an axis that always carries its unit, panels
locked to one scale, a threshold labelled rather than merely coloured -- is a guard on the
description, checkable without a renderer installed. The palette is in
:mod:`hydms.figures.palette`, validated rather than chosen.
"""

from __future__ import annotations

from hydms.figures.charts import (
    Axis,
    Band,
    Figure,
    FigureError,
    Marker,
    Neighbour,
    Panel,
    ParityPoint,
    Series,
    TemperatureSupport,
    domain_strip,
    nearest_neighbours,
    parity,
    prediction_band,
    temperature_sweep,
)
from hydms.figures.palette import DARK, LIGHT, Theme, theme

__all__ = [
    "DARK",
    "LIGHT",
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
    "Theme",
    "domain_strip",
    "nearest_neighbours",
    "parity",
    "prediction_band",
    "temperature_sweep",
    "theme",
]
