"""Repository integrity checks that run without the project environment.

What this promises, and therefore what a green run means:

  - Every kanban card parses, carries a unique id matching its filename prefix, and
    declares a legal status.
  - Every id in a `blocked_by` list refers to a card that exists.
  - The dependency graph is acyclic — a cycle silently deadlocks the board, because
    every card in it waits forever and nothing reports why.
  - No card sits in `doing` or `done` while one of its blockers is unfinished.
  - Every relative Markdown link in the prose set resolves to a real file or directory.

Deliberately stdlib-only and dependency-free: this is the check that must still run when
the conda environment is broken, unbuilt, or absent — which, until the environment card
lands, is every fresh clone. It is the seed of the CI fast lane, not a replacement for
it; the acceptance-criteria gates arrive later and plug in beside these.

Usage:  python scripts/check_board.py [--root .]
Exits non-zero and lists every violation found. Finding none prints a one-line summary.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LEGAL_STATUSES = {"backlog", "todo", "doing", "done"}
STARTED_STATUSES = {"doing", "done"}

# Prose whose links are checked. Machine_Model/ is excluded on purpose: it is the frozen
# archival record behind REPORT.md, and is not maintained.
LINKED_PROSE = ("README.md", "CLAUDE.md", "docs", "kanban", "research")

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
EXTERNAL = ("http://", "https://", "mailto:", "#")
LIST_VALUE = re.compile(r"^\[(.*)\]$")


class Card:
    """One kanban card: the frontmatter fields the board's rules are expressed in."""

    def __init__(self, path: Path, fields: dict[str, str]):
        self.path = path
        self.fields = fields
        self.id = _int_or_none(fields.get("id"))
        self.status = (fields.get("status") or "").strip().strip('"')
        self.blocked_by = _int_list(fields.get("blocked_by", "[]"))
        self.tags = _str_list(fields.get("tags", "[]"))


def _int_or_none(raw: str | None) -> int | None:
    try:
        return int((raw or "").strip())
    except ValueError:
        return None


def _split_list(raw: str) -> list[str]:
    match = LIST_VALUE.match((raw or "").strip())
    if not match:
        return []
    return [item.strip().strip('"').strip("'") for item in match.group(1).split(",") if item.strip()]


def _int_list(raw: str) -> list[int]:
    out = []
    for item in _split_list(raw):
        try:
            out.append(int(item))
        except ValueError:
            pass
    return out


def _str_list(raw: str) -> list[str]:
    return _split_list(raw)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return the `key: value` block between the leading `---` fences, or None if absent.

    A hand-rolled reader rather than a YAML dependency: the frontmatter is a flat map of
    scalars and inline lists, and requiring PyYAML would defeat the point of a check that
    runs before any environment exists.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return None


def load_cards(kanban: Path) -> tuple[list[Card], list[str]]:
    problems: list[str] = []
    cards: list[Card] = []
    for path in sorted(kanban.rglob("*.md")):
        if path.name == "README.md":
            continue
        fields = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fields is None:
            problems.append(f"{_rel(path)}: no frontmatter block")
            continue
        cards.append(Card(path, fields))
    return cards, problems


def check_cards(cards: list[Card]) -> list[str]:
    problems: list[str] = []
    seen: dict[int, Path] = {}

    for card in cards:
        name = _rel(card.path)
        if card.id is None:
            problems.append(f"{name}: frontmatter `id` missing or not an integer")
            continue
        if card.id in seen:
            problems.append(f"{name}: duplicate id {card.id}, already used by {_rel(seen[card.id])}")
        seen[card.id] = card.path

        prefix = _int_or_none(card.path.name.split("-")[0])
        if prefix != card.id:
            problems.append(f"{name}: filename prefix {prefix} does not match frontmatter id {card.id}")

        if card.status not in LEGAL_STATUSES:
            legal = ", ".join(sorted(LEGAL_STATUSES))
            problems.append(f"{name}: status {card.status!r} is not one of: {legal}")

    known = set(seen)
    by_id = {c.id: c for c in cards if c.id is not None}

    for card in cards:
        if card.id is None:
            continue
        name = _rel(card.path)
        for blocker in card.blocked_by:
            if blocker not in known:
                problems.append(f"{name}: blocked_by references card {blocker}, which does not exist")
            elif card.status in STARTED_STATUSES and by_id[blocker].status != "done":
                problems.append(
                    f"{name}: status is {card.status!r} but blocker {blocker} "
                    f"is {by_id[blocker].status!r}, not done"
                )
    return problems


def check_cycles(cards: list[Card]) -> list[str]:
    """Report each dependency cycle once, as the path that closes it."""
    graph = {c.id: [b for b in c.blocked_by] for c in cards if c.id is not None}
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in graph}
    problems: list[str] = []

    def walk(node: int, trail: list[int]) -> None:
        colour[node] = GREY
        for nxt in graph.get(node, []):
            if nxt not in colour:
                continue
            if colour[nxt] == GREY:
                loop = trail[trail.index(nxt):] + [nxt]
                problems.append("dependency cycle: " + " -> ".join(str(n) for n in loop))
            elif colour[nxt] == WHITE:
                walk(nxt, trail + [nxt])
        colour[node] = BLACK

    for node in sorted(graph):
        if colour[node] == WHITE:
            walk(node, [node])
    return problems


def check_links(root: Path) -> list[str]:
    problems: list[str] = []
    for entry in LINKED_PROSE:
        target = root / entry
        files = [target] if target.is_file() else sorted(target.rglob("*.md")) if target.is_dir() else []
        for path in files:
            for link in LINK.findall(path.read_text(encoding="utf-8")):
                if link.startswith(EXTERNAL):
                    continue
                bare = link.split("#", 1)[0]
                if not bare:
                    continue
                if not (path.parent / bare).exists():
                    problems.append(f"{_rel(path)}: link target does not exist -> {link}")
    return problems


_ROOT = Path.cwd()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main() -> int:
    global _ROOT
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    _ROOT = root
    kanban = root / "kanban"
    if not kanban.is_dir():
        print(f"FAIL  no kanban/ directory under {root}")
        return 1

    cards, problems = load_cards(kanban)
    problems += check_cards(cards)
    problems += check_cycles(cards)
    problems += check_links(root)

    if problems:
        print(f"FAIL  {len(problems)} problem(s) in {len(cards)} cards:\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"OK    {len(cards)} cards: ids unique, blockers resolve, graph acyclic, links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
