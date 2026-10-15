"""The thirteen named leaks, as data.

``docs/PHASE-H-RUNBOOK.md`` section 1 is the authority on what each leak *is*; this module is
the machine-readable copy that gate HG-1 counts against, and ``tests/leaks/test_inventory.py``
fails if the two disagree on the set of ids or on where a leak lives. The prose stays the
place you go to understand a leak; this stays the place that notices one has no sentinel.

**Why an inventory at all, rather than just a directory of tests.** HG-1's failure condition
is not "the sentinels are red" -- it is "a leak in section 1 could be reintroduced without a
test going red". That is a statement about *coverage*, and coverage cannot be measured against
a list nobody wrote down. Thirteen entries here and ten sentinels in ``sentinels.py`` is a
three-leak gap that the gate reports out loud, every run, naming the card that owes each one.

Card #71.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["INVENTORY", "Leak", "by_id"]


@dataclass(frozen=True)
class Leak:
    """One row of the runbook's leak inventory.

    Attributes:
        id: ``"L1"`` .. ``"L13"``. The addressing scheme every card, sentinel and narrative
            note uses.
        site: Where it lived in the removed archival pipeline, as ``file.py:lines``;
            readable at commit ``4348f6ff96`` (card #107).
        effect: What it does to the reported numbers, in one line.
        stage: The runbook stage that removes it, or ``"--"`` for a leak no stage ports the
            code of.
        closed_by: The card whose landing removes it.
    """

    id: str
    site: str
    effect: str
    stage: str
    closed_by: int


# Ordered as the runbook orders them. `closed_by` is the card that removes the leak, which is
# not always the card that owns its sentinel -- L10 and L13 are the two where they differ. L13
# is the sharper case: card #87 gives `Alloy_class` a composition to be re-joined on and writes
# the sentinel, but the leak is the *drop* at `extract_features_cbfv.py:19-21`, and it is gone
# only once #12 carries the class through featurisation. So #12 is what `audit()` names when
# the sentinel's subject appears unwired.
INVENTORY: tuple[Leak, ...] = (
    Leak(
        id="L1",
        site="Catboostmodel.py:604-606",
        effect="the test set chooses the stopping iteration, then is reported as held out",
        stage="S4",
        closed_by=26,
    ),
    Leak(
        id="L2",
        site="benchmark_model_selection.py:335-336",
        effect="ensemble members chosen on validation; the headline Val R2 reported on that "
        "same set",
        stage="S4",
        closed_by=88,
    ),
    Leak(
        id="L3",
        site="CleanLab.py:90",
        effect="validation and test ground truth replaced by the model's own predictions",
        stage="S2",
        closed_by=14,
    ),
    Leak(
        id="L4",
        site="benchmark_model_selection.py:1156",
        effect="the same splits object tunes and then scores -- no nested cross-validation",
        stage="S4",
        closed_by=88,
    ),
    Leak(
        id="L5",
        site="Catboostmodel.py:576-582",
        effect="every cross-validation fold early-stops on the fold it is scored on",
        stage="S4",
        closed_by=26,
    ),
    Leak(
        id="L6",
        site="Boruta_FeatEng.py:57-113",
        effect="feature selection fitted on all 896 training rows before cross-validation",
        stage="S4",
        closed_by=24,
    ),
    Leak(
        id="L7",
        site="benchmark_model_selection.py:895",
        effect="row-level StratifiedKFold with no groups -- 141 of 896 rows share a formula "
        "across folds",
        stage="S4",
        closed_by=88,
    ),
    Leak(
        id="L8",
        site="split_data.py:48,55",
        effect="the split key is the raw formula string, so 16 compositions span two splits",
        stage="S2",
        closed_by=13,
    ),
    Leak(
        id="L9",
        site="merge_datasets.py:46",
        effect="positional concat after reset_index -- silent row misalignment",
        stage="S2",
        closed_by=10,
    ),
    Leak(
        id="L10",
        site="Ashghal/Outliers_Management.py:60-72",
        effect="clips validation and test feature values using their own residuals",
        stage="--",
        closed_by=14,
    ),
    Leak(
        id="L11",
        site="benchmark_model_selection.py:1375,1383,1394",
        effect="PDP and SHAP computed on X_test -- REPORT section 6.1 is a test-set artefact",
        stage="S4",
        closed_by=29,
    ),
    Leak(
        id="L12",
        site="Catboostmodel.py:516-518",
        effect="target-conditioned sample weights with a hand-tuned threshold",
        stage="S4",
        closed_by=26,
    ),
    Leak(
        id="L13",
        site="extract_features_cbfv.py:19-21",
        effect="every object column but Composition is dropped, destroying Alloy_class",
        stage="S2",
        closed_by=12,
    ),
)


def by_id(leak_id: str) -> Leak:
    """Look one leak up by its id.

    Raises:
        KeyError: No such leak. Loud on purpose: a sentinel registered against ``"L14"`` would
            otherwise guard nothing while looking like coverage.
    """
    for leak in INVENTORY:
        if leak.id == leak_id:
            return leak
    known = ", ".join(entry.id for entry in INVENTORY)
    raise KeyError(f"no leak named {leak_id!r}. The inventory holds: {known}")
