"""L1 -- how featurisation outputs are joined into one table.

``merge_datasets.py:46`` joins three featurisation outputs with ``pd.concat(axis=1)`` after
``reset_index(drop=True)``: positionally, with no join key. If any featuriser drops,
reorders or skips a single row, every subsequent row's features belong to a different
composition and nothing anywhere notices. ``docs/FREEZE.md`` names it the highest-severity
correctness defect in the repository -- every other leak makes the numbers optimistic, this
one makes them describe different materials. It is leak **L9**.

This module is the replacement, and it is one function: :func:`merge_features` attaches
:class:`FeatureBlock` s to a spine by key, or refuses.

**What the spine is, and why it is not the chemistry.** The spine is the measurement table:
one row per (material, temperature, source) observation. Its row *identity* is its index
label, not its formula -- because the formula does not identify a row and neither does the
formula plus the temperature. Measured over ``hydride_data.csv``: 1279 rows carry 1149
distinct formula strings and only 1272 distinct ``(Composition, temperature(K))`` pairs.
Seven pairs appear twice:

    Mg0.95Ni0.05 @ 473 K              5.00 and 5.41 wt%, two citations
    Ti0.5Zr0.5Mn1Cr1 @ 298 K          1.82 and 2.18 wt%, two citations
    Ti0.8Zr0.2Mn0.8Cr1.0Fe0.2 @ 293 K 1.80 and 1.90 wt%, HydPark and Extracted
    Ti0.8Zr0.2Mn1.2Cr0.8 @ 293 K      2.00 and 2.05 wt%, HydPark and Extracted
    Ti1V1Nb1Ta1 @ 298 K               2.02 and 2.04 wt%, two citations
    Ti1V1Zr1Nb1 @ 298 K               2.74 and 2.81 wt%, two citations
    La0.9Ce0.1Ni5 @ 373 K             1.40 twice, one citation -- rows 687 and 694 are
                                      byte-identical across all six columns

Six of those are independent replicates and belong in the data. So card #10's own
``## Done when`` phrasing -- "joins on formula, and temperature where the row is a
measurement" -- names a key that is **not unique on the spine**, and a merge that keyed rows
that way would silently inflate the table: a block built row-wise on ``(formula,
temperature)`` and joined back takes 1279 rows to 1293. Measured, not reasoned about.

**So the direction of the join is fixed.** The spine keeps its rows and its order; a block is
*looked up* from it, one block row per spine row or one block row per many. That is a left
join with two-way coverage asserted, never a concatenation, and never a join that could
change the spine's shape. :class:`FeatureBlock` carries the key it is addressed by:

    ``key=("Composition",)``   one row per composition -- what every descriptor block is,
                               because every selected feature is a composition statistic or
                               the temperature (the enabling fact, PRD section 2.3), so a
                               descriptor block has 1149 rows and the join is one-to-many
    ``key=None``               one row per spine row, addressed by the spine's own index
                               labels -- the shape a per-measurement stage produces

Temperature is therefore never a join key here: it is a spine column that is already beside
every row it belongs to. A block *may* still be keyed on ``("Composition",
"temperature(K)")`` if some future featuriser is temperature-dependent -- the key is a tuple
for exactly that reason -- and the uniqueness check below is what makes that safe.

**What it refuses.** Every one of these is silent in the archival pipeline:

  - a block key that is not unique within the block -- the fan-out that turns 1279 into 1293
  - a spine key with no block row, or a block row no spine key asked for, both listed
  - a null in any key column, on either side, which no join can match
  - a column name arriving twice. ``merge_datasets.py:49`` is
    ``df_merged.loc[:, ~df_merged.columns.duplicated()]``, which keeps the *first* of two
    identically-named columns from different featurisers and discards the second without a
    word. Two featurisers computing ``avg_atomic_mass`` differently is a decision for a
    human, not a silent first-wins.

The key is a parameter rather than a constant because card #87 replaces the raw formula
string with a canonical composition key (leak L8), and when it does, the caller hands that
column here and this module does not change.

Card #10.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd

__all__ = ["FeatureBlock", "MergeError", "merge_features"]

# A failure that names two hundred compositions is a failure nobody reads to the end. The
# total is always reported; the listing is truncated. Same convention as `hydms/data/load.py`
# and `hydms/qa/detectors.py`.
_MAX_NAMED = 8


class MergeError(ValueError):
    """The merge cannot join these frames, and says exactly which rows or columns.

    Every raise from this module names the offenders. ``docs/QA-PROTOCOL.md`` section 4.6:
    an assertion that reads ``assert False`` costs the next person an hour, and a merge
    failure is the case where that hour is spent hunting the one row a featuriser dropped.

    A ``ValueError``, like :class:`~hydms.data.load.SchemaViolation`, and deliberately *not*
    :class:`~hydms.qa.detectors.LeakDetected`: this is the guard refusing, not a detector
    reporting that the guard failed. The L9 sentinel calls
    :func:`~hydms.qa.detectors.assert_merge_is_keyed` on this function from the outside, and
    any refusal at all is what it is looking for.
    """


def _named(items: Iterable[Any]) -> str:
    """Render offenders for a message: sorted, truncated, and counted."""
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


@dataclass(frozen=True)
class FeatureBlock:
    """One featuriser's output, and the key its rows are addressed by.

    Args:
        name: What this block is, for error messages. A merge failure that says "block 1"
            costs the reader a trip back to the call site.
        frame: The features. The key may be held either as columns or as the index -- a
            featuriser naturally returns it as a column and a groupby naturally returns it
            as an index, and forcing one on the caller only moves the reshaping outside
            this module where nothing checks it.
        key: The column name(s) addressing the block, as a tuple. ``None`` means the block
            is addressed by the *spine's own index labels* -- one block row per spine row.

    ``key`` accepts a bare string for convenience and stores a tuple, because ``key=("x")``
    is a missing comma away from being the string ``"x"`` and would otherwise be read as
    three separate key columns named ``'x'``... which is to say, as characters.
    """

    name: str
    frame: pd.DataFrame
    key: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.key is not None:
            normalised = (self.key,) if isinstance(self.key, str) else tuple(self.key)
            if not normalised:
                raise MergeError(
                    f"block {self.name!r} was given an empty key. Pass `key=None` to address "
                    f"it by the spine's row labels, or name the column(s) it is keyed on."
                )
            object.__setattr__(self, "key", normalised)


def _addressed(block: FeatureBlock) -> pd.DataFrame:
    """The block re-shaped so its index *is* its key, ready to be joined against.

    Accepts the key as columns or as index levels, and refuses a half-and-half split rather
    than guessing which half was meant.
    """
    frame = block.frame
    if block.key is None:
        return frame

    wanted = list(block.key)
    in_columns = [name for name in wanted if name in frame.columns]
    if len(in_columns) == len(wanted):
        return frame.set_index(wanted)

    index_names = [name for name in frame.index.names if name is not None]
    if index_names == wanted:
        return frame

    raise MergeError(
        f"block {block.name!r} is declared to be keyed on {_named(wanted)}, but its frame "
        f"holds {len(in_columns)} of those as columns ({_named(in_columns) or 'none'}) and "
        f"its index is named {_named(index_names) or 'nothing'}. The key must be entirely "
        f"columns or exactly the index."
    )


def _spine_keys(spine: pd.DataFrame, block: FeatureBlock) -> pd.Index:
    """The spine values that address ``block`` -- its own row labels, or its key columns."""
    if block.key is None:
        return spine.index

    missing = [name for name in block.key if name not in spine.columns]
    if missing:
        raise MergeError(
            f"block {block.name!r} is keyed on {_named(block.key)}, but the spine has no "
            f"column(s) {_named(missing)}. The key names the spine columns the block is "
            f"looked up by; the spine has {_named(spine.columns)}."
        )
    if len(block.key) == 1:
        return pd.Index(spine[block.key[0]])
    return pd.MultiIndex.from_frame(spine[list(block.key)])


def _null_mask(keys: pd.Index) -> Any:
    """Which key values are null, for a plain index or a compound one.

    ``MultiIndex.isna()`` reads its values as tuples, and a tuple containing a NaN is not
    itself null -- so a compound key has to be asked level by level, which is what
    ``to_frame`` gives cheaply.
    """
    if isinstance(keys, pd.MultiIndex):
        return keys.to_frame(index=False).isna().any(axis=1).to_numpy()
    return keys.isna()


def _refuse_nulls(keys: pd.Index, *, block: str, side: str) -> None:
    """A null key matches nothing, on either side, and must not be joined past in silence."""
    empty = _null_mask(keys)
    if not bool(empty.any()):
        return
    where = [label for label, flag in zip(keys, empty, strict=True) if flag]
    raise MergeError(
        f"the {side} of block {block!r} has {len(where)} null key value(s). A null key "
        f"matches nothing, so the join would drop or blank those rows without saying so."
    )


def _refuse_duplicate_block_keys(keys: pd.Index, block: FeatureBlock) -> None:
    """A repeated block key fans the spine out, which is a silent change of row count.

    This is the guard the measured data demands. ``(Composition, temperature(K))`` is not
    unique on ``hydride_data.csv`` -- seven pairs appear twice -- so a block built row-wise
    on that key and joined back would take the spine from 1279 rows to 1293, with the
    duplicated measurements each counted twice in every fold and metric downstream.
    """
    repeated = keys[keys.duplicated(keep="first")]
    if len(repeated) == 0:
        return
    raise MergeError(
        f"block {block.name!r} has {len(repeated)} repeated key value(s): "
        f"{_named(repeated.unique())}. A block key must identify one row of the block, or "
        f"the join multiplies spine rows instead of describing them. If those really are "
        f"distinct measurements, the block belongs on the spine's row labels (key=None), "
        f"not on its chemistry."
    )


def _refuse_uncovered_keys(spine_keys: pd.Index, block_keys: pd.Index, block: str) -> None:
    """Both directions, because each hides a different defect.

    A spine key with no block row is a featuriser that skipped a composition -- the L9
    scenario, where the archival ``concat`` pads the column with NaN and shifts nothing that
    anyone can see. A block key nothing asked for is the reverse: the block was built from a
    different dataset, or from a stale copy of this one, and the rows that *did* match are
    now the only evidence that the two were ever the same table.
    """
    unmatched = spine_keys.difference(block_keys)
    if len(unmatched) > 0:
        raise MergeError(
            f"{len(unmatched)} of the spine's {len(spine_keys.unique())} distinct key(s) "
            f"have no row in block {block!r}: {_named(unmatched)}. Every spine row must "
            f"carry every feature block; a missing key is a featuriser that skipped a row "
            f"(leak L9)."
        )

    surplus = block_keys.difference(spine_keys)
    if len(surplus) > 0:
        raise MergeError(
            f"block {block!r} has {len(surplus)} key(s) the spine never asked for: "
            f"{_named(surplus)}. The block was built from different rows than the spine "
            f"holds; joining anyway would silently keep only the overlap."
        )


def _refuse_column_collisions(existing: pd.Index, block: FeatureBlock, arriving: pd.Index) -> None:
    """Two blocks may not contribute the same column name.

    ``merge_datasets.py:49`` -- ``df_merged.loc[:, ~df_merged.columns.duplicated()]`` --
    keeps the first of two identically-named columns and discards the rest without a word.
    Which featuriser's ``avg_atomic_mass`` survives then depends on the order the frames were
    listed in, which is not a thing anybody decided.
    """
    clash = existing.intersection(arriving)
    if len(clash) == 0:
        return
    raise MergeError(
        f"block {block.name!r} contributes {len(clash)} column name(s) already present: "
        f"{_named(clash)}. Two featurisers computing a column of the same name is a "
        f"decision for a human -- rename one, or drop it before merging. The archival "
        f"pipeline kept whichever arrived first (merge_datasets.py:49)."
    )


def merge_features(spine: pd.DataFrame, blocks: Sequence[FeatureBlock]) -> pd.DataFrame:
    """Attach every block to ``spine`` by key, preserving its rows exactly.

    The result has the spine's rows, in the spine's order, under the spine's index, with the
    spine's columns first and each block's columns appended in the order given. Nothing else
    is a possible outcome: every way a join could quietly change the table is checked and
    refused before the join runs.

    Args:
        spine: The measurement table. Its index labels are the row identities, and must be
            unique -- nothing below means anything otherwise.
        blocks: The feature blocks to attach, in the order their columns should appear.

    Returns:
        One frame: ``spine`` plus every block's columns.

    Raises:
        MergeError: naming the rows or columns that stopped it -- a duplicated spine label,
            a non-unique or null block key, a key uncovered on either side, or a column name
            arriving twice.
    """
    if not blocks:
        raise MergeError(
            "merge_features was given no blocks. A merge with nothing to join returns its "
            "input unchanged, which is a caller error dressed as a result."
        )

    if not spine.index.is_unique:
        repeated = spine.index[spine.index.duplicated(keep="first")]
        raise MergeError(
            f"the spine has {len(repeated)} duplicated index label(s): "
            f"{_named(repeated.unique())}. The spine's label is a row's identity here, so a "
            f"repeated one makes every coverage check below ambiguous. Reset it to a unique "
            f"index before merging -- and note that `reset_index(drop=True)` after a filter "
            f"is what made the archival concat look aligned when it was not."
        )

    merged = spine
    for block in blocks:
        addressed = _addressed(block)
        block_keys = addressed.index
        spine_keys = _spine_keys(spine, block)

        _refuse_nulls(block_keys, block=block.name, side="key")
        _refuse_nulls(spine_keys, block=block.name, side="spine key")
        _refuse_duplicate_block_keys(block_keys, block)
        _refuse_uncovered_keys(spine_keys, block_keys, block.name)
        _refuse_column_collisions(merged.columns, block, addressed.columns)

        merged = (
            merged.join(addressed)
            if block.key is None
            else merged.join(addressed, on=list(block.key))
        )

    # A post-condition, not a check: with every key unique, covered both ways and non-null,
    # a left join cannot change the row count or the index. It is asserted anyway so that a
    # future edit which loosens one of the guards above fails here, at the merge, rather
    # than three stages later in a metric nobody can explain.
    if len(merged) != len(spine) or not merged.index.equals(spine.index):
        raise MergeError(
            f"the join changed the spine: {len(spine)} rows in, {len(merged)} rows out. "
            f"This is unreachable while the checks above hold, so reaching it means one of "
            f"them was weakened. Leak L9 is exactly this, made silent."
        )
    return merged
