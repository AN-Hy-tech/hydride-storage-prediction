"""L11 -- an explanation of a model may not be computed on the rows it is scored on.

``benchmark_model_selection.py:1375,1383,1394``::

    shap_values = explainer.shap_values(X_test)
    ...
    PartialDependenceDisplay.from_estimator(model, X_test, features)

and ``REPORT.md`` section 6.1 is what those three lines produced. A SHAP summary computed on
the test split describes how the model uses its features *on the rows its published score is
claimed on* -- so a feature that happens to help on those particular rows is promoted to an
explanation of the model, and the plot and the score corroborate each other by construction.

**The defect is the population, and the record of it.** There are two ways to have leak L11 and
this file asserts against both: an explanation computed on a held-out split, and an explanation
that names no population at all. The second is the archival state proper -- the script wrote a
figure and nothing else, and which rows produced it had to be recovered from the source three
years later. A record that cannot say is not a record that is fine.

This is the sentinel card #29 owed, and the **thirteenth of thirteen**: until it existed,
`hydms.qa.sentinels.DEFERRED` recorded the gap -- "there is no such record until #29 defines
what SHAP and PDP are computed on" -- and gate HG-1 could not report green. The decision is
`hydms.surrogate.evaluate.EXPLAINABILITY`: the deployed fit's own **training** rows, read off
the fit's record rather than re-derived from the split, because screening drops some of them.
There is no dedicated explainability split; it would cost rows the deployed fit needs and buys
nothing over training-row SHAP.

Card #71, closed by card #29.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the detector runs over a record")

import pandas as pd  # noqa: E402
from hydms.qa import (  # noqa: E402
    LeakDetected,
    assert_explanation_is_not_held_out,
    for_leak,
)

HELD_OUT = ("val", "test")
FEATURES = ("avg_atomic_mass", "temperature(K)", "avg_valence_d")


def _record(computed_on: str = "train") -> pd.DataFrame:
    """A SHAP record in miniature: one row per feature, naming what it ran on."""
    return pd.DataFrame(
        {
            "feature": list(FEATURES),
            "mean_abs_shap": [0.31, 0.12, 0.07],
            "computed_on": [computed_on] * len(FEATURES),
        }
    )


# --------------------------------------------------------------------------------------
# The detector
# --------------------------------------------------------------------------------------


@pytest.mark.leak
def test_an_explanation_computed_on_the_test_split_is_the_archival_defect() -> None:
    with pytest.raises(LeakDetected, match="leak L11"):
        assert_explanation_is_not_held_out(
            _record("test"), held_out=HELD_OUT, where="the SHAP record"
        )


@pytest.mark.leak
def test_the_validation_split_is_held_out_too() -> None:
    """`val` chose the stopping iteration, so it is not a population to explain on either.

    The archival line names `X_test`, but the property is about held-out rows and not about
    that one name -- which is why the detector takes the whole list rather than the string.
    """
    with pytest.raises(LeakDetected, match="leak L11"):
        assert_explanation_is_not_held_out(
            _record("val"), held_out=HELD_OUT, where="the SHAP record"
        )


@pytest.mark.leak
def test_an_explanation_that_names_no_population_is_also_the_defect() -> None:
    """A record with no `computed_on` column passes any check that only reads values."""
    with pytest.raises(LeakDetected, match="no 'computed_on' column"):
        assert_explanation_is_not_held_out(
            _record().drop(columns=["computed_on"]),
            held_out=HELD_OUT,
            where="the SHAP record",
        )


@pytest.mark.leak
def test_an_empty_record_explains_nothing_and_says_so() -> None:
    empty = _record().iloc[:0]
    with pytest.raises(LeakDetected, match="names no population"):
        assert_explanation_is_not_held_out(
            empty, held_out=HELD_OUT, where="the SHAP record"
        )


@pytest.mark.leak
def test_the_training_rows_are_accepted() -> None:
    """The corrected twin. A detector that rejects the fix is one nobody can satisfy."""
    assert_explanation_is_not_held_out(
        _record("train"), held_out=HELD_OUT, where="the SHAP record"
    )


@pytest.mark.leak
def test_an_empty_holdout_is_a_caller_error_not_a_pass() -> None:
    """`ValueError`, not `LeakDetected`: the check would be vacuous, not satisfied.

    The convention `hydms.qa.detectors` states in its own docstring. A detector that reports
    a clean bill of health when it was misused is a detector nobody will believe.
    """
    with pytest.raises(ValueError, match="no held-out split names"):
        assert_explanation_is_not_held_out(
            _record(), held_out=(), where="the SHAP record"
        )


# --------------------------------------------------------------------------------------
# The real explainability path
# --------------------------------------------------------------------------------------


@pytest.mark.leak
def test_the_project_refuses_to_explain_a_held_out_split_at_the_door() -> None:
    """`shap_table` and `pdp_table` refuse before a single SHAP value is computed.

    Two guards and they are not redundant: this one is an `EvaluationError` -- the caller made
    a bad call -- and the detector above is a `LeakDetected` on what came out. The first is
    cheap and stops the mistake; the second is what the sentinel asserts against.
    """
    pytest.importorskip("catboost", reason="the subject is a fitted CatBoost model")
    from hydms.surrogate.evaluate import EvaluationError, pdp_table, shap_table

    for entry in (shap_table, pdp_table):
        with pytest.raises(EvaluationError, match="leak L11"):
            entry(None, pd.DataFrame(), computed_on="test")  # type: ignore[arg-type]


@pytest.mark.leak
def test_l11_is_registered_and_no_longer_deferred() -> None:
    """The last gap in the inventory. HG-1 counts a deferral as incompleteness, not coverage."""
    from hydms.qa.sentinels import DEFERRED

    sentinel = for_leak("L11")
    assert sentinel is not None, "L11 has a sentinel now; #29 is the card that owed it"
    assert sentinel.subject == "hydms.surrogate.evaluate"
    assert sentinel.detector == "hydms.qa.detectors.assert_explanation_is_not_held_out"
    assert sentinel.live is not None, "a sentinel pointed at a miniature guards nothing"
    assert "L11" not in {entry.leak for entry in DEFERRED}


@pytest.mark.leak
def test_nothing_in_the_inventory_is_deferred_any_more() -> None:
    """Thirteen leaks, thirteen sentinels. The state this phase's HG-1 was built to reach.

    Asserted rather than left as an observation, because the interesting failure is the
    *silent* one: a fourteenth leak added to the inventory with a deferral and no card, which
    would leave this at 13 of 14 while every existing test stayed green.
    """
    from hydms.qa.leaks import INVENTORY
    from hydms.qa.sentinels import DEFERRED, SENTINELS

    assert DEFERRED == (), f"still deferred: {[entry.leak for entry in DEFERRED]}"
    assert {sentinel.leak for sentinel in SENTINELS} == {leak.id for leak in INVENTORY}
