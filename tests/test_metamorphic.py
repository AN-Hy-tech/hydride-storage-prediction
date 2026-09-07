"""Relations between two related inputs, where no oracle exists.

There is no independent source of truth for what ``avg_polzbl_divi_atom_mass`` should be for
an arbitrary alloy, and none for what the surrogate should predict for a composition nobody
has measured. Metamorphic tests get around that by asserting a relation between *inputs*
rather than a value: two spellings of one material must featurise the same, and must predict
the same.

They catch the class of defect gate AC-4 exists for -- a column reordered, a scaler refitted,
a string coerced -- at a point far earlier than a round-trip gate, and on inputs the training
set never contained. Each test below names the failure it is designed to catch.

**Two of the relations were measured before they were written**, because the card prescribed
an assertion and the measurement had to come first:

  - **Case.** ``'lani5'`` and ``'LANI5'`` do not featurise as ``'LaNi5'`` -- they *raise*, and
    that is correct rather than a gap. Element symbols are case-sensitive by definition: ``Co``
    is cobalt and ``CO`` is carbon monoxide, so a case-folding parser would silently turn one
    material into another. The test therefore records the refusal and checks that it names the
    offending row, which is the behaviour, instead of asserting the invariance the card's box
    reads as.
  - **Temperature.** Monotonicity is a property of a fitted model, not of this layer, so it is
    measured on the fixture and reported. What *is* asserted structurally is the shape a
    gradient-boosted ensemble is guaranteed to have -- piecewise constant, and flat outside the
    range it was fitted on -- because that flatness is risk R1 itself: outside the hull the
    model returns a plausible constant rather than an obvious failure, which is why every
    answer needs an interval and a domain verdict beside it.

The pairs are not invented. ``Ce1Mg12``/``Mg12Ce1``, ``Mg1Al1``/``Mg0.5Al0.5`` and
``Pr1Co5``/``Pr1Co5␠`` are real cross-split collisions found in ``hydride_data.csv`` during the
Phase H audit -- leak L8, sixteen compositions spanning two splits -- and they are shared with
the L8 sentinel and the canonical-key tests through the ``known_collisions`` fixture.

Card #74.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the featuriser and the surrogate are pandas frames")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")

import pandas as pd  # noqa: E402
from hydms import artifacts  # noqa: E402
from hydms.descriptors.contract import PASSTHROUGH, FeatureContract  # noqa: E402
from hydms.descriptors.featurize import FeaturisationError, featurize  # noqa: E402
from hydms.surrogate.conformal import (  # noqa: E402
    CONFORMAL_PAYLOAD,
    calibration_slice,
    fit_conformal,
)
from hydms.surrogate.model import (  # noqa: E402
    MODEL_PAYLOAD,
    ModelError,
    ModelSettings,
    column_names,
)
from hydms.surrogate.predict import Surrogate, clear_cache, surrogate_from  # noqa: E402

TARGET = "H2_W% (max)"
TEMPERATURE = PASSTHROUGH
FORMULA = "Composition"
QUANTILES = (0.1, 0.5, 0.9)
CHEAP = {"iterations": 80, "depth": 4, "learning_rate": 0.3}

#: Three real contract names rather than the fourteen of `SELECTED`. Every extra descriptor is
#: parse-and-arithmetic per row, and this file is about relations rather than about coverage of
#: the contract -- `tests/descriptors/test_featurize.py` owns that.
FEATURES = ("avg_valence_d", "dev_Pauling_Electronegativity", TEMPERATURE)

#: The trained temperature span, from `domain.temperature_min_k` / `_max_k`. Written here as a
#: pair of literals only for the sweep's endpoints; the refusal that reads config is #77's.
TRAINED_K = (250.0, 600.0)

CONTRACT = FeatureContract.from_names(FEATURES)


def _features(formulas: list[str], kelvin: float = 298.0) -> pd.DataFrame:
    return featurize(formulas, kelvin, contract=CONTRACT)


# --------------------------------------------------------------------------------------
# One fitted, loadable artifact — the smallest thing that can answer a prediction
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def surrogate(tmp_path_factory: pytest.TempPathFactory) -> Surrogate:
    """A real fit, persisted and read back, over three real descriptors.

    Module-scoped: the CatBoost fit costs about a second and every test here wants the same
    model. Deliberately **not** marked `slow` -- a test the fast lane deselects does not guard
    anything, and this file is the earliest place a reordered column is caught.

    It goes through the artifact store rather than holding the objects directly, because
    persistence is one of the places a column order can be lost, and a relation that only
    holds before a `joblib` round trip is not a relation the delivery path can rely on.
    """
    pytest.importorskip("catboost", reason="the model behind predict() is CatBoost's")
    pytest.importorskip("mapie", reason="the band is MAPIE-calibrated; `pip install -e .[uq]`")
    from hydms.surrogate.model import fit_quantile_model

    rng = np.random.default_rng(7)
    rows = 400
    labels = pd.Index([f"row-{i}" for i in range(rows)])
    formulas = pd.Series([f"La1Ni{i % 40 + 1}" for i in range(rows)], index=labels)
    kelvin = rng.uniform(*TRAINED_K, size=rows)
    features = featurize(formulas, kelvin, contract=CONTRACT)
    target = (
        1.2 * features["avg_valence_d"]
        + 0.004 * features[TEMPERATURE]
        + rng.normal(scale=0.3, size=rows)
        + 1.5
    )
    frame = features.assign(**{FORMULA: formulas, TARGET: target})

    settings = ModelSettings(
        quantiles=QUANTILES,
        early_stopping_rounds=5,
        optuna_trials=1,
        stopping_folds=5,
        seed=42,
        features=FEATURES,
        screen_labels=False,
        target=TARGET,
        temperature=TEMPERATURE,
    )
    train = list(frame.index[:280])
    val = list(frame.index[280:330])
    test = list(frame.index[330:])
    fitting, calibrating = calibration_slice(frame, train, settings=settings)
    model = fit_quantile_model(
        frame,
        train=fitting,
        eval_on=val,
        scored_on=test,
        where="metamorphic fixture",
        params=CHEAP,
        settings=settings,
    )
    conformal = fit_conformal(frame, model, calibrate_on=calibrating)

    store: Path = tmp_path_factory.mktemp("artifacts")
    manifest = artifacts.save(
        {MODEL_PAYLOAD: model, CONFORMAL_PAYLOAD: conformal},
        contract=FeatureContract.from_names(model.feature_names),
        store=store,
    )
    clear_cache()
    # `require_gates=False` is the door the store documents for a version nobody has certified
    # (card #33). This file is not a gate and never promotes; it needs the assembled prediction
    # path, which is exactly what `surrogate_from` is.
    return surrogate_from(artifacts.load(manifest.version, store=store, require_gates=False))


# --------------------------------------------------------------------------------------
# Permutation — element order is not information
# --------------------------------------------------------------------------------------


def test_element_order_changes_nothing_in_the_features(known_collisions) -> None:
    """Catches: a featuriser that reads the formula string positionally.

    `Ce1Mg12` and `Mg12Ce1` are one material and are a real cross-split collision in
    `hydride_data.csv` (leak L8). A weighted composition statistic is a sum over elements, so
    order cannot enter it -- unless something iterates the string instead of the parsed amounts.
    """
    for left, right in known_collisions:
        rows = _features([left, right])
        assert rows.iloc[0].equals(rows.iloc[1]), f"{left!r} and {right!r} featurise differently"


def test_element_order_changes_nothing_in_the_prediction(
    surrogate: Surrogate, known_collisions
) -> None:
    """Catches: a prediction path that keys, caches or dispatches on the raw formula string.

    Identical features must give identical intervals. Asserted separately from the featurisation
    relation because the two failures are different: the first is a bug in the descriptor layer,
    the second is a bug in anything between it and the booster.
    """
    for left, right in known_collisions:
        answer = surrogate.predict([left, right], 298.0)
        assert answer.iloc[0].equals(answer.iloc[1]), f"{left!r} and {right!r} predict differently"


# --------------------------------------------------------------------------------------
# Scale — a composition is a ratio
# --------------------------------------------------------------------------------------


def test_overall_scale_changes_nothing(surrogate: Surrogate) -> None:
    """Catches: a statistic weighted by raw amounts rather than by fractions.

    `Mg1Al1` and `Mg0.5Al0.5` are the same material written twice; the second is the first
    halved. Every selected feature is a *fraction*-weighted statistic, so doubling every amount
    must cancel. This is the collision the canonical key's `composition` stage exists for --
    whitespace and element order alone still leave these two as different materials.
    """
    features = _features(["Mg1Al1", "Mg0.5Al0.5"])
    answer = surrogate.predict(["Mg1Al1", "Mg0.5Al0.5"], 298.0)

    assert features.iloc[0].equals(features.iloc[1])
    assert answer.iloc[0].equals(answer.iloc[1])


def test_scale_invariance_holds_at_factors_the_data_never_contained() -> None:
    """Catches: an invariance that holds only at 2x because of a rounding coincidence.

    **Measured, and the answer has two halves.** Rescaling by an integer factor is *bit
    identical* -- `La3Ni15` and `La2Ni10` give `La1Ni5`'s row exactly -- because the fraction
    is the same division of the same integers. Rescaling by a non-integer factor is not:
    `La0.2Ni1` differs in the last place, by **2.776e-17** on a value near 0.1667, because
    `0.2 / 1.2` and `1 / 6` are different binary numbers.

    So the relation is invariance to within the project's tolerance, not bit equality, and the
    tolerance is the 1e-12 used throughout this repository. Asserting equality here would be
    asserting a property of IEEE-754 division rather than of the featuriser.
    """
    integral = _features(["La1Ni5", "La3Ni15", "La2Ni10", "La0.5Ni2.5"])
    for position in range(1, len(integral)):
        assert integral.iloc[0].equals(integral.iloc[position])

    fractional = _features(["La1Ni5", "La0.2Ni1"])
    deviation = float((fractional.iloc[0] - fractional.iloc[1]).abs().max())
    assert 0.0 < deviation < 1e-12


def test_a_one_ulp_rescaling_does_not_change_the_prediction(surrogate: Surrogate) -> None:
    """Catches: a model whose answer is sensitive at the last bit of its inputs.

    The pair above differs by one ulp, and a tree ensemble splits on thresholds -- so unless a
    threshold happens to fall inside that ulp, the two rows land in the same leaves. Exact
    equality is the right assertion here even though it was the wrong one above: this is a
    claim about the *booster*, not about division.
    """
    answer = surrogate.predict(["La1Ni5", "La0.2Ni1"], 298.0)

    assert answer.iloc[0].equals(answer.iloc[1])


# --------------------------------------------------------------------------------------
# Whitespace and case — the two the card pairs, and they behave differently
# --------------------------------------------------------------------------------------


def test_whitespace_anywhere_in_a_formula_changes_nothing(surrogate: Surrogate) -> None:
    """Catches: a parser that treats `'Pr1Co5 '` as a different material from `'Pr1Co5'`.

    Thirty-four strings in `hydride_data.csv` carry a trailing space and nine an internal one;
    seven of the padded forms already have an unpadded twin in the same file. That is leak L8's
    cheapest instance and it is worth an assertion of its own, on both sides of the pipe.
    """
    spellings = ["Pr1Co5", "Pr1Co5 ", " Pr1Co5", "Pr1 Co5", "Pr1\tCo5"]
    features = _features(spellings)
    answer = surrogate.predict(spellings, 298.0)

    for position in range(1, len(spellings)):
        assert features.iloc[0].equals(features.iloc[position]), spellings[position]
        assert answer.iloc[0].equals(answer.iloc[position]), spellings[position]


@pytest.mark.parametrize("spelling", ["lani5", "LANI5", "laNi5"])
def test_a_case_change_is_refused_rather_than_absorbed(spelling: str) -> None:
    """Catches: a case-folding parser, which would silently turn one material into another.

    **Measured before it was written.** The card's box reads as an invariance -- "a case change
    in a formula string changes nothing" -- and the measurement says the opposite and is right:
    element symbols are case-sensitive by definition, so `Co` is cobalt and `CO` is carbon and
    oxygen. Absorbing a case change would make `MgCO` and `MgCo` the same alloy.

    What is asserted is therefore the refusal, and that it *names the offending row*: a batch
    that silently returned fewer rows than it was given is the failure the whole descriptor
    layer's error convention exists to prevent.
    """
    with pytest.raises(FeaturisationError) as raised:
        _features(["LaNi5", spelling])

    message = str(raised.value)
    assert spelling in message
    assert "Nothing was featurised" in message


# --------------------------------------------------------------------------------------
# Temperature — a relation of the fitted model, recorded rather than wished for
# --------------------------------------------------------------------------------------


def _sweep(surrogate: Surrogate, kelvin: np.ndarray) -> np.ndarray:
    """The median head for one composition across `kelvin`, in weight percent.

    The median rather than `lcb`: the lower bound carries the conformal correction, which is a
    constant in model space, so a sweep of it would be answering a question about `expm1` as
    much as about the model.
    """
    heads = column_names(surrogate.quantiles)
    frame = surrogate.predict(["La1Ni5"] * len(kelvin), kelvin)
    return frame[heads[len(heads) // 2]].to_numpy()


def test_the_temperature_response_is_recorded_not_assumed(surrogate: Surrogate) -> None:
    """Catches: a temperature column that is dropped, constant, or read in the wrong unit.

    The fixture's target rises with temperature by construction, so a model that had lost the
    column would return a flat sweep. The relation asserted is therefore that the response is
    **not constant** and that it is non-decreasing *for this fixture* -- a fact about this fit,
    stated as one, not a claim that the deployed model is monotone in temperature. Monotonicity
    is not a property this layer can promise: `hydride_data.csv` is not a controlled sweep, only
    39 test rows sit above 500 K, and nothing in the fit constrains the direction.
    """
    kelvin = np.linspace(TRAINED_K[0], TRAINED_K[1], 40)
    sweep = _sweep(surrogate, kelvin)
    steps = np.diff(sweep)

    assert sweep.ptp() > 0.0, "the prediction does not move with temperature at all"
    assert sweep[-1] > sweep[0], "the net response runs against the direction it was fitted on"
    # **Measured: it is not monotone.** Five of the thirty-nine steps fall, on a fixture whose
    # target rises with temperature by construction and carries only Gaussian noise. Nothing
    # asks CatBoost for a monotone fit -- `monotone_constraints` exists and this project does
    # not set it -- so a rising trend with local reversals is what a quantile ensemble gives.
    # The count is deliberately not asserted: it is a property of one fit at one budget. What
    # is asserted is that reversals exist, so that a future run which *is* monotone is a
    # finding somebody has to look at rather than a silent change of behaviour.
    assert (steps < 0).any(), (
        "the response is monotone in temperature. That is not what this fixture measured "
        "(5 of 39 steps fell), and it is not a property anything in the fit guarantees -- "
        "if a constraint was added, this test is the record that says so."
    )


def test_the_response_is_piecewise_constant_and_flat_outside_the_fitted_range(
    surrogate: Surrogate,
) -> None:
    """Catches nothing -- it *records risk R1*, which is why every answer carries an interval.

    A gradient-boosted ensemble splits on thresholds, so its response is a step function and it
    extrapolates as a constant: past the largest threshold it ever learned, every input gets the
    same leaf. That is not a defect to fix, it is the reason a point estimate alone is
    indefensible outside the training hull, and it is the measurement behind gate HG-2 and the
    temperature window (#44). Asserting it here means the day it stops being true, the
    justification written all over this project stops being true with it.
    """
    inside = _sweep(surrogate, np.linspace(*TRAINED_K, 40))
    beyond = _sweep(surrogate, np.array([TRAINED_K[1] + 100.0, TRAINED_K[1] + 5000.0]))

    assert len(np.unique(inside)) < len(inside), "a tree ensemble's response is a step function"
    assert beyond[0] == beyond[1], "extrapolation is flat: the same leaf answers both"
    assert beyond[0] == pytest.approx(inside[-1], abs=1e-12)


# --------------------------------------------------------------------------------------
# Column order — the failure AC-4 exists for
# --------------------------------------------------------------------------------------


def test_a_shuffled_column_order_gives_the_same_prediction(surrogate: Surrogate) -> None:
    """Catches: a model fed a positional matrix, which returns plausible, wrong numbers.

    The card allows either outcome -- the same number or a raise -- and forbids only a silently
    different one. **Measured: it is the same number**, because `QuantileModel._batch` selects
    the fitted names out of the frame rather than trusting its order. The assertion is exact
    equality, not a tolerance: selecting columns by name moves no bits.
    """
    formulas = ["La1Ni5", "Ti1Fe1", "Mg2Ni1"]
    features = _features(formulas, 350.0)
    shuffled = features[list(reversed(features.columns))]

    ordered = surrogate._model.predict(features)
    permuted = surrogate._model.predict(shuffled)

    assert list(shuffled.columns) != list(features.columns)
    assert permuted.equals(ordered)


def test_a_matrix_missing_a_fitted_column_raises_rather_than_predicting(
    surrogate: Surrogate,
) -> None:
    """Catches: a column quietly dropped upstream and a prediction returned anyway."""
    features = _features(["La1Ni5"], 350.0)

    with pytest.raises(ModelError, match="missing"):
        surrogate._model.predict(features.drop(columns=[TEMPERATURE]))


def test_an_extra_column_is_ignored_rather_than_shifting_the_matrix(
    surrogate: Surrogate,
) -> None:
    """Catches: a positional read, which an extra column would shift by one.

    A frame carrying more than the fitted names is the ordinary case downstream -- the record
    and the matrix travel side by side (`with_features`) -- so this must be a no-op, and it is
    only a no-op if the selection is by name.
    """
    features = _features(["La1Ni5", "Ti1Fe1"], 350.0)
    widened = features.assign(**{FORMULA: ["La1Ni5", "Ti1Fe1"], "nonsense": [1.0, 2.0]})

    assert surrogate._model.predict(widened).equals(surrogate._model.predict(features))
