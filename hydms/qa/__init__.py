"""L0 -- the leak sentinels: the guarantee that a leak this phase removed stays removed.

Removing the thirteen leaks catalogued in ``docs/PHASE-H-RUNBOOK.md`` section 1 is stages S2
to S4. *Keeping* them removed is this package, and it is what makes Phase H durable rather
than a one-time cleanup: without it, nothing stops a later session reintroducing the exact
defect the phase spent forty days eliminating.

Three files, three kinds of knowledge:

``leaks.py``
    The thirteen leaks as data -- id, site, effect, the card that closes each. The runbook is
    the authority on what a leak *is*; this is the copy a gate can count.

``detectors.py``
    Eight assertions about what a stage did to its data, raising
    :class:`~hydms.qa.detectors.LeakDetected` with the offenders named. These are not test
    helpers: card #10's merge, card #13's split and card #26's fit are each meant to call the
    relevant one directly, so the sentinel then tests the real guard rather than a copy of it.

``sentinels.py``
    One sentinel per leak, each carrying the counterexample that gives it meaning -- a leaky
    case that must go red and a corrected twin that must not. :func:`~hydms.qa.sentinels.audit`
    runs them all, which is how gate HG-1 proves the sentinels can still fail without anyone
    having to remember doing it by hand.

Usage::

    from hydms.qa import audit

    for row in audit():
        print(row.leak, row.status, row.detail)

The sentinel suite is ``tests/leaks/``, marked ``leak`` and selectable with
``pytest -m leak``. The gate that reads the audit is ``hydms/gates/hg1_leak_sentinels.py``.

Card #71.
"""

from .detectors import (
    LeakDetected,
    SelectionRecord,
    assert_disjoint_groups,
    assert_early_stopping_is_honest,
    assert_explanation_is_not_held_out,
    assert_holdout_unchanged,
    assert_merge_is_keyed,
    assert_metadata_survives,
    assert_selection_ignores_holdout,
    assert_selection_is_nested,
    assert_weights_ignore_target,
)
from .leaks import INVENTORY, Leak, by_id
from .sentinels import (
    DEFERRED,
    RED,
    SENTINELS,
    Deferral,
    Reproduction,
    Sentinel,
    SentinelReport,
    audit,
    for_leak,
)

__all__ = [
    "DEFERRED",
    "INVENTORY",
    "RED",
    "SENTINELS",
    "Deferral",
    "Leak",
    "LeakDetected",
    "Reproduction",
    "SelectionRecord",
    "Sentinel",
    "SentinelReport",
    "assert_disjoint_groups",
    "assert_early_stopping_is_honest",
    "assert_explanation_is_not_held_out",
    "assert_holdout_unchanged",
    "assert_merge_is_keyed",
    "assert_metadata_survives",
    "assert_selection_ignores_holdout",
    "assert_selection_is_nested",
    "assert_weights_ignore_target",
    "audit",
    "by_id",
    "for_leak",
]
