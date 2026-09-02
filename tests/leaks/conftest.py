"""The HG-1 sentinel suite: one test per named leak.

Every test under this directory is marked ``leak`` automatically. Doing it here rather than by
hand on each function is not tidiness -- ``conda run -n Project python -m pytest -m leak`` is
how ``docs/QA-PROTOCOL.md`` section 6 and gate HG-1 select this suite, and a sentinel that
someone forgot to decorate would be silently deselected from the one run that exists to find
it. The marker is declared in ``pyproject.toml`` and ``--strict-markers`` is on, so a typo in
the name is a collection error rather than a quiet miss.

What each sentinel must show, from ``docs/QA-PROTOCOL.md`` section 1:

  - it goes **red** when its leak is deliberately reintroduced, and
  - it goes **green** on the corrected version of the same thing, differing in as little as
    possible -- otherwise it passes for the wrong reason.

Both halves live in ``hydms/qa/sentinels.py`` as :class:`~hydms.qa.sentinels.Reproduction`
pairs, so gate HG-1 can run them without running pytest. The files here exercise the same
detectors more widely: the edge cases, the failure messages, and the two properties that only
make sense side by side -- see ``test_l7_l8_grouping.py``, where the archival assertion passing
is itself the finding.

Card #71.
"""

from __future__ import annotations

from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark everything collected from this directory as a leak sentinel."""
    for item in items:
        path = getattr(item, "path", None)
        if path is not None and HERE in Path(path).resolve().parents:
            item.add_marker(pytest.mark.leak)
