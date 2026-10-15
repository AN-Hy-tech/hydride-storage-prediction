"""``python -m hydms.delivery.api`` -- run the service without remembering the uvicorn line.

Equivalent to ``uvicorn hydms.delivery.api:app``, which stays the documented command
(``docs/PHASE-H-RUNBOOK.md`` section 6 runs it that way). This exists so that the service can
be started the same way every other entry point in this package is -- ``python -m
hydms.gates``, ``python -m hydms.pipeline.smoke`` -- and it takes no options that would let a
deployment differ from the documented one in a way nothing records.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Serve the application. Returns non-zero if it could not start.

    The bundle is resolved by the application's own startup, so a store with nothing
    promoted in it fails here rather than at the first request -- with
    :func:`~hydms.delivery.predict.load_bundle`'s sentence, which names the fix.
    """
    parser = argparse.ArgumentParser(
        prog="python -m hydms.delivery.api",
        description="Serve the HydMS prediction API.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="default: 8000")
    args = parser.parse_args(argv)

    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn is not installed. It is the `api` extra: pip install -e '.[api]'.",
            file=sys.stderr,
        )
        return 2

    uvicorn.run("hydms.delivery.api:app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":  # pragma: no cover - the entry point itself
    raise SystemExit(main())
