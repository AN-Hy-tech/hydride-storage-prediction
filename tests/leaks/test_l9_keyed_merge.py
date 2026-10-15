"""L9 -- the merge joins on a key, or it silently attaches features to the wrong composition.

``merge_datasets.py:46``: three feature frames concatenated positionally with
``pd.concat(..., axis=1)`` after ``reset_index(drop=True)``. One skipped CBFV row shifts every
subsequent row by one, and nothing anywhere notices. ``docs/FREEZE.md`` names it as the
highest-severity **correctness** defect in the repository -- every other leak makes the numbers
optimistic, this one makes them describe different materials.

The card asks for "a deliberately shuffled input frame makes the merge fail, not pass
silently". Two properties are hiding inside that sentence and only both together pin the
defect down:

  1. **Order-invariance.** A keyed merge is *supposed* to survive a reordering -- joining by
     key is what makes row order irrelevant. So the failure is not "it did not raise", it is
     "it produced a different answer and said nothing".
  2. **Coverage.** A row the merge cannot key must make it fail. This is where "must fail"
     belongs, and it is the assertion card #10's `## Done when` calls for by name.

That refinement is recorded in the card's narrative rather than left implicit here, because
taking the sentence literally -- assert that a shuffle raises -- would produce a sentinel that
is red against a *correct* keyed merge.

Card #71.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest
from hydms.qa import LeakDetected, assert_merge_is_keyed

pd = pytest.importorskip("pandas", reason="pandas is not installed in this interpreter")

KEYS = ["LaNi5", "TiFe", "Mg2Ni", "ZrV2"]


@pytest.fixture()
def frames() -> tuple[pd.DataFrame, ...]:
    """A spine and two feature blocks, keyed by composition -- the merge's real shape.

    The archival pipeline joined three frames exactly like these: the target table plus the
    `oliynyk` and `jarvis` descriptor blocks (`docs/PHASE-H-RUNBOOK.md` section 1).
    """
    index = pd.Index(KEYS, name="Composition")
    return (
        pd.DataFrame({"target": [1.4, 1.9, 7.6, 2.0]}, index=index),
        pd.DataFrame({"oliynyk_0": [10.0, 20.0, 30.0, 40.0]}, index=index),
        pd.DataFrame({"jarvis_0": [0.1, 0.2, 0.3, 0.4]}, index=index),
    )


def positional_concat(frames: Sequence[Any]) -> Any:
    """`merge_datasets.py:46`, reintroduced."""
    return pd.concat([frame.reset_index(drop=True) for frame in frames], axis=1)


def keyed_join(frames: Sequence[Any]) -> Any:
    """What card #10 must build: join on the key, and assert the join covered the spine."""
    merged = frames[0]
    for right in frames[1:]:
        joined = merged.join(right, how="inner")
        if len(joined) != len(merged):
            raise ValueError(
                f"the join dropped {len(merged) - len(joined)} row(s) of the spine; every "
                f"composition must carry every feature block"
            )
        merged = joined
    return merged


def test_l9_the_positional_concat_is_red(frames: tuple[pd.DataFrame, ...]) -> None:
    with pytest.raises(LeakDetected) as exc:
        assert_merge_is_keyed(positional_concat, frames)
    message = str(exc.value)
    assert "leak L9" in message
    assert "joining on position" in message


def test_l9_the_keyed_join_is_green(frames: tuple[pd.DataFrame, ...]) -> None:
    assert_merge_is_keyed(keyed_join, frames)


def test_l9_the_two_merges_agree_on_the_untouched_inputs(
    frames: tuple[pd.DataFrame, ...],
) -> None:
    """Both produce the same table when nothing is out of order.

    Without this the sentinel could be passing because the two merges simply differ. They do
    not: on well-ordered inputs the defect is invisible, which is precisely why it survived
    into a published pipeline.
    """
    positional = positional_concat(list(frames)).reset_index(drop=True)
    keyed = keyed_join(list(frames)).reset_index(drop=True)
    assert positional.equals(keyed)


def test_l9_the_misalignment_the_leak_produces_is_real(
    frames: tuple[pd.DataFrame, ...],
) -> None:
    """Name the damage, not just the detection: Mg2Ni's 7.6 wt% ends up beside TiFe's features.

    `docs/QA-PROTOCOL.md` section 4.1 -- delete a line of the implementation and see whether
    something goes red. This is that check for the merge, stated in the units of the problem.
    """
    reordered = list(frames)
    reordered[1] = frames[1].loc[["TiFe", "LaNi5", "Mg2Ni", "ZrV2"]]

    damaged = positional_concat(reordered)
    assert damaged.loc[0, "target"] == 1.4  # LaNi5
    assert damaged.loc[0, "oliynyk_0"] == 20.0  # ...carrying TiFe's descriptor

    intact = keyed_join(reordered)
    assert intact.loc["LaNi5", "oliynyk_0"] == 10.0


def test_l9_a_missing_row_must_make_the_merge_fail(frames: tuple[pd.DataFrame, ...]) -> None:
    """The coverage half, on its own. This is the `## Done when` box card #10 carries.

    `extract_features_cbfv.py` silently discarded CBFV failures, so the count of feature rows
    was never guaranteed to match the count of compositions -- card #9 asserts
    `len(skipped) == 0` upstream, and this is what catches it if that assertion ever softens.
    """
    thinned = list(frames)
    thinned[1] = frames[1].iloc[1:]

    with pytest.raises(ValueError, match="dropped 1 row"):
        keyed_join(thinned)

    absorbed = positional_concat(thinned)
    assert len(absorbed) == 4, "the positional concat pads instead of complaining"
    assert absorbed["oliynyk_0"].isna().sum() == 1


def test_l9_a_merge_that_refuses_a_reordering_is_not_this_leak(
    frames: tuple[pd.DataFrame, ...],
) -> None:
    """Refusing is loud. The leak is silence, so a stricter merge must still pass.

    A merge that demands its inputs arrive pre-sorted is worse ergonomics and not a
    correctness defect; a sentinel that failed it would be enforcing a preference.
    """

    def sorted_inputs_only(inner: Sequence[Any]) -> Any:
        for frame in inner:
            if list(frame.index) != sorted(frame.index):
                raise ValueError("inputs must be sorted by key")
        return keyed_join(inner)

    ordered = tuple(frame.sort_index() for frame in frames)
    assert_merge_is_keyed(sorted_inputs_only, ordered)


# --------------------------------------------------------------------------------------
# Misuse is not a finding
# --------------------------------------------------------------------------------------


def test_a_single_frame_is_a_caller_error(frames: tuple[pd.DataFrame, ...]) -> None:
    with pytest.raises(ValueError, match="at least two frames"):
        assert_merge_is_keyed(keyed_join, frames[:1])


def test_a_merge_that_cannot_run_at_all_is_a_caller_error(
    frames: tuple[pd.DataFrame, ...],
) -> None:
    """Nothing can be measured against a baseline that never existed, so this is not a leak."""

    def broken(inner: Sequence[Any]) -> Any:
        raise RuntimeError("the feature directory has no producer in this repository")

    with pytest.raises(ValueError, match="raised on its own unmodified inputs"):
        assert_merge_is_keyed(broken, frames)


# --------------------------------------------------------------------------------------
# The live wiring -- card #10
# --------------------------------------------------------------------------------------


def test_l9_is_green_against_the_real_merge() -> None:
    """`hydms/data/merge.py` exists, and the sentinel is pointed at it rather than at the
    miniature above. Until card #10 wired it, this leak sat in the `unwired` state and HG-1
    was red -- which is the mechanism, not a bug (card #71)."""
    from hydms.qa import audit

    row = next(entry for entry in audit() if entry.leak == "L9")
    assert row.status == "green", row.detail
    assert "hydms.data.merge" in row.detail


def test_l9_goes_red_when_the_real_merge_stops_keying(monkeypatch: pytest.MonkeyPatch) -> None:
    """Seen red, and against the real subject rather than a copy of it.

    The live hook imports `merge_features` at call time, so replacing it here is enough to
    prove the sentinel is watching the actual function the pipeline calls. Put the archival
    positional concat back and the audit must report L9 broken.
    """
    from hydms.qa import audit
    from hydms.qa.sentinels import for_leak

    def archival(spine: Any, blocks: Any) -> Any:
        frames = [spine.reset_index(drop=True)]
        frames += [block.frame.reset_index(drop=True) for block in blocks]
        return pd.concat(frames, axis=1)

    monkeypatch.setattr("hydms.data.merge.merge_features", archival)

    live = for_leak("L9").live
    assert live is not None
    with pytest.raises(LeakDetected):
        live()

    row = next(entry for entry in audit() if entry.leak == "L9")
    assert row.status == "broken"
    assert "hydms.data.merge has leak L9" in row.detail
