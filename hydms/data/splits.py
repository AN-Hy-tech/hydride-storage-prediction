"""L1 -- train, validation and test, grouped by material rather than by spelling.

``split_data.py`` does something better than most published hydride ML: it splits on unique
*formulae*, stratified on binned temperature and target, and then asserts at ``:126-129`` that
no formula spans two splits. That assertion is green. It is also not the property anyone
wants.

Measured on the real data, through the faithful reproduction in
``tests/data/test_canonical.py``: 1279 rows carry 1149 distinct formula strings and only
**1115 distinct compositions**, and under the published seed **16 of those compositions -- 35
rows -- sit on both sides of a line**. ``Ce1Mg12`` is in test and ``Mg12Ce1`` is in
validation: 6.0 wt% at 598 K, written two ways. ``Pr1Co5`` differs from ``Pr1Co5 `` by a
trailing space. Every selected feature is a composition statistic or the temperature (PRD
section 2.3), so those rows carry byte-identical feature vectors up to temperature, and a
model trained on one and scored on the other is scored on its training data. That is leak
**L8**.

This module is the same protocol with one thing changed: the unit is
:func:`hydms.data.canonical.group_keys`, **called rather than re-derived**, which is also the
key #88's cross-validation folds group on and the key ``Alloy_class`` is joined on (#12). One
function, so "the same material" cannot come to mean three different things in three modules.

**Everything else is ported unchanged**, because this card is not a redesign of the
stratification:

  1. mean temperature and mean **model-space** target per group;
  2. five quantile bins of each, combined into one stratification key;
  3. strata below ``min_stratum_size`` merged into the nearest sufficiently large one by
     Euclidean distance in ``(T_bin, Wt%_bin)`` space;
  4. ``StratifiedShuffleSplit`` for train against the rest, then again to cut the rest into
     validation and test.

The mean is taken **after** the log transform, as ``split_data.py`` did -- it read the
already-transformed ``target`` column. That is not a free choice: quantile binning is
invariant to a monotone transform, but a *mean over a group* is not, so a group with two rows
lands in a different bin depending on which space the averaging happens in. It happens in
model space, through :func:`hydms.data.target.to_model_space`.

**The row counts move, and that is the fix working.** Grouping on the composition rather than
the string means the split has 1115 units instead of 1149, so it cannot reproduce 896/136/247
exactly -- and an exact match would mean the key had not changed anything. Measured, under
seed 42::

    published (raw formula string)   train 896   val 136   test 247
    this module (canonical key)      train 893   val 131   test 255
                                           780        111        224   compositions

The fractions still land where ``pipeline.yaml`` asks: 0.698 / 0.102 / 0.199 against
0.70 / 0.10 / 0.20. What the module guarantees, and asserts before returning, is that no
canonical composition appears in two splits. The archival assertion is left able to pass;
this one cannot -- and the raw-string check stays green here too, because grouping on the
composition implies grouping on the string and never the reverse.

**The four repeats that only exist after canonicalisation.** Distinct
``(composition, temperature)`` pairs fall from 1272 to 1268 (#87), so four pairs are two
measurements of one material at one temperature, made distinct only by spelling. Grouping
places both rows on the same side for free. Nothing here deduplicates them, and anything added
later that does must not drop one of the two silently -- they are independent measurements.

Card #13.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Sequence
from typing import Any

import pandas as pd

from hydms.config import Split as SplitSettings
from hydms.config import load as load_config
from hydms.data.canonical import group_keys
from hydms.data.target import to_model_space
from hydms.qa import assert_disjoint_groups

__all__ = ["SPLIT_NAMES", "SplitError", "assign_splits", "split_summary", "stratify"]

#: The three splits, in the order they are cut. ``val`` is the one CatBoost's ``eval_set``
#: must point at (leak L1): the test split never chooses a stopping iteration.
SPLIT_NAMES: tuple[str, ...] = ("train", "val", "test")

_TEMPERATURE_BIN = "T_bin"
_TARGET_BIN = "Wt%_bin"
_STRATUM = "stratum"
_TARGET = "target"


class SplitError(ValueError):
    """The split protocol cannot run, or its result fails its own guarantee.

    A ``ValueError``, like :class:`~hydms.data.load.SchemaViolation` and its siblings across
    the data layer: a guard refusing. The *leak* detector for the same defect is
    :func:`hydms.qa.detectors.assert_disjoint_groups`, which raises ``LeakDetected`` and is
    what gate HG-1 reads.
    """


def _sklearn() -> tuple[Any, Any]:
    """Import scikit-learn lazily, with a message that says what it is needed for.

    Deferred so that ``import hydms.data.splits`` -- and therefore ``hydms.gates list`` and
    the board scripts -- stays answerable on an interpreter with no scientific stack.
    """
    try:
        from sklearn.model_selection import StratifiedShuffleSplit
        from sklearn.preprocessing import KBinsDiscretizer
    except ImportError as exc:  # pragma: no cover -- exercised only on a bare interpreter
        raise SplitError(
            "the split protocol is scikit-learn's -- KBinsDiscretizer for the quantile bins "
            "and StratifiedShuffleSplit for both cuts -- and it is not importable here. It is "
            "a core dependency; see docs/ENVIRONMENT.md."
        ) from exc
    return KBinsDiscretizer, StratifiedShuffleSplit


def _group_statistics(
    frame: pd.DataFrame,
    keys: pd.Series,
    *,
    temperature_column: str,
    target_column: str,
) -> pd.DataFrame:
    """One row per canonical composition: its mean temperature and mean model-space target.

    ``groupby`` sorts, so the row order is a function of the keys alone -- which is what makes
    the shuffle below reproducible from the seed rather than from the order rows happened to
    arrive in.
    """
    for column in (temperature_column, target_column):
        if column not in frame.columns:
            raise SplitError(
                f"the frame has no column {column!r} to stratify on; it holds "
                f"{', '.join(map(repr, frame.columns))}"
            )
    stats = pd.DataFrame(
        {
            "key": keys,
            temperature_column: frame[temperature_column],
            _TARGET: to_model_space(frame[target_column]),
        }
    )
    return stats.groupby("key").agg({temperature_column: "mean", _TARGET: "mean"})


def _merge_rare_strata(stratum: pd.Series, minimum: int) -> pd.Series:
    """``split_data.py:88-111``, transcribed: rare strata absorbed by their nearest neighbour.

    Distances are Euclidean in ``(T_bin, Wt%_bin)`` space and are measured against the counts
    as they were *before* any merging, exactly as the archival loop does -- so two rare strata
    never absorb each other, and the result does not depend on the order they are visited.
    """
    counts = stratum.value_counts()
    rare = counts[counts < minimum].index
    merged = stratum.copy()
    for small in rare:
        here = [float(part) for part in str(small).split("_")]
        distances = {
            other: math.hypot(
                here[0] - float(str(other).split("_")[0]),
                here[1] - float(str(other).split("_")[1]),
            )
            for other in counts.index
            if other != small and counts[other] >= minimum
        }
        nearest = min(distances, key=lambda name: distances[name]) if distances else counts.index[0]
        merged[stratum == small] = nearest

    remaining = merged.value_counts()
    if bool((remaining < minimum).any()):
        offenders = remaining[remaining < minimum]
        raise SplitError(
            f"{len(offenders)} stratification key(s) still hold fewer than {minimum} "
            f"composition(s) after merging: {dict(offenders)}. Reduce the bin counts or "
            f"min_stratum_size in pipeline.yaml -- StratifiedShuffleSplit cannot place a "
            f"stratum it cannot divide."
        )
    return merged


def stratify(
    frame: pd.DataFrame,
    *,
    formula_column: str | None = None,
    temperature_column: str | None = None,
    target_column: str | None = None,
    settings: SplitSettings | None = None,
) -> pd.Series:
    """The stratification key of every canonical composition.

    Exposed because it is the half of the protocol that is a *judgement* -- how many bins,
    how small a stratum may be -- and because #88's folds stratify the same way. The split
    itself is :func:`assign_splits`.

    Args:
        frame: A table with a formula, a temperature and a target column.
        formula_column: Defaults to ``columns.formula``.
        temperature_column: Defaults to ``columns.temperature``.
        target_column: Defaults to ``columns.target``, in **weight percent** -- it is
            transformed here.
        settings: Bin counts and the minimum stratum size, defaulting to ``pipeline.yaml``'s.

    Returns:
        A ``Series`` named ``stratum``, indexed by canonical key, holding
        ``"<T_bin>_<Wt%_bin>"`` after rare strata have been merged.

    Raises:
        SplitError: A needed column is missing, or a stratum is still too small to divide.
    """
    config = load_config()
    names = config.columns
    rules = settings if settings is not None else config.split
    temperature = temperature_column if temperature_column is not None else names.temperature
    target = target_column if target_column is not None else names.target

    keys = group_keys(frame, formula_column)
    stats = _group_statistics(
        frame, keys, temperature_column=temperature, target_column=target
    )

    binner_class, _ = _sklearn()
    for column, name, count in (
        (temperature, _TEMPERATURE_BIN, rules.temperature_bins),
        (_TARGET, _TARGET_BIN, rules.target_bins),
    ):
        binner = binner_class(n_bins=count, encode="ordinal", strategy="quantile")
        stats[name] = binner.fit_transform(stats[[column]])

    stratum = stats[_TEMPERATURE_BIN].astype(str) + "_" + stats[_TARGET_BIN].astype(str)
    return _merge_rare_strata(stratum, rules.min_stratum_size).rename(_STRATUM)


def _cut(members: Sequence[Hashable], strata: pd.Series, *, fraction: float, seed: int) -> Any:
    """One ``StratifiedShuffleSplit``, returning the two index arrays.

    ``X`` is only measured for length by scikit-learn, so the group labels are passed
    directly; the permutation is a function of the sample count, the stratum counts and the
    seed, which is what makes the same seed reproduce the same split.
    """
    _, splitter_class = _sklearn()
    splitter = splitter_class(n_splits=1, test_size=fraction, random_state=seed)
    labels = strata.loc[list(members)]
    return next(splitter.split(list(members), labels))


def assign_splits(
    frame: pd.DataFrame,
    *,
    formula_column: str | None = None,
    temperature_column: str | None = None,
    target_column: str | None = None,
    seed: int | None = None,
    settings: SplitSettings | None = None,
) -> pd.Series:
    """Which split each row belongs to: ``"train"``, ``"val"`` or ``"test"``.

    The split is decided over canonical compositions and then *mapped* back onto rows, so
    every row describing one material lands on one side however the file spelled it. The
    disjointness guarantee is checked with
    :func:`hydms.qa.detectors.assert_disjoint_groups` -- the same detector gate HG-1 runs --
    before the result is returned, so a caller cannot receive a leaking split.

    Args:
        frame: A table with a formula, a temperature and a target column, e.g. the output of
            :func:`hydms.data.load.load_hydride_data`.
        formula_column: Defaults to ``columns.formula``.
        temperature_column: Defaults to ``columns.temperature``.
        target_column: Defaults to ``columns.target``, in weight percent.
        seed: Defaults to ``seed`` in ``pipeline.yaml``. Both cuts use it.
        settings: Fractions, bin counts and the minimum stratum size, defaulting to
            ``pipeline.yaml``'s ``split`` section.

    Returns:
        A ``Series`` named ``split``, indexed exactly as ``frame`` is.

    Raises:
        SplitError: A needed column is missing, a stratum cannot be divided, or a row came
            back unassigned.
        LeakDetected: A canonical composition landed in two splits, which is leak L8. It is
            raised rather than returned because there is no useful thing to do with a split
            that leaks.
    """
    config = load_config()
    rules = settings if settings is not None else config.split
    rng_seed = config.seed if seed is None else seed

    keys = group_keys(frame, formula_column)
    strata = stratify(
        frame,
        formula_column=formula_column,
        temperature_column=temperature_column,
        target_column=target_column,
        settings=rules,
    )
    compositions = list(strata.index)

    held_out = rules.test_fraction + rules.val_fraction
    train_at, rest_at = _cut(compositions, strata, fraction=held_out, seed=rng_seed)
    rest = [compositions[position] for position in rest_at]
    val_at, test_at = _cut(
        rest, strata, fraction=rules.test_fraction / held_out, seed=rng_seed
    )

    assignment: dict[Hashable, str] = {compositions[position]: "train" for position in train_at}
    assignment.update({rest[position]: "val" for position in val_at})
    assignment.update({rest[position]: "test" for position in test_at})

    split = keys.map(assignment).rename("split")
    unassigned = split.isna()
    if bool(unassigned.any()):
        raise SplitError(
            f"{int(unassigned.sum())} of {len(frame)} row(s) were left unassigned. Every "
            f"canonical composition is placed exactly once, so this means the key of a row "
            f"is not the key of any group -- the split and the grouping disagree."
        )

    assert_disjoint_groups({name: keys[split == name] for name in SPLIT_NAMES})
    return split


def split_summary(split: pd.Series, keys: Iterable[Hashable]) -> pd.DataFrame:
    """Rows and compositions per split, in ``train``, ``val``, ``test`` order.

    Compositions is the column that matters for anything that groups: a split with many rows
    over few materials is smaller than it looks. Reported together so the difference is
    visible.

    Args:
        split: The output of :func:`assign_splits`.
        keys: The canonical key of every row, in the same order.

    Returns:
        A frame indexed by split name with ``rows``, ``compositions`` and ``fraction``
        (of rows).
    """
    table = pd.DataFrame({"split": list(split), "key": list(keys)})
    total = len(table)
    records = [
        {
            "split": name,
            "rows": int((table["split"] == name).sum()),
            "compositions": int(table.loc[table["split"] == name, "key"].nunique()),
            "fraction": round(float((table["split"] == name).sum()) / total, 4) if total else 0.0,
        }
        for name in SPLIT_NAMES
    ]
    return pd.DataFrame.from_records(records).set_index("split")
