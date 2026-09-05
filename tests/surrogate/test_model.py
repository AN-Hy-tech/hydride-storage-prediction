"""The capacity model: what its columns mean, what it is fitted on, and what weighs it.

The row-identity half of card #26 lives in ``test_no_test_leak.py``. This file is about
everything else the module promises, and two of its assertions are the ones the card names
explicitly: the **quantile column order**, because position is the only thing identifying
P10 from P90 in CatBoost's output; and the **search space**, because "ported from the
archived script" is a claim that can quietly stop being true.

Card #26.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")

import pandas as pd  # noqa: E402
from hydms.config import load  # noqa: E402
from hydms.descriptors.contract import SELECTED  # noqa: E402
from hydms.surrogate.model import (  # noqa: E402
    FIXED,
    SEARCH_SPACE,
    SENTINEL_BUDGET,
    FitLog,
    FitRecord,
    Hyperparameter,
    ModelError,
    ModelSettings,
    column_names,
    loss_function,
    quantile_metrics,
    sample_weights,
    sentinel_settings,
    stopping_slice,
)

TARGET = "H2_W% (max)"
TEMPERATURE = "temperature(K)"
FORMULA = "Composition"
CHEAP = {"iterations": 60, "depth": 4, "learning_rate": 0.3}


def _settings(**overrides: object) -> ModelSettings:
    return ModelSettings(
        **{  # type: ignore[arg-type]
            "quantiles": (0.1, 0.5, 0.9),
            "early_stopping_rounds": 5,
            "optuna_trials": 1,
            "stopping_folds": 5,
            "seed": 42,
            "features": ("avg_atomic_mass", TEMPERATURE),
            "screen_labels": False,
            # Resolved here rather than left to `pipeline.yaml`: a fit that re-reads the
            # configuration is card #29's box (i), and these settings never went through
            # `ModelSettings.from_config`, so they have to say what the target is.
            "target": TARGET,
            "temperature": TEMPERATURE,
            **overrides,
        }
    )


def _frame(rows: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    mass = rng.uniform(20.0, 140.0, size=rows)
    return pd.DataFrame(
        {
            FORMULA: [f"La1Ni{i % 9 + 1}" for i in range(rows)],
            TEMPERATURE: rng.uniform(250.0, 600.0, size=rows),
            "avg_atomic_mass": mass,
            TARGET: 0.02 * mass + rng.normal(scale=0.4, size=rows) + 1.5,
        },
        index=[f"row-{i}" for i in range(rows)],
    )


# --------------------------------------------------------------------------------------
# The quantile heads -- position becomes name, once
# --------------------------------------------------------------------------------------


def test_the_loss_string_and_the_column_names_are_built_from_one_list() -> None:
    """Both derive from the same sequence, so they cannot drift into disagreeing."""
    assert loss_function((0.1, 0.5, 0.9)) == "MultiQuantile:alpha=0.1,0.5,0.9"
    assert column_names((0.1, 0.5, 0.9)) == ("q0.1", "q0.5", "q0.9")
    assert loss_function((0.05, 0.5, 0.95)) == "MultiQuantile:alpha=0.05,0.5,0.95"
    assert column_names((0.05, 0.5, 0.95)) == ("q0.05", "q0.5", "q0.95")


def test_the_configured_quantiles_are_the_ones_the_module_would_fit() -> None:
    """`pipeline.yaml` owns the order and this module reads it, rather than restating it."""
    configured = load().model.quantiles
    assert ModelSettings.from_config().quantiles == tuple(configured)
    assert loss_function(configured).endswith(",".join(f"{q:g}" for q in configured))


def test_the_first_column_is_the_lowest_quantile_and_not_the_highest() -> None:
    """The assertion the card asks for, made against a fitted model rather than a docstring.

    CatBoost returns an unlabelled ``(n, 3)`` array and the only thing saying which column is
    P10 is the order of the alphas in the loss string. So this fits a real model on 200 rows
    of a known distribution and checks the columns *empirically*: the share of truths at or
    below each head must come out near that head's alpha. A transposed mapping would put 0.9
    where 0.1 belongs and this fails by 0.8, not by a rounding.

    **Not marked `slow`, deliberately.** It fits a real CatBoost model and takes **0.97 s**,
    measured -- sixty iterations of a four-deep tree on 200 rows. The card asks for the column
    order to be asserted in a test, and a test the CI fast lane deselects does not assert it.
    """
    pytest.importorskip("catboost", reason="the model being fitted is CatBoost's")
    from hydms.surrogate.model import fit_quantile_model

    frame = _frame()
    settings = _settings()
    fitted = list(frame.index[:150])
    model = fit_quantile_model(
        frame,
        train=fitted,
        eval_on=list(frame.index[150:175]),
        scored_on=list(frame.index[175:]),
        where="test",
        params=CHEAP,
        settings=settings,
    )
    assert list(model.columns) == ["q0.1", "q0.5", "q0.9"]

    grown = frame.loc[fitted]
    predicted = model.predict(grown)
    below = [float((grown[TARGET] <= predicted[name]).mean()) for name in model.columns]
    assert below == sorted(below), f"the heads are not ordered: {below}"
    for alpha, share in zip(model.quantiles, below, strict=True):
        assert abs(share - alpha) < 0.15, f"the q{alpha:g} column covers {share:.2f} in sample"


def test_weight_percent_and_model_space_are_the_same_prediction() -> None:
    """`predict` is `expm1` of `predict_model_space`, exactly -- a monotone map on quantiles."""
    pytest.importorskip("catboost", reason="the model being fitted is CatBoost's")
    from hydms.data.target import to_wt_pct
    from hydms.surrogate.model import fit_quantile_model

    frame = _frame(80)
    model = fit_quantile_model(
        frame,
        train=list(frame.index[:50]),
        eval_on=list(frame.index[50:65]),
        scored_on=list(frame.index[65:]),
        where="test",
        params=CHEAP,
        settings=_settings(),
    )
    batch = frame.loc[list(frame.index[:50])]
    model_space = model.predict_model_space(batch)
    wt_pct = model.predict(batch)
    for name in model.columns:
        assert wt_pct[name].tolist() == to_wt_pct(model_space[name]).tolist()


def test_predicting_from_an_array_is_refused() -> None:
    """An ndarray carries no column names, so a permuted matrix would be plausible and wrong."""
    from hydms.surrogate.model import QuantileModel

    model = QuantileModel(
        booster=None,
        feature_names=("a", "b"),
        quantiles=(0.1, 0.5, 0.9),
        record=FitRecord(where="x", fitted=(), eval_on=(), scored_on=()),
    )
    with pytest.raises(ModelError, match="not a ndarray"):
        model.predict(np.zeros((3, 2)))  # type: ignore[arg-type]
    with pytest.raises(ModelError, match="missing 1 of 2 fitted feature"):
        model.predict(pd.DataFrame({"a": [1.0]}))


# --------------------------------------------------------------------------------------
# The search space -- ported, and asserted to still be the port
# --------------------------------------------------------------------------------------


def test_the_search_space_is_the_archival_one_but_for_one_measured_bound() -> None:
    """`Catboostmodel.py:545-563`, parameter for parameter -- and one bound deliberately not.

    Written out here rather than derived, because that is the whole content of the claim: if
    somebody widens a bound to make a run cheaper, or narrows one to make it faster, this is
    what says so out loud. It is the test card #29 was told to update *deliberately*.

    **`learning_rate` starts at 5e-4, not the archival 1e-4.** Measured on a real inner fold,
    one fit per rate, everything else held: the best iteration goes as roughly
    `4.2 / learning_rate` -- 813 at 0.005, 8,501 at 0.0005, 13,991 at 0.0003 and **29,999 at
    0.0001, which is the `iterations` cap itself**, so the fit at the archival lower bound
    never converged. R2 over that whole decade is 0.6800 to 0.6847: flat. Since `iterations`
    is sampled from 10,000, the bound is the measured rate whose optimum still falls inside
    the *smallest* budget the space can hand a trial. Nineteen times the wall time for the
    same model, and the full table is on `SEARCH_SPACE`.

    Every other bound is the archival one, including `depth` to 25 -- inert under `Lossguide`
    rather than expensive, so there is no run to protect from it.
    """
    assert {knob.name: (knob.kind, knob.low, knob.high, knob.log) for knob in SEARCH_SPACE} == {
        "learning_rate": ("float", 0.0005, 0.005, True),
        "depth": ("int", 7, 25, False),
        "iterations": ("int", 10000, 30000, False),
        "l2_leaf_reg": ("float", 1.0, 10.0, False),
        "bagging_temperature": ("float", 0.0, 1.0, False),
        "random_strength": ("float", 0.5, 15.0, False),
        "max_leaves": ("int", 16, 128, False),
        "min_data_in_leaf": ("int", 1, 20, False),
        "border_count": ("int", 32, 256, False),
    }


def test_a_hyperparameter_refuses_a_range_nothing_can_be_sampled_from() -> None:
    with pytest.raises(ModelError, match="low bound"):
        Hyperparameter("depth", "int", 10, 3)
    with pytest.raises(ModelError, match="log of a non-positive bound"):
        Hyperparameter("learning_rate", "float", 0.0, 1.0, log=True)
    with pytest.raises(ModelError, match="'int' or 'float'"):
        Hyperparameter("depth", "integer", 1, 2)


def test_a_fit_never_reads_the_configuration_file() -> None:
    """The race card #29 moved off #34, asserted rather than reasoned about.

    `hydms.config.load` parses and revalidates `pipeline.yaml` on every call and caches
    nothing. `_columns` used to reach for it from inside the scoring path -- about six reads a
    fit, some 2,300 in a 381-fit run, and every one of them a window in which an edit to the
    working tree changes what the run believes it is fitting. It has already fired once,
    killing a probe on its third trial, and two sessions share this checkout.

    A 3.5-hour run that reads a half-written configuration produces numbers that look fine and
    are wrong, and nothing downstream can tell. So the count is zero, not "few": the target
    column is resolved once, into `ModelSettings`, by `from_config`.
    """
    import hydms.surrogate.model as module
    from hydms.surrogate.model import fit_quantile_model

    frame = _frame(rows=40)
    settings = _settings()
    reads: list[str] = []

    original = module.load_config
    module.load_config = lambda *a, **k: reads.append("read") or original(*a, **k)  # type: ignore[assignment]
    try:
        fit_quantile_model(
            frame,
            train=list(frame.index[:24]),
            eval_on=list(frame.index[24:32]),
            scored_on=list(frame.index[32:]),
            where="a fit that must not read the configuration",
            params=CHEAP,
            settings=settings,
        )
    finally:
        module.load_config = original  # type: ignore[assignment]

    assert reads == [], (
        f"fit_quantile_model read pipeline.yaml {len(reads)} time(s). Every column name a fit "
        f"needs is on ModelSettings; reaching for the file mid-run is card #29's box (i)."
    )


def test_settings_from_the_configuration_carry_the_column_names() -> None:
    """What makes the zero above reachable rather than an accident of this fixture."""
    settings = ModelSettings.from_config()
    cfg = load()
    assert settings.target == cfg.columns.target
    assert settings.temperature == cfg.columns.temperature
    # And they survive the substitution the sentinels make.
    assert sentinel_settings(settings).target == cfg.columns.target


def test_a_fit_with_no_target_anywhere_refuses_rather_than_reading_the_file() -> None:
    """The alternative to refusing is a fallback that fires only sometimes.

    That would be the same race with a smaller window, and a smaller window is harder to find
    than an obvious one. A settings object with no target did not come from `from_config`, and
    saying so by name is cheaper than a run whose answer depends on when it ran.
    """
    from hydms.surrogate.model import fit_quantile_model

    frame = _frame(rows=40)
    with pytest.raises(ModelError, match="ModelSettings.from_config"):
        fit_quantile_model(
            frame,
            train=list(frame.index[:24]),
            eval_on=list(frame.index[24:32]),
            scored_on=list(frame.index[32:]),
            where="a fit with no target named",
            params=CHEAP,
            settings=_settings(target=None),
        )


def test_the_bootstrap_is_pinned_so_bagging_temperature_is_not_a_dead_dimension() -> None:
    """Measured: under CatBoost's CPU default, `bagging_temperature` changes nothing at all.

    Temperature 0.0 and 1.0 gave a bit-identical fit -- same trees, same best iteration, the
    same loss to six decimals -- while under `Bayesian` they gave 0.1444 and 0.1526. The
    archival search sampled the parameter without pinning the bootstrap, so one of its nine
    dimensions was noise. This is the one place that is fixed rather than recorded.
    """
    assert FIXED["bootstrap_type"] == "Bayesian"
    assert any(knob.name == "bagging_temperature" for knob in SEARCH_SPACE)


def test_multiquantile_trains_on_cpu_and_writes_nothing() -> None:
    """`MultiQuantile` has no GPU kernel, so the slow lane's budget is a CPU budget."""
    assert FIXED["task_type"] == "CPU"
    assert FIXED["allow_writing_files"] is False
    assert "od_type" not in FIXED and "od_pval" not in FIXED


def test_the_sentinel_budget_changes_cost_and_nothing_else() -> None:
    """The reduced settings differ from the real ones in exactly the four declared keys."""
    real, reduced = ModelSettings.from_config(), sentinel_settings()
    assert set(SENTINEL_BUDGET) == {"optuna_trials", "space", "early_stopping_rounds", "screen_labels"}
    changed = {
        name
        for name in vars(real)
        if getattr(real, name) != getattr(reduced, name)
    }
    assert changed <= set(SENTINEL_BUDGET)
    assert reduced.quantiles == real.quantiles
    assert reduced.features == real.features
    assert reduced.seed == real.seed
    assert reduced.stopping_folds == real.stopping_folds


# --------------------------------------------------------------------------------------
# What it is fitted on
# --------------------------------------------------------------------------------------


def test_the_declared_features_are_card_25s_consensus_and_not_the_published_22() -> None:
    """The box #25 left: fit on `SELECTED`, and let `CONTRACT` stay the archival record."""
    from hydms.descriptors.contract import CONTRACT

    assert ModelSettings.from_config().features == SELECTED.names
    assert len(SELECTED.names) < len(CONTRACT.names)
    assert set(SELECTED.names) < set(CONTRACT.names)


# --------------------------------------------------------------------------------------
# The weights -- leak L12
# --------------------------------------------------------------------------------------


def test_the_weights_are_one_per_row_and_uniform() -> None:
    frame = _frame(12)
    weights = sample_weights(frame, settings=_settings())
    assert list(weights.index) == list(frame.index)
    assert weights.tolist() == [1.0] * 12


def test_the_weights_do_not_move_when_the_target_does() -> None:
    """The property, asserted directly as well as through the sentinel.

    The archival threshold was 3 wt%, so the perturbation below straddles it: every row moves
    from one side to the other. A weighting that read the target could not stay still.
    """
    frame = _frame(12)
    settings = _settings()
    before = sample_weights(frame, settings=settings)
    moved = frame.copy()
    moved[TARGET] = moved[TARGET] * 4.0 + 2.0
    assert sample_weights(moved, settings=settings).tolist() == before.tolist()


def test_the_weighting_refuses_a_frame_without_the_declared_features() -> None:
    with pytest.raises(ModelError, match="missing 1 of 2 declared feature"):
        sample_weights(_frame(4).drop(columns=[TEMPERATURE]), settings=_settings())


# --------------------------------------------------------------------------------------
# The early-stopping slice
# --------------------------------------------------------------------------------------


def test_the_stopping_slice_is_grouped_and_disjoint() -> None:
    """It is cut by the project's only fold generator, so no composition spans the two sides."""
    from hydms.data.canonical import group_keys

    frame = _frame(200)
    fitting, stopping = stopping_slice(frame, list(frame.index), settings=_settings())
    assert not set(fitting) & set(stopping)
    assert set(fitting) | set(stopping) == set(frame.index)
    keys = group_keys(frame)
    assert not set(keys.loc[list(fitting)]) & set(keys.loc[list(stopping)])


def test_the_stopping_slice_is_about_a_fifth_at_five_folds() -> None:
    """`stopping_folds` is a fold count, so the slice is one fold of it -- stated, and checked."""
    frame = _frame(200)
    _, stopping = stopping_slice(frame, list(frame.index), settings=_settings(stopping_folds=5))
    assert 0.1 <= len(stopping) / len(frame) <= 0.35


def test_the_stopping_slice_refuses_rows_it_was_not_given() -> None:
    frame = _frame(40)
    with pytest.raises(ModelError, match="not in the frame"):
        stopping_slice(frame, [*frame.index[:20], "row-999"], settings=_settings())


# --------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------


def _predicted(rows: int, spread: float) -> tuple[pd.Series, pd.DataFrame]:
    index = pd.Index([f"row-{i}" for i in range(rows)])
    truth = pd.Series(np.linspace(1.0, 5.0, rows), index=index, name=TARGET)
    return truth, pd.DataFrame(
        {"q0.1": truth - spread, "q0.5": truth, "q0.9": truth + spread}, index=index
    )


def test_a_perfect_median_scores_one_and_a_perfect_interval_covers_everything() -> None:
    truth, predicted = _predicted(50, 0.5)
    metrics = quantile_metrics(truth, predicted, (0.1, 0.5, 0.9))
    assert metrics["r2"] == pytest.approx(1.0)
    assert metrics["rmse"] == pytest.approx(0.0)
    assert metrics["interval_coverage"] == pytest.approx(1.0)
    assert metrics["interval_width"] == pytest.approx(1.0)
    assert metrics["crossings"] == 0.0


def test_a_crossed_interval_is_counted_rather_than_hidden() -> None:
    """Measured at 23 % of rows on a small real fit, so this is a number, not a guard."""
    truth, predicted = _predicted(10, 0.5)
    predicted.loc["row-0", "q0.9"] = float(truth.loc["row-0"]) - 1.0
    assert quantile_metrics(truth, predicted, (0.1, 0.5, 0.9))["crossings"] == pytest.approx(0.1)


def test_no_metric_is_named_after_a_split_the_protocol_never_touches() -> None:
    """A record carrying a held-out metric is leak L2, and `nested_scores` refuses it."""
    from hydms.surrogate.validation import HELD_OUT_SPLITS

    truth, predicted = _predicted(10, 0.5)
    metrics = quantile_metrics(truth, predicted, (0.1, 0.5, 0.9))
    assert not set(metrics) & set(HELD_OUT_SPLITS)


def test_metrics_refuse_a_prediction_that_is_not_this_quantile_set() -> None:
    truth, predicted = _predicted(10, 0.5)
    with pytest.raises(ModelError, match="Position identifies a quantile"):
        quantile_metrics(truth, predicted.rename(columns={"q0.9": "upper"}), (0.1, 0.5, 0.9))
    with pytest.raises(ModelError, match="paired by label"):
        quantile_metrics(truth.iloc[:5], predicted, (0.1, 0.5, 0.9))


# --------------------------------------------------------------------------------------
# The fit log
# --------------------------------------------------------------------------------------


def test_the_fit_log_is_a_table_of_row_counts_and_costs() -> None:
    """It records identities and reports counts, which is what makes it writable to a CSV."""
    log = FitLog()
    log.add(
        FitRecord(
            where="outer-0",
            fitted=("a", "b", "c"),
            eval_on=("d",),
            scored_on=("e", "f"),
            removed=("g",),
            best_iteration=11,
            trees=12,
            seconds=1.234,
        )
    )
    table = log.table()
    assert len(log) == 1
    assert table.loc[0, "where"] == "outer-0"
    assert table.loc[0, "fitted"] == 3
    assert table.loc[0, "scored_on"] == 2
    assert table.loc[0, "seconds"] == pytest.approx(1.234)
