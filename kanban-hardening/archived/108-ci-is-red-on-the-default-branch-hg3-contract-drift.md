---
id: 108
status: done
priority: P1
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l0]
---

# CI is red on the default branch: HG-3 contract drift (16 tests)

## Narrative

- 2026-10-15: Found while pushing an unrelated README/kanban-only commit (04c13ad) — no Python or
  `openapi.json` touched, so this is pre-existing, not caused by that push. `Suite — pytest and the
  fast gates` fails 16 of 1,805 tests, all in `tests/gates/test_hg3_transport_parity.py` and
  `tests/delivery/test_openapi.py`: the committed `openapi.json` has discriminator-mapping keys
  `"True"`/`"False"` (Python bool repr) while the code now produces the spec-correct lowercase
  `"true"`/`"false"`, an 8-value drift HG-3 is doing exactly its job catching. Likely a dependency
  bump (FastAPI/Pydantic) changed how discriminator mapping keys serialize since `openapi.json` was
  last committed. Since this branch is now the GitHub default, **the repo's front door is showing
  red CI to anyone who looks.** Fix is probably mechanical — `python -m hydms.delivery.api.openapi
  --emit` and commit the regenerated contract, per the gate's own error message — but verify the
  lowercase form is actually correct before committing it, not just the one that makes the diff go
  away. Hygiene (board, freeze, ruff, mypy) is unaffected and still green. (by @assistant)
- 2026-10-15: Closed. Root cause was not the snapshot but the lane: `suite` installed
  `-e ".[dev,uq,novelty,api,figures]"` with no constraints, so pip resolved pyproject's floors to
  the newest releases (pydantic 2.14.1, FastAPI 0.143.2) while `requirements-lock.txt` pins
  pydantic 2.12.5 / FastAPI 0.115.0. pydantic 2.14 writes boolean discriminator keys as JSON
  (`true`/`false`), 2.12.5 as Python reprs. Re-emitting the snapshot would have turned the machine
  lane red instead. Fix: `ci.yml` installs with `-c requirements-lock.txt`, so every package the lane
  installs is held to its lock version (Windows-only lock entries are inert as constraints); the
  lock file joins the pip cache key. `openapi.json` is unchanged, as `openapi.py`'s docstring
  already intended ("the pins in requirements-lock.txt are what stop it moving"). The lowercase
  form is the spec-correct one, so adopting it is a deliberate lock bump plus `--emit` in one
  commit, not a CI side effect. Verified on Linux, Python 3.10, pip with the constraints: the
  fast lane had no failures apart from four `tests/gates/test_cli.py` cases, which failed only
  because the sandbox's newer ruff/mypy came first on PATH; with the pinned 0.8.4/1.13.0 first,
  `test_cli.py`, `test_hg3_transport_parity.py` and `test_openapi.py` passed 49/49. Coverage 89.43%.
  ruff, mypy, check_board and check_freeze are green. (by @assistant)
