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
- 2026-10-15: Done. Root cause: CI installs from `pyproject.toml` ranges, not the lock, and got
  Pydantic 2.14.1 (the lock pinned 2.12.5). Verified the lowercase form is the correct one, not
  just the one that clears the diff: a minimal `Literal[True]`/`Literal[False]` discriminated
  union, run under both versions, dumps `{"refused":true}` on the wire under each, and only 2.14
  maps the key `"true"` to it — 2.12's `"True"` could never match a real payload. Regenerated
  `openapi.json` under CI's versions (4 keys change, nothing else), raised the api extra to
  `pydantic>=2.14` so an older install cannot write the old keys back, and moved the lock's
  pydantic/pydantic-core to the 2.14.1/2.50.1 pair CI ran. **The `Project` conda env still has
  2.12.5:** run `pip install pydantic==2.14.1 pydantic-core==2.50.1` in it, or HG-3 fails
  locally. (by @assistant)
