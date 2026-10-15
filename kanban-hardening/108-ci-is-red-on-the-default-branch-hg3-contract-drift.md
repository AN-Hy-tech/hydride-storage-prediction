---
id: 108
status: doing
priority: P1
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l6, HG-3]
---

# CI is red on the default branch: HG-3 contract drift (16 tests)

**No stage** · **L6 Delivery** · Estimate: 0.25 d

> **Owns (hidden behind this module):** How a boolean discriminator value is spelled in the published OpenAPI document, whichever pydantic is installed.

**This card is NOT an unfreeze condition.**

## Why this exists

The `suite` lane installs what `pyproject.toml` declares, unpinned (`ci.yml` says why), so it
resolved pydantic 2.14.1 while `requirements-lock.txt` pins 2.12.5. Pydantic 2.14 writes a boolean
discriminator's `mapping` keys as `"true"`/`"false"`; 2.13.5 and earlier write `str(True)`,
`"True"`/`"False"`. The committed `openapi.json` was emitted under the pin, so HG-3 and
`test_openapi.py` went red in CI (16 tests) while staying green on the maintainer's machine. The
contract was a function of the installed library, not of the code.

Lowercase is the correct form: a client matches the key against the `refused` it received, which
is JSON `true`. `"True"` was Python leaking into the contract.

## Done when

- [x] `create_app()` serves a document whose boolean discriminator keys are `"true"`/`"false"`
      under pydantic 2.12.5 **and** 2.14.1 (`service._json_discriminator_keys`); a mapping holding
      both spellings of one value raises rather than merging silently.
- [x] `openapi.json` re-emitted; `python -m hydms.delivery.api.openapi` reports *current* under
      both versions. `docs/API.md` re-emitted, unchanged.
- [x] A test asserts the JSON spelling on whatever pydantic is installed.
- [ ] `Suite — pytest and the fast gates` green on the default branch after the push.

## Runnable check

```bash
python -m pytest -q tests/delivery/test_openapi.py tests/gates/test_hg3_transport_parity.py
```

## Traces to

HG-3 (#79). Not an unfreeze condition.

## Narrative

- 2026-10-15: Fixed at the source rather than by re-emitting under 2.14 (would turn the pinned
  environment red) or capping `pydantic<2.14` (would keep the wrong spelling). Isolated by
  emitting under four installs: fastapi 0.115.0 with pydantic 2.12.5 and 2.13.5 → `"True"`;
  pydantic 2.14.1 with fastapi 0.115.0 or 0.143.2 → `"true"`. So pydantic, not FastAPI. The
  rewrite wraps `application.openapi`, so the served `/openapi.json` and the committed snapshot
  agree in every environment, not only the snapshot. Lesson for HG-3: an unpinned lane compares a
  pinned snapshot against whatever resolved today; any generated file is exposed the same way.
  (by @assistant)
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
