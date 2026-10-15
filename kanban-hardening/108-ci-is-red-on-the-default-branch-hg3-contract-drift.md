---
id: 108
status: backlog
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
