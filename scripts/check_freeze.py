"""Enforce the Phase H implementation freeze against a pull request's diff.

The freeze is declared in `docs/FREEZE.md`. While its frontmatter says `freeze: in-force`,
a change may not touch the frozen inverse-design programme. This check is what makes that
a build failure rather than a thing the next session has to remember.

What counts as a violation, and what deliberately does not:

  - Editing, adding or deleting a *card* on the frozen board is a violation.
  - **Renaming a card out of `kanban/` into `kanban-hardening/` is not** — that is the
    migration this phase is built on, and forbidding it would make the freeze unable to
    establish itself.
  - `kanban/README.md` is board metadata, not a card, and stays editable: the freeze has
    to be able to say so on the board it freezes.
  - Moving a card off `backlog` is caught by `check_board.py`, not here. This check reads
    the diff; that one reads the board.

Deliberately stdlib-only and dependency-free, for the same reason as `check_board.py`:
it must run on a bare `setup-python` with no environment built.

Usage:  python scripts/check_freeze.py [--base origin/main] [--root .]
Exits non-zero and lists every violation found.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CARD = re.compile(r"^\d{3}-.*\.md$")

# Paths the freeze protects. A changed path is a violation if it is under one of these,
# unless an exemption below applies.
DENIED = (
    "kanban/",
    "docs/PRD-inverse-design.md",
    "research/",
)

WHY = {
    "kanban/": "the frozen board — no card may be added, edited or deleted",
    "docs/PRD-inverse-design.md": "the frozen programme's specification",
    "research/": "new memos are research effort spent outside the phase",
}


def freeze_in_force(root: Path) -> bool:
    charter = root / "docs" / "FREEZE.md"
    if not charter.is_file():
        return False
    for line in charter.read_text(encoding="utf-8").splitlines()[:12]:
        key, sep, value = line.partition(":")
        if sep and key.strip() == "freeze":
            return value.strip().strip('"') == "in-force"
    return False


def _git(root: Path, *args: str) -> tuple[int, str]:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return done.returncode, done.stdout


def changed_paths(root: Path, base: str) -> tuple[list[tuple[str, str, str]], str]:
    """Return (status, path, destination) triples and a one-line description of the mode used.

    Rename detection is on (-M): a rename arrives as ('R', old, new), which is what lets a
    card migrate out of the frozen board without tripping the check.
    """
    code, out = _git(root, "diff", "--name-status", "-M", f"{base}...HEAD")
    mode = f"diff against {base}...HEAD"
    if code != 0:
        code, out = _git(root, "diff", "--name-status", "-M", "HEAD")
        mode = "working tree against HEAD (base ref unavailable)"
    if code != 0:
        return [], "no diff available"

    entries: list[tuple[str, str, str]] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            entries.append((parts[0].strip(), parts[1].strip(), ""))
        elif len(parts) >= 3:
            entries.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return entries, mode


def exempt(status: str, path: str, dest: str) -> str | None:
    """Return the reason this changed path is allowed, or None if it must be judged."""
    if path == "kanban/README.md":
        return "board metadata, not a card"

    # A card leaving the frozen board for the hardening board is the migration itself.
    if status.startswith("R") and path.startswith("kanban/") and dest.startswith("kanban-hardening/"):
        return f"migrated to the hardening board -> {dest}"

    # The same move recorded as a plain delete (rename detection misses it when the card
    # was also renamed, or its content changed too much). Judged below: it needs the
    # filesystem, and it matches on the card **id**, not the filename — a migrated card is
    # free to be renamed, and #24 was.
    return None


def check(root: Path, entries: list[tuple[str, str, str]]) -> list[str]:
    problems: list[str] = []
    for status, path, dest in entries:
        rule = next((d for d in DENIED if path == d or path.startswith(d)), None)
        if rule is None:
            continue

        reason = exempt(status, path, dest)
        if reason:
            continue

        name = path.rsplit("/", 1)[-1]
        if status == "D" and path.startswith("kanban/") and CARD.match(name):
            # Match on the id prefix, not the filename: a card may be renamed as it moves.
            if list((root / "kanban-hardening").rglob(f"{name[:3]}-*.md")):
                continue  # the card moved boards; that is the migration
            problems.append(f"{path}: card deleted from the frozen board, not migrated")
            continue

        problems.append(f"{path}: {WHY.get(rule, 'frozen')} [{status}]")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="origin/main", help="base ref to diff against")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if not freeze_in_force(root):
        print("OK    no freeze in force (docs/FREEZE.md absent or lifted).")
        return 0

    entries, mode = changed_paths(root, args.base)
    problems = check(root, entries)

    if problems:
        print(f"FAIL  freeze violated by {len(problems)} path(s) [{mode}]:\n")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\n  The freeze protects these three paths and nothing else, and the reason for "
            "each\n  is the denied-paths table in docs/FREEZE.md. It is a deny-list: every "
            "other path\n  in the repository is editable, and DENIED is short on purpose "
            "(card #72)."
        )
        return 1

    print(f"OK    freeze respected across {len(entries)} changed path(s) [{mode}].")
    return 0


if __name__ == "__main__":
    sys.exit(main())
