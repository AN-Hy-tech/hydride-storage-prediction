---
id: 42
status: backlog
priority: Normal
blocked_by: [40]
assignee: "@amirhossein"
tags: [pt, l3, S8]
---

# van 't Hoff module

**Phase T — Thermodynamics** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The relation between enthalpy, entropy, temperature and plateau pressure.

## Why this exists

`ln p_H2 = ΔH/RT - ΔS/R`. With predicted ΔH and ΔS, every candidate can be placed on a
temperature/pressure map — which is the difference between 'high wt% on paper' and 'usable
at the target conditions'.

Pure function, no model dependency: it takes ΔH, ΔS and T and returns p_eq.

## Done when

- [ ] `vant_hoff(dH, dS, T) -> p_eq` implemented as a pure, vectorised function
- [ ] Units documented explicitly and asserted at the boundary
- [ ] Round-trip test against published plateau pressures for two or three well-characterised alloys
- [ ] Uncertainty propagated from the ΔH and ΔS intervals, not dropped

## Runnable check

```bash
python -m pytest tests/thermo/test_vant_hoff.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S8

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
