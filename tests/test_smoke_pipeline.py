"""Does the chain still connect? The one test that answers card #73's question.

The audit found the pipeline did not run end to end at all, and a full retrain is far too slow
to guard against that on every push. This file runs every stage over the committed fixture and
asserts three things, in descending order of how easy they are to lose:

  - **Every stage runs, in the live order.** Not a smoke *screen* -- the stage list is compared
    to :data:`~hydms.pipeline.smoke.STAGES`, so a stage silently dropped from the run is a
    failure rather than a shorter table nobody reads.
  - **The same seed reproduces the run exactly.** The digest is every stage's shape, the chosen
    features and every predicted number at full precision, and it excludes every wall-clock
    number -- reproducibility is a claim about arithmetic, not about how fast the machine was.
  - **No absolute path appears anywhere in the run.** Checked twice: the module and the fixture
    are scanned for a rooted path literal, and the whole chain is run from a different working
    directory. The archival pipeline hard-coded ``D:\\Hydride_Machine_learning_project\\...``
    in nine scripts, so this is the defect the check is shaped around.

**It is deliberately not marked `slow`.** The whole file is about 25 s, of which two full runs
of the chain are 24; the fast lane deselects `slow`, and a smoke test the fast lane deselects
is not a smoke test. The budget the card sets is 60 s per run and the measured cost is 12.

Card #73.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the pipeline is pandas frames end to end")
pytest.importorskip("catboost", reason="the fit stage is CatBoost's")
pytest.importorskip("mapie", reason="the band is MAPIE-calibrated; `pip install -e .[uq]`")
pytest.importorskip("cleanlab", reason="the screening stage is CleanLab's")

from hydms.pipeline import smoke  # noqa: E402

#: A rooted path literal: a Windows drive, a UNC share, or a POSIX absolute path deep enough to
#: be a real machine's rather than a URL fragment. Three things it deliberately does not match,
#: and the first two because the first draft matched them and was wrong: ``https:/`` -- a drive
#: letter is *one* letter, so the lookbehind is load-bearing and the fixture's ``Citation``
#: column is full of DOIs -- a bare leading ``/``, since ``/1`` in a docstring is not a path,
#: and a relative path, which is the thing the pipeline is supposed to use.
ROOTED = re.compile(
    r"(?<![A-Za-z])[A-Za-z]:[\\/]"
    r"|\\\\[A-Za-z]"
    r"|(?:^|['\"\s(])/(?:home|Users|mnt|opt|var)/"
)

#: The budget card #73 sets. Generous against a measured 12 s so that a slower CI runner is not
#: a red build, and tight enough that a stage which quietly became a retrain is caught.
BUDGET_S = 60.0


@pytest.fixture(scope="module")
def result() -> smoke.SmokeRun:
    """One run of the whole chain. Module-scoped: it is the expensive thing in this file."""
    return smoke.run()


# --------------------------------------------------------------------------------------
# The chain connects
# --------------------------------------------------------------------------------------


def test_every_stage_runs_in_the_live_order(result: smoke.SmokeRun) -> None:
    """The whole point of the card: load reaches a prediction, through every stage."""
    assert tuple(stage.name for stage in result.stages) == smoke.STAGES


def test_every_stage_produced_rows(result: smoke.SmokeRun) -> None:
    """A stage that ran and returned nothing is a broken link that did not raise."""
    for stage in result.stages:
        assert stage.rows > 0, f"the {stage.name!r} stage produced no rows"


def test_the_run_finishes_inside_the_budget(result: smoke.SmokeRun) -> None:
    assert result.seconds < BUDGET_S


def test_the_prediction_is_a_calibrated_interval_and_not_a_bare_number(
    result: smoke.SmokeRun,
) -> None:
    """The last link: a formula string reaches an interval, through the artifact store.

    Read back from a saved version rather than from the objects in hand, so a `joblib` change
    or a lost column order fails here rather than in production.
    """
    from hydms.surrogate.predict import INTERVAL_WIDTH, LOWER_BOUND

    predictions = result.predictions

    assert list(predictions.index) == list(range(len(smoke.PROBE_ALLOYS)))
    assert LOWER_BOUND in predictions.columns
    assert INTERVAL_WIDTH in predictions.columns
    assert (predictions[INTERVAL_WIDTH] > 0.0).all()


def test_the_features_the_fit_used_are_the_ones_selection_chose(
    result: smoke.SmokeRun,
) -> None:
    """Catches: a fit that reached past the selector for the full contract."""
    from hydms.descriptors.contract import SELECTED

    assert result.features
    assert set(result.features) <= set(SELECTED.names)
    fit = next(stage for stage in result.stages if stage.name == "fit")
    assert fit.columns == len(result.features)


# --------------------------------------------------------------------------------------
# The same seed reproduces the run
# --------------------------------------------------------------------------------------


def test_two_runs_with_the_same_seed_are_identical(result: smoke.SmokeRun) -> None:
    """Card #73's reproducibility box, and the second full run this file pays for.

    The digest excludes wall-clock time and the artifact version, and includes every predicted
    number at full `repr` precision -- so a model that changed by one ulp fails here, and a
    machine that was busy does not.
    """
    assert smoke.run().digest() == result.digest()


def test_the_digest_carries_the_numbers_and_not_the_timings(result: smoke.SmokeRun) -> None:
    """A digest that rounded its predictions would pass while the model quietly changed."""
    digest = result.digest()

    assert repr(float(result.predictions.iloc[0, 0])) in digest
    assert "seconds" not in digest
    assert result.version not in digest


# --------------------------------------------------------------------------------------
# No absolute path anywhere in the run
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path", [Path(smoke.__file__), smoke.FIXTURE_FILE], ids=["module", "fixture"]
)
def test_no_rooted_path_literal_appears(path: Path) -> None:
    """The archival pipeline hard-coded a drive letter in nine scripts. Never again."""
    found = ROOTED.findall(path.read_text(encoding="utf-8"))

    assert not found, f"{path.name} carries a rooted path literal: {found}"


def test_the_chain_runs_from_a_different_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, result: smoke.SmokeRun
) -> None:
    """The real property behind 'no absolute path': nothing resolves against the caller's cwd.

    `hydms.config.repo_root` walks up from the package rather than from `os.getcwd`, and this
    is what measures that end to end. Reuses the module-scoped run's digest as the expected
    value, so it also says the answer does not depend on where you stood.
    """
    monkeypatch.chdir(tmp_path)

    assert smoke.run().digest() == result.digest()


# --------------------------------------------------------------------------------------
# The fixture
# --------------------------------------------------------------------------------------


def test_the_fixture_preserves_the_shapes_the_chain_depends_on() -> None:
    """Several classes, a repeated composition, a formula spelled more than one way.

    Without the second, the grouping that closes leak L8 has nothing to group; without the
    third, the canonical key is doing no work the raw string would not do.
    """
    found = smoke.check_fixture(smoke.load_fixture())

    assert found["classes"] >= 2
    assert found["repeated_compositions"] >= 1
    assert found["multiply_spelled"] >= 1


def test_the_fixture_is_small_enough_to_be_a_smoke_test() -> None:
    """A fixture that grew into a dataset is a retrain wearing a smoke test's name."""
    assert len(smoke.load_fixture()) < 2 * smoke.FIXTURE_ROWS


def test_the_committed_fixture_is_what_emit_produces(tmp_path: Path, raw_data_path: Path) -> None:
    """A fixture nobody can regenerate quietly stops representing its source.

    The same shape `tests/screens/test_applicability.py` asserts for the domain reference:
    the committed bytes are the command's output, so `--emit` is a real regeneration path and
    not a comment. Skips where the curated data is absent, since that is what it samples from.
    """
    assert raw_data_path.is_file()
    regenerated = smoke.emit(tmp_path / "smoke-fixture.csv")

    assert regenerated.read_bytes() == smoke.FIXTURE_FILE.read_bytes()


def test_a_fixture_that_lost_a_shape_is_refused_rather_than_run() -> None:
    """Catches: a fixture trimmed until the grouping stages have nothing to do.

    Such a fixture still *runs*, which is the danger -- the run then proves less than it
    claims and nothing says so.
    """
    frame = smoke.load_fixture()
    one_class = frame[frame["Alloy_class"] == frame["Alloy_class"].iloc[0]]

    with pytest.raises(smoke.SmokeError, match="classes"):
        smoke.check_fixture(one_class.head(3))


def test_a_missing_fixture_says_how_to_regenerate_it(tmp_path: Path) -> None:
    with pytest.raises(smoke.SmokeError, match="--emit"):
        smoke.load_fixture(tmp_path / "absent.csv")


# --------------------------------------------------------------------------------------
# The command, and its place in the fast lane
# --------------------------------------------------------------------------------------


def test_the_command_reports_the_stage_table_and_exits_zero(capsys) -> None:
    assert smoke.main([]) == smoke.EXIT_OK

    printed = capsys.readouterr().out
    for stage in smoke.STAGES:
        assert stage in printed
    assert "say nothing about accuracy" in printed


def test_the_digest_flag_prints_only_what_must_reproduce(capsys) -> None:
    assert smoke.main(["--digest"]) == smoke.EXIT_OK

    printed = capsys.readouterr().out
    assert "features:" in printed
    assert "the chain connects" not in printed


def test_an_unreadable_config_is_a_bad_invocation_not_a_broken_chain(
    tmp_path: Path, capsys
) -> None:
    """Exit 2 and exit 1 mean different things, and CI reads the difference."""
    assert smoke.main(["--config", str(tmp_path / "absent.yaml")]) == smoke.EXIT_BAD_INVOCATION
    capsys.readouterr()


def test_the_smoke_run_is_in_the_ci_fast_lane(
    repo_root: Path, request: pytest.FixtureRequest
) -> None:
    """Card #73's last box, checked rather than remembered.

    The fast lane runs `python -m pytest` over the whole `tests` tree, so this file is in it
    as long as nothing in it is marked `slow`. The marker half is read off the *collected
    items* rather than grepped out of this file: a source scan for the string finds its own
    assertion, which is how that first draft failed.

    **The other half used to assert `"not slow" not in workflow`, and that was a proxy rather
    than the subject.** It stood for "the lane deselects nothing, so everything is in it",
    which was true until card #86 had to make it false: the `suite` job was running the full
    24 m 58 s suite against a 20-minute cap and three consecutive pushes died on the timeout.
    It now runs `-m "not slow"`, which is what `pyproject.toml` has always said the marker
    means. This card's guarantee is untouched by that -- nothing here is marked slow -- so the
    assertion is rewritten to check the guarantee instead of the proxy: if the lane deselects
    by marker at all, the expression must be exactly `not slow`, because any other one could
    drop this file for a reason this test would not see.
    """
    workflow = (repo_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    deselected = [
        item.nodeid
        for item in request.session.items
        if item.path == request.node.path and item.get_closest_marker("slow") is not None
    ]

    assert "python -m pytest" in workflow
    assert not deselected, f"the fast lane would deselect {deselected}"

    selectors = re.findall(r'-m\s+"([^"]+)"', workflow)
    assert set(selectors) <= {"not slow"}, (
        f"the fast lane deselects by {selectors}, which this test cannot reason about. Only "
        f'`-m "not slow"` is understood here, and this file carries no slow marker.'
    )
