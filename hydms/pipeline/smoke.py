"""Does the chain still connect? One command, one small fixture, under a minute.

    python -m hydms.pipeline.smoke                  # run it
    python -m hydms.pipeline.smoke --emit           # regenerate the committed fixture
    python -m hydms.pipeline.smoke --store out/     # keep the artifact version it writes

The audit's second finding was that the pipeline did not run end to end **at all**: four
broken links, one of them a featurisation input with no producer anywhere in the repository's
history. A full retrain is far too slow to guard against that on every push -- ``train`` is
about 3.5 hours and ``loco`` about twice that -- so the guard is a smoke run over a sampled
fixture: every stage executes, in order, on real rows shaped like the real thing.

**This is not a performance test and not an accuracy test.** Nothing here is a number anybody
may quote. The R² of a model fitted on a hundred and fifty rows at a sentinel budget is
meaningless, and the run prints none. It answers one question -- *does the chain still
connect?* -- which is exactly the question this repository could not answer before Phase H.

The order the stages actually run in
------------------------------------

Card #73's box reads ``load -> merge -> canonicalise -> split -> screen -> featurise ->
select -> fit -> predict``. That is the *archival* script order, and the live pipeline's is
different, so this module runs the live one:

    load -> canonicalise -> split -> featurise -> merge -> screen -> select -> fit -> predict

Two of the arrows moved, and both moves are the fix for a leak rather than a preference.
**Canonicalisation precedes the split** because the split groups on the canonical composition
and not on the formula string -- leak L8, sixteen compositions spanning two splits. **The
merge follows featurisation** because the merge that exists in this pipeline is
:func:`~hydms.data.metadata.with_features`, the label-addressed join of the descriptor matrix
back onto the record, which is where ``Alloy_class`` survives featurisation (leak L13) and
where the positional ``concat`` of ``merge_datasets.py:46`` used to be (leak L9). Running a
sequence the pipeline does not have would prove nothing about the pipeline that ships.

What the fixture has to preserve
--------------------------------

Not just "some rows". Three shapes, each of which a stage depends on and each of which is
asserted by :func:`emit` before the file is written:

  - **Several alloy classes**, or the class column is constant and nothing about the
    reconciliation or the class-aware folds is exercised.
  - **A canonical composition appearing more than once**, or the grouping that stops leak L8
    has nothing to group and the split is a row-level split by accident.
  - **A near-duplicate formula string** -- two spellings that differ only in whitespace or in
    element order -- or the canonical key is doing no work the raw string would not do.

The fixture is **generated, not curated by hand**: ``--emit`` samples it from the raw data by
a deterministic stride over a sorted key, with the collision rows force-included, and
``tests/test_smoke_pipeline.py`` asserts the committed file is what that command produces. A
fixture nobody can regenerate is a fixture that quietly stops representing its source.

The budget
----------

Every knob that costs time is turned down to a sentinel budget, and each is named where it is
set: Boruta at :data:`~hydms.surrogate.selection.SENTINEL_BUDGET`'s ten iterations rather than
two thousand, CatBoost at a fixed cheap configuration rather than an Optuna search. The
budget changes *how well* every stage runs and not *which* stages run, which is the only
property a smoke test needs.

Card #73.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, TextIO

import pandas as pd

from hydms.config import Config, ConfigError
from hydms.config import load as load_config

EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_BAD_INVOCATION = 2

#: The committed fixture, beside this module and shipped as package data -- the same choice
#: ``hydms/screens/domain-reference.json`` makes, and for the same reason: the smoke run must
#: work in a container that has no curated data in it.
FIXTURE_FILE = Path(__file__).with_name("smoke-fixture.csv")

#: How many rows :func:`emit` aims for. Chosen against the budget, not for tidiness: the whole
#: chain must finish inside a minute on the CI runner, and the stage that scales worst with
#: rows is CleanLab's cross-fit.
FIXTURE_ROWS = 200

#: How many multiply-spelled compositions and how many repeated ones :func:`sample` forces in,
#: each. A cap rather than "all of them": the curated data holds 130 of the second kind, which
#: alone would be two thirds of the fixture, and the assertions in :func:`check_fixture` need
#: the shapes to *exist*, not to dominate.
FIXTURE_COLLISIONS = 12

#: The stratification budget the smoke split runs at, and the whole of what it changes.
#:
#: ``pipeline.yaml`` cuts five temperature bins against five target bins over 1,115 canonical
#: compositions. Two hundred compositions do not fill twenty-five strata: the *second* cut runs
#: over the 30 % held out by the first, so a stratum of five compositions contributes one and a
#: half to it, and ``StratifiedShuffleSplit`` cannot divide a class with one member. That is
#: arithmetic about the fixture's size, not a defect in the split, and it is fixed here by
#: stratifying more coarsely rather than by making the fixture large enough to be slow.
#:
#: **It changes how finely the split stratifies and nothing else.** The fractions, the seed,
#: the grouping on the canonical composition and the L8 disjointness check are all the real
#: ones -- which is what this stage is here to exercise.
SMOKE_SPLIT: Mapping[str, int] = {
    "target_bins": 3,
    "temperature_bins": 3,
    "min_stratum_size": 10,
}

#: Trees in the forest CleanLab cross-fits during the screening stage.
#:
#: :func:`~hydms.data.screening.label_issues` defaults to the archival selector's forest, which
#: is scikit-learn's hundred trees, and CleanLab cross-fits it five times. **Measured on this
#: fixture: 18.5 s of a 21 s run** -- almost the whole budget, spent on the one stage whose
#: verdict this run does not read. Twenty trees is the same estimator, the same depth from
#: ``selection.boruta_max_depth`` and the same seed, cross-fitted the same way; what changes is
#: how well the forest fits, which is a question about the verdict rather than about whether
#: the stage runs.
SMOKE_FOREST_TREES = 20

#: The CatBoost configuration the smoke fit uses. Fixed rather than searched: an Optuna study
#: is the single most expensive thing in the real pipeline and it tunes a model whose quality
#: this run does not look at.
SMOKE_PARAMS: Mapping[str, Any] = {"iterations": 60, "depth": 4, "learning_rate": 0.3}

#: The stages, in the order they run. Named here so the run table, this docstring and the test
#: cannot drift apart.
STAGES: tuple[str, ...] = (
    "load",
    "canonicalise",
    "split",
    "featurise",
    "merge",
    "screen",
    "select",
    "fit",
    "predict",
)

#: Candidates the loaded surrogate is asked about at the end. Three real alloys from three
#: different families, none of which needs to be in the fixture: the point is that a formula
#: string reaches a calibrated interval.
PROBE_ALLOYS: tuple[str, ...] = ("La1Ni5", "Ti1Fe1", "Mg2Ni1")

#: The temperature the probe asks at, in kelvin. Inside ``domain.temperature_min_k`` and
#: ``_max_k`` by a wide margin, because a refusal is #77's subject and not this one's.
PROBE_KELVIN = 298.0


class SmokeError(RuntimeError):
    """The chain is broken, and the message says at which stage and why.

    A ``RuntimeError`` rather than the ``ValueError`` the layer guards raise: nothing here is
    a caller passing something inadmissible. Every stage's own exception is allowed to
    propagate untouched -- a ``SchemaViolation`` from the loader is a better message than
    anything this module could wrap it in -- and this is raised only for the failures that
    belong to the *run*, such as a fixture that has stopped having the shape the chain needs.
    """


# --------------------------------------------------------------------------------------
# What a run produced
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Stage:
    """One stage's result: what it was, how big its output was, how long it took.

    Attributes:
        name: One of :data:`STAGES`.
        rows: Rows leaving the stage.
        columns: Columns leaving it, where that means something; ``0`` where it does not.
        seconds: Wall clock. Reported so the sixty-second budget is inspectable rather than
            asserted once and forgotten -- the same reason
            :class:`~hydms.screens.protocol.Verdicts` carries its durations.
        note: One clause a reader gets, e.g. which features were selected.
    """

    name: str
    rows: int
    columns: int
    seconds: float
    note: str = ""


@dataclass(frozen=True)
class SmokeRun:
    """Everything one run of the chain produced.

    Attributes:
        stages: Every stage, in run order.
        features: The features selection chose, in its order.
        version: The artifact version the fit was written as, inside the run's store.
        predictions: The probe alloys' calibrated intervals.
        seconds: The whole run.
    """

    stages: tuple[Stage, ...]
    features: tuple[str, ...]
    version: str
    predictions: pd.DataFrame
    seconds: float

    def table(self) -> pd.DataFrame:
        """The stages as a table, indexed by stage name."""
        return pd.DataFrame(
            [
                {
                    "rows": stage.rows,
                    "columns": stage.columns,
                    "seconds": round(stage.seconds, 3),
                    "note": stage.note,
                }
                for stage in self.stages
            ],
            index=pd.Index([stage.name for stage in self.stages], name="stage"),
        )

    def digest(self) -> str:
        """Everything about this run that a **second run with the same seed must reproduce**.

        Deliberately excludes every wall-clock number, and deliberately includes every
        prediction to full precision. The reproducibility box on card #73 is about the
        pipeline's arithmetic, not about how fast the machine was; and a digest that rounded
        the predictions would pass while the model quietly changed.

        The artifact version is excluded too. A run writes into a fresh store and always
        assigns ``v1``; including it would assert a property of the store rather than of the
        chain, and would make a run into a pre-existing directory look like a difference.
        """
        lines = [f"{stage.name}: {stage.rows} x {stage.columns}" for stage in self.stages]
        lines.append("features: " + ", ".join(self.features))
        for label, row in self.predictions.iterrows():
            values = " ".join(f"{name}={row[name]!r}" for name in self.predictions.columns)
            lines.append(f"{label}: {values}")
        return "\n".join(lines)


# --------------------------------------------------------------------------------------
# The fixture
# --------------------------------------------------------------------------------------


def fixture_schema(rows: int, cfg: Config | None = None) -> Any:
    """The curated dataset's own schema, with its row count replaced.

    The loader validates a source against a declared shape and refuses one that has changed
    size, on the ground that "a source that has changed size is a decision, not a detail". The
    fixture *is* that decision, made here and once: everything else about the schema -- the
    column names, the allowed alloy classes, the formula parsing, the target bounds -- is the
    real one, so a fixture whose contents drift out of the curated vocabulary fails at the
    door exactly as the real file would.
    """
    from hydms.data.load import hydride_data_schema

    return replace(hydride_data_schema(cfg.columns if cfg is not None else None), expected_rows=rows)


def load_fixture(path: Path | None = None, cfg: Config | None = None) -> pd.DataFrame:
    """Read the committed fixture and validate it against the curated schema."""
    from hydms.data.load import validate

    source = FIXTURE_FILE if path is None else Path(path)
    if not source.is_file():
        raise SmokeError(
            f"the smoke fixture is missing at {source}. Regenerate it with "
            f"`python -m hydms.pipeline.smoke --emit`, which samples it from the curated data."
        )
    frame = pd.read_csv(source)
    return validate(frame, fixture_schema(len(frame), cfg), source=str(source))


def sample(frame: pd.DataFrame, *, rows: int = FIXTURE_ROWS, cfg: Config | None = None) -> pd.DataFrame:
    """Choose the fixture's rows from the curated data, deterministically and without an RNG.

    A stride over a sorted key rather than ``DataFrame.sample``: a seeded sample is
    reproducible only for as long as the library's sampler is, and this file is committed and
    diffed. Sorting by ``(alloy class, canonical key, temperature, target, label)`` and then
    walking every ``k``-th row spreads the selection across each family's compositions and
    depends on nothing but the data.

    Two groups of compositions are taken **first**, whatever the stride would have chosen,
    because the chain's grouping stages are vacuous without them: the ones the file spells more
    than one way, and the ones measured more than once. Both are **capped**
    (:data:`FIXTURE_COLLISIONS`) rather than taken whole -- the curated data holds 130 repeated
    compositions and 32 multiply-spelled ones, which on their own would be one and a half times
    the fixture's whole budget, and a dozen of each is as much as any grouping assertion needs.
    The stride then fills the rest.

    Args:
        frame: The curated dataset, as :func:`~hydms.data.load.load_hydride_data` returns it.
        rows: How many rows to aim for. The result may be slightly larger: a composition is
            never split across the boundary, because half a composition in the fixture would
            make the grouping guarantee untestable.
        cfg: Defaults to the packaged configuration.

    Returns:
        The sampled rows, in the curated file's own order, with its own index labels.
    """
    from hydms.data.canonical import group_keys
    from hydms.data.load import parse_formula
    from hydms.descriptors.contract import SELECTED

    config = cfg if cfg is not None else load_config()
    names = config.columns
    # Only rows the contract can serve completely, which is the same filter
    # `hydms.surrogate.model.capacity_matrix` applies before it fits: four of the fourteen
    # selected features are empty cells in the `jarvis` table for Eu, and such a row is refused
    # rather than filled. Sampling them into the fixture would make the smoke run fail at
    # featurisation on a defect of the published tables rather than of the chain.
    servable = [
        label
        for label, formula in frame[names.formula].items()
        if SELECTED.computability(parse_formula(formula)).complete
    ]
    frame = frame.loc[servable]
    keys = group_keys(frame, names.formula)
    work = frame.assign(_key=keys)

    per_key = work.groupby("_key")[names.formula].agg(["nunique", "size"])
    kept_keys = set(sorted(per_key.index[per_key["nunique"] > 1])[:FIXTURE_COLLISIONS])
    kept_keys.update(sorted(per_key.index[per_key["size"] > 1])[:FIXTURE_COLLISIONS])
    required = set(work.index[work["_key"].isin(kept_keys)])

    ordered = work.sort_values(
        [names.alloy_class, "_key", names.temperature, names.target], kind="stable"
    )
    remaining = [label for label in ordered.index if label not in required]
    still_wanted = max(rows - len(required), 0)
    if still_wanted and remaining:
        stride = max(len(remaining) // still_wanted, 1)
        required.update(remaining[::stride][:still_wanted])

    # Whole compositions, never half of one: a group split across the fixture boundary would
    # leave the L8 guarantee with nothing to catch. `work` carries `frame`'s index in `frame`'s
    # order, so the boolean mask below preserves the curated file's row order for free -- which
    # is what makes the emitted CSV a readable diff against its source.
    chosen_keys = set(work.loc[work.index.isin(required), "_key"])
    return frame.loc[work["_key"].isin(chosen_keys).to_numpy()]


def check_fixture(frame: pd.DataFrame, cfg: Config | None = None) -> dict[str, int]:
    """Assert the three shapes the chain depends on, and return what was found.

    Raises:
        SmokeError: naming the shape that is missing. A fixture that has lost one of them
            still *runs* -- which is the whole danger, because the run then proves less than
            it claims and nothing says so.
    """
    from hydms.data.canonical import group_keys

    config = cfg if cfg is not None else load_config()
    names = config.columns
    keys = group_keys(frame, names.formula)
    spellings = frame.groupby(keys.to_numpy())[names.formula].nunique()

    found = {
        "rows": len(frame),
        "classes": int(frame[names.alloy_class].nunique()),
        "compositions": int(keys.nunique()),
        "repeated_compositions": int((keys.value_counts() > 1).sum()),
        "multiply_spelled": int((spellings > 1).sum()),
    }
    for what, minimum, why in (
        ("classes", 2, "the class column would be constant and the class-aware folds vacuous"),
        (
            "repeated_compositions",
            1,
            "the grouping that stops leak L8 would have nothing to group, and the split "
            "would be a row-level split by accident",
        ),
        (
            "multiply_spelled",
            1,
            "the canonical key would be doing no work the raw formula string does not do",
        ),
    ):
        if found[what] < minimum:
            raise SmokeError(
                f"the smoke fixture has {found[what]} {what.replace('_', ' ')}, and needs at "
                f"least {minimum}: {why}. Regenerate it with `--emit`."
            )
    return found


def emit(path: Path | None = None, *, rows: int = FIXTURE_ROWS, cfg: Config | None = None) -> Path:
    """Sample the fixture out of the curated data and write it, checked.

    The slow half of this module, and the reason it exists as a command: a fixture nobody can
    regenerate is a fixture that quietly stops representing its source. The same shape
    ``python -m hydms.screens.domain --emit`` has, and a test asserts the committed bytes are
    what this produces.
    """
    from hydms.data.load import load_hydride_data

    destination = FIXTURE_FILE if path is None else Path(path)
    chosen = sample(load_hydride_data(), rows=rows, cfg=cfg)
    check_fixture(chosen, cfg)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # `lineterminator` explicitly: pandas writes the platform's terminator otherwise, so a
    # file emitted on Windows and one emitted on Linux would differ in every line and the
    # committed-bytes test would fail on whichever machine did not write it.
    chosen.to_csv(destination, index=False, lineterminator="\n")
    return destination


# --------------------------------------------------------------------------------------
# The chain
# --------------------------------------------------------------------------------------


def _elapsed(started: float) -> float:
    return time.perf_counter() - started


def run(
    *,
    fixture: Path | None = None,
    store: Path | None = None,
    cfg: Config | None = None,
) -> SmokeRun:
    """Every stage of the pipeline, in order, on the fixture. The whole of the smoke test.

    Args:
        fixture: The sampled CSV. Defaults to the committed :data:`FIXTURE_FILE`.
        store: Where to write the artifact version the fit produces. Defaults to a temporary
            directory that is removed when the run returns -- so a smoke run leaves nothing
            behind and two runs cannot see each other's versions, which is what makes the
            reproducibility check a check of the *chain*.
        cfg: Defaults to the packaged configuration.

    Returns:
        A :class:`SmokeRun`.

    Raises:
        SmokeError: the fixture is missing, or has lost one of the shapes the chain needs.
        Anything a stage raises: a broken link is meant to surface as that stage's own
        message, at that stage's own layer, rather than as a uniform "the pipeline failed".
    """
    if store is None:
        with tempfile.TemporaryDirectory(prefix="hydms-smoke-") as scratch:
            return run(fixture=fixture, store=Path(scratch), cfg=cfg)

    from hydms import artifacts
    from hydms.data.metadata import with_features, with_metadata
    from hydms.data.screening import label_issues, screen
    from hydms.data.splits import SPLIT_NAMES, assign_splits
    from hydms.data.target import to_model_space
    from hydms.descriptors.contract import SELECTED, FeatureContract
    from hydms.descriptors.featurize import featurize
    from hydms.surrogate.deploy import deployed_fit, save_deployed
    from hydms.surrogate.model import ModelSettings
    from hydms.surrogate.predict import clear_cache, surrogate_from
    from hydms.surrogate.selection import SelectionSettings, select_features, sentinel_settings

    config = cfg if cfg is not None else load_config()
    names = config.columns
    stages: list[Stage] = []
    whole = time.perf_counter()

    def done(name: str, frame_rows: int, frame_columns: int, started: float, note: str = "") -> None:
        stages.append(Stage(name, frame_rows, frame_columns, _elapsed(started), note))

    # -- load ---------------------------------------------------------------------------
    started = time.perf_counter()
    raw = load_fixture(fixture, config)
    shape = check_fixture(raw, config)
    done(
        "load",
        len(raw),
        len(raw.columns),
        started,
        f"{shape['classes']} alloy class(es), {shape['compositions']} composition(s)",
    )

    # -- canonicalise -------------------------------------------------------------------
    started = time.perf_counter()
    record = with_metadata(raw)
    done(
        "canonicalise",
        len(record),
        len(record.columns),
        started,
        f"{shape['multiply_spelled']} composition(s) the file spells more than one way",
    )

    # -- split --------------------------------------------------------------------------
    started = time.perf_counter()
    split = assign_splits(record, settings=replace(config.split, **SMOKE_SPLIT))
    counts = {name: int((split == name).sum()) for name in SPLIT_NAMES}
    done(
        "split",
        len(split),
        0,
        started,
        ", ".join(f"{k} {v}" for k, v in counts.items()) + " (SMOKE_SPLIT stratification)",
    )
    for name, count in counts.items():
        if count == 0:
            raise SmokeError(
                f"the {name!r} split is empty on this fixture, so the stages that read it "
                f"cannot run. The fixture is too small or too concentrated; regenerate it "
                f"with `--emit --rows N` for a larger N."
            )

    # -- featurise ----------------------------------------------------------------------
    started = time.perf_counter()
    features = featurize(record[names.formula], record[names.temperature], contract=SELECTED)
    done("featurise", len(features), len(features.columns), started, "the SELECTED contract")

    # -- merge --------------------------------------------------------------------------
    #
    # The keyed, label-addressed join of the matrix back onto the record. This is the merge
    # stage: `merge_datasets.py:46`'s positional `concat` is leak L9, and the class column
    # surviving the join is leak L13.
    started = time.perf_counter()
    frame = with_features(record, features)
    done("merge", len(frame), len(frame.columns), started, "with_features, joined by label")

    # -- screen -------------------------------------------------------------------------
    #
    # CleanLab over the TRAINING rows only, declared as `train` to the screening stage, which
    # is what entitles it to drop any of them and what stops it touching anything else
    # (leaks L3 and L10).
    started = time.perf_counter()
    train = list(frame.index[split == "train"])
    from sklearn.ensemble import RandomForestRegressor

    verdict = label_issues(
        frame.loc[train, list(SELECTED.names)],
        to_model_space(frame.loc[train, names.target]),
        estimator=RandomForestRegressor(
            n_estimators=SMOKE_FOREST_TREES,
            max_depth=config.selection.boruta_max_depth,
            # One thread, which `label_issues` now requires: a parallel forest sums its trees
            # in thread-finishing order and the verdict moves between runs (card #104).
            n_jobs=1,
            random_state=config.seed,
        ),
        seed=config.seed,
    )
    screening = screen(frame, split, label_issues=verdict.issues, label_quality=verdict.quality)
    screened, split = screening.frame, split.loc[screening.frame.index]
    done(
        "screen",
        len(screened),
        len(screened.columns),
        started,
        f"{verdict.flagged} flagged, {len(screening.removed)} removed, all of them train",
    )

    # -- select -------------------------------------------------------------------------
    started = time.perf_counter()
    budget = sentinel_settings(replace(SelectionSettings.from_config(config), seed=config.seed))
    selection = select_features(screened, list(screened.index[split == "train"]), settings=budget)
    if not selection.features:
        raise SmokeError(
            "selection chose no features, so there is nothing to fit. On the real matrix that "
            "would be a defect; on this fixture it means the sentinel budget is too small for "
            "the sample."
        )
    done("select", selection.rows, len(selection.features), started, ", ".join(selection.features))

    # -- fit ----------------------------------------------------------------------------
    #
    # `screen_labels=False`: the screening stage above already ran, over the same rows and by
    # the same function. Leaving it on would pay CleanLab's cross-fit twice for one verdict.
    started = time.perf_counter()
    settings = replace(
        ModelSettings.from_config(config),
        features=selection.features,
        optuna_trials=1,
        early_stopping_rounds=5,
        screen_labels=False,
    )
    fit = deployed_fit(screened, split, params=SMOKE_PARAMS, settings=settings, config=config)
    manifest = save_deployed(
        fit,
        settings=settings,
        contract=FeatureContract.from_names(selection.features),
        notes="smoke run over the sampled fixture — not a deployable fit",
        store=Path(store),
    )
    done(
        "fit",
        len(fit.fitting),
        len(selection.features),
        started,
        f"{len(fit.calibration)} calibration row(s), correction "
        f"{fit.conformal.correction:+.6f} in model space",
    )

    # -- predict ------------------------------------------------------------------------
    #
    # Through the artifact store, not from the objects in hand: reading the version back is
    # the last link in the chain and the one a `joblib` change would break.
    started = time.perf_counter()
    clear_cache()
    surrogate = surrogate_from(
        artifacts.load(manifest.version, store=Path(store), require_gates=False)
    )
    predictions = surrogate.predict(list(PROBE_ALLOYS), PROBE_KELVIN)
    done(
        "predict",
        len(predictions),
        len(predictions.columns),
        started,
        f"{', '.join(PROBE_ALLOYS)} at {PROBE_KELVIN:g} K from {manifest.version}",
    )

    return SmokeRun(
        stages=tuple(stages),
        features=tuple(selection.features),
        version=manifest.version,
        predictions=predictions,
        seconds=_elapsed(whole),
    )


# --------------------------------------------------------------------------------------
# The command
# --------------------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.pipeline.smoke",
        description=(
            "Run every pipeline stage end to end on a sampled fixture. Answers 'does the "
            "chain connect', and nothing about accuracy."
        ),
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help="regenerate the committed fixture from the curated data and exit",
    )
    parser.add_argument(
        "--rows", type=int, default=FIXTURE_ROWS, help="rows to aim for when emitting"
    )
    parser.add_argument(
        "--fixture", type=Path, default=None, help="a fixture CSV; defaults to the committed one"
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=None,
        help="keep the artifact version the run writes here; defaults to a temporary "
        "directory that is removed when the run ends",
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    parser.add_argument(
        "--digest",
        action="store_true",
        help="print only what a second run with the same seed must reproduce",
    )
    return parser


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    """Run the chain, or emit the fixture. Returns the process exit code.

    Exit codes:

        0   every stage ran
        1   a stage failed, or the fixture no longer has the shape the chain needs
        2   the invocation itself was wrong (unreadable config, unwritable path)
    """
    stream = out if out is not None else sys.stdout
    args = _parser().parse_args(list(argv) if argv is not None else None)

    try:
        config = load_config(args.config)
    except (ConfigError, OSError) as error:
        print(f"could not read the configuration: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    if args.emit:
        try:
            written = emit(args.fixture, rows=args.rows, cfg=config)
        except OSError as error:
            print(f"could not write the fixture: {error}", file=sys.stderr)
            return EXIT_BAD_INVOCATION
        except SmokeError as error:
            print(f"the sampled fixture is not usable: {error}", file=sys.stderr)
            return EXIT_BROKEN
        found = check_fixture(load_fixture(written, config), config)
        print(
            f"wrote {written}: {found['rows']} row(s), {found['classes']} alloy class(es), "
            f"{found['repeated_compositions']} composition(s) measured more than once, "
            f"{found['multiply_spelled']} spelled more than one way",
            file=stream,
        )
        return EXIT_OK

    try:
        result = run(fixture=args.fixture, store=args.store, cfg=config)
    except SmokeError as error:
        print(f"the chain is broken: {error}", file=sys.stderr)
        return EXIT_BROKEN

    if args.digest:
        print(result.digest(), file=stream)
        return EXIT_OK

    print(result.table().to_string(), file=stream)
    print(
        f"\nthe chain connects: {len(result.stages)} stage(s) in "
        f"{result.seconds:.1f} s. These numbers say nothing about accuracy — the fit is "
        f"{len(result.features)} feature(s) at a sentinel budget over a sampled fixture, and "
        f"no number from it may be quoted.",
        file=stream,
    )
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
