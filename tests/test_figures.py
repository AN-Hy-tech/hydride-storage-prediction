"""L6 -- the chart vocabulary (card #81).

Two halves, and the split is the point.

**The guarantees** are checked against :mod:`hydms.figures.charts` and
:mod:`hydms.figures.palette`, which import no plotting library. Every box on card #81 is one
of them: an estimate never drawn without its interval, an axis that always carries its unit,
an axis that cannot rescale to hide a wide band, panels locked to one scale, a threshold
labelled rather than merely coloured. None of these needs matplotlib and none of them skips.

**The rendering** is checked at the end, and it is a smoke test. It runs in CI -- the
workflow installs the `figures` extra on purpose -- but nothing above depends on it, so if it
ever could not run, what would be lost is a check that the drawing code executes, not a check
that a chart tells the truth.

The real-data tests at the bottom read committed CSVs under ``reports/``, which are
un-ignored precisely so that a check can read them.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from hydms.delivery.contract import (
    DomainVerdict,
    Interval,
    Novelty,
    PredictionRequest,
    PredictionResult,
)
from hydms.figures import palette
from hydms.figures.charts import (
    CATEGORICAL,
    MEASURED,
    PREDICTED,
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

OUT_OF_FOLD = Path("reports/model/model-out-of-fold.csv")
LOCO_SUMMARY = Path("reports/loco/loco-summary.csv")
LOCO_OUT_OF_FOLD = Path("reports/loco/loco-out-of-fold.csv")

TARGET = "H2_W% (max)"
TEMPERATURE = "temperature(K)"

#: The temperature the card's thinning claim is made at.
THINNING_K = 500.0


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------


def answer(
    formula: str = "La0.9Ce0.1Ni5",
    temperature_k: float = 298.0,
    capacity: float = 1.42,
    lower: float = 0.98,
    upper: float = 2.05,
    *,
    novelty: Novelty | None = None,
) -> PredictionResult:
    """A complete answer, built through the real contract so its guards run too."""
    return PredictionResult(
        request=PredictionRequest(formula=formula, temperature_k=temperature_k),
        capacity=capacity,
        interval=Interval(lower=lower, upper=upper, level=0.8),
        domain=DomainVerdict.admitted_by(["temperature", "applicability-domain", "novelty"]),
        novelty=novelty if novelty is not None else Novelty(distance=0.043, nearest="La1Ni5"),
        model_version="v3",
    )


@pytest.fixture(scope="module")
def out_of_fold(repo_root: Path) -> list[dict[str, str]]:
    """The committed out-of-fold table: one scored row per training row (card #29)."""
    path = repo_root / OUT_OF_FOLD
    if not path.is_file():
        pytest.skip(f"the out-of-fold table is not in this checkout: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture()
def support(out_of_fold: list[dict[str, str]]) -> TemperatureSupport:
    """Training support per temperature bin, measured from the committed table."""
    return TemperatureSupport.measured(
        [float(row[TEMPERATURE]) for row in out_of_fold],
        edges=[195.0, 250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0, 700.0, 773.0],
        source="scored out-of-fold rows",
    )


@pytest.fixture()
def neighbours() -> list[Neighbour]:
    return [
        Neighbour("La1Ni5", 0.043, 1.49, 298.0, "AB5"),
        Neighbour("La1Ni4.5Al0.5", 0.11, 1.31, 313.0, "AB5"),
        Neighbour("Ce1Ni5", 0.18, 1.22, 298.0, "AB5"),
    ]


# --------------------------------------------------------------------------------------
# The palette: pinned, because the check that decides safety runs elsewhere
# --------------------------------------------------------------------------------------


def test_the_validated_hexes_are_pinned_so_a_change_forces_a_revalidation() -> None:
    """The slots are what the validator passed. Changing one must fail here.

    This test cannot tell anyone the palette is colour-blind safe -- the simulation that
    decides that lives in the `dataviz` skill's Node validator, outside this repository. What
    it can do is make any edit to a hex go red, so the command in the module docstring is
    re-run rather than the reasoning re-done in someone's head.
    """
    assert palette.LIGHT.series == ("#2a78d6", "#eb6834", "#1baf7a")
    assert palette.DARK.series == ("#3987e5", "#d95926", "#199e70")
    assert palette.CVD_SEPARATION == {"light": 9.2, "dark": 9.4}
    assert palette.NORMAL_SEPARATION == {"light": 24.0, "dark": 20.9}
    assert palette.NEEDS_RELIEF == {"light": (3,), "dark": ()}


def test_every_recorded_separation_clears_the_gate_it_is_recorded_against() -> None:
    """8 for CVD, 15 for normal vision -- the skill's hard floors, both modes."""
    for mode in ("light", "dark"):
        assert palette.CVD_SEPARATION[mode] >= 8.0
        assert palette.NORMAL_SEPARATION[mode] >= 15.0


def test_a_fourth_slot_is_refused_rather_than_cycled() -> None:
    with pytest.raises(palette.PaletteError, match="does not exist"):
        palette.LIGHT.slot(palette.SLOTS + 1)
    with pytest.raises(palette.PaletteError, match="does not exist"):
        palette.DARK.slot(0)


def test_a_status_role_is_never_a_series_colour() -> None:
    """The reserved palette and the categorical one do not overlap, in either theme."""
    for theme in (palette.LIGHT, palette.DARK):
        assert not set(theme.series) & set(palette.STATUS.values())
    with pytest.raises(palette.PaletteError, match="not a status role"):
        palette.LIGHT.status("series 4")


def test_there_is_no_automatic_third_theme() -> None:
    with pytest.raises(palette.PaletteError, match="no 'auto' theme"):
        palette.theme("auto")


def test_the_light_slot_below_contrast_is_the_one_that_needs_relief() -> None:
    assert palette.LIGHT.relief_required(3)
    assert not palette.LIGHT.relief_required(1)
    assert not palette.DARK.relief_required(3)


# --------------------------------------------------------------------------------------
# The vocabulary's guards
# --------------------------------------------------------------------------------------


def test_a_quantitative_axis_without_a_unit_cannot_be_built() -> None:
    """Card #81: every axis carries units. Not a review note -- a construction error."""
    with pytest.raises(FigureError, match="names no unit"):
        Axis(label="capacity", lower=0.0, upper=7.0)


def test_a_categorical_axis_may_not_claim_a_unit() -> None:
    with pytest.raises(FigureError, match="names the unit"):
        Axis(label="candidate", kind=CATEGORICAL, unit="wt%", categories=("La1Ni5",))


def test_a_categorical_axis_positions_its_categories_at_integers() -> None:
    axis = Axis(label="lane", kind=CATEGORICAL, categories=("training", "candidate"))
    assert (axis.lower, axis.upper) == (-0.5, 1.5)
    assert axis.contains(0.0) and axis.contains(1.0)


def test_an_axis_whose_bounds_meet_is_refused() -> None:
    with pytest.raises(FigureError, match="draws every value on top"):
        Axis(label="capacity", unit="wt%", lower=2.0, upper=2.0)


def test_a_predicted_series_cannot_be_drawn_without_its_interval() -> None:
    """The headline guarantee, and the one the whole card is shaped around."""
    with pytest.raises(FigureError, match="drawn without its interval"):
        Series(name="candidate", origin=PREDICTED, mark="point", x=(0.0,), y=(1.4,))


def test_a_series_says_where_its_marks_came_from_not_which_reading_it_is() -> None:
    """`reading` is spent: three readings of one model is `CONTEXT.md`'s own vocabulary, and
    `evaluation-metrics.csv` has a column of that name. A series has an `origin`."""
    known = Series(name="rows", origin=MEASURED, mark="dot", x=(0.0,), y=(1.4,))
    assert known.origin == MEASURED
    assert not hasattr(known, "reading")
    with pytest.raises(FigureError, match="has origin"):
        Series(name="rows", origin="observed", mark="dot", x=(0.0,), y=(1.4,))


def test_a_measured_series_needs_no_interval() -> None:
    known = Series(name="training rows", origin=MEASURED, mark="dot", x=(0.0,), y=(1.4,))
    assert known.band is None


def test_an_inverted_band_is_refused_the_way_the_delivery_contract_refuses_one() -> None:
    with pytest.raises(FigureError, match="its width is negative"):
        Band(lower=(2.0,), upper=(1.0,), level=0.8)


def test_a_band_belongs_to_the_points_it_surrounds() -> None:
    with pytest.raises(FigureError, match="belongs to the estimate"):
        Series(
            name="candidate",
            origin=PREDICTED,
            mark="point",
            x=(0.0, 1.0),
            y=(1.4, 1.5),
            band=Band(lower=(1.0,), upper=(2.0,), level=0.8),
        )


def test_two_series_in_one_panel_never_share_a_colour_slot() -> None:
    first = Series(name="a", origin=MEASURED, mark="dot", x=(0.5,), y=(1.0,), slot=1)
    second = Series(name="b", origin=MEASURED, mark="dot", x=(0.5,), y=(1.0,), slot=1)
    with pytest.raises(FigureError, match="Colour follows the entity"):
        Panel(
            title="two",
            x=Axis(label="x", unit="wt%", lower=0.0, upper=1.0),
            y=Axis(label="y", unit="wt%", lower=0.0, upper=2.0),
            series=(first, second),
        )


def test_a_panel_refuses_a_band_its_axis_would_cut() -> None:
    """Nothing clips. An axis that cuts a band makes a wide interval look narrow."""
    wide = Series(
        name="candidate",
        origin=PREDICTED,
        mark="point",
        x=(0.5,),
        y=(1.4,),
        band=Band(lower=(0.2,), upper=(6.0,), level=0.8),
    )
    with pytest.raises(FigureError, match="makes a wide interval look narrow"):
        Panel(
            title="clipped",
            x=Axis(label="x", unit="wt%", lower=0.0, upper=1.0),
            y=Axis(label="capacity", unit="wt%", lower=0.0, upper=2.0),
            series=(wide,),
        )


def test_a_threshold_drawn_past_the_edge_is_refused() -> None:
    series = Series(name="a", origin=MEASURED, mark="dot", x=(0.5,), y=(1.0,))
    with pytest.raises(FigureError, match="threshold drawn past the edge"):
        Panel(
            title="off",
            x=Axis(label="x", unit="wt%", lower=0.0, upper=1.0),
            y=Axis(label="capacity", unit="wt%", lower=0.0, upper=2.0),
            series=(series,),
            markers=(Marker(label="ceiling", value=9.0, axis="y", status="warning"),),
        )


def test_a_marker_cannot_be_a_colour_alone() -> None:
    with pytest.raises(FigureError, match="a marker label is blank"):
        Marker(label="   ", value=1.0, axis="y", status="critical")


def test_the_identity_line_needs_both_axes_in_the_same_unit() -> None:
    series = Series(name="a", origin=MEASURED, mark="dot", x=(0.5,), y=(1.0,))
    with pytest.raises(FigureError, match="same quantity in the same unit"):
        Panel(
            title="mixed",
            x=Axis(label="temperature", unit="K", lower=0.0, upper=1.0),
            y=Axis(label="capacity", unit="wt%", lower=0.0, upper=2.0),
            series=(series,),
            identity=True,
        )


def test_panels_that_disagree_about_a_shared_scale_cannot_be_assembled() -> None:
    """The parity figure's guarantee, checked at the type rather than in the builder."""

    def panel(title: str, top: float) -> Panel:
        return Panel(
            title=title,
            x=Axis(label="measured", unit="wt%", lower=0.0, upper=8.0),
            y=Axis(label="predicted", unit="wt%", lower=0.0, upper=top),
            series=(Series(name=title, origin=MEASURED, mark="dot", x=(1.0,), y=(1.0,)),),
        )

    with pytest.raises(FigureError, match="comparison quietly withdrawn"):
        Figure(
            name="two",
            title="two",
            panels=(panel("optimistic", 8.0), panel("honest", 4.0)),
            caption="two panels",
            shared=("y",),
        )


def test_a_stacked_figure_must_share_its_x_axis() -> None:
    panel = Panel(
        title="one",
        x=Axis(label="temperature", unit="K", lower=0.0, upper=800.0),
        y=Axis(label="capacity", unit="wt%", lower=0.0, upper=8.0),
        series=(Series(name="a", origin=MEASURED, mark="line", x=(1.0,), y=(1.0,)),),
    )
    with pytest.raises(FigureError, match="Stacking is itself the claim"):
        Figure(
            name="stacked",
            title="stacked",
            panels=(panel, panel),
            caption="stacked",
            layout="column",
        )


def test_unequal_bins_may_carry_unequal_bar_widths_and_only_bars_may() -> None:
    with pytest.raises(FigureError, match="only a bar has a width"):
        Series(
            name="support",
            origin=MEASURED,
            mark="dot",
            x=(1.0, 2.0),
            y=(3.0, 4.0),
            widths=(1.0, 1.0),
        )


# --------------------------------------------------------------------------------------
# 1. The prediction band
# --------------------------------------------------------------------------------------


def test_the_prediction_band_states_its_width_numerically() -> None:
    figure = prediction_band(answer())
    assert "1.07" in figure.caption
    assert "wt%" in figure.caption


def test_the_prediction_bands_axis_is_anchored_and_says_to_what() -> None:
    figure = prediction_band(answer())
    y = figure.panels[0].y
    assert y.anchored, "an unanchored capacity axis rescales to whatever band it is given"
    assert "trained capacity range" in y.anchored


def test_a_wide_interval_occupies_more_of_the_axis_than_a_narrow_one() -> None:
    """The chart's whole reason for existing, measured rather than asserted in prose.

    Both answers are drawn on an axis anchored to the same trained range, so the fraction of
    the frame each band covers is comparable -- which is exactly what an axis fitted to the
    band would destroy.
    """
    narrow = prediction_band(answer(capacity=1.42, lower=1.35, upper=1.49))
    wide = prediction_band(answer(capacity=1.42, lower=0.20, upper=4.90))

    def fraction(figure: Figure) -> float:
        panel = figure.panels[0]
        band = panel.series[0].band
        assert band is not None
        return band.widths[0] / (panel.y.upper - panel.y.lower)

    assert fraction(wide) > 10 * fraction(narrow)


def test_a_band_running_past_the_trained_range_widens_the_axis_rather_than_being_cut() -> None:
    figure = prediction_band(answer(capacity=6.0, lower=3.0, upper=9.5))
    panel = figure.panels[0]
    assert panel.y.upper >= 9.5
    band = panel.series[0].band
    assert band is not None
    assert panel.y.contains(band.upper[0])


def test_the_prediction_band_carries_the_material_versus_system_caveat() -> None:
    """PRD 4.4. A capacity beside a DOE number is a two-step overstatement."""
    caption = prediction_band(answer()).caption
    assert "material" in caption and "DOE" in caption


# --------------------------------------------------------------------------------------
# 2. The domain strip
# --------------------------------------------------------------------------------------


def test_the_domain_strip_needs_the_distribution_it_places_the_candidate_against() -> None:
    with pytest.raises(FigureError, match="given no training rows"):
        domain_strip(answer(), training=[])


def test_the_domain_strip_draws_the_cross_family_rule_and_names_the_family(
    out_of_fold: list[dict[str, str]],
) -> None:
    capacities = [float(row[TARGET]) for row in out_of_fold]
    figure = domain_strip(answer(), training=capacities, physical_ceiling=1.63)
    labels = [marker.label for marker in figure.panels[0].markers]
    assert any("cross-family evidence ends" in label for label in labels)
    assert any("physical ceiling" in label for label in labels)
    assert "Mg" in figure.caption


def test_an_uncomputable_ceiling_is_stated_rather_than_drawn_as_unbounded(
    out_of_fold: list[dict[str, str]],
) -> None:
    capacities = [float(row[TARGET]) for row in out_of_fold]
    figure = domain_strip(answer(), training=capacities, physical_ceiling=None)
    assert "could not be computed" in figure.caption
    assert not any("physical ceiling" in m.label for m in figure.panels[0].markers)


def test_the_domain_strips_band_runs_along_the_capacity_axis(
    out_of_fold: list[dict[str, str]],
) -> None:
    """The strip is horizontal, so its band is read on x. A band measured against the wrong
    axis would be drawn at a plausible size and nothing would look wrong."""
    capacities = [float(row[TARGET]) for row in out_of_fold]
    figure = domain_strip(answer(), training=capacities)
    candidate = figure.panels[0].series[1]
    assert candidate.band_axis == "x"
    assert candidate.band is not None
    assert candidate.band.widths[0] == pytest.approx(2.05 - 0.98, abs=1e-12)


# --------------------------------------------------------------------------------------
# 3. The temperature sweep
# --------------------------------------------------------------------------------------


def test_the_sweep_reports_the_thinning_it_measured_not_a_remembered_number(
    support: TemperatureSupport,
) -> None:
    """REPORT.md's ``n = 39`` is the archival 247-row test split's, and this project no
    longer has that split. The committed out-of-fold table scores 893 rows and 130 of them
    sit above 500 K; the *claim* the card makes survives and only its number was inherited."""
    assert support.rows == 893
    assert support.above(THINNING_K) == 130
    figure = temperature_sweep(
        [answer(temperature_k=t) for t in (195.0, 400.0, 773.0)], support=support
    )
    assert "130 of 893" in figure.caption
    assert "39" not in figure.caption


def test_the_sweep_puts_the_support_under_the_curve_on_one_shared_axis(
    support: TemperatureSupport,
) -> None:
    figure = temperature_sweep(
        [answer(temperature_k=t) for t in (195.0, 400.0, 773.0)], support=support
    )
    assert figure.layout == "column"
    assert figure.shared == ("x",)
    assert figure.panels[0].x == figure.panels[1].x
    assert figure.panels[1].series[0].origin == MEASURED


def test_the_sweep_draws_unequal_bins_at_unequal_widths(
    support: TemperatureSupport,
) -> None:
    figure = temperature_sweep([answer(temperature_k=400.0)], support=support)
    bars = figure.panels[1].series[0]
    assert len(set(bars.widths)) > 1
    assert bars.widths == support.widths


def test_a_sweep_over_two_compositions_is_refused(support: TemperatureSupport) -> None:
    with pytest.raises(FigureError, match="draws one composition"):
        temperature_sweep(
            [answer(formula="La1Ni5"), answer(formula="Mg2Ni")], support=support
        )


def test_support_counts_every_row_exactly_once() -> None:
    counted = TemperatureSupport.measured(
        [195.0, 200.0, 299.9, 300.0, 773.0],
        edges=[195.0, 300.0, 773.0],
        source="a fixture",
    )
    assert counted.counts == (3, 2)
    assert counted.rows == 5


# --------------------------------------------------------------------------------------
# 4. The nearest neighbours
# --------------------------------------------------------------------------------------


def test_a_neighbours_chart_refuses_an_answer_that_measured_no_distance(
    neighbours: list[Neighbour],
) -> None:
    """'Not measured' is a stated absence and must not become a zero: zero means the
    candidate *is* a training alloy."""
    unmeasured = PredictionResult(
        request=PredictionRequest(formula="La1Ni5", temperature_k=298.0),
        capacity=1.4,
        interval=Interval(lower=1.0, upper=1.8, level=0.8),
        domain=DomainVerdict.admitted_by(["temperature"]),
        novelty=None,
        model_version="v3",
    )
    with pytest.raises(FigureError, match="must not become a zero"):
        nearest_neighbours(unmeasured, neighbours)


def test_the_neighbours_carry_measurements_and_the_candidate_carries_a_prediction(
    neighbours: list[Neighbour],
) -> None:
    figure = nearest_neighbours(answer(), neighbours, novelty_ceiling=0.62)
    known, candidate = figure.panels[0].series
    assert known.origin == MEASURED and known.band is None
    assert candidate.origin == PREDICTED and candidate.band is not None
    assert known.labelled, "a neighbour with no label is a dot nobody can name"


def test_the_neighbours_chart_says_the_measurements_are_at_their_own_temperatures(
    neighbours: list[Neighbour],
) -> None:
    caption = nearest_neighbours(answer(), neighbours).caption
    assert "298-313 K" in caption
    assert "capacity depends on temperature" in caption


def test_the_distance_axis_starts_at_zero_because_zero_is_a_meaning(
    neighbours: list[Neighbour],
) -> None:
    figure = nearest_neighbours(answer(), neighbours)
    assert figure.panels[0].x.lower == 0.0
    assert "training alloy" in figure.panels[0].x.anchored


# --------------------------------------------------------------------------------------
# 5. The parity plot
# --------------------------------------------------------------------------------------


def parity_points(rows: list[dict[str, str]]) -> list[ParityPoint]:
    return [
        ParityPoint(
            measured=float(row[TARGET]),
            predicted=float(row["q0.5"]),
            lower=float(row["q0.1"]),
            upper=float(row["q0.9"]),
        )
        for row in rows
    ]


def test_a_single_reading_parity_plot_cannot_be_built(
    out_of_fold: list[dict[str, str]],
) -> None:
    """'It puts the optimistic number and the honest number on one page' -- card #81's own
    narrative -- as a refusal rather than a convention."""
    with pytest.raises(FigureError, match="at least two readings"):
        parity({"grouped nested CV": parity_points(out_of_fold)}, level=0.8)


def test_the_refusal_names_the_evidence_that_is_missing(
    out_of_fold: list[dict[str, str]],
) -> None:
    with pytest.raises(FigureError, match="card #98"):
        parity({"grouped nested CV": parity_points(out_of_fold)}, level=0.8)


def test_both_parity_panels_are_locked_to_one_scale(
    out_of_fold: list[dict[str, str]],
) -> None:
    points = parity_points(out_of_fold)
    figure = parity(
        {"grouped nested CV": points, "leave-one-alloy-class-out": points[:100]}, level=0.8
    )
    assert figure.shared == ("x", "y")
    first, second = figure.panels
    assert first.x == second.x and first.y == second.y
    assert first.identity and second.identity


def test_every_parity_point_carries_its_band(out_of_fold: list[dict[str, str]]) -> None:
    points = parity_points(out_of_fold)
    figure = parity({"a": points, "b": points[:10]}, level=0.8)
    for panel in figure.panels:
        band = panel.series[0].band
        assert band is not None
        assert len(band) == len(panel.series[0].y)


# --------------------------------------------------------------------------------------
# What the committed evidence actually holds
# --------------------------------------------------------------------------------------


def test_the_committed_loco_run_keeps_every_scored_row(repo_root: Path) -> None:
    """The second parity panel's evidence: LOACO's scored rows, not only their averages -- #98.

    Until card #98, ``hydms.surrogate.loco`` wrote four aggregate tables and no scored rows,
    so :func:`parity` could not be built from committed evidence and this test asserted the
    gap as a measurement. It now writes ``loco-out-of-fold.csv``; this skips until the
    maintainer's LOACO run has committed it, and from then on checks it is the *whole* record:
    one row per row the class folds scored, every one carrying the band a parity point needs.
    """
    path = repo_root / LOCO_OUT_OF_FOLD
    if not path.is_file():
        pytest.skip(
            f"{path} is not committed yet: it is written by the full LOACO run card #98 hands "
            f"over (`python -m hydms.surrogate.loco --target capacity`), which the maintainer runs"
        )
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (repo_root / LOCO_SUMMARY).open(encoding="utf-8", newline="") as handle:
        summary = list(csv.DictReader(handle))
    assert len(rows) == sum(int(row["rows_scored"]) for row in summary)
    assert {"q0.1", "q0.5", "q0.9"} <= set(rows[0])
    assert all(row["fold"].startswith("class:") for row in rows)
    points = parity_points(rows)
    assert len(points) == len(rows)


def test_the_out_of_fold_table_is_the_whole_training_split(
    out_of_fold: list[dict[str, str]],
) -> None:
    """893 scored rows, every one predicted by a model that had not seen it."""
    assert len(out_of_fold) == 893
    assert {row["model"] for row in out_of_fold} == {"catboost-multiquantile"}


# --------------------------------------------------------------------------------------
# Both themes, every figure
# --------------------------------------------------------------------------------------


def figures(rows: list[dict[str, str]], neighbours: list[Neighbour]) -> list[Figure]:
    """One of each, built the way a page would build them."""
    capacities = [float(row[TARGET]) for row in rows]
    points = parity_points(rows)
    counted = TemperatureSupport.measured(
        [float(row[TEMPERATURE]) for row in rows],
        edges=[195.0, 300.0, 400.0, 500.0, 600.0, 773.0],
        source="scored out-of-fold rows",
    )
    return [
        prediction_band(answer()),
        domain_strip(answer(), training=capacities, physical_ceiling=1.63),
        temperature_sweep(
            [answer(temperature_k=t) for t in (195.0, 400.0, 773.0)], support=counted
        ),
        nearest_neighbours(answer(), neighbours, novelty_ceiling=0.62),
        parity({"grouped nested CV": points, "held-out family": points[:80]}, level=0.8),
    ]


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_no_figure_breaks_the_relief_rule_in_either_theme(
    mode: str, out_of_fold: list[dict[str, str]], neighbours: list[Neighbour]
) -> None:
    """A slot below 3:1 against its own surface carries a visible direct label, or it is not
    used. The rule is not dismissable, so this is not a warning."""
    for figure in figures(out_of_fold, neighbours):
        assert figure.relief(mode) == ()


def test_every_quantitative_axis_in_every_figure_names_its_unit(
    out_of_fold: list[dict[str, str]], neighbours: list[Neighbour]
) -> None:
    """Enumerated rather than sampled: the guard is per-axis, so the claim 'every axis' is
    only true if every axis of every figure is read."""
    for figure in figures(out_of_fold, neighbours):
        for panel in figure.panels:
            for axis in (panel.x, panel.y):
                if axis.kind != CATEGORICAL:
                    assert axis.unit.strip(), f"{figure.name}/{panel.title}: {axis.label}"


def test_no_figure_draws_a_prediction_without_a_band(
    out_of_fold: list[dict[str, str]], neighbours: list[Neighbour]
) -> None:
    for figure in figures(out_of_fold, neighbours):
        for panel in figure.panels:
            for series in panel.series:
                if series.origin == PREDICTED:
                    assert series.band is not None


def test_every_figure_carries_a_caption(
    out_of_fold: list[dict[str, str]], neighbours: list[Neighbour]
) -> None:
    for figure in figures(out_of_fold, neighbours):
        assert figure.caption.strip()


# --------------------------------------------------------------------------------------
# The renderer -- a smoke test, and nothing above depends on it
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_every_figure_renders_in_both_themes(
    mode: str,
    tmp_path: Path,
    out_of_fold: list[dict[str, str]],
    neighbours: list[Neighbour],
) -> None:
    """Smoke only. CI installs the `figures` extra so this runs rather than skips, but no
    guarantee above rests on it: what would be lost is a check that the drawing code
    executes, not a check that a chart tells the truth."""
    pytest.importorskip("matplotlib", reason="the `figures` extra is not installed")
    from hydms.figures.render import save

    for figure in figures(out_of_fold, neighbours):
        written = save(figure, tmp_path / f"{figure.name}-{mode}.png", theme=mode)
        assert Path(written).stat().st_size > 0


#: Rendered in a *fresh* interpreter by the test below. It reports two facts about the process
#: after one `save()`: whether pyplot was dragged in, and whether the stored backend moved.
#:
#: The backend is read the way matplotlib stores it rather than through `rcParams["backend"]`,
#: because that key resolves an "auto" sentinel on first read -- importing pyplot and a GUI
#: toolkit as a side effect. The obvious spelling of this check would manufacture the state it
#: is meant to detect.
_STATE_PROBE = """
import sys

import matplotlib

stored = dict.__getitem__(matplotlib.rcParams, "backend")

from hydms.figures.charts import Axis, Figure, MEASURED, Panel, Series
from hydms.figures.render import save

save(
    Figure(
        name="probe",
        title="probe",
        panels=(
            Panel(
                title="one",
                x=Axis(label="x", unit="wt%", lower=0.0, upper=2.0),
                y=Axis(label="y", unit="wt%", lower=0.0, upper=2.0),
                series=(
                    Series(
                        name="measured",
                        origin=MEASURED,
                        mark="dot",
                        x=(1.0,),
                        y=(1.0,),
                        slot=1,
                    ),
                ),
            ),
        ),
        caption="a render in a process that has done nothing else",
    ),
    sys.argv[1],
)

print("pyplot:", "matplotlib.pyplot" in sys.modules)
print("backend-moved:", dict.__getitem__(matplotlib.rcParams, "backend") != stored)
"""


def test_rendering_leaves_the_interpreter_as_it_found_it(tmp_path: Path) -> None:
    """Card #100: a render must not depend on what ran before it, or change what runs after.

    The defect that card describes -- this file green on its own and red in a full suite -- is
    only *possible* because rendering read and wrote process-wide state: it chose a backend, and
    it registered every figure in pyplot's global list. This asserts the property that puts the
    whole class of defect out of reach, rather than the one symptom, because the symptom is
    invisible to every per-file run and did not reproduce in two full runs.

    **It runs in a subprocess, and that is the point.** In this process pyplot may already be
    imported and the backend already pinned by whatever ran earlier -- including, before the
    repair, the smoke test a few lines up. An in-process version of this check would therefore
    compare two identical values and pass against the very code it exists to reject. A fresh
    interpreter is the only place where "renders without ever importing pyplot" is observable.
    """
    pytest.importorskip("matplotlib", reason="the `figures` extra is not installed")
    import subprocess
    import sys

    finished = subprocess.run(
        [sys.executable, "-c", _STATE_PROBE, str(tmp_path / "probe.png")],
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert finished.returncode == 0, (
        f"a render in a fresh interpreter failed outright:\n{finished.stderr}"
    )
    assert "pyplot: False" in finished.stdout, (
        "rendering imported pyplot, whose global figure registry is what `save()` used to have "
        f"to clean up after itself:\n{finished.stdout}"
    )
    assert "backend-moved: False" in finished.stdout, (
        "rendering changed the interpreter's matplotlib backend -- the process-wide state that "
        f"lets one test's result depend on whether another ran first:\n{finished.stdout}"
    )
    assert (tmp_path / "probe.png").stat().st_size > 0


def test_the_renderer_refuses_a_figure_that_breaks_the_relief_rule() -> None:
    """The relief rule is enforced where the colour is actually applied, not only described."""
    pytest.importorskip("matplotlib", reason="the `figures` extra is not installed")
    from hydms.figures.render import render

    unlabelled = Series(
        name="third entity",
        origin=MEASURED,
        mark="dot",
        x=(1.0,),
        y=(1.0,),
        slot=3,
    )
    figure = Figure(
        name="unlabelled",
        title="unlabelled",
        panels=(
            Panel(
                title="one",
                x=Axis(label="x", unit="wt%", lower=0.0, upper=2.0),
                y=Axis(label="y", unit="wt%", lower=0.0, upper=2.0),
                series=(unlabelled,),
            ),
        ),
        caption="a slot below contrast with nothing naming it",
    )
    assert figure.relief("light") == ("third entity",)
    with pytest.raises(ValueError, match="relief rule is not dismissable"):
        render(figure, theme="light")
