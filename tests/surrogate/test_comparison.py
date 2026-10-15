"""L3 -- the old 22 against the declared set, and the guards that keep the story true.

Card #25. The comparison itself is a document, and a document is the one artifact a test
suite normally cannot defend. Three things are checkable and all three are checked here:

  - **The numbers it quotes are measurements.** ``row_cost`` and ``placeholder_exposure`` run
    over the real curated rows, so the computability argument in the write-up is pinned to the
    dataset rather than to a paragraph.
  - **The declared contract is the run's own answer.** ``SELECTED`` is a hand-typed list of
    names -- it has to be, because importing the contract module reads no files -- so a test
    asserts those names *are* the consensus of the run table published beside the document.
    Edit either one alone and this goes red.
  - **The published document is the one this code generates.** It is regenerable in a second
    (nothing is fitted), which is what makes that assertion affordable. ``REPORT.md`` came to
    disagree with the CSVs committed beside it precisely because no such check existed.
"""

from __future__ import annotations

import io
from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the comparison is pandas frames end to end")

import pandas as pd  # noqa: E402
from hydms.descriptors.contract import CONTRACT, PASSTHROUGH, SELECTED  # noqa: E402
from hydms.surrogate.comparison import (  # noqa: E402
    DOCUMENT,
    Comparison,
    ComparisonError,
    placeholder_exposure,
    row_cost,
)

#: Where card #25 publishes. Versioned, unlike ``reports/selection/``: the run costs an hour
#: and its raw output stays local, but the evidence behind the declared contract travels with
#: the contract.
PUBLISHED = Path("reports") / "feature_selection"

#: The feature card #24 traded away, and the one number in this file that is a property of the
#: *sources* rather than of the selector: the citable 2024 Oliynyk table leaves ``gordy_en``
#: blank for 21 of the 55 elements this dataset uses.
GORDY = "dev_Gordy_electonegativity"


@pytest.fixture(scope="module")
def published(repo_root: Path) -> Path:
    directory = repo_root / PUBLISHED
    if not (directory / "selection-per-fold.csv").is_file():
        pytest.skip(f"{PUBLISHED} is not in this checkout")
    return directory


@pytest.fixture(scope="module")
def comparison(published: Path, raw_data_path: Path) -> Comparison:
    return Comparison.read(published)


# --------------------------------------------------------------------------------------
# The axis SHAP does not measure
# --------------------------------------------------------------------------------------


def test_one_feature_costs_266_of_the_1279_curated_rows(raw_data_path: Path) -> None:
    """The computability charge the whole Gordy trade turns on, measured not quoted.

    266 is the number card #24 weighed against the feature's usefulness and card #25 reports
    beside its importance. If the shipped Oliynyk table ever gains the missing column this
    goes red, which is the correct outcome: the trade would need re-deciding.
    """
    cost = row_cost()
    assert int(cost.loc[GORDY, "rows_blocked"]) == 266
    assert int(cost.loc[GORDY, "of"]) == 1279


def test_six_features_cost_one_row_each_and_it_is_the_same_row(raw_data_path: Path) -> None:
    """Everything else in the published 22 is free, or costs the single europium row.

    The number that makes the consensus cut *free* on this axis: no feature dropped by the
    fold disagreement was carrying rows with it, so the new set covers exactly what the
    21-candidate pool covered.
    """
    cost = row_cost()
    charged = cost[cost["rows_blocked"] > 0]
    assert set(charged.index) - {GORDY} == {
        name for name in charged.index if int(charged.loc[name, "rows_blocked"]) == 1
    }
    assert len(charged) - 1 == 6
    blocking = {
        element
        for name in charged.index
        if name != GORDY
        for element in str(charged.loc[name, "blocking_elements"]).split(", ")
    }
    assert blocking == {"Eu"}


def test_the_placeholder_reaches_eighteen_rows_through_gadolinium(raw_data_path: Path) -> None:
    """`voro_coord` is filler for two elements; only one of them is in the dataset.

    The measurement behind card #25's decision to keep ``dev_voro_coord_divi_mol_vol``: the
    exposure is 18 of 1,279 rows, all of them gadolinium, and caesium contributes none.
    """
    exposure = placeholder_exposure()
    assert exposure.elements == ("Cs", "Gd")
    assert exposure.per_element == {"Cs": 0, "Gd": 18}
    assert exposure.rows == 18
    assert exposure.of == 1279


# --------------------------------------------------------------------------------------
# The declared contract cannot drift from the run behind it
# --------------------------------------------------------------------------------------


def test_the_declared_set_is_the_consensus_of_the_published_run(
    comparison: Comparison,
) -> None:
    """`SELECTED` is what every fold chose -- names *and* order.

    This is the guard that makes a hand-typed contract honest. ``SELECTED`` cannot be computed
    at import (the contract module reads no files), so the tie between the declaration and
    the run is this assertion and nothing else.
    """
    assert tuple(SELECTED.names) == comparison.consensus


def test_nothing_was_added_because_nothing_could_be(comparison: Comparison) -> None:
    """The candidate pool is the published 22, so old-versus-new is a subset relation."""
    assert set(SELECTED.names) < set(CONTRACT.names)
    assert set(comparison.union) < set(CONTRACT.names)
    assert set(comparison.candidates) == set(CONTRACT.names) - {GORDY}


def test_the_declared_order_is_the_selectors_not_the_reports() -> None:
    """The order is what the selector left, which is the contract's order with one move.

    ``CONTRACT`` declares ``REPORT.md`` 3.2's SHAP-descending order; the selector emits
    candidate order with the ``must_keep`` restore *appending* ``temperature(K)``. The two
    therefore differ in exactly one position, and saying so here stops a future reader from
    "fixing" the order back and silently changing what a stored model expects.
    """
    expected = [name for name in CONTRACT.names if name in set(SELECTED.names)]
    expected.remove(PASSTHROUGH)
    expected.append(PASSTHROUGH)
    assert list(SELECTED.names) == expected


def test_the_regenerated_contract_carries_its_own_provenance() -> None:
    """Card #19's box: names alone rebuild table attribution and dtype, so nothing is typed twice."""
    assert all(
        spec.table in {"oliynyk", "jarvis"} or spec.is_passthrough for spec in SELECTED
    )
    assert SELECTED.digest != CONTRACT.digest


# --------------------------------------------------------------------------------------
# The document
# --------------------------------------------------------------------------------------


def test_the_published_document_is_the_one_this_code_generates(
    published: Path, comparison: Comparison
) -> None:
    """Regenerate and compare. A hand-edited paragraph of numbers goes red here.

    The document is a pure function of the tables published beside it -- including the run
    date, which comes from ``provenance.csv`` rather than a file's modification time, so a
    fresh clone reproduces the same bytes.
    """
    assert (published / DOCUMENT).read_text(encoding="utf-8") == comparison.to_markdown()


def test_rows_tied_on_cost_are_published_in_contract_order(comparison: Comparison) -> None:
    """Card #97: a tie on ``rows_blocked`` must not decide the published row order.

    The real table ties only six rows, and numpy sorts a run that short by insertion, which
    happens to be stable -- so the byte-identity test above passes here and failed once on a
    runner. Twenty-one tied rows is past the insertion cutoff, and the default quicksort was
    measured reordering exactly this shape on this machine.
    """
    cost = comparison.cost.copy()
    cost.loc[cost.index != comparison.costliest, "rows_blocked"] = 1
    tied = [name for name in cost.index if name != comparison.costliest]

    document = replace(comparison, cost=cost).to_markdown()
    section = document.split("## Computability", 1)[1].split("\n## ", 1)[0]
    rows = [line.split("|")[1].strip() for line in section.splitlines() if line.startswith("| ")]
    published = [name for name in rows if name in tied]

    assert published == tied


def test_the_document_states_the_reading_it_published(comparison: Comparison) -> None:
    """The three readings are named and the rejected ones say why -- the card's own ask."""
    document = comparison.to_markdown()
    for phrase in (
        "The published set is the consensus",
        "What was considered and not done",
        "leak **L6**",
        "What this does not claim",
    ):
        assert phrase in document


def test_the_verdict_covers_every_published_feature(comparison: Comparison) -> None:
    """One row per old feature, and the one that was never a candidate says so."""
    verdict = comparison.verdict()
    assert list(verdict.index) == list(CONTRACT.names)
    assert verdict.loc[GORDY, "verdict"].startswith("not a candidate")
    assert verdict.loc[GORDY, "folds"] == "—"
    kept = verdict[verdict["verdict"] == "kept"]
    assert set(kept.index) == set(SELECTED.names)


def test_the_consensus_is_a_subset_of_the_leaking_whole_split_answer(
    comparison: Comparison,
) -> None:
    """The finding the write-up leans on: the two protocols disagree only about the middle.

    Asserted rather than narrated because it is the argument for the consensus reading -- if
    a future run made the consensus contain something the whole-split pass rejects, the
    write-up's claim would be false and the document would need rewriting.
    """
    once = set(str(comparison.whole_split.iloc[0]["features"]).split(", "))
    assert set(comparison.consensus) < once


# --------------------------------------------------------------------------------------
# Reading, and the runnable check
# --------------------------------------------------------------------------------------


def test_a_missing_table_names_the_command_that_writes_it(tmp_path: Path) -> None:
    """The recovery from an empty report directory is a run, so the error prints the run."""
    with pytest.raises(ComparisonError, match="python -m hydms.surrogate.select"):
        Comparison.read(tmp_path)


def test_the_archival_pool_column_is_optional(
    published: Path, tmp_path: Path, raw_data_path: Path
) -> None:
    """A comparison without the 22-candidate run is narrower, not broken.

    The five-fold run and the whole-split run are the result and its contrast; the pool run is
    context. A reader who has not paid for it still gets every other column, and the column it
    would have filled reads ``—`` rather than ``no``.
    """
    for stem in ("selection-per-fold", "selection-stability", "selection-once", "provenance"):
        (tmp_path / f"{stem}.csv").write_bytes((published / f"{stem}.csv").read_bytes())
    narrower = Comparison.read(tmp_path)
    assert narrower.archival_pool is None
    assert set(narrower.verdict()["22-candidate run"]) == {"—"}
    assert "has not been done" in narrower.to_markdown()


def test_emit_comparison_publishes_the_document_and_its_evidence(
    published: Path, tmp_path: Path, raw_data_path: Path
) -> None:
    """Card #25's runnable check, end to end, fitting nothing."""
    from hydms.surrogate.select import main

    code = main(
        ["--emit-comparison", "--report", str(published), "--publish", str(tmp_path)]
    )
    assert code == 0
    assert (tmp_path / DOCUMENT).is_file()
    for stem in ("old-vs-new", "feature-row-cost", "selection-stability", "provenance"):
        assert (tmp_path / f"{stem}.csv").is_file()


def test_the_consensus_follows_the_first_folds_order(
    tmp_path: Path, raw_data_path: Path
) -> None:
    """`chosen_by` orders as `FoldSelection.consensus` does, on a table with no real run in it.

    Ordering is the property a stored model is broken by, and it is the one thing the real
    tables cannot test in isolation -- there, the fold order and the contract order happen to
    agree except at ``temperature(K)``. Here they are deliberately made to disagree.
    """
    features = "gamma, alpha, beta"
    pd.DataFrame(
        [
            {
                "fold": "outer-0",
                "rows_offered": 10,
                "rows_fitted": 9,
                "removed": 1,
                "flagged": 1,
                "held_out": 3,
                "selected": 3,
                "features": features,
            },
            {
                "fold": "outer-1",
                "rows_offered": 10,
                "rows_fitted": 10,
                "removed": 0,
                "flagged": 0,
                "held_out": 3,
                "selected": 2,
                "features": "alpha, gamma",
            },
        ]
    ).set_index("fold").to_csv(tmp_path / "selection-per-fold.csv")
    pd.DataFrame(
        {"folds": [2, 2, 1], "of": [2, 2, 2]},
        index=pd.Index(["alpha", "gamma", "beta"], name="feature"),
    ).to_csv(tmp_path / "selection-stability.csv")
    pd.DataFrame(
        [{"run": "training-split", "rows_offered": 10, "rows_fitted": 10, "removed": 0,
          "flagged": 0, "held_out": 0, "selected": 3, "features": features}]
    ).set_index("run").to_csv(tmp_path / "selection-once.csv")

    built = Comparison.read(tmp_path)
    assert built.consensus == ("gamma", "alpha")
    assert built.union == ("gamma", "alpha", "beta")


# --------------------------------------------------------------------------------------
# The run date comes from a run record, never from a file's mtime (card #106)
# --------------------------------------------------------------------------------------


def _tables_only(published: Path, into: Path) -> Path:
    """The run's tables with no date beside them: no record and no ``provenance.csv``."""
    for stem in ("selection-per-fold", "selection-stability", "selection-once"):
        (into / f"{stem}.csv").write_bytes((published / f"{stem}.csv").read_bytes())
    return into


def _stamped(directory: Path, started_at: str) -> None:
    from hydms import provenance

    provenance.write(
        directory / provenance.SELECTION_RECORD,
        {"probe": "False", "protocol": provenance.FEATURE_SELECTION, "started_at": started_at},
    )


def test_the_run_date_is_read_from_the_selection_runs_record(
    published: Path, tmp_path: Path, raw_data_path: Path
) -> None:
    _stamped(_tables_only(published, tmp_path), "2026-10-02T23:40:00+03:30")
    built = Comparison.read(tmp_path)
    assert built.dated == "2026-10-02"
    assert "on **2026-10-02**" in built.to_markdown()
    assert built.tables()["provenance"].loc["dated", "value"] == "2026-10-02"


def test_with_no_record_the_date_is_not_recorded_whatever_the_mtime(
    published: Path, tmp_path: Path, raw_data_path: Path
) -> None:
    # The fallback this replaced: `_written_on(selection-per-fold.csv)`. Touching the file to a
    # known day would have made that day the published run date.
    import os
    from datetime import datetime

    _tables_only(published, tmp_path)
    touched = datetime(2026, 1, 1, 12, 0).timestamp()
    os.utime(tmp_path / "selection-per-fold.csv", (touched, touched))
    built = Comparison.read(tmp_path)
    assert built.dated is None
    assert "2026-01-01" not in built.to_markdown()
    assert "on a date that was **not recorded**" in built.to_markdown()
    assert built.tables()["provenance"].loc["dated", "value"] == "not recorded"


def test_a_record_that_predates_the_run_date_is_not_recorded_not_backfilled(
    published: Path, tmp_path: Path, raw_data_path: Path
) -> None:
    from hydms import provenance

    _tables_only(published, tmp_path)
    provenance.write(tmp_path / provenance.SELECTION_RECORD, {"probe": "False"})
    assert Comparison.read(tmp_path).dated is None


def test_a_published_not_recorded_stamp_reads_back_as_not_recorded(
    published: Path, tmp_path: Path, raw_data_path: Path
) -> None:
    _tables_only(published, tmp_path)
    Comparison.read(tmp_path).tables()["provenance"].to_csv(tmp_path / "provenance.csv")
    assert Comparison.read(tmp_path).dated is None


def test_emit_comparison_publishes_the_record_it_dated_from(
    published: Path, tmp_path: Path, raw_data_path: Path
) -> None:
    from hydms import provenance
    from hydms.surrogate.select import main

    source = tmp_path / "run"
    source.mkdir()
    _stamped(_tables_only(published, source), "2026-10-02T09:00:00+03:30")
    target = tmp_path / "published"
    assert main(["--emit-comparison", "--report", str(source), "--publish", str(target)]) == 0
    assert (target / provenance.SELECTION_RECORD).read_bytes() == (
        source / provenance.SELECTION_RECORD
    ).read_bytes()
    assert Comparison.read(target).dated == "2026-10-02"


@pytest.mark.parametrize(
    ("flags", "name", "probe"),
    [
        ([], "selection-run.csv", False),
        (["--once"], "selection-once-run.csv", True),
        (["--no-screening"], "selection-unscreened-run.csv", True),
        (["--all-features"], "selection-all-features-run.csv", True),
        (
            ["--once", "--all-features", "--no-screening"],
            "selection-once-all-features-unscreened-run.csv",
            True,
        ),
    ],
)
def test_a_variant_run_never_writes_the_published_runs_record(
    flags: list[str], name: str, probe: bool
) -> None:
    from hydms.config import load
    from hydms.surrogate.select import _begin, _parser, _record_name
    from hydms.surrogate.selection import SelectionSettings

    args = _parser().parse_args(flags)
    cfg = load()
    assert _record_name(args) == name
    stamp = _begin(cfg, SelectionSettings.from_config(cfg), args)
    assert stamp.probe is probe
    assert stamp.finish()["protocol"] == "feature-selection"


def test_select_writes_its_record_beside_its_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ``--once`` path end to end, with the matrix and Boruta replaced by stand-ins."""
    from hydms import provenance
    from hydms.surrogate import select

    frame = pd.DataFrame({"f": [0.0, 1.0]}, index=["r0", "r1"])
    split = pd.Series(["train", "train"], index=frame.index)

    class StandIn:
        features = ("f",)
        candidates = ("f",)

        def __len__(self) -> int:
            return 1

        def trace(self) -> pd.DataFrame:
            return pd.DataFrame({"stage": ["boruta"]})

        def record(self) -> dict[str, object]:
            return {"selected": 1, "features": "f"}

    monkeypatch.setattr(select, "_matrix", lambda cfg, *, all_features: (frame, split))
    monkeypatch.setattr(select, "select_features", lambda *a, **k: StandIn())
    assert select.main(["--once", "--report", str(tmp_path)], out=io.StringIO()) == 0
    record = provenance.read(tmp_path / "selection-once-run.csv")
    assert record.probe is True
    assert record.run_date is not None
    assert not (tmp_path / provenance.SELECTION_RECORD).exists()
