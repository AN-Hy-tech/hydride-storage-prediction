---
id: 16
status: backlog
priority: High
blocked_by: [8]
assignee: "@amirhossein"
tags: [p1, l2, S12]
---

# Element property tables with cited provenance

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** The numeric element properties, and where each came from.

## Why this exists

CBFV carries **no licence at all** (`spdx_id` null on GitHub and PyPI), is unmaintained
since 2022 and will break under NumPy 2.x. Under a GPL-3.0 deliverable it cannot be
vendored. The replacement sources the tables from citable, redistributable publications:

- Oliynyk elemental properties — Lee et al. 2024, *Data in Brief* 53, 110178
- JARVIS descriptors — Choudhary et al. 2020, *npj Comput. Mater.* (NIST)

Depends on ticket 8 having named which tables are actually needed.

## Done when

- [ ] Tables stored as versioned CSV under `hydms/descriptors/data/` with a `SOURCES.md` citing each
- [ ] Loader validates element coverage against the 54 elements present in the dataset
- [ ] A missing element for a requested property raises, never silently yields NaN
- [ ] No CBFV import anywhere in `hydms/descriptors/`

## Runnable check

```bash
python -m pytest tests/descriptors/test_element_data.py -q && ! grep -rn 'import CBFV' hydms/
```

## Traces to

`docs/PRD-inverse-design.md` — S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
