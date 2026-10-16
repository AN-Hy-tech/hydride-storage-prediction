"""Card #7 — the promoted model reaches a fresh clone, through git and Git LFS.

Two sockets have to agree with the store's plug, and neither is Python, so nothing else checks
them. ``.gitignore`` decides which of the files the store writes reach git at all, and
``.gitattributes`` decides which of those go through LFS. Every file name below is read from the
module that writes it, so a rename in the store turns this file red instead of quietly sending
a new file nowhere.

The second half reads what is actually committed. It skips while nothing under ``artifacts/`` is
tracked yet, and from the first commit of a version on it holds that commit to three rules: the
pointer names a version that is committed whole, every payload is an LFS pointer rather than a
raw pickle (the failure a machine without ``git lfs install`` produces silently), and the JSON is
plain text.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from hydms.artifacts.store import (
    _LFS_POINTER_HEADS,
    _SUFFIX,
    CURRENT_POINTER,
    MANIFEST_NAME,
    read_manifest,
    staging_name,
)
from hydms.gates.__main__ import REPORT_NAME

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE = "artifacts"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or not (REPO_ROOT / ".git").exists(),
    reason="these rules are git's; there is no git work tree here",
)


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, check=check
    )


def _ignored(path: str) -> bool:
    # --no-index: judge the rule, not whether some file happens to be tracked already.
    result = _git("check-ignore", "--no-index", "-q", path, check=False)
    assert result.returncode in (0, 1), result.stderr.decode()
    return result.returncode == 0


def _filter(path: str) -> str:
    line = _git("check-attr", "filter", "--", path).stdout.decode().strip()
    return line.rsplit(": ", 1)[-1]


# --------------------------------------------------------------------------------------
# The rules, checked against the names the store writes
# --------------------------------------------------------------------------------------


def test_the_rules_below_are_written_for_the_configured_store() -> None:
    from hydms.config import load

    assert load().paths.artifacts == REPO_ROOT / STORE, (
        "paths.artifacts moved; .gitignore and .gitattributes still route `artifacts/`"
    )


@pytest.mark.parametrize(
    ("path", "tracked", "lfs"),
    [
        (f"{STORE}/{CURRENT_POINTER}", True, False),
        (f"{STORE}/v3/{MANIFEST_NAME}", True, False),
        (f"{STORE}/v3/model{_SUFFIX}", True, True),
        (f"{STORE}/v12/scaler{_SUFFIX}", True, True),
        (f"{STORE}/{REPORT_NAME}", False, False),
        (f"{STORE}/{staging_name('v4')}/model{_SUFFIX}", False, False),
        (f"{STORE}/scratch.txt", False, False),
    ],
    ids=["pointer", "manifest", "payload", "two-digit-version", "gate-report", "staging", "other"],
)
def test_each_file_the_store_writes_is_routed_once(path: str, tracked: bool, lfs: bool) -> None:
    assert _ignored(path) is not tracked
    if tracked:
        assert (_filter(path) == "lfs") is lfs


# --------------------------------------------------------------------------------------
# What is committed
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def committed() -> set[str]:
    files = set(_git("ls-files", "--", STORE).stdout.decode().split())
    if not files:
        pytest.skip("nothing under artifacts/ is committed yet")
    return files


def _blob(path: str) -> bytes:
    """The bytes git stores for ``path``: after LFS's clean filter, before its smudge."""
    return _git("cat-file", "blob", f":{path}").stdout


def test_every_committed_payload_is_an_lfs_pointer(committed: set[str]) -> None:
    raw = sorted(
        path
        for path in committed
        if path.endswith(_SUFFIX) and not _blob(path).startswith(_LFS_POINTER_HEADS)
    )
    assert not raw, (
        f"committed as raw bytes, not through LFS: {raw}. The committing machine had no "
        f"`git lfs install`; run it, then `git rm --cached` and re-add these files."
    )


def test_the_json_is_committed_as_plain_text(committed: set[str]) -> None:
    for path in sorted(p for p in committed if p.endswith(".json")):
        json.loads(_blob(path))


def test_the_committed_pointer_names_a_version_committed_whole(committed: set[str]) -> None:
    pointer = f"{STORE}/{CURRENT_POINTER}"
    if pointer not in committed:
        pytest.skip("versions are committed but none is promoted")
    version = json.loads(_blob(pointer))["version"]
    manifest = f"{STORE}/{version}/{MANIFEST_NAME}"
    assert manifest in committed, f"current.json points at {version}, which is not committed"

    recorded = read_manifest(REPO_ROOT / STORE / version)
    missing = sorted(
        f"{STORE}/{version}/{record.file}"
        for record in recorded.payloads
        if f"{STORE}/{version}/{record.file}" not in committed
    )
    assert not missing, f"{version}'s manifest records payloads that are not committed: {missing}"
