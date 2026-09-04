"""Fixtures shared by the harness tests and the CLI tests.

One fixture, and it exists because of a mistake worth not repeating. Both files used the
literal name ``AC-2`` wherever they needed "a criterion nobody has written yet" -- so landing
card #21, the first real gate, turned four tests about *strictness* into tests about
featuriser parity, and they failed for a reason none of them was about. The registry knows
which gates are still :class:`~hydms.gates.Pending`; asking it costs nothing and the question
stays the one the test is actually asking.

Card #5 wrote those tests; card #21 moved them onto this.
"""

from __future__ import annotations

import pytest
from hydms.gates import Gate, Pending, registry


@pytest.fixture(scope="session")
def unwritten() -> tuple[Gate, ...]:
    """Every registered criterion whose check has not been written yet.

    Asserted non-empty: when the phase finishes there will be none, and these tests must
    disappear loudly -- onto a stub gate -- rather than quietly passing over nothing, which is
    the exact failure the harness they test exists to prevent.
    """
    pending = tuple(g for g in registry() if isinstance(g, Pending))
    assert pending, (
        "every registered gate is implemented -- move the harness's strictness tests onto a "
        "stub gate rather than letting them run over an empty selection"
    )
    return pending
