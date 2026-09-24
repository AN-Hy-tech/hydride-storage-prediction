"""``docs/REPORT-RECONCILIATION.md``: generated, quoted faithfully, and measured rather than typed.

Card #89. Three properties, each one a way a hand-written evidence table goes wrong silently:
the page drifts from the code (the byte test), a quotation drifts from ``REPORT.md`` (the
verbatim test), and a value is typed in rather than read (the perturbation test, which changes
a committed CSV in a copy of the tree and demands that the page follow it).
"""

from __future__ import annotations

import io
import shutil
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the reconciliation reads committed CSVs")

import pandas as pd  # noqa: E402
from hydms.config import repo_root  # noqa: E402
from hydms.evidence import reconciliation  # noqa: E402
from hydms.evidence.reconciliation import (  # noqa: E402
    DISAGREEMENTS,
    DOCUMENT,
    document,
    emit,
    main,
)

ROOT = repo_root()


@pytest.fixture(scope="module")
def page() -> str:
    return document()


def test_the_committed_page_is_what_the_code_produces(page: str) -> None:
    assert DOCUMENT.is_file(), (
        f"{DOCUMENT} is missing. Publish it with `python -m hydms.evidence.reconciliation --emit`."
    )
    assert DOCUMENT.read_text(encoding="utf-8") == page, (
        "docs/REPORT-RECONCILIATION.md is stale or hand-edited. Regenerate it with "
        "`python -m hydms.evidence.reconciliation --emit`."
    )


def test_emit_writes_the_same_bytes_somewhere_else(tmp_path: Path, page: str) -> None:
    written = emit(tmp_path / "REPORT-RECONCILIATION.md")

    assert written.read_bytes() == page.encode("utf-8")


@pytest.mark.parametrize("item", DISAGREEMENTS, ids=lambda item: item.key)
def test_every_quotation_occurs_in_report_md_verbatim(item: reconciliation.Disagreement) -> None:
    report = (ROOT / reconciliation.REPORT).read_text(encoding="utf-8")

    assert item.claim in report, f"{item.key}: REPORT.md does not say {item.claim!r}"


@pytest.mark.parametrize("item", DISAGREEMENTS, ids=lambda item: item.key)
def test_every_cited_artifact_is_in_the_repository(item: reconciliation.Disagreement) -> None:
    assert (ROOT / item.artifact).is_file(), item.artifact


def test_every_row_has_its_own_key() -> None:
    keys = [item.key for item in DISAGREEMENTS]

    assert len(keys) == len(set(keys))


def _copy(tmp_path: Path) -> Path:
    """Every file the page reads, copied under a fresh root with the same relative paths."""
    paths = {item.artifact for item in DISAGREEMENTS if item.artifact.endswith(".csv")}
    paths |= {
        reconciliation._IMPROVED,
        reconciliation._EVALUATION,
        reconciliation._LOCO,
        reconciliation._RAW,
    }
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return tmp_path


def test_a_value_on_the_page_moves_when_its_csv_moves(tmp_path: Path, page: str) -> None:
    """The perturbation: if a number were typed in, changing the file would not change the page."""
    root = _copy(tmp_path)
    stacked = root / reconciliation._STACKING
    frame = pd.read_csv(stacked)
    frame.loc[0, "Val_R2_Orig"] = 0.123456
    frame.to_csv(stacked, index=False)

    moved = document(root)

    assert "Val R² 0.377" in page
    assert "Val R² 0.123" in moved and "Val R² 0.377" not in moved


def test_the_page_built_from_a_faithful_copy_is_the_committed_page(
    tmp_path: Path, page: str
) -> None:
    """The copy above is complete: every file the page reads was copied, none read from ROOT."""
    assert document(_copy(tmp_path)) == page


def test_the_unique_compositions_example_is_one_material() -> None:
    """Row 11 says `La1Ni5` and `LaNi5` are one alloy; the canonical key must agree."""
    from hydms.data.canonical import group_keys

    keys = group_keys(pd.DataFrame({"Composition": ["La1Ni5", "LaNi5"]}))

    assert keys.iloc[0] == keys.iloc[1]


def test_the_command_prints_the_page_without_writing(page: str) -> None:
    out = io.StringIO()

    assert main([], out=out) == 0
    assert out.getvalue() == page + "\n"
