"""L3 -- what the model is worth, with an interval on every number and a name on every claim.

    python -m hydms.surrogate.evaluate                     # the out-of-fold reading
    python -m hydms.surrogate.evaluate --emit              # rebuild the write-up, fits nothing
    python -m hydms.surrogate.evaluate --artifact current  # the artifact reading (card #34)

The domain memo's item 3.3.5 warns that at n=239 a test R2 of 0.916 carries a wide interval and
that a bare point estimate should not be reported. Every number that goes into the Chapter 1
revision comes out of this module, so an interval is not an option here -- there is no entry
point that returns a point estimate alone.

**Two readings, and they are different claims.** This module emits both and labels every row
with which one it belongs to, exactly as card #25 forced for the feature set.

- **The out-of-fold reading** is the primary one. Every row of the training split was
  predicted by the outer fold that held it out, so the score is honest -- but it comes from
  *five different models*. It is a claim about the **procedure**: what this pipeline produces,
  on average, when it is run. It needs no artifact.
- **The artifact reading** is one promoted model scored on rows it has never seen. That is a
  claim about **a model**. It needs card #34's ``artifacts/v{N}``, and until one is promoted
  ``--artifact`` refuses by name rather than failing somewhere deeper.

**The interval is knowingly too narrow, and the table says so in a column.** The out-of-fold
predictions come from five models whose training sets overlap, so they are not exchangeable
draws from one procedure, and there is no unbiased estimator of the variance of K-fold
cross-validation (Bengio & Grandvalet, *JMLR* 5:1089, 2004). The bootstrap below resamples the
*rows*, which prices the sampling of materials and not the sampling of folds. In a chapter
whose whole argument is that the old numbers were too optimistic, an interval that is too
narrow has to be labelled where it cannot be dropped: :data:`INTERVAL_CAVEAT` is a column on
every row of the emitted table, not a sentence in this docstring. Beside it rides a second,
cruder interval over the five fold scores (:data:`PER_FOLD`), which prices fold-to-fold spread
and nothing else. Two intervals that disagree are more honest than one that looks
authoritative -- and card #24 measured why they will: screening removes between 15 and 144 of
a fold's ~710 training rows, so part of the per-fold spread is training size and not the model.

**The bootstrap resamples canonical compositions, never rows.**
:func:`~hydms.data.canonical.group_keys` is the seam -- card #13 splits on it, #88 folds on it,
#87 re-joins on it -- and a row-level resample here would be a fourth meaning of "the same
material", which is leak L8's logic applied to intervals instead of splits. **Measured on the
real matrix:** the training split is 893 rows in **780 canonical groups**, sizes 1 to 6, of
which **692 are singletons**. So the correction is real and it is *small*: a 13 % reduction in
independent units, not a halving. It is taken on principle, and because the magnitude could be
oversold, both readings are computed and published side by side (:data:`GROUPS` against
:data:`ROWS`) so that no later session has to re-litigate the choice from a paragraph.

**One resample at the split level; every breakdown is computed from it.** 83 of the 780 groups
span more than one temperature, up to six distinct values, so a resampled group carries all of
its temperature rows with it and resampling *within* a temperature bin would split those groups
and break the seam locally. The consequence is that a subgroup's *n* varies between replicates,
so the table records the smallest and largest it took -- a bin that is thin in most replicates
is then visible rather than implied.

**Every row names the feature set it belongs to.** There are two and they are not
interchangeable: :data:`~hydms.descriptors.contract.SELECTED`, the consensus fourteen a shipped
model is fitted on, and the per-fold sets of 16 to 20 that card #25's five-fold run actually
produced. An interval over folds that each chose their own columns is an interval about a
*procedure including selection*; one over a fixed fourteen-column pipeline is about this model.
Selection does not run inside card #26's tuning loop, so everything here is the second -- and
it says so in a column rather than in a paragraph the Chapter 1 revision would have to trust.

**Explainability is computed on the deployed fit's training rows -- never on test.** That is
leak L11: ``benchmark_model_selection.py:1375,1383,1394`` computed PDP and SHAP on ``X_test``,
which makes ``REPORT.md`` section 6.1 a test-set artefact. :func:`shap_table` and
:func:`pdp_table` take the rows they run on and record their split name in a ``computed_on``
column, and the L11 sentinel asserts that value is not in
:data:`~hydms.surrogate.validation.HELD_OUT_SPLITS` -- the project's one definition of a
held-out name, asserted against rather than restated. There is no dedicated explainability
split: it would cost rows the deployed fit needs and buys nothing over training-row SHAP.

**Nothing here fits a model.** The expensive run is ``python -m hydms.surrogate.train``, which
writes the row-level predictions and the explainability tables as it goes; this module reads
them. Regenerating the published write-up therefore costs a second rather than three and a half
hours, which is the only reason the committed document can be checked against the code that
produces it -- the same shape card #25 gave ``--emit-comparison``.

Exit codes:

    0   the tables were read and written
    2   the invocation itself was wrong (unreadable config or tables, nothing promoted)

Card #29.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import numpy as np
import pandas as pd

from hydms.artifacts.manifest import describe_git
from hydms.config import Config, ConfigError, load
from hydms.data.metadata import CANONICAL_KEY_COLUMN
from hydms.data.target import model_space_name
from hydms.descriptors.contract import SELECTED
from hydms.qa import assert_explanation_is_not_held_out
from hydms.surrogate.model import (
    QuantileModel,
    column_names,
    quantile_metrics_from_arrays,
)
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.validation import HELD_OUT_SPLITS

EXIT_OK = 0
EXIT_BAD_INVOCATION = 2

__all__ = [
    "CONFIDENCE",
    "EXPLAINABILITY",
    "GROUPS",
    "INTERVAL_CAVEAT",
    "PDP_POINTS",
    "PER_FOLD",
    "PUBLISHED",
    "RESAMPLES",
    "ROWS",
    "SOURCE_TABLES",
    "TABLES",
    "UNKNOWN_RUN",
    "EvaluationError",
    "Interval",
    "metrics_table",
    "pdp_table",
    "per_fold_intervals",
    "read_out_of_fold",
    "read_run",
    "shap_table",
    "subgroup_table",
    "to_markdown",
]


class EvaluationError(ValueError):
    """A table cannot be read, or does not carry what a metric needs.

    A ``ValueError``, like :class:`~hydms.surrogate.model.ModelError` and
    :class:`~hydms.surrogate.conformal.ConformalError`: a refusal at the door, not a detector
    reporting that a guard failed.
    """


#: Resamples per interval. Card #29's number, and the domain memo's convention.
#:
#: **Not a cost worth measuring.** 2,000 resamples over a few hundred rows is milliseconds --
#: the expensive thing in this layer is the run that produced the predictions, not the interval
#: around them. It is a module constant rather than a ``pipeline.yaml`` setting because it is a
#: statistical convention rather than a threshold this project tuned: nothing about the model
#: changes if it moves, only the Monte-Carlo noise on the third decimal of an interval bound.
RESAMPLES = 2000

#: The interval's coverage. 95 %, the convention for a confidence interval on a metric.
#:
#: **Not ``conformal.confidence_level``**, which is 0.80 and is a *prediction* band around a
#: single alloy's capacity. The two are different objects that would both be called "the
#: interval" in conversation, and pointing this one at that setting would silently retitle a
#: thesis table.
CONFIDENCE = 0.95

#: How many points a partial-dependence curve is drawn at, on quantiles of the feature's own
#: observed range. Eleven puts a point every decile plus both ends, which is enough for a
#: monotonicity claim and cheap enough that the whole grid costs one prediction pass a point.
PDP_POINTS = 11

#: The three resampling units, as they appear in the ``interval_from`` column.
GROUPS = "out-of-fold canonical groups"
ROWS = "out-of-fold rows"
PER_FOLD = "per-fold scores"

#: What the explainability tables record as the population they were computed on. It is a
#: **split name**, so that the L11 sentinel can check it against
#: :data:`~hydms.surrogate.validation.HELD_OUT_SPLITS` rather than against a string this
#: module also owns.
EXPLAINABILITY = TRAIN

#: The caveat that rides on every interval row. A column, not prose.
#:
#: Card #29 settled this deliberately: prose is what a session drops -- the session that opened
#: the card dropped the word "probe" off a number in three places on the same day. A reader who
#: quotes a bound out of this table cannot quote it without this sentence.
INTERVAL_CAVEAT = (
    "too narrow: the out-of-fold predictions come from five models with overlapping training "
    "sets, so K-fold cross-validation has no unbiased variance estimator (Bengio & Grandvalet "
    "2004); this prices the sampling of materials, not of folds"
)

#: What ``python -m hydms.surrogate.train`` leaves behind that this module reads.
SOURCE_TABLES = ("model-out-of-fold", "model-per-fold", "model-run")

#: What a run is called when nothing on disk says. **Not "full"**: a probe's tables and a real
#: run's tables are the same shape, and defaulting an unlabelled one to the good case is how a
#: cost check becomes a thesis number.
UNKNOWN_RUN = "unknown — no model-run.csv beside these tables"

#: What this module writes, one file per question.
TABLES = ("evaluation-metrics", "evaluation-subgroups")

#: The generated write-up, beside the tables it is generated from.
PUBLISHED = "evaluation.md"


# --------------------------------------------------------------------------------------
# The interval
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Interval:
    """One metric, its point estimate, and the bootstrap interval around it.

    Attributes:
        point: The statistic on the full sample. **Not** the mean of the replicates: the
            bootstrap estimates the *spread* of the statistic, and reporting its resampled
            mean instead would publish a number nobody computed on the data.
        low: The lower percentile bound.
        high: The upper percentile bound.
        resamples: How many replicates the bounds came from.
        units: How many independent units were resampled -- groups, rows, or folds.
        rows: How many rows the point estimate was computed on.
        rows_min: The smallest the resampled subgroup ever got.
        rows_max: The largest.
    """

    point: float
    low: float
    high: float
    resamples: int
    units: int
    rows: int
    rows_min: int
    rows_max: int


def _percentiles(draws: np.ndarray) -> tuple[float, float]:
    """The two percentile bounds of a replicate distribution, ignoring replicates that failed.

    A replicate can be degenerate: a resample that happens to draw one group repeatedly has no
    variance in its truth, and R2 is then ``nan`` by the definition
    :func:`~hydms.surrogate.model.quantile_metrics_from_arrays` gives it. Dropping those is not
    the same as pretending they did not happen, so the count that survives is what
    :class:`Interval` reports as ``resamples``.
    """
    finite = draws[np.isfinite(draws)]
    if finite.size == 0:
        return float("nan"), float("nan")
    tail = (1.0 - CONFIDENCE) / 2.0
    low, high = np.percentile(finite, [100.0 * tail, 100.0 * (1.0 - tail)])
    return float(low), float(high)


def _replicates(
    keys: Sequence[Any], *, resamples: int, seed: int, by_group: bool
) -> list[np.ndarray]:
    """``resamples`` arrays of positional row indices, drawn with replacement.

    **The unit is the canonical composition, and this is where that is decided.** Grouping the
    positions by ``keys`` first and then drawing groups means a resampled composition arrives
    whole -- every row of it, at every temperature it was measured at. Drawing rows instead
    would let two rows describing one material land in the same replicate independently, which
    is the assumption of independence leak L8 is about.

    ``by_group=False`` gives the row-level draw, computed only so that the comparison between
    the two can be published rather than asserted.
    """
    rng = np.random.default_rng(seed)
    if not by_group:
        count = len(keys)
        return [rng.integers(0, count, size=count) for _ in range(resamples)]

    positions: dict[Any, list[int]] = {}
    for at, key in enumerate(keys):
        positions.setdefault(key, []).append(at)
    blocks = [np.asarray(where, dtype="int64") for where in positions.values()]
    count = len(blocks)
    return [
        np.concatenate([blocks[at] for at in rng.integers(0, count, size=count)])
        for _ in range(resamples)
    ]


def _bootstrap(
    truth: np.ndarray,
    heads: np.ndarray,
    quantiles: Sequence[float],
    draws: Sequence[np.ndarray],
    *,
    units: int,
    within: np.ndarray | None = None,
) -> dict[str, Interval]:
    """Every metric with an interval, from one set of replicate index arrays.

    The replicates are passed in rather than drawn here, because card #29 settled that there
    is **one** resample at the split level and every breakdown is computed from it. A subgroup
    is therefore a *mask* applied to each replicate, not a fresh draw -- which is what keeps a
    group that spans two temperature bins from being split between them.

    ``truth`` and ``heads`` are always the **full** arrays and the draws index into them, so
    that a subgroup's replicates are a filtering of the split-level draw rather than a
    renumbering of it. ``within`` is the subgroup's own mask, used for the point estimate
    only: the point is the statistic on that band's observed rows, while the interval comes
    from the same replicates every other band is computed from.
    """
    sample = truth if within is None else truth[within]
    sample_heads = heads if within is None else heads[within]
    point = quantile_metrics_from_arrays(sample, sample_heads, quantiles)
    names = sorted(point)
    collected = {name: np.empty(len(draws), dtype="float64") for name in names}
    sizes = np.empty(len(draws), dtype="int64")

    for at, index in enumerate(draws):
        sizes[at] = index.size
        if index.size == 0:
            for name in names:
                collected[name][at] = float("nan")
            continue
        replicate = quantile_metrics_from_arrays(truth[index], heads[index], quantiles)
        for name in names:
            collected[name][at] = replicate[name]

    result: dict[str, Interval] = {}
    for name in names:
        low, high = _percentiles(collected[name])
        result[name] = Interval(
            point=point[name],
            low=low,
            high=high,
            resamples=int(np.isfinite(collected[name]).sum()),
            units=units,
            rows=int(sample.size),
            rows_min=int(sizes.min()) if sizes.size else 0,
            rows_max=int(sizes.max()) if sizes.size else 0,
        )
    return result


# --------------------------------------------------------------------------------------
# Reading what the run left behind
# --------------------------------------------------------------------------------------


def read_out_of_fold(source: Path, *, config: Config) -> pd.DataFrame:
    """The row-level predictions a nested run wrote, checked for what a metric needs.

    Args:
        source: The directory ``python -m hydms.surrogate.train`` wrote into.
        config: For the target and temperature column names.

    Returns:
        The table, indexed by the matrix's own row labels.

    Raises:
        EvaluationError: The file is absent, empty, or is missing the truth, a head, or the
            canonical key. Named rather than discovered later: a bootstrap over a frame with
            no key column would silently become the row-level bootstrap this module publishes
            *as the comparison*, and the two would then be the same number under two labels.
    """
    path = source / f"{SOURCE_TABLES[0]}.csv"
    if not path.is_file():
        raise EvaluationError(
            f"{path} does not exist, so there are no out-of-fold predictions to put an "
            f"interval around. It is written by `python -m hydms.surrogate.train`, which is "
            f"the run that produces them; nothing in this module fits a model."
        )
    try:
        table = pd.read_csv(path, index_col=0)
    except (OSError, ValueError) as exc:
        raise EvaluationError(f"{path} could not be read: {exc}") from exc

    if table.empty:
        raise EvaluationError(f"{path} holds no rows. A run that scored nothing wrote it.")

    raw = config.columns.target
    wanted = [raw, model_space_name(raw), CANONICAL_KEY_COLUMN, "model", "fold"]
    missing = [name for name in wanted if name not in table.columns]
    if missing:
        raise EvaluationError(
            f"{path} is missing column(s) {missing}; it holds {sorted(table.columns)}. It is "
            f"written from hydms.surrogate.model.scored_table, and a table missing the "
            f"canonical key cannot be resampled by material."
        )
    return table


def read_run(source: Path) -> str:
    """What kind of run wrote these tables, as a phrase for the ``run`` column.

    ``train.py`` writes ``model-run.csv`` beside its numbers because its ``PROBE:`` line goes
    to a terminal somebody closes, and card #37 reads the files six weeks later. A reduced run
    and a real one produce the same seven tables with the same columns; the only thing that
    separates them is written down here, and an *absent* record is reported as unknown rather
    than assumed to be the good case.
    """
    path = source / f"{SOURCE_TABLES[2]}.csv"
    if not path.is_file():
        return UNKNOWN_RUN
    try:
        record = pd.read_csv(path)
    except (OSError, ValueError):
        return UNKNOWN_RUN
    if record.empty:
        return UNKNOWN_RUN

    row = record.iloc[0]
    if not bool(row.get("probe", False)):
        return f"full — {row.get('optuna_trials')} trial(s), screening on"
    detail = f"{row.get('optuna_trials')} of {row.get('configured_optuna_trials')} trial(s)"
    if not bool(row.get("screening", True)):
        detail += ", screening off"
    return f"PROBE ({detail}) — a cost check, not a result"


def _heads(table: pd.DataFrame, quantiles: Sequence[float], *, prefix: str) -> np.ndarray:
    """The head columns of one scale, in quantile order, as a float array."""
    names = [f"{prefix}{name}" for name in column_names(quantiles)]
    missing = [name for name in names if name not in table.columns]
    if missing:
        raise EvaluationError(
            f"the predictions are missing head column(s) {missing}. Position is the only "
            f"thing identifying a quantile in CatBoost's output, so a missing head cannot be "
            f"inferred from the ones that are there."
        )
    return table.loc[:, names].to_numpy(dtype="float64")


def _scales(
    table: pd.DataFrame, *, config: Config, quantiles: Sequence[float]
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """The truth and the heads in both spaces, neither derived from the other.

    Card #11 measured that ``expm1(log1p(y))`` returns ``y`` exactly on only 794 of 1,279 rows,
    so a log-scale metric computed by re-transforming the weight-percent columns would be a
    metric about a round trip. Both spaces are carried in the table by
    :func:`~hydms.surrogate.model.scored_table` for exactly this reason.
    """
    raw = config.columns.target
    return {
        "wt_pct": (
            table[raw].to_numpy(dtype="float64"),
            _heads(table, quantiles, prefix=""),
        ),
        "log": (
            table[model_space_name(raw)].to_numpy(dtype="float64"),
            _heads(table, quantiles, prefix="log_"),
        ),
    }


# --------------------------------------------------------------------------------------
# The tables
# --------------------------------------------------------------------------------------


def _row(
    interval: Interval,
    *,
    metric: str,
    scale: str,
    interval_from: str,
    subgroup: str,
    value: str,
    features: Sequence[str],
    reading: str,
    run: str,
) -> dict[str, object]:
    """One row of an emitted table. Every column that names a claim is filled here.

    ``feature_set`` and ``reading`` are on **every** row rather than in a header, because a row
    is what gets quoted: card #37 lifts a number out of this table into a sentence, and a
    qualifier that lives one row up does not travel with it.
    """
    return {
        "reading": reading,
        "run": run,
        "scale": scale,
        "subgroup": subgroup,
        "subgroup_value": value,
        "metric": metric,
        "point": interval.point,
        "ci_low": interval.low,
        "ci_high": interval.high,
        "confidence": CONFIDENCE,
        "interval_from": interval_from,
        "resamples": interval.resamples,
        "units": interval.units,
        "rows": interval.rows,
        "rows_min": interval.rows_min,
        "rows_max": interval.rows_max,
        "feature_set": "hydms.descriptors.contract.SELECTED",
        "feature_count": len(features),
        "selection_refitted_per_fold": False,
        "interval_caveat": INTERVAL_CAVEAT,
    }


def metrics_table(
    table: pd.DataFrame,
    *,
    config: Config,
    quantiles: Sequence[float],
    seed: int,
    resamples: int = RESAMPLES,
    features: Sequence[str] = SELECTED.names,
    reading: str = "out-of-fold",
    run: str = UNKNOWN_RUN,
) -> pd.DataFrame:
    """R2, RMSE, MAE and the quantile metrics on both scales, each with two intervals.

    Two intervals per metric, from the same replicates: one resampling **canonical groups**,
    which is the principled unit, and one resampling **rows**, which is the unit the objection
    is against. Both are published because the group correction is worth only 13 % of the
    independent units on this data, and a choice defended by principle should show the
    magnitude it is not being defended by.

    Args:
        table: :func:`read_out_of_fold`'s frame, or one fold's slice of it.
        config: For the column names.
        quantiles: The alphas the heads were fitted at, ascending.
        seed: ``pipeline.yaml``'s. The same seed gives the same interval, which is AC-1's
            question asked of this module.
        resamples: Defaults to :data:`RESAMPLES`.
        features: The set the numbers belong to, named on every row.
        reading: ``"out-of-fold"`` or ``"artifact"`` -- which claim these rows are.

    Returns:
        One row per (scale, metric, resampling unit).
    """
    keys = table[CANONICAL_KEY_COLUMN].tolist()
    scales = _scales(table, config=config, quantiles=quantiles)
    rows: list[dict[str, object]] = []

    for unit, by_group in ((GROUPS, True), (ROWS, False)):
        draws = _replicates(keys, resamples=resamples, seed=seed, by_group=by_group)
        units = len(set(keys)) if by_group else len(keys)
        for scale, (truth, heads) in scales.items():
            for metric, interval in _bootstrap(
                truth, heads, quantiles, draws, units=units
            ).items():
                rows.append(
                    _row(
                        interval,
                        metric=metric,
                        scale=scale,
                        interval_from=unit,
                        subgroup="all",
                        value="all",
                        features=features,
                        reading=reading,
                        run=run,
                    )
                )
    return pd.DataFrame.from_records(rows)


def subgroup_table(
    table: pd.DataFrame,
    *,
    config: Config,
    quantiles: Sequence[float],
    seed: int,
    resamples: int = RESAMPLES,
    features: Sequence[str] = SELECTED.names,
    reading: str = "out-of-fold",
    run: str = UNKNOWN_RUN,
) -> pd.DataFrame:
    """The same metrics per outer fold and per temperature band, from one split-level resample.

    **Every subgroup is a mask on the split-level resample**, never a fresh draw inside the
    band. 83 of the 780 training groups span more than one temperature -- up to six distinct
    values -- so a resample taken *inside* a temperature band would cut those groups in half
    and break the canonical seam locally, in exactly the bins where the data is thinnest. The
    price of doing it correctly is that a subgroup's *n* varies between replicates, so every
    row carries the smallest and largest it took: a band that is thin in most replicates shows
    it.

    **"Per split" means per outer fold here, and that is a substitution worth naming.** Card
    #29 asks for metrics "per split and per temperature subgroup". The out-of-fold reading has
    only *one* split in it -- every row of it is a training row, because that is what an
    out-of-fold prediction is -- so the partition available to break it down by is the outer
    fold that held each row out. The ``val``-and-``test`` breakdown the phrase also suggests is
    a property of the **artifact** reading, and it arrives with card #34; it is not silently
    absent here, it is a different claim about a different object.

    The draw is the *same* draw :func:`metrics_table` uses, and it is shared by determinism
    rather than by passing an object: :func:`_replicates` is a pure function of the keys, the
    count and the seed, so both functions given the same table and seed see the same
    replicates. That is the property AC-1 asks of everything in this project, and
    ``test_the_split_level_resample_is_shared_with_the_headline_table`` is what pins it here.

    The temperature bands are quantile bins of the out-of-fold rows' own temperatures, as many
    as ``split.temperature_bins`` -- the same count the split stratification uses, so a reader
    comparing the two is comparing like with like. They are not the split's bins: those were
    cut on the whole dataset and these describe the rows that were actually scored.
    """
    keys = table[CANONICAL_KEY_COLUMN].tolist()
    scales = _scales(table, config=config, quantiles=quantiles)
    draws = _replicates(keys, resamples=resamples, seed=seed, by_group=True)
    units = len(set(keys))

    memberships: list[tuple[str, str, np.ndarray]] = []
    for fold in sorted(table["fold"].astype(str).unique()):
        memberships.append(("fold", fold, (table["fold"].astype(str) == fold).to_numpy()))

    temperature = config.columns.temperature
    if temperature in table.columns:
        bands = pd.qcut(
            table[temperature], config.split.temperature_bins, duplicates="drop"
        )
        for band in bands.cat.categories:
            memberships.append(
                ("temperature", str(band), (bands == band).to_numpy())
            )

    rows: list[dict[str, object]] = []
    for subgroup, value, mask in memberships:
        # The mask is applied to each replicate, so a group drawn twice contributes twice to
        # every band it spans -- which is the point of drawing it whole.
        selected = [index[mask[index]] for index in draws]
        for scale, (truth, heads) in scales.items():
            for metric, interval in _bootstrap(
                truth, heads, quantiles, selected, units=units, within=mask
            ).items():
                rows.append(
                    _row(
                        interval,
                        metric=metric,
                        scale=scale,
                        interval_from=GROUPS,
                        subgroup=subgroup,
                        value=value,
                        features=features,
                        reading=reading,
                        run=run,
                    )
                )
    return pd.DataFrame.from_records(rows)


def per_fold_intervals(
    per_fold: pd.DataFrame,
    *,
    seed: int,
    resamples: int = RESAMPLES,
    features: Sequence[str] = SELECTED.names,
    reading: str = "out-of-fold",
    run: str = UNKNOWN_RUN,
) -> pd.DataFrame:
    """The second, cruder interval: a bootstrap over the five fold scores themselves.

    It costs nothing -- ``Evaluation.per_fold`` already exists -- and it prices a different
    thing from the row bootstrap: fold-to-fold spread rather than the sampling of materials.
    The two will disagree, and card #29's judgement is that two intervals that disagree are
    more honest than one that looks authoritative.

    **What it is confounded with is stated rather than hidden.** ``rows_fitted`` is in this
    table because card #24 measured screening removing between 15 and 144 of a fold's ~710
    training rows -- 571 against 704 in practice -- so one fold's model saw 23 % less data than
    another's before it predicted anything. Part of the spread this interval prices is training
    size and not the model, which is exactly why it is the *second* reading and not the first.
    """
    numeric = [
        name
        for name in per_fold.columns
        if name not in ("model", "fold") and pd.api.types.is_numeric_dtype(per_fold[name])
    ]
    rng = np.random.default_rng(seed)
    count = len(per_fold)
    rows: list[dict[str, object]] = []
    for metric in sorted(numeric):
        values = per_fold[metric].to_numpy(dtype="float64")
        draws = np.asarray(
            [values[rng.integers(0, count, size=count)].mean() for _ in range(resamples)]
        )
        low, high = _percentiles(draws)
        rows.append(
            _row(
                Interval(
                    point=float(values.mean()),
                    low=low,
                    high=high,
                    resamples=int(np.isfinite(draws).sum()),
                    units=count,
                    rows=count,
                    rows_min=count,
                    rows_max=count,
                ),
                metric=metric,
                scale="wt_pct",
                interval_from=PER_FOLD,
                subgroup="all",
                value="all",
                features=features,
                reading=reading,
                run=run,
            )
        )
    return pd.DataFrame.from_records(rows)


# --------------------------------------------------------------------------------------
# Explainability -- leak L11
# --------------------------------------------------------------------------------------


def _refuse_held_out(computed_on: str) -> None:
    """The check that makes L11 unwritable rather than merely tested.

    ``benchmark_model_selection.py:1375,1383,1394`` computed PDP and SHAP on ``X_test`` and
    published the result as REPORT section 6.1. Here the population has to be named to be
    explained, and a held-out name is refused at the door --
    :data:`~hydms.surrogate.validation.HELD_OUT_SPLITS` is the one definition of what that
    means, asserted against rather than restated.
    """
    if computed_on in HELD_OUT_SPLITS:
        raise EvaluationError(
            f"explainability was asked for on {computed_on!r}, which is a held-out split "
            f"({', '.join(HELD_OUT_SPLITS)}). That is leak L11: SHAP and a partial-dependence "
            f"curve computed on the rows a model is scored on describe the model's fit to its "
            f"own report card. Run them on {TRAIN!r}."
        )


def _asserted(record: pd.DataFrame, *, where: str) -> pd.DataFrame:
    """The record, having been checked by the detector the L11 sentinel points at.

    Two guards, and they are not redundant. :func:`_refuse_held_out` runs at the door, before
    a single SHAP value is computed, and raises :class:`EvaluationError` -- the caller made a
    bad call. This runs on what came *out*, and raises
    :class:`~hydms.qa.detectors.LeakDetected` -- the record itself is the archival defect. The
    distinction is the one :mod:`hydms.qa.detectors` states in its own docstring, and it is
    what lets the L11 sentinel assert against the shipped function rather than against a
    miniature of it.
    """
    assert_explanation_is_not_held_out(
        record, held_out=HELD_OUT_SPLITS, where=where
    )
    return record


def shap_table(
    model: QuantileModel,
    frame: pd.DataFrame,
    *,
    computed_on: str = EXPLAINABILITY,
) -> pd.DataFrame:
    """Mean absolute and mean signed SHAP per feature per head, on the rows named.

    **CatBoost's own TreeSHAP, not the ``shap`` package.** Measured 2026-09-05: the booster
    answers ``get_feature_importance(type="ShapValues")`` for a ``MultiQuantile`` loss and
    returns an ``(n, heads, features + 1)`` array -- one explanation per head, with the base
    value last -- in 0.02 s on a 200-tree fit over 708 rows. It is exact rather than sampled,
    it needs no extra dependency, and it costs a fraction of what card #29 budgeted for this
    step. That premise of the card was measured and was wrong in the cheap direction.

    Args:
        model: The deployed fit.
        frame: The rows to explain, carrying the fitted feature columns.
        computed_on: The split those rows are. Refused if it is a held-out one.

    Returns:
        One row per (head, feature): ``mean_abs_shap``, ``mean_shap``, and ``computed_on``.

    Raises:
        EvaluationError: ``computed_on`` is a held-out split, or CatBoost declined the request.
    """
    _refuse_held_out(computed_on)
    from catboost import Pool

    features = list(model.feature_names)
    try:
        values = np.asarray(
            model.booster.get_feature_importance(
                Pool(frame.loc[:, features]), type="ShapValues"
            ),
            dtype="float64",
        )
    except Exception as exc:  # CatBoost raises its own error type, from its own module
        raise EvaluationError(
            f"CatBoost declined to compute SHAP values for this model: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    heads = column_names(model.quantiles)
    # (rows, heads, features + 1): the trailing column is the base value, which is not a
    # feature and must not become one in the table.
    if values.ndim != 3 or values.shape[1] != len(heads) or values.shape[2] != len(features) + 1:
        raise EvaluationError(
            f"CatBoost returned SHAP values shaped {values.shape} where "
            f"({len(frame)}, {len(heads)}, {len(features) + 1}) was expected. The last axis is "
            f"the features plus a base value, and the middle one is the quantile heads in the "
            f"order the loss names them; a different shape means a different contract."
        )

    rows: list[dict[str, object]] = []
    for at, head in enumerate(heads):
        block = values[:, at, : len(features)]
        for column, name in enumerate(features):
            rows.append(
                {
                    "head": head,
                    "feature": name,
                    "mean_abs_shap": float(np.mean(np.abs(block[:, column]))),
                    "mean_shap": float(np.mean(block[:, column])),
                    "computed_on": computed_on,
                    "rows": int(len(frame)),
                }
            )
    return _asserted(pd.DataFrame.from_records(rows), where="the SHAP record")


def pdp_table(
    model: QuantileModel,
    frame: pd.DataFrame,
    *,
    computed_on: str = EXPLAINABILITY,
    points: int = PDP_POINTS,
) -> pd.DataFrame:
    """Partial dependence of every head on every feature, over the rows named.

    Computed directly rather than through ``sklearn.inspection.partial_dependence``: this model
    predicts three columns at once, and scikit-learn's estimator checks are written for one.
    The definition is short enough to own -- hold every other column, set this one to a grid
    value, average the predictions -- and owning it means the grid is on the feature's *own
    observed quantiles*, so no curve is drawn over a region the data does not cover. That is
    a real hazard in composition space, where features are strongly correlated and a Cartesian
    grid walks straight out of the applicability domain.

    Args:
        model: The deployed fit.
        frame: The rows the curve is averaged over.
        computed_on: The split those rows are. Refused if it is a held-out one.
        points: Grid points per feature.

    Returns:
        One row per (feature, grid point, head): the feature's value and the averaged
        prediction, with ``computed_on``.
    """
    _refuse_held_out(computed_on)
    features = list(model.feature_names)
    matrix = frame.loc[:, features]
    heads = column_names(model.quantiles)
    quantile_grid = np.linspace(0.0, 1.0, points)

    rows: list[dict[str, object]] = []
    for name in features:
        observed = matrix[name].to_numpy(dtype="float64")
        grid = np.unique(np.quantile(observed, quantile_grid))
        for value in grid:
            probe = matrix.copy()
            probe[name] = value
            averaged = model.predict(probe).mean(axis=0)
            for head in heads:
                rows.append(
                    {
                        "feature": name,
                        "value": float(value),
                        "head": head,
                        "prediction": float(averaged[head]),
                        "computed_on": computed_on,
                        "rows": int(len(frame)),
                    }
                )
    return _asserted(pd.DataFrame.from_records(rows), where="the partial-dependence record")


# --------------------------------------------------------------------------------------
# The write-up
# --------------------------------------------------------------------------------------


def _format(value: object) -> str:
    if isinstance(value, float):
        return "nan" if not np.isfinite(value) else f"{value:.4f}"
    return str(value)


def _headline(metrics: pd.DataFrame, *, metric: str, scale: str, unit: str) -> str:
    match = metrics[
        (metrics["metric"] == metric)
        & (metrics["scale"] == scale)
        & (metrics["interval_from"] == unit)
    ]
    if match.empty:
        return "not computed"
    row = match.iloc[0]
    return (
        f"{_format(row['point'])} "
        f"[{_format(row['ci_low'])}, {_format(row['ci_high'])}]"
    )


def to_markdown(
    metrics: pd.DataFrame,
    subgroups: pd.DataFrame,
    *,
    sha: str | None,
    dirty: bool | None,
    dated: datetime,
) -> str:
    """The published write-up, generated from the tables and from nothing else.

    Card #25's pattern: the slow run writes CSVs, a cheap flag rebuilds the prose from them,
    and a test asserts that the committed document is what the code produces. A document
    written by hand beside its tables is a document that stops agreeing with them, silently,
    on the day somebody edits one of the two.

    The git SHA is stamped in because a table produced from an uncommitted tree cannot be tied
    to the code that made it, and card #34's manifest records the same thing for the artifact
    cut from the same run.
    """
    lines: list[str] = []
    lines.append("# Model evaluation — point estimates with intervals")
    lines.append("")
    lines.append(
        "Generated by `python -m hydms.surrogate.evaluate --emit`. Do not edit: a test "
        "asserts this file is what the code produces from the committed tables."
    )
    lines.append("")
    run = str(metrics["run"].iloc[0]) if "run" in metrics.columns else UNKNOWN_RUN
    if not run.startswith("full"):
        # First, above everything, and in the loudest thing Markdown has. A reduced run and a
        # real one write the same eight tables with the same columns; `train.py` says which on
        # stdout, and stdout is not what card #37 reads six weeks later.
        lines.append(f"> ## ⚠ These numbers are **not a result**: {run}")
        lines.append(">")
        lines.append(
            "> A reduced run produces tables of exactly this shape. Do not quote a bound from "
            "this document in Chapter 1 until it is regenerated from a full run."
        )
        lines.append("")
    stamp = sha[:12] if sha else "unknown"
    state = "" if dirty is None else (" (working tree dirty)" if dirty else " (clean tree)")
    lines.append(f"- Run: {run}")
    lines.append(f"- Code: `{stamp}`{state}")
    lines.append(f"- Generated: {dated:%Y-%m-%d}")
    lines.append(f"- Resamples: {int(metrics['resamples'].max())} at {CONFIDENCE:.0%} confidence")
    lines.append(
        f"- Feature set: `{metrics['feature_set'].iloc[0]}` "
        f"({int(metrics['feature_count'].iloc[0])} features), selection not refitted per fold"
    )
    lines.append("")
    lines.append("## What these numbers are a claim about")
    lines.append("")
    lines.append(
        "Every row of the tables below is an **out-of-fold** reading: each training row was "
        "predicted by the outer fold that held it out, so the score is honest, but it comes "
        "from five different models. It is a claim about the *procedure*, not about the model "
        "that ships. The artifact reading — one promoted model on rows it has never seen — is "
        "a claim about *a model*, and it arrives with card #34."
    )
    lines.append("")
    lines.append(f"> **The interval is {INTERVAL_CAVEAT}.**")
    lines.append("")
    lines.append(
        "A second, cruder interval over the five fold scores rides beside it in the same "
        "table, under `interval_from = "
        f"{PER_FOLD}`. It prices fold-to-fold spread — part of which is training size rather "
        "than the model, because screening removes between 15 and 144 of a fold's ~710 rows. "
        "The two intervals will disagree. That is the honest state of the estimate."
    )
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append("| Metric | Weight percent | Model space (log1p) |")
    lines.append("|---|---|---|")
    for metric in ("r2", "rmse", "mae"):
        lines.append(
            f"| {metric.upper()} | {_headline(metrics, metric=metric, scale='wt_pct', unit=GROUPS)} "
            f"| {_headline(metrics, metric=metric, scale='log', unit=GROUPS)} |"
        )
    lines.append("")
    lines.append(
        "Intervals resample **canonical compositions**, not rows: `group_keys` is the one "
        "definition of the same material in this project, and a row-level resample here would "
        "be a fourth one. Measured on the training split, that is 780 groups over 893 rows "
        "with 692 singletons — a 13 % reduction in independent units, which is a real "
        "correction and a small one. Both readings are in the table so the choice can be "
        "checked rather than believed."
    )
    lines.append("")
    lines.append("## Every metric, both scales, both resampling units")
    lines.append("")
    lines.append(_table(metrics))
    lines.append("")
    lines.append("## Per outer fold and per temperature band")
    lines.append("")
    lines.append(
        "One resample at the split level; every band below is a mask on it, because 83 of the "
        "780 groups span more than one temperature. `rows_min` and `rows_max` are the smallest "
        "and largest that band ever took across replicates — a band that is thin in most of "
        "them is visible here rather than implied."
    )
    lines.append("")
    lines.append(_table(subgroups[subgroups["metric"].isin(("r2", "rmse", "mae"))]))
    lines.append("")
    return "\n".join(lines)


def _table(frame: pd.DataFrame) -> str:
    """A Markdown table of the columns a reader needs, from the frame the CSV carries.

    ``run`` and ``interval_caveat`` are deliberately not among them: both are the same long
    sentence on every row, and both are already stated once, loudly, above -- the run as the
    banner at the top of the document, the caveat as the blockquote under it. They stay
    *columns* in the CSV, which is what gets quoted out of context; here they would be noise
    that pushes the numbers off the side of the page.
    """
    columns = [
        "reading",
        "scale",
        "subgroup_value",
        "metric",
        "point",
        "ci_low",
        "ci_high",
        "interval_from",
        "units",
        "rows",
        "rows_min",
        "rows_max",
    ]
    shown = [name for name in columns if name in frame.columns]
    lines = ["| " + " | ".join(shown) + " |", "|" + "---|" * len(shown)]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(_format(row[name]) for name in shown) + " |")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# The command
# --------------------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.surrogate.evaluate",
        description=(
            "Metrics with bootstrap confidence intervals over the out-of-fold predictions a "
            "nested run left behind. Fits nothing."
        ),
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="the directory the training run wrote into; defaults to the configured reports path",
    )
    parser.add_argument(
        "--resamples",
        type=int,
        default=RESAMPLES,
        help=f"bootstrap resamples per interval (default {RESAMPLES})",
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help="also rebuild the published write-up from the tables — the cheap half",
    )
    parser.add_argument(
        "--artifact",
        default=None,
        help="score a promoted artifact version instead: the second reading, a claim about a "
        "model rather than about the procedure (card #34)",
    )
    return parser


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """Read the tables, put an interval on every number, and report. Returns the exit code."""
    stream = out if out is not None else sys.stdout
    args = _parser().parse_args(argv)

    try:
        cfg = load(args.config)
    except (ConfigError, OSError) as error:
        print(f"could not read the configuration: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    if args.artifact is not None:
        # Named and refused rather than attempted. `load_surrogate()` would raise
        # `PredictionError: nothing is promoted` from three frames down, and card #29's
        # runnable check is this flag, so the refusal has to say what is actually missing.
        print(
            f"--artifact {args.artifact} is the *second* reading and it needs a promoted "
            f"version. `artifacts/` holds no version directory and no current.json until card "
            f"#34 cuts one, and #34 is blocked on this card's run. The primary number needs no "
            f"artifact: run this command without --artifact and it reads the out-of-fold "
            f"predictions instead.",
            file=sys.stderr,
        )
        return EXIT_BAD_INVOCATION

    source = args.report if args.report is not None else (cfg.paths.reports / "model")
    try:
        table = read_out_of_fold(source, config=cfg)
    except EvaluationError as error:
        print(f"{error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    quantiles = tuple(cfg.model.quantiles)
    print(
        f"{len(table)} out-of-fold prediction(s) in "
        f"{table[CANONICAL_KEY_COLUMN].nunique()} canonical group(s), "
        f"{table['fold'].nunique()} fold(s)",
        file=stream,
    )

    run = read_run(source)
    print(f"run: {run}", file=stream)
    metrics = metrics_table(
        table,
        config=cfg,
        quantiles=quantiles,
        seed=cfg.seed,
        resamples=args.resamples,
        run=run,
    )
    subgroups = subgroup_table(
        table,
        config=cfg,
        quantiles=quantiles,
        seed=cfg.seed,
        resamples=args.resamples,
        run=run,
    )

    per_fold_path = source / f"{SOURCE_TABLES[1]}.csv"
    if per_fold_path.is_file():
        try:
            per_fold = pd.read_csv(per_fold_path)
        except (OSError, ValueError) as error:
            print(f"could not read {per_fold_path}: {error}", file=sys.stderr)
            return EXIT_BAD_INVOCATION
        metrics = pd.concat(
            [
                metrics,
                per_fold_intervals(
                    per_fold, seed=cfg.seed, resamples=args.resamples, run=run
                ),
            ],
            ignore_index=True,
        )
    else:
        print(
            f"note: {per_fold_path} is absent, so the second per-fold interval is not in this "
            f"table. It is written by the same run as the predictions.",
            file=stream,
        )

    for metric in ("r2", "rmse", "mae"):
        print(
            f"  {metric} (wt%): {_headline(metrics, metric=metric, scale='wt_pct', unit=GROUPS)}"
            f"  |  rows: {_headline(metrics, metric=metric, scale='wt_pct', unit=ROWS)}"
            f"  |  folds: {_headline(metrics, metric=metric, scale='wt_pct', unit=PER_FOLD)}",
            file=stream,
        )

    try:
        source.mkdir(parents=True, exist_ok=True)
        for name, frame in zip(TABLES, (metrics, subgroups), strict=True):
            path = source / f"{name}.csv"
            frame.to_csv(path, index=False)
            print(f"wrote {path}", file=stream)
        if args.emit:
            git = describe_git(cfg.root)
            document = source / PUBLISHED
            document.write_text(
                to_markdown(
                    metrics,
                    subgroups,
                    sha=git.sha,
                    dirty=git.dirty,
                    dated=datetime.now(timezone.utc),
                ),
                encoding="utf-8",
            )
            print(f"wrote {document}", file=stream)
    except OSError as error:
        print(f"could not write the tables: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
