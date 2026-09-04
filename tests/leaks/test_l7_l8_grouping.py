"""L7 and L8 -- two rows that describe the same material belong on the same side of every line.

**L8** ``split_data.py:48,55``: the split key is the raw formula string. 1,149 raw strings
describe 1,115 normalised compositions, and 16 of those -- 35 rows -- span two splits under the
published seed. `Ce1Mg12` sits in test while `Mg12Ce1` sits in validation: the same
measurement, the same 6.0 wt%, the same 598 K, written two ways. `Pr1Co5` and `Pr1Co5 ` differ
by a trailing space.

**L7** ``benchmark_model_selection.py:895`` and ``Catboostmodel.py:522``: row-level
``StratifiedKFold`` with no groups, so 141 of 896 training rows share a formula across folds.

Since every selected feature is a composition statistic plus temperature, colliding rows have
byte-identical feature vectors up to temperature -- so this is not a near-duplicate problem, it
is the same point on both sides of the line.

The sharpest test in this file is
``test_the_archival_assertion_passes_on_the_raw_strings_while_the_data_leaks``: the check the
archival pipeline actually performed is **green** on the leaking data. A sentinel that only
proved "the fixed code passes" would have missed that entirely.

Card #71.
"""

from __future__ import annotations

import pytest
from hydms.qa import LeakDetected, assert_disjoint_groups, audit, for_leak

# Two of the sixteen measured collisions, written both ways. The canonical column is what a
# correct key produces; card #87 owns the function that produces it.
COLLISIONS = [
    ("Ce1Mg12", "Mg12Ce1", "ce1mg12"),
    ("Pr1Co5", "Pr1Co5 ", "pr1co5"),
]


# --------------------------------------------------------------------------------------
# L8 -- splits
# --------------------------------------------------------------------------------------


def test_l8_one_composition_in_two_splits_is_red() -> None:
    test = [canonical for _, _, canonical in COLLISIONS] + ["lani5"]
    val = [canonical for _, _, canonical in COLLISIONS] + ["tife"]
    with pytest.raises(LeakDetected) as exc:
        assert_disjoint_groups({"test": test, "val": val})
    message = str(exc.value)
    assert "leaks L7 and L8" in message
    assert "2 canonical composition(s)" in message
    assert "'ce1mg12' in test+val" in message, "the message must say which splits, not just how many"


def test_l8_disjoint_splits_are_green() -> None:
    assert_disjoint_groups(
        {
            "train": ["lani5", "tife", "mg2ni"],
            "val": ["zrv2", "ticr2"],
            "test": ["ce1mg12", "pr1co5"],
        }
    )


def test_the_archival_assertion_passes_on_the_raw_strings_while_the_data_leaks() -> None:
    """`split_data.py`'s own check is green on data that leaks. That is the finding.

    Under the raw formula string these four spellings are four independent identities, so
    asserting that no *formula* spans two splits succeeds -- which is exactly what the archival
    pipeline asserted, and why nobody noticed. The same rows under a canonical key are red.

    This is what makes the L8 sentinel a sentinel rather than decoration: it fails for a
    reason the previous check was structurally unable to see.
    """
    raw_test = [raw for raw, _, _ in COLLISIONS]
    raw_val = [other for _, other, _ in COLLISIONS]

    assert_disjoint_groups({"test": raw_test, "val": raw_val}, key_name="formula string")

    with pytest.raises(LeakDetected):
        assert_disjoint_groups(
            {
                "test": [canonical for _, _, canonical in COLLISIONS],
                "val": [canonical for _, _, canonical in COLLISIONS],
            }
        )


def test_l8_a_composition_repeated_inside_one_split_is_not_a_finding() -> None:
    """Several measurements of one material in one split is the normal case, not a leak.

    1,279 rows carry 1,115 compositions; a detector that flagged repetition would be red on
    correct data and would be switched off within a week.
    """
    assert_disjoint_groups({"train": ["lani5", "lani5", "lani5", "tife"], "test": ["mg2ni"]})


def test_l8_a_collision_across_three_splits_names_all_three() -> None:
    with pytest.raises(LeakDetected, match=r"'lani5' in test\+train\+val"):
        assert_disjoint_groups(
            {"train": ["lani5"], "val": ["lani5"], "test": ["lani5"]}
        )


# --------------------------------------------------------------------------------------
# L7 -- cross-validation folds
# --------------------------------------------------------------------------------------


def test_l7_a_composition_in_two_folds_is_red() -> None:
    with pytest.raises(LeakDetected, match="cross-validation folds"):
        assert_disjoint_groups(
            {"fold-0": ["lani5", "tife", "mg2ni"], "fold-1": ["lani5", "zrv2"]},
            what="cross-validation folds",
        )


def test_l7_group_aware_folds_are_green() -> None:
    """The `StratifiedGroupKFold` shape card #88 must produce."""
    assert_disjoint_groups(
        {
            "fold-0": ["lani5", "tife"],
            "fold-1": ["mg2ni", "zrv2"],
            "fold-2": ["ticr2", "ce1mg12"],
            "fold-3": ["pr1co5", "lani5_ni"],
            "fold-4": ["mg2al3", "fetiv"],
        },
        what="cross-validation folds",
    )


def test_l7_one_bad_fold_among_five_is_enough() -> None:
    folds = {f"fold-{i}": [f"alloy-{i}-{j}" for j in range(4)] for i in range(5)}
    assert_disjoint_groups(folds, what="cross-validation folds")

    folds["fold-3"] = [*folds["fold-3"], "alloy-0-0"]
    with pytest.raises(LeakDetected, match=r"'alloy-0-0' in fold-0\+fold-3"):
        assert_disjoint_groups(folds, what="cross-validation folds")


def test_l7_the_message_truncates_but_still_reports_the_total() -> None:
    """141 of 896 rows shared a formula across folds. Listing all of them helps nobody."""
    shared = [f"alloy-{i}" for i in range(30)]
    with pytest.raises(LeakDetected) as exc:
        assert_disjoint_groups({"fold-0": shared, "fold-1": shared}, what="cross-validation folds")
    message = str(exc.value)
    assert "30 canonical composition(s)" in message
    assert "22 more" in message


# --------------------------------------------------------------------------------------
# Misuse is not a finding
# --------------------------------------------------------------------------------------


def test_a_single_partition_is_a_caller_error() -> None:
    """Nothing can straddle one split, so a green answer here would mean nothing."""
    with pytest.raises(ValueError, match="at least two"):
        assert_disjoint_groups({"train": ["lani5", "tife"]})


# --------------------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------------------


def test_l7_is_wired_to_the_real_fold_generator() -> None:
    """Card #88's folds are the subject now, not the five-key miniature above."""
    sentinel = for_leak("L7")
    assert sentinel is not None
    assert sentinel.subject == "hydms.surrogate.validation"
    assert sentinel.live is not None, "an unwired sentinel guards its subject in name only"

    row = next(entry for entry in audit() if entry.leak == "L7")
    assert row.status == "green", row.detail
    assert row.owed_by == 88


def test_l7_goes_red_when_the_real_folds_stop_grouping() -> None:
    """Seen red against the real fold generator, not against a dictionary of strings.

    `benchmark_model_selection.py:895` put back: the same rows, folded without `groups=`. The
    detector is handed the canonical keys of the folds that protocol produces, and 1,279 rows
    over 1,115 compositions cannot be cut five ways at row level without splitting one.
    """
    pytest.importorskip("pandas", reason="the real fold generator is pandas frames end to end")
    from hydms.data.canonical import group_keys
    from hydms.qa.sentinels import _validation_run
    from sklearn.model_selection import StratifiedKFold

    frame, _ = _validation_run()
    keys = group_keys(frame)
    labels = list(frame.index)
    ungrouped = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    folds = {
        f"fold-{position}": keys.loc[[labels[at] for at in held]]
        for position, (_, held) in enumerate(
            ungrouped.split(frame, group_keys(frame).str.len() % 3)
        )
    }
    with pytest.raises(LeakDetected, match="cross-validation folds"):
        assert_disjoint_groups(folds, what="cross-validation folds")
