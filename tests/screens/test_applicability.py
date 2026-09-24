"""L4 -- the applicability-domain ceiling. Card #48.

``docs/QA-PROTOCOL.md`` names this layer's obligation as *every screen returns a verdict with
a reason; no silent drop*, and *boundary cases on each window, both sides*. This screen has
four thresholds rather than one window, so the boundary work is done four times: the capacity
ceiling, the physical ceiling, the interval width and the transfer floor, each admitted
exactly at the bound and refused one step past it.

The other half is what the card decided. Three assertions here are about the *derivation*
rather than about the code, and they exist so the decision cannot be quietly undone:

  - the committed reference is what the code measures from the curated data (``--emit``);
  - the ceiling is the highest capacity **more than one class** reaches, computed rather than
    typed, so new data moves it;
  - the physical ceiling admits every curated row except the four #48 named, which is the
    check that caught the card's own prescribed constant refusing 31 real materials.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("pandas", reason="the screen layer is pandas frames end to end")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from hydms.config import load as load_config  # noqa: E402
from hydms.screens.domain import (  # noqa: E402
    ABOVE_PHYSICAL_CEILING,
    CEILING_COLUMN,
    HIGH_UNCERTAINTY,
    HM_COLUMN,
    HM_MAX,
    OUT_OF_DOMAIN,
    OUTSIDE_FEATURE_RANGE,
    REFERENCE_FILE,
    SUPPORT_BIN_K,
    TRANSFER_COLUMN,
    UNTRUSTED_FAMILY,
    ApplicabilityDomain,
    DomainReference,
    applicability_domain,
    capacity_ceiling,
    emit,
    support_edges,
)
from hydms.screens.protocol import (  # noqa: E402
    ADMITTED,
    INDETERMINATE,
    Screen,
    ScreenError,
    apply_screens,
)

FORMULA = "Composition"
PREDICTION = "q0.5"
WIDTH = "interval_width"
CLASS = "Alloy_class"
FEATURE = "avg_valence_d"

#: A reference small enough to reason about, shaped exactly like the committed one.
REFERENCE = DomainReference(
    rows=893,
    trained_min=0.1,
    trained_max=7.19,
    cross_family_max=5.19,
    sole_family="Mg",
    rows_above=21,
    feature_span={FEATURE: (0.0, 10.0)},
    transfer={"Mg": -0.3381, "SS": 0.7626, "AB2": 0.3043},
)


@pytest.fixture()
def screen() -> ApplicabilityDomain:
    return ApplicabilityDomain(
        reference=REFERENCE,
        formula=FORMULA,
        prediction=PREDICTION,
        width=WIDTH,
        alloy_class=CLASS,
        hm_floor=2.5,
        max_interval_width=1.12,
        min_transfer_r2=0.0,
    )


def candidates(**columns: object) -> pd.DataFrame:
    """A batch whose length is taken from the longest column given."""
    length = max(len(value) for value in columns.values() if isinstance(value, list))
    return pd.DataFrame(
        {
            name: (value if isinstance(value, list) else [value] * length)
            for name, value in columns.items()
        }
    )


# --------------------------------------------------------------------------------------
# It is a screen at all
# --------------------------------------------------------------------------------------


def test_satisfies_the_screen_protocol(screen: ApplicabilityDomain) -> None:
    assert isinstance(screen, Screen)
    assert screen.name == "domain"
    assert ADMITTED not in screen.reasons
    assert len(set(screen.reasons)) == len(screen.reasons)


def test_runs_through_apply_screens(screen: ApplicabilityDomain) -> None:
    """The runner is the enforcement point, so the contract is asserted through it."""
    batch = candidates(
        **{FORMULA: ["LaNi5", "Mg2Ni"], PREDICTION: [1.4, 3.5], WIDTH: [0.9, 0.9]}
    )
    verdicts = apply_screens(batch, [screen])
    assert list(verdicts.table.index) == list(batch.index)
    assert verdicts.admitted.all()
    # the evidence columns arrive prefixed, which is the seam #44 built for this card
    assert f"domain.{CEILING_COLUMN}" in verdicts.table.columns
    assert f"domain.{HM_COLUMN}" in verdicts.table.columns
    assert f"domain.{TRANSFER_COLUMN}" in verdicts.table.columns


def test_every_declared_code_is_reachable(screen: ApplicabilityDomain) -> None:
    """QA-PROTOCOL L6: every refusal reason code is reachable and asserted.

    Asserted here rather than in the delivery layer because this screen declares them, and a
    code no batch can produce is a promise #75 would have to explain and #77 could not test.
    """
    # One row per code, each tripping exactly one signal so precedence cannot hide another.
    # LaNi5's physical ceiling is 4.197 wt%, which is below the 5.19 domain ceiling -- so
    # 4.5 is unphysical without also being unevidenced.
    batch = candidates(
        **{
            FORMULA: ["LaNi5", "Mg2Ni", "LaNi5", "LaNi5", "LaNi5", "LaNi5", "Nh2Ni"],
            PREDICTION: [1.4, 6.0, 4.5, 1.4, 1.4, 1.4, 1.4],
            WIDTH: [0.9, 0.9, 0.9, 2.0, 0.9, 0.9, 0.9],
            CLASS: ["AB2", "AB2", "AB2", "AB2", "AB2", "Mg", "AB2"],
            FEATURE: [5.0, 5.0, 5.0, 5.0, 99.0, 5.0, 5.0],
        }
    )
    verdicts = apply_screens(batch, [screen])
    seen = set(verdicts.table["domain.code"])
    assert set(screen.reasons) | {ADMITTED} >= seen
    for code in screen.reasons:
        assert code in seen, f"{code} was never emitted"


def test_every_rejection_carries_a_sentence(screen: ApplicabilityDomain) -> None:
    batch = candidates(
        **{FORMULA: ["Mg2Ni", "LaNi5"], PREDICTION: [6.0, 1.4], CLASS: ["Mg", "AB5"]}
    )
    verdicts = apply_screens(batch, [screen])
    rejections = verdicts.rejections()
    assert not rejections.empty
    assert rejections["reason"].str.strip().ne("").all()
    # the code names the worst failure; the reason names every one of them
    assert "5.19" in rejections.loc[0, "reason"]
    assert "Mg" in rejections.loc[0, "reason"]


# --------------------------------------------------------------------------------------
# The capacity ceiling -- both sides of the bound
# --------------------------------------------------------------------------------------


def test_the_ceiling_is_admitted_and_a_step_past_it_is_not(
    screen: ApplicabilityDomain,
) -> None:
    """5.19 wt% is a measured training capacity, so a candidate sitting on it is inside."""
    batch = candidates(
        **{FORMULA: "Mg2Ni", PREDICTION: [5.18, 5.19, 5.1900001, 5.20]}
    )
    verdict = screen.verdict(batch)
    assert list(verdict["passed"]) == [True, True, False, False]
    assert list(verdict["code"])[2:] == [OUT_OF_DOMAIN, OUT_OF_DOMAIN]


def test_out_of_domain_names_the_sole_family_and_its_transfer(
    screen: ApplicabilityDomain,
) -> None:
    verdict = screen.verdict(candidates(**{FORMULA: "Mg2Ni", PREDICTION: [6.5]}))
    reason = verdict.loc[0, "reason"]
    assert "Mg" in reason and "21" in reason and "-0.3381" in reason


def test_out_of_domain_is_not_high_uncertainty(screen: ApplicabilityDomain) -> None:
    """#30 measured the two coming apart, so they must be separable codes here.

    A candidate out of domain with a *narrow* band, and one inside the domain with a wide
    one. If either collapsed onto the other code this screen would have no argument.
    """
    batch = candidates(
        **{FORMULA: "Mg2Ni", PREDICTION: [6.5, 2.0], WIDTH: [0.30, 2.00]}
    )
    verdict = screen.verdict(batch)
    assert list(verdict["code"]) == [OUT_OF_DOMAIN, HIGH_UNCERTAINTY]
    assert not verdict["passed"].any()


# --------------------------------------------------------------------------------------
# The physical ceiling -- the arithmetic, and the instruction that was wrong
# --------------------------------------------------------------------------------------


def test_ceiling_is_the_stated_arithmetic() -> None:
    """MgH2: 2 x 1.008 / 24.305 x 100 = 8.294 wt%, and Mg's H/M is 2 not the 2.5 floor."""
    evidence = capacity_ceiling(["Mg"], floor=2.0)
    assert evidence.loc[0, HM_COLUMN] == pytest.approx(2.0)
    assert evidence.loc[0, CEILING_COLUMN] == pytest.approx(8.294, abs=1e-3)


def test_the_floor_is_a_floor_and_the_element_maximum_wins_above_it() -> None:
    """Y forms YH3, so an Mg-Y alloy is bounded at 3 and not at the 2.5 floor.

    This is the half of the rule the card's prescribed constant did not have, and it is why
    ``Mg22Y3`` at 6.48 wt% is a real material rather than an unphysical one.
    """
    evidence = capacity_ceiling(["Mg22Y3", "LaNi5", "TiFe"], floor=2.5)
    assert list(evidence[HM_COLUMN]) == [3.0, 3.0, 2.5]
    assert evidence.loc[0, CEILING_COLUMN] > 6.48


def test_a_weighted_average_would_not_be_a_bound() -> None:
    """The rejected alternative, asserted so nobody re-derives it.

    ``LaNi5`` holds H/M 1.0. The element-wise maximum bounds it at 3.0; a composition
    weighted average of the constituents' binary stoichiometries gives (3 + 5x0)/6 = 0.5,
    which is *below* the measured value -- so it is not an upper bound at all.
    """
    weighted = (HM_MAX["La"] * 1 + HM_MAX.get("Ni", 0.0) * 5) / 6
    assert weighted < 1.0
    assert capacity_ceiling(["LaNi5"], floor=2.5).loc[0, HM_COLUMN] == 3.0


def test_a_prediction_above_the_physical_ceiling_is_refused(
    screen: ApplicabilityDomain,
) -> None:
    """LaNi5's ceiling is ~4.2 wt%; a model claiming 5 wt% for it is claiming hydrogen."""
    ceiling = capacity_ceiling(["LaNi5"], floor=2.5).loc[0, CEILING_COLUMN]
    batch = candidates(**{FORMULA: "LaNi5", PREDICTION: [ceiling, ceiling + 0.01]})
    verdict = screen.verdict(batch)
    assert list(verdict["passed"]) == [True, False]
    assert verdict.loc[1, "code"] == ABOVE_PHYSICAL_CEILING


def test_physical_ceiling_outranks_the_domain_ceiling(
    screen: ApplicabilityDomain,
) -> None:
    """Both fire; "impossible" is the more useful thing to tell a caller than "unevidenced"."""
    verdict = screen.verdict(candidates(**{FORMULA: "LaNi5", PREDICTION: [6.0]}))
    assert verdict.loc[0, "code"] == ABOVE_PHYSICAL_CEILING
    assert "above" in verdict.loc[0, "reason"]
    # the reason still says both
    assert "5.19" in verdict.loc[0, "reason"]


def test_the_physical_ceiling_admits_the_curated_rows_it_should() -> None:
    """The check that caught the card's own constant. Four rows over, and they are named.

    **Not marked slow, and it was measured before being left unmarked**: it reads and parses
    all 1,279 curated formulae in **0.27 s**, because it featurises nothing. Marking it would
    have put the one regression test guarding a physics bound against tightening onto real
    materials behind a lane CI deselects, which is the failure mode
    ``docs/QA-PROTOCOL.md`` 5 exists to stop.
    """
    from hydms.data.canonical import alloy_classes
    from hydms.data.load import load_hydride_data
    from hydms.data.metadata import with_metadata

    cfg = load_config()
    record = with_metadata(load_hydride_data())
    evidence = capacity_ceiling(
        record[cfg.columns.formula],
        floor=cfg.domain.capacity_ceiling_hm_floor,
        index=record.index,
    )
    target = record[cfg.columns.target].astype(float)
    over = target > evidence[CEILING_COLUMN]
    assert evidence[CEILING_COLUMN].notna().all(), "every curated formula must be bounded"
    assert int(over.sum()) == 4, f"{int(over.sum())} rows above their ceiling, expected 4"
    named = set(record.loc[over, cfg.columns.formula])
    assert named == {
        "Ce1Ni3Cr2",
        "Ce1Ni4Zr1",
        "Ce1Ni4Cr1",
        "Ti1.1Cr1Mn1V0.255Fe0.045",
    }
    # three of the four are the Ce-Ni data defects boxed on #14; the fourth is Sahlberg's
    # limit to within a rounding, so it must be over by a hair rather than by a margin
    classes = alloy_classes(record)
    excess = (target - evidence[CEILING_COLUMN])[over]
    hair = record.loc[over, cfg.columns.formula] == "Ti1.1Cr1Mn1V0.255Fe0.045"
    assert float(excess[hair].iloc[0]) < 0.01
    assert set(classes[over]) == {"AB5", "AB2"}


# --------------------------------------------------------------------------------------
# The other two signals
# --------------------------------------------------------------------------------------


def test_a_feature_outside_the_trained_span_is_refused(
    screen: ApplicabilityDomain,
) -> None:
    """Closed interval: both bounds are measured training values, so both are inside."""
    batch = candidates(
        **{FORMULA: "LaNi5", PREDICTION: 1.4, FEATURE: [-0.001, 0.0, 10.0, 10.001]}
    )
    verdict = screen.verdict(batch)
    assert list(verdict["passed"]) == [False, True, True, False]
    assert verdict.loc[0, "code"] == OUTSIDE_FEATURE_RANGE
    assert FEATURE in verdict.loc[0, "reason"]
    assert "0 to 10" in verdict.loc[0, "reason"]


def test_an_untrusted_class_is_refused_and_the_boundary_is_the_floor(
    screen: ApplicabilityDomain,
) -> None:
    """R2 exactly at the floor is admitted; below it is not. Mg (-0.3381) is below."""
    batch = candidates(
        **{FORMULA: "LaNi5", PREDICTION: 1.4, CLASS: ["SS", "AB2", "Mg"]}
    )
    verdict = screen.verdict(batch)
    assert list(verdict["passed"]) == [True, True, False]
    assert verdict.loc[2, "code"] == UNTRUSTED_FAMILY
    assert list(verdict[TRANSFER_COLUMN]) == pytest.approx([0.7626, 0.3043, -0.3381])


def test_the_class_signal_is_independent_of_composition_and_prediction(
    screen: ApplicabilityDomain,
) -> None:
    """The card asks for a *second, independent* signal, so it must fire on its own."""
    verdict = screen.verdict(
        candidates(**{FORMULA: "LaNi5", PREDICTION: [1.4], CLASS: ["Mg"]})
    )
    assert verdict.loc[0, "code"] == UNTRUSTED_FAMILY
    assert verdict.loc[0, CEILING_COLUMN] > 1.4  # the composition itself is fine


def test_the_interval_width_boundary(screen: ApplicabilityDomain) -> None:
    batch = candidates(**{FORMULA: "LaNi5", PREDICTION: 1.4, WIDTH: [1.12, 1.1200001]})
    verdict = screen.verdict(batch)
    assert list(verdict["passed"]) == [True, False]
    assert verdict.loc[1, "code"] == HIGH_UNCERTAINTY


# --------------------------------------------------------------------------------------
# Fail-closed
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("column", "value"),
    [(PREDICTION, np.nan), (WIDTH, np.nan), (FEATURE, np.nan)],
)
def test_a_value_it_cannot_read_is_a_rejection(
    screen: ApplicabilityDomain, column: str, value: float
) -> None:
    batch = candidates(
        **{FORMULA: "LaNi5", PREDICTION: 1.4, WIDTH: 0.9, FEATURE: 5.0, column: [value]}
    )
    verdict = screen.verdict(batch)
    assert verdict.loc[0, "code"] == INDETERMINATE
    assert not verdict.loc[0, "passed"]


def test_an_unparseable_formula_is_indeterminate(screen: ApplicabilityDomain) -> None:
    verdict = screen.verdict(
        candidates(**{FORMULA: ["!!not a formula!!"], PREDICTION: [1.4]})
    )
    assert verdict.loc[0, "code"] == INDETERMINATE
    assert np.isnan(verdict.loc[0, CEILING_COLUMN])


def test_an_element_with_no_mass_is_indeterminate_not_zero(
    screen: ApplicabilityDomain,
) -> None:
    """A ceiling computed with a missing mass would be infinite and admit everything."""
    evidence = capacity_ceiling(["Og2Ni"], floor=2.5)
    assert np.isnan(evidence.loc[0, CEILING_COLUMN])


def test_a_class_the_protocol_never_measured_is_indeterminate(
    screen: ApplicabilityDomain,
) -> None:
    verdict = screen.verdict(
        candidates(**{FORMULA: "LaNi5", PREDICTION: [1.4], CLASS: ["Perovskite"]})
    )
    assert verdict.loc[0, "code"] == INDETERMINATE
    assert "Perovskite" in verdict.loc[0, "reason"]


def test_a_missing_formula_column_raises(screen: ApplicabilityDomain) -> None:
    """That is the wrong frame, not a fact about any candidate in it."""
    with pytest.raises(ScreenError, match=FORMULA):
        screen.verdict(pd.DataFrame({PREDICTION: [1.4]}))


def test_a_batch_with_nothing_to_judge_raises(screen: ApplicabilityDomain) -> None:
    """Admitting a batch nothing could judge is the silent drop's mirror image."""
    with pytest.raises(ScreenError, match="nothing to judge"):
        screen.verdict(pd.DataFrame({FORMULA: ["LaNi5"]}))


def test_a_batch_with_only_features_is_judgeable(screen: ApplicabilityDomain) -> None:
    """Screening before predicting is a legitimate call, and the range check still runs."""
    verdict = screen.verdict(candidates(**{FORMULA: "LaNi5", FEATURE: [5.0, 99.0]}))
    assert list(verdict["passed"]) == [True, False]


@pytest.mark.parametrize("floor", [0.0, -1.0, float("nan")])
def test_a_useless_floor_raises(floor: float) -> None:
    with pytest.raises(ScreenError, match="floor"):
        capacity_ceiling(["LaNi5"], floor=floor)


def test_a_threshold_that_refuses_everything_raises() -> None:
    with pytest.raises(ScreenError, match="max_interval_width"):
        ApplicabilityDomain(
            reference=REFERENCE,
            formula=FORMULA,
            prediction=PREDICTION,
            width=WIDTH,
            alloy_class=CLASS,
            hm_floor=2.5,
            max_interval_width=0.0,
            min_transfer_r2=0.0,
        )


# --------------------------------------------------------------------------------------
# The derivation, pinned
# --------------------------------------------------------------------------------------


def test_the_committed_reference_reads_back(screen: ApplicabilityDomain) -> None:
    reference = DomainReference.packaged()
    assert reference.rows == 893
    assert reference.cross_family_max == 5.19
    assert reference.sole_family == "Mg"
    assert reference.rows_above == 21
    assert len(reference.feature_span) == 14
    assert len(reference.transfer) == 10
    assert DomainReference.from_json(reference.to_json()) == reference


def test_the_committed_reference_is_the_file_on_disk() -> None:
    """Round-trip through the exact bytes, so a hand edit shows up as a diff and a failure."""
    assert REFERENCE_FILE.read_text(encoding="utf-8") == DomainReference.packaged().to_json()


def test_the_ceiling_is_computed_not_typed() -> None:
    """The level is the highest capacity **more than one class** reaches.

    Asserted on a synthetic corpus so the rule is visible independently of the real numbers:
    change the data and the ceiling moves, which is the property that stops 5.19 becoming a
    constant somebody later trusts for its own sake.
    """
    training = pd.DataFrame({"y": [1.0, 2.0, 9.0, 3.0], FEATURE: [0.0, 1.0, 2.0, 3.0]})
    classes = pd.Series(["A", "B", "A", "B"], index=training.index)
    reference = DomainReference.measured(
        training, classes, target="y", features=[FEATURE], transfer={"A": 0.5, "B": 0.5}
    )
    assert reference.trained_max == 9.0
    assert reference.sole_family == "A"
    assert reference.cross_family_max == 3.0  # the best class B does, not the best overall
    assert reference.rows_above == 1


def test_a_single_family_corpus_cannot_derive_a_ceiling() -> None:
    training = pd.DataFrame({"y": [1.0, 2.0], FEATURE: [0.0, 1.0]})
    classes = pd.Series(["A", "A"], index=training.index)
    with pytest.raises(ScreenError, match="single-family"):
        DomainReference.measured(
            training, classes, target="y", features=[FEATURE], transfer={"A": 0.5}
        )


def test_the_builder_reads_every_threshold_from_config() -> None:
    """The card's third criterion: an R1 iteration tightens the domain without a code change."""
    cfg = load_config()
    screen = applicability_domain(cfg)
    assert screen.hm_floor == cfg.domain.capacity_ceiling_hm_floor
    assert screen.max_interval_width == cfg.domain.max_interval_width_wt_pct
    assert screen.min_transfer_r2 == cfg.domain.min_transfer_r2
    assert screen.formula == cfg.columns.formula
    assert screen.alloy_class == cfg.columns.alloy_class
    # the point estimate, not the lower confidence bound -- see the dataclass docstring
    assert screen.prediction == "q0.5"


def test_the_screen_composes_with_the_temperature_window() -> None:
    """The two bounds are different things, and #44's runner is where they meet."""
    from hydms.screens.window import temperature_window

    cfg = load_config()
    batch = pd.DataFrame(
        {
            cfg.columns.formula: ["LaNi5", "Mg2Ni"],
            cfg.columns.temperature: [300.0, 1200.0],
            "q0.5": [1.4, 6.0],
        }
    )
    verdicts = apply_screens(batch, [temperature_window(cfg), applicability_domain(cfg)])
    assert list(verdicts.admitted) == [True, False]
    rejections = verdicts.rejections()
    assert set(rejections["screen"]) == {"temperature", "domain"}


def test_an_empty_batch_is_judged_without_special_casing(
    screen: ApplicabilityDomain,
) -> None:
    """A screen can be handed nothing left after an earlier filter, and must not raise.

    #76 composes predict-then-screen, so an empty frame is reachable in the delivery path
    rather than only in a test. The columns must still be there: a caller writing the verdict
    table out should not have to branch on the happy path.
    """
    batch = pd.DataFrame({FORMULA: pd.Series([], dtype=object), PREDICTION: pd.Series([], dtype=float)})
    verdict = screen.verdict(batch)
    assert len(verdict) == 0
    assert list(verdict.columns)[:3] == ["passed", "code", "reason"]
    assert CEILING_COLUMN in verdict.columns


# --------------------------------------------------------------------------------------
# The temperature support (card #82)
# --------------------------------------------------------------------------------------


def test_the_committed_support_counts_every_training_row_across_the_configured_window() -> None:
    """The histogram ``GET /v1/model`` serves, so a sweep can say how many rows back it."""
    reference = DomainReference.packaged()
    config = load_config()

    assert sum(reference.temperature_counts) == reference.rows == 893
    assert len(reference.temperature_edges) == len(reference.temperature_counts) + 1
    assert reference.temperature_edges[0] <= config.domain.temperature_min_k
    assert reference.temperature_edges[-1] >= config.domain.temperature_max_k
    assert all(edge % SUPPORT_BIN_K == 0 for edge in reference.temperature_edges)


def test_the_committed_reference_is_what_emit_measures() -> None:
    """The module docstring has claimed this since #48 and no test checked it until #82.

    Not marked slow: it re-measures from the curated data in a few seconds, the same budget
    ``test_novelty.py``'s twin was measured at, and a committed file whose only guard is in the
    lane CI deselects has no guard.
    """
    assert REFERENCE_FILE.read_text(encoding="utf-8") == emit().to_json()


def test_support_edges_are_aligned_and_cover_the_window() -> None:
    assert support_edges(195.0, 773.0) == tuple(float(k) for k in range(150, 801, 50))
    assert support_edges(200.0, 300.0) == (200.0, 250.0, 300.0)
    with pytest.raises(ScreenError, match="no support bins"):
        support_edges(300.0, 300.0)


def test_the_support_is_counted_half_open_with_the_last_bin_closed() -> None:
    """The convention `TemperatureSupport.measured` states, so the served bars match a redraw."""
    training = pd.DataFrame(
        {"y": [1.0, 2.0, 3.0, 4.0], "T": [200.0, 250.0, 260.0, 300.0], FEATURE: [0.0] * 4}
    )
    classes = pd.Series(["A", "B", "A", "B"], index=training.index)
    reference = DomainReference.measured(
        training, classes, target="y", features=[FEATURE], transfer={},
        temperature="T", temperature_edges=(200.0, 250.0, 300.0),
    )

    assert reference.temperature_counts == (1, 3)
    assert DomainReference.from_json(reference.to_json()) == reference


def test_a_row_outside_the_support_edges_is_an_error_not_a_row_left_uncounted() -> None:
    training = pd.DataFrame({"y": [1.0, 2.0], "T": [200.0, 900.0], FEATURE: [0.0, 1.0]})
    classes = pd.Series(["A", "B"], index=training.index)
    with pytest.raises(ScreenError, match="outside the support edges"):
        DomainReference.measured(
            training, classes, target="y", features=[FEATURE], transfer={},
            temperature="T", temperature_edges=(150.0, 200.0, 250.0),
        )


def test_edges_without_a_column_measure_nothing_and_say_so() -> None:
    training = pd.DataFrame({"y": [1.0, 2.0], FEATURE: [0.0, 1.0]})
    classes = pd.Series(["A", "B"], index=training.index)
    with pytest.raises(ScreenError, match="both the column"):
        DomainReference.measured(
            training, classes, target="y", features=[FEATURE], transfer={},
            temperature_edges=(150.0, 200.0),
        )


def test_a_support_that_counts_different_rows_is_refused() -> None:
    """Same rows counted twice; a mismatch means one count was of something else."""
    payload = json.loads(DomainReference.packaged().to_json())
    payload["temperature_support"]["counts"][0] += 1
    with pytest.raises(ScreenError, match="counts 894 row"):
        DomainReference.from_json(json.dumps(payload))


def test_a_reference_without_a_support_serialises_without_one() -> None:
    """Absent is omitted, never written as an empty histogram that reads as 'no rows'."""
    assert "temperature_support" not in json.loads(REFERENCE.to_json())
    assert DomainReference.from_json(REFERENCE.to_json()).temperature_counts == ()
