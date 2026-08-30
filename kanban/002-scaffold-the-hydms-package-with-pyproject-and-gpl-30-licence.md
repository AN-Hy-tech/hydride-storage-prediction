---
id: 2
status: backlog
priority: High
blocked_by: []
assignee: "@amirhossein"
tags: [p0, l0, S12]
---

# Scaffold the hydms package with pyproject and GPL-3.0 licence

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Where new code lives and under what licence it ships.

## Why this exists

`Machine_Model/src/` stays untouched as the archival record backing `REPORT.md`
(PRD 7.2). All new work goes in a new top-level `hydms/` package.

GPL-3.0 is the decided licence. Record it now so every file added afterwards is unambiguous,
and so the CBFV replacement has a licence to be clean *against*.

## Done when

- [ ] `hydms/` exists with `__init__.py` and the layer subpackages
- [ ] `pyproject.toml` declares the package, dependencies and `license = "GPL-3.0-or-later"`
- [ ] `LICENSE` contains the GPL-3.0 text
- [ ] `pip install -e .` succeeds inside the `Project` env
- [ ] `Machine_Model/src/` is unmodified (`git diff --stat Machine_Model/` is empty)

## Runnable check

```bash
pip install -e . && python -c "import hydms; print(hydms.__file__)" && git diff --stat Machine_Model/
```

## Traces to

`docs/PRD-inverse-design.md` — S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
