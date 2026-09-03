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
- [ ] Loader validates element coverage against the **55** elements present in the dataset —
      not 54. `REPORT.md` §2.3 and the PRD's dataset table both say 54; counted from the parsed
      compositions of all 1279 rows the answer is 55, seven of them appearing exactly once
      (N, Eu, Lu, Pb, Au, Os, Re). Measured by #9 and asserted in `tests/data/test_load.py`;
      recorded as a disagreement on #89. A table validated against 54 would pass while one
      element silently had no properties
- [ ] A missing element for a requested property raises, never silently yields NaN
- [ ] No CBFV import anywhere in `hydms/descriptors/`

- [ ] **NumPy cannot currently be imported anywhere under `hydms/`, and this card is where that
      stops.** mypy runs outside the `Project` environment by design (the conda-free lint lane,
      #68, `docs/QA-PROTOCOL.md` §6), so it resolves numpy from the machine's 3.13 site-packages,
      whose `__init__.pyi` uses PEP 695 `type` statements that `python_version = "3.10"` rejects as
      a **syntax** error. That aborts the *entire* run — `Found 1 error in 1 file (errors prevented
      further checking)` — not just the importing file, and `ignore_missing_imports` does not
      suppress it. #71 sidestepped it with stdlib `random`, #11 with `math.log1p`; the descriptor
      layer cannot sidestep it.
      **A remedy was tested on 2026-09-03 and works** — verified by adding a numpy-importing module
      under `hydms/descriptors/` and running the real `mypy` invocation, which reported
      `Success: no issues found in 40 source files`:

      ```toml
      [[tool.mypy.overrides]]
      module = ["numpy", "numpy.*"]
      follow_imports = "skip"
      follow_imports_for_stubs = true
      ignore_missing_imports = true
      ```

      It is not applied, because applying it is this card's decision, not a fix made in passing.
      **Its cost is real and should be stated in `pyproject.toml` beside it:** numpy becomes `Any`,
      so mypy stops checking dtype and shape mistakes in exactly the layer that has the most array
      code. That is the same trade already made for pandas, scipy and scikit-learn. If a better
      answer exists — vendored stubs pinned to the 1.26 line, or a second mypy target — this is the
      card to find it on

## Runnable check

```bash
python -m pytest tests/descriptors/test_element_data.py -q && ! grep -rn 'import CBFV' hydms/
```

## Traces to

`docs/PRD-inverse-design.md` — S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-03: Two boxes added while closing S2. The element count is **55**, not the 54 this card
  asked the loader to validate against — measured by #9, and a table checked against 54 would pass
  while one element silently had no properties. And the numpy/mypy wall that #71 and #11 both
  sidestepped now has a *tested* remedy recorded above; it is left unapplied because choosing it,
  and stating what it costs, belongs to this card. (by @assistant)
