"""Card #30 — leave-one-alloy-class-out, and the ways a per-class table can mislead.

Most of this file is about *reporting*, because that is what AC-6 is about: the criterion asks
that the extrapolation number be published alongside the interpolation one, not that it clear a
bar. So the properties under test are that no class disappears, that no score is printed without
the support it rests on, and that the two averages which can be computed here are both computed
— a support-weighted mean over these ten classes is mostly a statement about AB2 and AB5, which
between them carry 403 of the 893 training rows, and is not the transfer question AC-6 asks.

The scoring itself is deliberately **not** re-tested here: it is
`hydms.surrogate.validation.nested_scores`, unchanged, with the outer partition passed as an
argument. `tests/surrogate/test_validation.py` owns the protocol. What this file checks is the
thin layer that turns its output into a table somebody can read without being misled, plus one
real-data test that the class folds are the ten families with the supports card #88 measured.

`Fold` and `FoldSet` are the real dataclasses rather than stand-ins, so a change to the shape
the protocol emits reaches this file rather than being absorbed by a fake.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the tables are pandas frames end to end")
pytest.importorskip("sklearn", reason="the fold protocol is scikit-learn's")

import pandas as pd  # noqa: E402
from hydms.surrogate import loco  # noqa: E402
from hydms.surrogate.validation import Evaluation, Fold, FoldSet  # noqa: E402

TARGET = "H2_W% (max)"


def _training(rows: dict[str, tuple[str, str, float]]) -> pd.DataFrame:
    """A tiny record frame: label -> (formula, class, target).

    The class column is here because ``per_class`` reads it: ``rows_in_class`` is measured from
    the frame while ``rows_scored`` is measured from the fold, and publishing both is what lets
    a reader check that a class fold held out the *whole* family rather than part of one. A
    fixture without the column would have hidden that the two are different measurements.
    """
    return pd.DataFrame(
        {
            "Composition": [formula for formula, _, _ in rows.values()],
            "Alloy_class": [label for _, label, _ in rows.values()],
            TARGET: [value for _, _, value in rows.values()],
        },
        index=list(rows),
    )


def _evaluation(
    folds: dict[str, list[str]], metrics: dict[str, dict[str, float]], model: str = "m"
) -> Evaluation:
    """One contender, one fold per class, with the metrics each fold produced."""
    every = [label for labels in folds.values() for label in labels]
    fold_objects = tuple(
        Fold(
            id=position,
            name=name,
            train=tuple(label for label in every if label not in set(labels)),
            test=tuple(labels),
            held_out=frozenset(labels),
        )
        for position, (name, labels) in enumerate(folds.items())
    )
    per_fold = pd.DataFrame.from_records(
        [{"model": model, "fold": name, **metrics[name]} for name in folds]
    )
    return Evaluation(
        records=(),
        outer=FoldSet(name="class", folds=fold_objects, grouped_on="alloy class"),
        per_fold=per_fold,
    )


# --------------------------------------------------------------------------------------
# The per-class table
# --------------------------------------------------------------------------------------


def test_the_fold_name_becomes_the_class_and_the_support_travels_with_the_score() -> None:
    """A score with no count beside it invites the reading AC-6 exists to prevent."""
    training = _training(
        {
            "a": ("La1Ni5", "AB5", 1.4),
            "b": ("La1Ni5", "AB5", 1.5),
            "c": ("Ti1Fe1", "AB", 1.8),
            "d": ("Ti1Fe1", "AB", 1.9),
            "e": ("Mg2Ni1", "Mg", 3.6),
        }
    )
    evaluation = _evaluation(
        {"class:AB5": ["a", "b"], "class:AB": ["c", "d"], "class:Mg": ["e"]},
        {
            "class:AB5": {"r2": 0.5, "mae": 0.1},
            "class:AB": {"r2": 0.2, "mae": 0.3},
            "class:Mg": {"r2": 0.0, "mae": 0.4},
        },
    )
    table = loco.per_class(evaluation, training)

    assert list(table.index.get_level_values("alloy_class")) == ["AB", "AB5", "Mg"]
    assert int(table.loc[("m", "AB5"), "rows_scored"]) == 2
    # Two rows, one material: the composition count is what says how many independent
    # materials the score rests on, and it is not the row count.
    assert int(table.loc[("m", "AB5"), "compositions_scored"]) == 1
    # A class fold holds out every row of its family, so these two must agree. They are
    # measured from different places — the frame and the fold — which is what makes agreeing
    # a check rather than a restatement.
    assert int(table.loc[("m", "AB5"), "rows_in_class"]) == 2


def test_a_class_whose_target_does_not_vary_is_reported_as_unestimable_not_dropped() -> None:
    """R2 is a ratio to the total sum of squares, so a constant held-out column makes it
    *undefined* rather than bad. The class still appears, with the reason in words."""
    training = _training(
        {
            "a": ("La1Ni5", "AB5", 1.4),
            "b": ("La1Ni5", "AB5", 1.5),
            "c": ("Ti1Fe1", "AB", 1.8),
            "d": ("Ti1Cr1", "AB", 1.8),
        }
    )
    evaluation = _evaluation(
        {"class:AB5": ["a", "b"], "class:AB": ["c", "d"]},
        {"class:AB5": {"r2": 0.5, "mae": 0.1}, "class:AB": {"r2": float("nan"), "mae": 0.0}},
    )
    table = loco.per_class(evaluation, training)

    assert ("m", "AB") in table.index, "an unestimable class must still be in the table"
    assert not bool(table.loc[("m", "AB"), "estimable"])
    assert "undefined rather than bad" in str(table.loc[("m", "AB"), "not_estimable_because"])
    assert bool(table.loc[("m", "AB5"), "estimable"])
    assert str(table.loc[("m", "AB5"), "not_estimable_because"]) == ""


def test_a_class_with_one_held_out_row_is_reported_as_unestimable() -> None:
    training = _training(
        {"a": ("La1Ni5", "AB5", 1.4), "b": ("La1Ni5", "AB5", 1.6), "c": ("Ti1Fe1", "AB", 1.8)}
    )
    evaluation = _evaluation(
        {"class:AB5": ["a", "b"], "class:AB": ["c"]},
        {"class:AB5": {"r2": 0.5, "mae": 0.1}, "class:AB": {"r2": 0.0, "mae": 0.2}},
    )
    table = loco.per_class(evaluation, training)

    assert not bool(table.loc[("m", "AB"), "estimable"])
    assert "at least 2" in str(table.loc[("m", "AB"), "not_estimable_because"])


def test_a_small_class_is_estimable_and_is_not_filtered_for_being_small() -> None:
    """The module makes no judgement about sample size; it prints the support and lets the
    reader make one. A filter here would make that judgement silently on their behalf."""
    training = _training(
        {
            "a": ("La1Ni5", "AB5", 1.4),
            "b": ("La1Ni5", "AB5", 1.6),
            "c": ("Ti1Fe1", "AB", 1.8),
            "d": ("Ti1Cr1", "AB", 2.1),
        }
    )
    evaluation = _evaluation(
        {"class:AB5": ["a", "b"], "class:AB": ["c", "d"]},
        {"class:AB5": {"r2": 0.5, "mae": 0.1}, "class:AB": {"r2": -3.0, "mae": 0.9}},
    )
    table = loco.per_class(evaluation, training)

    assert bool(table.loc[("m", "AB"), "estimable"])
    assert float(table.loc[("m", "AB"), "r2"]) == -3.0, "a bad score is a result, not an error"


# --------------------------------------------------------------------------------------
# The summary — the row AC-6 is actually about
# --------------------------------------------------------------------------------------


def _summary_table() -> pd.DataFrame:
    """Two classes of very different size, so the two averages cannot agree."""
    return pd.DataFrame(
        {
            "r2": [0.80, 0.10],
            "mae": [0.20, 0.60],
            "rows_scored": [260, 20],
            "estimable": [True, True],
        },
        index=pd.MultiIndex.from_tuples(
            [("m", "AB2"), ("m", "LEA")], names=["model", "alloy_class"]
        ),
    )


def test_both_averages_are_reported_and_they_are_computed_differently() -> None:
    """Which one is larger is a property of the run, not of the design — a sentinel-budget
    probe had the weighted mean *below* the macro one, the opposite of what the module's first
    draft asserted. What is tested here is the arithmetic and that both are published."""
    once = loco.summary(_summary_table(), None)
    macro = float(once.loc["m", "macro_r2"])
    weighted = float(once.loc["m", "weighted_r2"])

    assert macro == pytest.approx(0.45)
    assert weighted == pytest.approx((0.80 * 260 + 0.10 * 20) / 280)
    assert weighted != pytest.approx(macro), (
        "the fixture exists to make the two disagree — if they stop disagreeing the test is "
        "no longer checking that both are published"
    )


@pytest.mark.parametrize(
    ("weighted", "macro", "expected"),
    [(0.60, 0.45, "higher"), (0.16, 0.22, "lower"), (0.45, 0.45, "identical")],
)
def test_the_document_states_the_direction_it_measured_not_one_it_predicted(
    weighted: float, macro: float, expected: str
) -> None:
    """The sentence that got this wrong once is now generated from the two numbers."""
    assert expected in loco._direction(weighted, macro)


def test_an_undefined_average_is_not_described_as_higher_or_lower() -> None:
    assert "not comparable" in loco._direction(float("nan"), 0.45)


def test_the_random_split_number_is_carried_into_the_row_that_reports_the_class_one() -> None:
    """AC-6 is 'reported alongside'. A summary with one number and not the other does not meet
    it, so the two live in one row and neither can be published without the other."""
    record = pd.DataFrame({"r2": [0.7481]}, index=pd.Index(["m"], name="model"))
    once = loco.summary(_summary_table(), record)
    assert float(once.loc["m", "random_split_r2"]) == pytest.approx(0.7481)


def test_no_random_split_run_on_disk_reads_as_absent_rather_than_as_zero() -> None:
    once = loco.summary(_summary_table(), None)
    value = float(once.loc["m", "random_split_r2"])
    assert value != value, "a missing comparison must be NaN, never a number AC-6 could pass on"


def test_an_unestimable_class_is_excluded_from_the_averages_and_counted() -> None:
    table = _summary_table()
    table.loc[("m", "SS"), :] = [float("nan"), float("nan"), 1, False]
    once = loco.summary(table, None)

    assert int(once.loc["m", "classes"]) == 3
    assert int(once.loc["m", "classes_scored"]) == 2
    assert int(once.loc["m", "classes_not_estimable"]) == 1
    assert float(once.loc["m", "macro_r2"]) == pytest.approx(0.45), "NaN must not reach the mean"


def test_the_worst_class_is_named_because_the_average_hides_it() -> None:
    once = loco.summary(_summary_table(), None)
    assert once.loc["m", "worst_class"] == "LEA"
    assert float(once.loc["m", "worst_class_r2"]) == pytest.approx(0.10)
    assert once.loc["m", "best_class"] == "AB2"


# --------------------------------------------------------------------------------------
# The document
# --------------------------------------------------------------------------------------


def _tables(*, probe: bool = False) -> dict[str, pd.DataFrame]:
    table = _summary_table()
    table["compositions_scored"] = [207, 19]
    table["not_estimable_because"] = ["", ""]
    record = pd.DataFrame({"r2": [0.7481]}, index=pd.Index(["m"], name="model"))
    return {
        "loco-per-class": table,
        "loco-summary": loco.summary(table, record),
        "loco-chosen": pd.DataFrame(),
        "loco-run": pd.DataFrame.from_records(
            [{"probe": probe, "optuna_trials": 2, "configured_optuna_trials": 25,
              "screening": True}]
        ),
    }


def test_the_document_puts_the_two_numbers_in_one_table() -> None:
    text = loco.document(_tables())
    assert "0.7481" in text and "0.4500" in text
    assert "interpolation" in text and "extrapolation" in text


def test_the_document_lists_every_class_with_its_support() -> None:
    text = loco.document(_tables())
    assert "| AB2 |" in text and "| LEA |" in text
    assert "260" in text and "19" in text


def test_a_probes_document_says_so_at_the_top() -> None:
    """A probe's tables and a real run's tables are the same shape. The difference has to be
    somewhere a reader cannot miss, and generated from `loco-run.csv` rather than remembered."""
    assert "probe, not a result" in loco.document(_tables(probe=True))
    assert "probe, not a result" not in loco.document(_tables(probe=False))


def test_emit_refuses_a_partial_set_of_tables_and_names_what_is_missing(
    tmp_path: Path, capsys
) -> None:
    """Half a document is worse than none: it would publish an average with no per-class
    evidence under it, which is the shape AC-6 is trying to prevent."""
    (tmp_path / "loco-summary.csv").write_text("model,macro_r2\nm,0.45\n", encoding="utf-8")
    code = loco.main(["--emit", "--report", str(tmp_path)])
    assert code == loco.EXIT_BAD_INVOCATION
    assert "loco-per-class.csv" in capsys.readouterr().err


def test_budget_fits_nothing_and_says_how_this_compares_to_the_random_split_run(capsys) -> None:
    code = loco.main(["--budget"])
    out = capsys.readouterr().out
    assert code == loco.EXIT_OK
    assert "class fold(s)" in out
    assert "another one of it and then some" in out, "the ratio is the point, not the total"


def test_an_unknown_target_is_refused_by_name(capsys) -> None:
    assert loco.main(["--target", "entropy"]) == loco.EXIT_BAD_INVOCATION
    assert "capacity" in capsys.readouterr().err


# --------------------------------------------------------------------------------------
# The real data
# --------------------------------------------------------------------------------------


def test_the_committed_document_is_what_the_code_produces() -> None:
    """The rule card #29 established: a published document is generated, never typed.

    It skips until the 4.7-hour run has happened and its tables are committed, and that skip is
    not a hole — AC-6 reports SKIPPED for the same absence, and `hydms.artifacts.promote`
    refuses a skip, so nothing can be certified while this is unchecked. The moment
    `reports/loco/` carries tables, this asserts the committed `loco.md` is byte-for-byte what
    `--emit` builds from them.
    """
    from hydms.config import load as load_config

    directory = load_config().paths.reports / loco.REPORTS
    published = directory / loco.DOCUMENT
    if not published.exists():
        pytest.skip(
            f"{published} does not exist yet: the leave-one-alloy-class-out run has not "
            f"happened. AC-6 reports the same absence as SKIPPED, which blocks promotion."
        )
    assert published.read_text(encoding="utf-8") == loco.document(loco._read_tables(directory))


@pytest.mark.slow
def test_the_class_folds_are_the_ten_families_with_the_supports_88_measured() -> None:
    """Card #30's own numbers, checked against the file rather than trusted.

    These ten supports are what makes AC-6 runnable at all: the smallest fold is 19 rows, so
    every class is estimable and none is reported as a class the protocol could not score. If a
    class ever drops below two rows this is the test that says so before a run spends 4.7 h
    discovering it.
    """
    from hydms.data.canonical import alloy_classes
    from hydms.surrogate.model import ModelSettings, capacity_matrix
    from hydms.surrogate.scaler import TRAIN
    from hydms.surrogate.validation import leave_one_class_out

    frame, split = capacity_matrix(settings=ModelSettings.from_config())
    training = frame.loc[split == TRAIN]
    counts = alloy_classes(training).value_counts().to_dict()

    assert counts == {
        "AB2": 260, "AB5": 143, "Mg": 96, "MIC": 87, "MEA": 76,
        "SS": 73, "AB": 59, "HEA": 51, "A2B": 29, "LEA": 19,
    }
    assert sum(counts.values()) == 893

    folds = leave_one_class_out(training)
    assert len(folds) == 10
    assert min(len(fold.test) for fold in folds) >= loco.MIN_SCORED_ROWS
    assert {fold.name for fold in folds} == {f"class:{label}" for label in counts}


def test_the_document_never_prints_the_word_nan_for_a_missing_comparison() -> None:
    """A cell reading `nan` invites a reader to treat it as a measurement that came out
    strange. AC-6 fails on this state anyway; the document should say so in words."""
    tables = _tables()
    tables["loco-summary"] = loco.summary(tables["loco-per-class"], None)
    text = loco.document(tables)

    assert "not published" in text
    assert "| nan |" not in text
