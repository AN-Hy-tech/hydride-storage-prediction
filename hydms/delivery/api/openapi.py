"""The published contract as a file, and the comparator that says when it moved.

    python -m hydms.delivery.api.openapi          # is the committed document current?
    python -m hydms.delivery.api.openapi --emit   # rewrite it

The OpenAPI document is the only thing a client author reads. It is generated from the route
declarations and the models in :mod:`hydms.delivery.api.schemas`, which means it changes as a
side effect of editing code -- a field renamed, a response model narrowed, a status code
dropped from ``responses`` -- and nothing about that edit looks like a contract change in a
diff. So the document is **committed**, beside the package that produces it, and gate HG-3
fails while the two disagree. A breaking change is then a visible diff that somebody approved,
rather than a surprise for whoever wrote the client.

It is generated, never edited. ``--emit`` rewrites it and a test asserts the committed bytes
are what that command produces; an edit here fails the suite and is the exact drift the file
exists to prevent.

**What the snapshot is a snapshot of.** :func:`document` builds a *fresh* application with
:func:`~hydms.delivery.api.service.create_app`'s defaults and asks it for its document, so the
file describes the deployment the project ships rather than whatever the importing process
happened to configure. Nothing is loaded: the document is a function of the code, so the
comparison runs in a checkout with no artifact on disk -- which is the half of HG-3 that can go
red on a push.

**A dependency upgrade can move it, and that is not a false alarm.** FastAPI and pydantic
generate this document; a version bump that changes it changes what a client reads, so it is a
contract change whoever ran the upgrade should see and approve. The pins in
``requirements-lock.txt`` are what stop it moving on its own.

Card #79.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

__all__ = [
    "SNAPSHOT_FILE",
    "committed",
    "differences",
    "document",
    "drift",
    "emit",
    "serialise",
]

#: The committed document, beside the package that produces it. Ships as package data, for the
#: same reason ``screens/domain-reference.json`` does: the gate must be answerable in a
#: container that has an installed wheel and no repository around it.
SNAPSHOT_FILE = Path(__file__).with_name("openapi.json")

#: How much of a differing value a failure line shows. A diff that prints two 4 kB schema
#: objects in full is a diff nobody reads to the end.
_WIDTH = 90


def document() -> dict[str, Any]:
    """The OpenAPI document this package serves, built from a fresh default application.

    Fresh rather than :data:`hydms.delivery.api.app`: the snapshot describes the shipped
    deployment, and a process that had mutated the shared application would otherwise write
    its own configuration into the committed contract. Builds an application; loads nothing.
    """
    from .service import create_app

    return dict(create_app().openapi())


def serialise(doc: Mapping[str, Any]) -> str:
    """The document as the committed bytes: sorted keys, two-space indent, trailing newline.

    Sorted because a key order that depends on the order routes were declared in would turn
    every reordering into a contract diff, and the point of the snapshot is that a diff means
    something.
    """
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def committed() -> dict[str, Any]:
    """The document as it is committed on disk.

    Raises:
        FileNotFoundError: the snapshot is absent. A missing contract is a failure and never
            an absent check: write it with ``--emit`` and commit it.
    """
    loaded: dict[str, Any] = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    return loaded


def _leaves(node: Any, at: str = "") -> dict[str, Any]:
    """Every scalar in a JSON document, by JSON pointer.

    Flattened rather than compared structurally so a failure names the one path that moved --
    ``/paths/~1v1~1predict/post/responses/422`` -- instead of printing two documents and
    leaving the reader to find the difference.
    """
    if isinstance(node, dict) and node:
        found: dict[str, Any] = {}
        for key, value in node.items():
            found.update(_leaves(value, f"{at}/{_escaped(key)}"))
        return found
    if isinstance(node, list) and node:
        found = {}
        for position, value in enumerate(node):
            found.update(_leaves(value, f"{at}/{position}"))
        return found
    # An *empty* container is its own leaf. Recursing into it would emit nothing at all, and a
    # key whose value is `{}` or `[]` would then be invisible to the comparison -- so a response
    # model that dropped an empty `screens` list would compare equal to one that kept it. Found
    # by a test that expected the dropped key to be reported and got silence.
    return {at or "/": node}


def _escaped(key: object) -> str:
    """One JSON-pointer token: ``~`` and ``/`` are the two characters a pointer must escape."""
    return str(key).replace("~", "~0").replace("/", "~1")


def _shown(value: Any) -> str:
    text = repr(value)
    return text if len(text) <= _WIDTH else text[: _WIDTH - 3] + "..."


def differences(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    left_name: str = "committed",
    right_name: str = "produced",
) -> list[str]:
    """Every pointer at which two JSON documents disagree, as sentences.

    General over JSON rather than special to OpenAPI, and deliberately so: gate HG-3 compares a
    served answer against :meth:`~hydms.delivery.contract.PredictionResult.to_dict` with the
    same function, so "the interval's lower bound was truncated in transport" and "the response
    model dropped a field" are reported in one vocabulary and formatted in one place.

    Args:
        left: The document being checked against.
        right: The document under test.
        left_name: What to call ``left`` in the sentences -- 'committed', 'the library'.
        right_name: What to call ``right``.

    Returns:
        One line per differing pointer, sorted. Empty when the documents are equal, which is
        the only thing a caller should treat as agreement: two documents can serialise
        identically under a formatter that drops a key, and this compares values.
    """
    here = _leaves(dict(left))
    there = _leaves(dict(right))
    lines: list[str] = []
    for pointer in sorted(set(here) | set(there)):
        if pointer not in there:
            lines.append(f"{pointer}: in {left_name} ({_shown(here[pointer])}), absent from {right_name}")
        elif pointer not in here:
            lines.append(f"{pointer}: in {right_name} ({_shown(there[pointer])}), absent from {left_name}")
        elif here[pointer] != there[pointer]:
            lines.append(
                f"{pointer}: {left_name} {_shown(here[pointer])}, "
                f"{right_name} {_shown(there[pointer])}"
            )
    return lines


def drift() -> list[str]:
    """How the committed document differs from the one the code produces right now.

    Empty is the only passing state. Raises :class:`FileNotFoundError` if nothing is committed.
    """
    return differences(committed(), document())


def emit() -> Path:
    """Rewrite the committed document from the code. The whole of ``--emit``."""
    SNAPSHOT_FILE.write_text(serialise(document()), encoding="utf-8")
    return SNAPSHOT_FILE


def _summary(doc: Mapping[str, Any]) -> str:
    routes = sorted(
        f"{method.upper():6} {path}"
        for path, operations in dict(doc.get("paths", {})).items()
        for method in operations
    )
    schemas = sorted(dict(doc.get("components", {})).get("schemas", {}))
    return (
        f"{len(routes)} operation(s):\n"
        + "\n".join(f"  {route}" for route in routes)
        + f"\n{len(schemas)} declared schema(s): "
        + ", ".join(schemas)
    )


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    """``--emit`` rewrites the committed document; no argument reports whether it is current.

    Exit codes: 0 when the committed document is what the code produces, 1 when it is not or
    when nothing is committed. So this is runnable as a check on its own, and gate HG-3 is the
    same comparison with the phase's own reporting around it.
    """
    parser = argparse.ArgumentParser(
        prog="python -m hydms.delivery.api.openapi",
        description="The served OpenAPI document, and the committed snapshot of it.",
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help=f"rewrite {SNAPSHOT_FILE.name} from the code, and commit the diff deliberately",
    )
    args = parser.parse_args(argv)
    stream = out if out is not None else sys.stdout

    if args.emit:
        print(f"wrote {emit()}", file=stream)
        return 0

    print(_summary(document()), file=stream)
    try:
        moved = drift()
    except FileNotFoundError:
        print(
            f"\nno contract is committed at {SNAPSHOT_FILE}. Write it with --emit and commit "
            f"it: gate HG-3 has nothing to compare a served document against until you do.",
            file=stream,
        )
        return 1

    if moved:
        print(
            f"\nthe committed contract is {len(moved)} value(s) behind the code:\n"
            + "\n".join(f"  {line}" for line in moved[:20])
            + (f"\n  ... ({len(moved) - 20} more)" if len(moved) > 20 else "")
            + "\n\nIf every line above is a change you meant, run --emit and commit it. If "
            "any of them is not, the code moved the published contract by accident, which is "
            "what this file exists to catch.",
            file=stream,
        )
        return 1

    print(f"\nthe committed contract at {SNAPSHOT_FILE.name} is current.", file=stream)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
