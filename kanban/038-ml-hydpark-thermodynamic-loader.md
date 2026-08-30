---
id: 38
status: backlog
priority: Normal
blocked_by: [9]
assignee: "@amirhossein"
tags: [pt, l1, S8]
---

# ML-HydPARK thermodynamic loader

**Phase T — Thermodynamics** · **L1 Data** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The thermodynamic training set and its completeness.

## Why this exists

`data/raw/ML-HYDPARK_v0.0.5.csv` carries **772 rows with 100% non-null
`Heat_of_Formation_kJperMolH2`, `Entropy_of_Formation_JperMolH2perK` and
`LnEquilibrium_Pressure_25C`** across 744 unique formulae — verified during the audit.

Class mix is AB2-family 454 of 772 (59%) and AB5 106, densest exactly where Architecture A
searches. This is why training our own model is cheap rather than speculative.

## Done when

- [ ] Loader returns the 772 complete rows with validated schema
- [ ] Formula column normalised to match the capacity dataset's convention so features are comparable
- [ ] Material_Class carried as metadata for class-held-out validation
- [ ] Row and completeness counts asserted (772 rows, 744 unique formulae)

## Runnable check

```bash
python -m pytest tests/data/test_hydpark.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S8

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
