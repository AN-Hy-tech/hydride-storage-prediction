"""L1 -- the canonical composition key and the Alloy_class re-join. Card #87.

Five questions, and they are different:

  - **Identity.** Two spellings of one material receive one key -- element order, overall
    scale, whitespace and parenthesised grouping all stop mattering. The six measured
    collision pairs in ``tests/conftest.py`` are the regression fixture.
  - **Resolution.** Rounding decides identity one formula at a time, so it cannot know
    whether the digit it dropped was the only thing separating two materials. ``separation``
    is what knows, and ``test_three_significant_digits_would_merge_two_materials`` is the
    demonstration that it can still go red -- ``docs/QA-PROTOCOL.md`` section 5.
  - **Accounting.** The collapse from 1149 strings to 1115 compositions is reported in three
    steps, because one number hides which normalisation did what -- and the first step is the
    one a stray ``str.strip()`` downstream could silently reproduce.
  - **The split key.** The archival protocol, re-run here, puts 16 canonical compositions --
    35 rows -- on both sides of a split while its own assertion passes. Grouping the same
    protocol on the key produces none. That is leak L8, before and after, on the real data.
  - **Alloy_class.** Ten canonical compositions carry more than one label, not the five the
    card predicted, and the five extra are created by canonicalisation itself. Precedence
    resolves them, reproducibly, and the resolutions are pinned one by one.

``docs/QA-PROTOCOL.md`` section 4.1: delete a line of the implementation in your head and
something here must go red.
"""

from __future__ import annotations

from collections import Counter

import pytest

pytest.importorskip("pandas", reason="the canonical key is measured over pandas frames")

import pandas as pd  # noqa: E402  -- only importable once the skip above has passed
from hydms.data.canonical import (  # noqa: E402
    ALLOY_CLASS_PRECEDENCE,
    ML_HYDPARK_CLASS_ALIASES,
    SIGNIFICANT_DIGITS,
    CanonicalisationError,
    alloy_class_table,
    alloy_classes,
    canonical_key,
    collapse,
    group_keys,
    reconcile_class,
    separation,
)
from hydms.data.load import (  # noqa: E402
    HYDRIDE_ALLOY_CLASSES,
    ML_HYDPARK_MATERIAL_CLASSES,
    FormulaError,
    load_hydride_data,
    load_ml_hydpark,
    parse_formula,
)
from hydms.qa import LeakDetected, assert_disjoint_groups  # noqa: E402

# Measured on `Machine_Model/data/raw/hydride_data.csv`, 1279 rows. Every number here is
# reproduced by `tests/data/test_canonical.py` itself; none is copied from a document.
RAW_STRINGS = 1149
AFTER_WHITESPACE = 1142
AFTER_ORDER = 1121
COMPOSITIONS = 1115

# The published split protocol, `split_data.py:63-135`, reproduced in `published_split`.
PUBLISHED_ROWS = (896, 136, 247)
STRADDLING_KEYS = 16
STRADDLING_ROWS = 35

# The ten canonical compositions whose rows disagree about the class, and what
# ALLOY_CLASS_PRECEDENCE resolves each to. Five of these are conflicts already present on the
# raw formula string; the other five exist only because canonicalisation merged two spellings.
RESOLVED_CONFLICTS = {
    "Al0.5Mg0.5": "Mg",
    "Al0.6Mg0.4": "Mg",
    "Ce0.07692Mg0.9231": "Mg",
    "Ce0.1Mg0.9": "Mg",
    "Cr0.08197Fe0.5738Zr0.3443": "AB2",
    "Cr0.3333Mn0.3333Ti0.2667Zr0.06667": "AB2",
    "Fe0.08333Mg0.6667Ni0.25": "A2B",
    "Mg0.5Ni0.5": "Mg",
    "Mg0.6667Ni0.3333": "A2B",
    "Mn0.6Ti0.4": "AB2",
}
RAW_STRING_CONFLICTS = 5


@pytest.fixture(scope="module")
def hydride() -> pd.DataFrame:
    """The curated dataset through card #9's loader. Read once; nothing here mutates it."""
    return load_hydride_data()


@pytest.fixture(scope="module")
def corpus(hydride: pd.DataFrame) -> list[str]:
    """Every formula string in both raw files -- 1784 distinct, over 2051 rows."""
    return list(hydride["Composition"]) + list(load_ml_hydpark()["Composition_Formula"])


# --------------------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------------------


def test_the_measured_collision_pairs_share_one_key(
    known_collisions: list[tuple[str, str]],
) -> None:
    """The regression fixture: six pairs the audit found spanning two splits.

    Two by element order, one by scale, two by trailing whitespace, one by both. Under the
    raw string each pair is two materials, which is why `split_data.py`'s assertion passed.
    """
    for left, right in known_collisions:
        assert canonical_key(left) == canonical_key(right), (
            f"{left!r} and {right!r} are the same material and received two keys: "
            f"{canonical_key(left)!r} and {canonical_key(right)!r}"
        )


@pytest.mark.parametrize(
    ("left", "right", "why"),
    [
        ("Ce1Mg12", "Mg12Ce1", "element order"),
        ("Mg1Al1", "Mg0.5Al0.5", "overall scale"),
        ("LaNi5", "La2Ni10", "overall scale, integer multiple"),
        ("Pr1Co5", "  Pr1Co5  ", "surrounding whitespace"),
        ("Ti0.8Zr0.2", "Ti0.8 Zr0.2", "internal whitespace"),
        ("LaNi5", "La(Ni)5", "parenthesised group"),
        ("LaNi5", "La0.16667Ni0.83333", "written as fractions"),
        ("Mg2Ni", "Mg1Ni1Mg1", "a symbol written twice"),
    ],
)
def test_the_key_ignores(left: str, right: str, why: str) -> None:
    assert canonical_key(left) == canonical_key(right), why


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("LaNi5", "LaNi4.9"),
        ("LaNi5", "CeNi5"),
        ("Ti0.8Zr0.2Mn1Cr1", "Ti0.8Zr0.2Mn1.2Cr0.8"),
        ("Mg2Ni", "Mg2Ni0.999La0.001"),
    ],
)
def test_the_key_separates_materials_that_differ(left: str, right: str) -> None:
    assert canonical_key(left) != canonical_key(right)


def test_the_key_is_itself_a_formula_naming_the_same_material() -> None:
    """It reads as chemistry, not as a hash -- and `parse_formula` can read it back."""
    key = canonical_key("LaNi5")
    assert key == "La0.1667Ni0.8333"

    amounts = parse_formula(key)
    assert set(amounts) == {"La", "Ni"}
    assert amounts["Ni"] / amounts["La"] == pytest.approx(5.0, rel=1e-3)


def test_re_keying_a_key_never_lands_on_another_material(corpus: list[str]) -> None:
    """A key is a label, not an input, and this is the guard on saying so.

    Rounded fractions no longer sum to exactly one, so re-normalising them can move a final
    digit -- for 185 of these 1784 formulae it does. What must never happen is that the moved
    digit lands on a *different* material's key, which would silently merge two groups the
    moment somebody keyed a key.
    """
    keys = {canonical_key(text) for text in corpus}
    for key in keys:
        again = canonical_key(key)
        assert again == key or again not in keys, (
            f"re-keying {key!r} produced {again!r}, which is another material's key"
        )


def test_a_miscased_symbol_is_refused_rather_than_repaired() -> None:
    """`co` is `Co`, or `C` and `O`, and nothing here can tell which.

    Both shapes of refusal come from the one grammar in `hydms.data.load`: a lowercase
    opening character is not a symbol at all, and an all-caps one is a symbol that no element
    answers to. Neither is repaired into a guess.
    """
    with pytest.raises(FormulaError, match="not a chemical element"):
        canonical_key("MG12CE1")

    with pytest.raises(FormulaError, match="unexpected character 'm'"):
        canonical_key("mg12ce1")


def test_no_two_formula_strings_in_the_file_differ_by_case_alone(
    hydride: pd.DataFrame,
) -> None:
    """Which is why refusing above costs nothing. Measured, not assumed."""
    strings = list(dict.fromkeys(hydride["Composition"]))
    lowered = Counter(text.lower() for text in strings)
    assert [text for text, count in lowered.items() if count > 1] == []


def test_an_element_below_the_resolution_is_refused_not_written_as_zero() -> None:
    """A key naming an element at zero would claim a composition nobody wrote.

    Unreachable on the current corpus -- the smallest atomic fraction in either raw file is
    2.58e-05, five orders above the floor -- and the reason the key rounds to significant
    digits rather than to decimal places.
    """
    with pytest.raises(CanonicalisationError, match="below the resolution"):
        canonical_key("Mg1000000000000La0.0000001")


def test_the_trace_element_the_raw_file_actually_contains_survives() -> None:
    """`Mg0853Ni0.125La0.022` is a missing decimal point: 0.853 + 0.125 + 0.022 = 1.000.

    The row is a data defect, boxed on card #14. What this asserts is that the key does not
    quietly turn its 2.58e-05 of lanthanum into `La0` -- four decimal places would.
    """
    key = canonical_key("Mg0853Ni0.125La0.022")
    assert key == "La0.00002579Mg0.9998Ni0.0001465"
    assert parse_formula(key)["La"] > 0.0


# --------------------------------------------------------------------------------------
# The collapse, in three steps
# --------------------------------------------------------------------------------------


def test_the_collapse_is_reported_step_by_step(hydride: pd.DataFrame) -> None:
    """1149 -> 1142 -> 1121 -> 1115. A single endpoint hides which step did what."""
    stages = collapse(hydride["Composition"]).stages
    assert [stage.name for stage in stages] == ["raw", "whitespace", "order", "composition"]
    assert [stage.distinct for stage in stages] == [
        RAW_STRINGS,
        AFTER_WHITESPACE,
        AFTER_ORDER,
        COMPOSITIONS,
    ]
    assert [stage.merged for stage in stages] == [0, 7, 21, 6]


def test_the_whitespace_step_is_the_one_a_stray_strip_could_reproduce(
    hydride: pd.DataFrame,
) -> None:
    """34 trailing spaces, 9 internal, 7 padded forms with an unpadded twin already in file.

    `str.strip()` alone reaches 1142 and stops there, leaving element order and scaling
    undone -- and leaving whoever wrote it convinced the formulae are now normalised.
    """
    strings = list(dict.fromkeys(hydride["Composition"]))
    assert len([text for text in strings if text != text.rstrip()]) == 34
    assert len([text for text in strings if text != text.lstrip()]) == 0
    assert len([text for text in strings if " " in text.strip()]) == 9

    padded = [text for text in strings if text != "".join(text.split())]
    assert len([text for text in padded if "".join(text.split()) in set(strings)]) == 7

    assert hydride["Composition"].str.strip().nunique() == AFTER_WHITESPACE
    assert group_keys(hydride).nunique() == COMPOSITIONS


# --------------------------------------------------------------------------------------
# Resolution -- the property clustering would have given for free
# --------------------------------------------------------------------------------------


def test_canonicalisation_never_silently_merges_two_different_materials(
    corpus: list[str],
) -> None:
    """Asserted over every formula in both raw files, which is what the card asks for.

    The widest gap the key merged is narrower than the narrowest it did not, so no pair
    straddles the rounding boundary: on this corpus the key behaves exactly like clustering
    at a 1e-4 tolerance, without needing the corpus to compute one key.
    """
    measured = separation(corpus)

    assert measured.safe, str(measured)
    assert measured.widest_within_key == pytest.approx(3.4646e-05, rel=1e-3)
    assert measured.closest_between_keys == pytest.approx(1.0120e-04, rel=1e-3)
    assert measured.widest_pair == (
        "Ti0.2167V0.2167Nb0.2167Cr0.35",
        "Ti0.216667V0.216667Nb0.216667Cr0.35",
    ), "the widest merge is the one that decided the resolution: the same alloy, two precisions"
    assert measured.comparisons == 8920


def test_three_significant_digits_would_merge_two_materials(
    corpus: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`docs/QA-PROTOCOL.md` section 5: the measurement is shown red on purpose.

    At three digits the widest pair sharing a key (3.10e-04) is wider than the closest pair
    not sharing one (1.98e-04) -- which is precisely a silent merge, and precisely what
    `separation` exists to refuse to let through unnoticed.
    """
    monkeypatch.setattr("hydms.data.canonical.SIGNIFICANT_DIGITS", 3)
    coarse = separation(corpus)

    assert not coarse.safe
    assert coarse.widest_within_key > coarse.closest_between_keys


def test_five_significant_digits_would_split_one_material(corpus: list[str], monkeypatch) -> None:
    """The other side of the choice: finer is not safer, it is just differently wrong.

    At five digits `Ti0.2167V0.2167Nb0.2167Cr0.35` and its 0.216667 twin become two
    compositions and the count leaves the 1115 every document in this repository states.
    """
    monkeypatch.setattr("hydms.data.canonical.SIGNIFICANT_DIGITS", 5)
    assert canonical_key("Ti0.2167V0.2167Nb0.2167Cr0.35") != canonical_key(
        "Ti0.216667V0.216667Nb0.216667Cr0.35"
    )


def test_the_resolution_is_four_significant_digits() -> None:
    """Pinned, because the two tests above are what justify it and both would change."""
    assert SIGNIFICANT_DIGITS == 4


# --------------------------------------------------------------------------------------
# The split key -- leak L8, before and after, on the real data
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def published_split(hydride: pd.DataFrame) -> dict[str, str]:
    """`split_data.py:63-135` re-run: formula string -> "train" | "val" | "test".

    Card #13 owns the split protocol; this reproduces the *published* one so that L8 can be
    measured where it actually happened. It reproduces the published row counts exactly,
    which is what says the reproduction is faithful. Binning is quantile-based and therefore
    invariant to the log1p the archival file had already applied to the target.
    """
    pytest.importorskip("sklearn", reason="the published split protocol is scikit-learn's")
    import numpy as np
    from sklearn.model_selection import StratifiedShuffleSplit
    from sklearn.preprocessing import KBinsDiscretizer

    seed, min_members = 42, 5
    stats = (
        pd.DataFrame(
            {
                "formula": hydride["Composition"],
                "temperature(K)": hydride["temperature(K)"],
                "target": np.log1p(hydride["H2_W% (max)"]),
            }
        )
        .groupby("formula")
        .agg({"temperature(K)": "mean", "target": "mean"})
        .reset_index()
    )
    for column, name in (("temperature(K)", "T_bin"), ("target", "Wt%_bin")):
        binner = KBinsDiscretizer(n_bins=5, encode="ordinal", strategy="quantile")
        stats[name] = binner.fit_transform(stats[[column]])
    stats["strat_key"] = stats["T_bin"].astype(str) + "_" + stats["Wt%_bin"].astype(str)

    counts = stats["strat_key"].value_counts()
    for small in counts[counts < min_members].index:
        here = [float(part) for part in small.split("_")]
        distances = {
            other: float(
                np.hypot(here[0] - float(other.split("_")[0]), here[1] - float(other.split("_")[1]))
            )
            for other in counts.index
            if other != small and counts[other] >= min_members
        }
        nearest = min(distances, key=lambda name: distances[name]) if distances else counts.index[0]
        stats.loc[stats["strat_key"] == small, "strat_key"] = nearest

    first = StratifiedShuffleSplit(n_splits=1, test_size=0.30, random_state=seed)
    train_index, rest_index = next(first.split(stats, stats["strat_key"]))
    train, rest = stats.iloc[train_index]["formula"], stats.iloc[rest_index]["formula"]

    strata = stats.set_index("formula")["strat_key"].loc[rest.to_numpy()].to_numpy()
    second = StratifiedShuffleSplit(n_splits=1, test_size=2 / 3, random_state=seed)
    val_index, test_index = next(second.split(rest, strata))

    assignment = {formula: "train" for formula in train}
    assignment.update({formula: "val" for formula in rest.iloc[val_index]})
    assignment.update({formula: "test" for formula in rest.iloc[test_index]})
    return assignment


def test_the_reproduced_split_matches_the_published_row_counts(
    hydride: pd.DataFrame, published_split: dict[str, str]
) -> None:
    """896 / 136 / 247, as REPORT.md section 2.6 reports them. Otherwise L8 is unmeasured."""
    where = hydride["Composition"].map(published_split)
    assert (
        int((where == "train").sum()),
        int((where == "val").sum()),
        int((where == "test").sum()),
    ) == PUBLISHED_ROWS


def test_sixteen_compositions_span_two_splits_while_the_archival_assertion_passes(
    hydride: pd.DataFrame, published_split: dict[str, str]
) -> None:
    """Leak L8, measured where it happened.

    `split_data.py:126-129` asserts that no *formula string* spans two splits. That assertion
    is green here, on the same rows where 16 canonical compositions -- 35 of 1279 rows -- sit
    on both sides of a line. The archival check was structurally unable to see it.
    """
    keys = group_keys(hydride)
    by_split: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    raw_by_split: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    for formula, key in zip(hydride["Composition"], keys, strict=True):
        by_split[published_split[formula]].append(key)
        raw_by_split[published_split[formula]].append(formula)

    assert_disjoint_groups(raw_by_split, key_name="formula string")

    with pytest.raises(LeakDetected) as failure:
        assert_disjoint_groups(by_split)
    assert f"{STRADDLING_KEYS} canonical composition(s)" in str(failure.value)

    straddling = {
        key
        for key in set(keys)
        if len({split for split, members in by_split.items() if key in members}) > 1
    }
    assert len(straddling) == STRADDLING_KEYS
    assert int(keys.isin(straddling).sum()) == STRADDLING_ROWS


def test_grouping_the_same_protocol_on_the_key_leaves_nothing_straddling(
    hydride: pd.DataFrame, published_split: dict[str, str]
) -> None:
    """The fix, on the real data: group the split on the key and the 35 rows stop leaking.

    Card #13 builds the split module; what is asserted here is the property that makes it
    worth building -- that the key is a usable split key, and the same key #88 groups folds
    on. One composition, one side of the line, however it was spelled.
    """
    keys = group_keys(hydride)
    first_split_of_key = {}
    for formula, key in zip(hydride["Composition"], keys, strict=True):
        first_split_of_key.setdefault(key, published_split[formula])

    regrouped: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    for key in keys:
        regrouped[first_split_of_key[key]].append(key)

    assert_disjoint_groups(regrouped)


# --------------------------------------------------------------------------------------
# What the key is not: a row identity
# --------------------------------------------------------------------------------------


def test_the_key_and_temperature_still_do_not_identify_a_row(hydride: pd.DataFrame) -> None:
    """1272 distinct (string, T) pairs become 1268 distinct (key, T) pairs over 1279 rows.

    Card #10 measured the seven repeats on the raw string, six of them independent replicates
    from different citations, and keyed the merge on the spine's index label because of them.
    Canonicalisation can only merge, so the count falls: eleven repeats now, four of which
    exist only because two spellings became one material. Those four are what #13's splits
    and #88's folds must see as one material measured twice.
    """
    keyed = pd.DataFrame({"key": group_keys(hydride), "T": hydride["temperature(K)"]})
    raw = pd.DataFrame({"key": hydride["Composition"], "T": hydride["temperature(K)"]})

    assert len(raw.drop_duplicates()) == 1272
    assert len(keyed.drop_duplicates()) == 1268

    repeated = keyed[keyed.duplicated(keep=False)]
    groups = repeated.groupby(["key", "T"], sort=False).ngroups
    assert groups == 11
    spellings = (
        pd.DataFrame(
            {
                "key": keyed["key"],
                "T": keyed["T"],
                "formula": hydride["Composition"],
            }
        )
        .loc[repeated.index]
        .groupby(["key", "T"])["formula"]
        .nunique()
    )
    assert int((spellings > 1).sum()) == 4


# --------------------------------------------------------------------------------------
# Alloy_class
# --------------------------------------------------------------------------------------


def test_the_class_conflicts_are_ten_not_five(hydride: pd.DataFrame) -> None:
    """The card predicted five. Five is the count on the raw *string*; the key has ten.

    Canonicalisation can only merge, so the count could only rise -- and it does, by exactly
    the five compositions whose two spellings were labelled independently. Confirming this
    was a box on the card: had the two fives been the same set, the reconciliation rule would
    have had less work to do than it does.
    """
    raw_conflicts = (
        hydride.groupby("Composition")["Alloy_class"].nunique().pipe(lambda s: s[s > 1])
    )
    assert len(raw_conflicts) == RAW_STRING_CONFLICTS

    table = alloy_class_table(hydride)
    conflicted = table[table["conflicted"]]
    assert len(conflicted) == len(RESOLVED_CONFLICTS)

    keyed_raw_conflicts = {canonical_key(formula) for formula in raw_conflicts.index}
    assert keyed_raw_conflicts <= set(conflicted.index), (
        "canonicalisation must not resolve a conflict the raw string already had"
    )
    assert len(set(conflicted.index) - keyed_raw_conflicts) == 5


def test_every_conflict_resolves_to_the_stated_label(hydride: pd.DataFrame) -> None:
    """Pinned one by one, because the rule is a decision and a decision must be visible.

    Each of these is the label a metallurgist gives the material: Mg2Ni is A2B, TiMn1.5 is a
    C14 Laves AB2, Zr(Fe,Cr)2 is AB2, and the Mg-Al and Mg-Ce intermetallics are Mg-based.
    Precedence gets all ten right; a majority vote would tie on eight and be wrong on the
    other two, because it counts citations rather than chemistry.
    """
    table = alloy_class_table(hydride)
    resolved = table[table["conflicted"]]["Alloy_class"].to_dict()
    assert resolved == RESOLVED_CONFLICTS


def test_reconciliation_is_reproducible_under_any_row_order(hydride: pd.DataFrame) -> None:
    """Same input, same labels -- and row order is not part of the input.

    A rule that depended on which row came first would be a rule nobody could re-derive, and
    the splits and folds grouped on it would move whenever the file was re-sorted.
    """
    first = alloy_class_table(hydride)
    again = alloy_class_table(hydride)
    shuffled = alloy_class_table(hydride.sample(frac=1.0, random_state=7))

    assert first.equals(again)
    assert first.equals(shuffled.sort_index())


def test_no_row_loses_its_class_and_no_class_is_invented(hydride: pd.DataFrame) -> None:
    """The re-join covers every row, and stays inside the vocabulary the file declares."""
    labels = alloy_classes(hydride)

    assert labels.index.equals(hydride.index)
    assert not bool(labels.isna().any())
    assert set(labels) <= set(HYDRIDE_ALLOY_CLASSES)
    assert set(labels) == set(hydride["Alloy_class"]), "all ten classes survive the re-join"
    assert int((labels != hydride["Alloy_class"]).sum()) == 13


def test_two_spellings_of_one_composition_receive_one_class(hydride: pd.DataFrame) -> None:
    """`Ce1Mg12` is MIC in the file and `Mg12Ce1` is Mg. They are one material.

    A fold that holds out a class must hold out every row of it, so the same composition
    appearing in two folds under two labels is leak L8 arriving through the class column.
    """
    labels = alloy_classes(hydride)
    rows = hydride["Composition"].isin(["Ce1Mg12", "Mg12Ce1"])

    assert set(hydride.loc[rows, "Alloy_class"]) == {"MIC", "Mg"}
    assert set(labels[rows]) == {"Mg"}


def test_the_class_table_carries_the_evidence_for_every_composition(
    hydride: pd.DataFrame,
) -> None:
    """A resolved label with no record of what was resolved is a decision nobody can audit."""
    table = alloy_class_table(hydride)

    assert len(table) == COMPOSITIONS
    assert list(table.columns) == ["Alloy_class", "labels", "rows", "conflicted"]
    assert int(table["rows"].sum()) == len(hydride)
    assert table.loc["Mg0.6667Ni0.3333", "labels"] == "A2B, Mg"
    assert int(table.loc["Mg0.6667Ni0.3333", "rows"]) == 4


def test_precedence_covers_the_declared_vocabulary_exactly() -> None:
    """A class outside the order would fail on the row that carried it, not before."""
    assert set(ALLOY_CLASS_PRECEDENCE) == set(HYDRIDE_ALLOY_CLASSES)
    assert len(ALLOY_CLASS_PRECEDENCE) == len(HYDRIDE_ALLOY_CLASSES)


@pytest.mark.parametrize(
    ("labels", "winner"),
    [
        (["AB2"], "AB2"),
        (["Mg", "A2B"], "A2B"),
        (["MIC", "AB2"], "AB2"),
        (["LEA", "Mg"], "Mg"),
        (["MEA", "AB2"], "AB2"),
        (["SS", "MIC"], "SS"),
        (["Mg", "Mg", "Mg", "A2B"], "A2B"),
    ],
)
def test_precedence_prefers_the_more_specific_structural_claim(
    labels: list[str], winner: str
) -> None:
    """The last case is the one a majority vote gets wrong: Mg2Ni, three rows to one."""
    assert reconcile_class(labels) == winner


def test_an_unknown_class_is_refused() -> None:
    """An eleventh class changes the fold structure of AC-6 and is a human decision."""
    with pytest.raises(CanonicalisationError, match="not one of the 10 classes"):
        reconcile_class(["AB2", "AB2(C14)"])

    with pytest.raises(CanonicalisationError, match="no labels"):
        reconcile_class([])


def test_a_missing_class_is_refused_rather_than_guessed(hydride: pd.DataFrame) -> None:
    """Labelling an unlabelled row UNKNOWN is card #12's decision, not this module's."""
    damaged = hydride.copy(deep=True)
    damaged.loc[damaged.index[3], "Alloy_class"] = None

    with pytest.raises(CanonicalisationError, match="1 row\\(s\\) have no 'Alloy_class'"):
        alloy_class_table(damaged)


def test_keying_a_frame_without_a_formula_column_is_refused(hydride: pd.DataFrame) -> None:
    with pytest.raises(CanonicalisationError, match="no column 'Dataset '"):
        group_keys(hydride, "Dataset ")


def test_a_frame_with_an_unkeyable_row_names_the_row(hydride: pd.DataFrame) -> None:
    """Named, not counted: hunting one bad formula through 1279 rows costs an hour."""
    damaged = hydride.copy(deep=True)
    damaged.loc[damaged.index[7], "Composition"] = "Xx2"

    with pytest.raises(CanonicalisationError, match="1 of 1279 row"):
        group_keys(damaged)


# --------------------------------------------------------------------------------------
# The second vocabulary
# --------------------------------------------------------------------------------------


def test_the_two_class_vocabularies_are_not_nested() -> None:
    """Neither file's class set contains the other's, so a re-join needs a stated mapping."""
    curated, upstream = set(HYDRIDE_ALLOY_CLASSES), set(ML_HYDPARK_MATERIAL_CLASSES)

    assert not upstream <= curated, "ML-HydPARK splits AB2 into its two Laves polytypes"
    assert not curated <= upstream, "the curated file adds the HEA/LEA/MEA families"
    assert curated - upstream == {"HEA", "LEA", "MEA"}
    assert upstream - curated == {"AB2(C14)", "AB2(C15)"}


def test_the_alias_map_folds_ml_hydpark_into_the_curated_vocabulary() -> None:
    translated = {ML_HYDPARK_CLASS_ALIASES.get(name, name) for name in ML_HYDPARK_MATERIAL_CLASSES}
    assert translated <= set(ALLOY_CLASS_PRECEDENCE)
    assert ML_HYDPARK_CLASS_ALIASES == {"AB2(C14)": "AB2", "AB2(C15)": "AB2"}


def test_the_two_sources_disagree_often_enough_that_a_casual_join_would_relabel(
    hydride: pd.DataFrame,
) -> None:
    """378 canonical keys are shared; 30 of the 377 that carry both labels disagree.

    That is the measurement behind "a stated mapping, not a merge". Nothing consumes the
    upstream class -- `Alloy_class` is complete on all 1279 curated rows -- and this is the
    number that says why joining it in casually would be a mistake: one composition in
    twelve would change family, and with it which fold holds it out.
    """
    park = load_ml_hydpark().dropna(subset=["Material_Class"])
    upstream = alloy_class_table(
        park,
        formula_column="Composition_Formula",
        class_column="Material_Class",
        aliases=ML_HYDPARK_CLASS_ALIASES,
    )
    curated = alloy_class_table(hydride)

    shared = curated.index.intersection(upstream.index)
    assert len(shared) == 377

    disagreeing = [
        key
        for key in shared
        if not set(curated.loc[key, "labels"].split(", "))
        & set(upstream.loc[key, "labels"].split(", "))
    ]
    assert len(disagreeing) == 30
