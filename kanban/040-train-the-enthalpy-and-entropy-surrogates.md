---
id: 40
status: backlog
priority: Normal
blocked_by: [38, 39]
assignee: "@amirhossein"
tags: [pt, l3, S8]
---

# Train the enthalpy and entropy surrogates

**Phase T — Thermodynamics** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** The thermodynamic predictions themselves.

## Why this exists

Same featuriser, same split protocol, same UQ machinery — only the target changes. Both
ΔH and ΔS are trained here because they share every code path.

Witman et al.'s pretrained models exist but carry **no licence**, are four years stale with
no dependency pins, and are built on data version v0.0.4 against our v0.0.5. They are the
benchmark (ticket 43), not a dependency.

## Done when

- [ ] ΔH and ΔS models trained on the 772-row set through the parameterised path
- [ ] Same conformal calibration applied so both emit intervals
- [ ] Class-held-out validation reported, as for capacity
- [ ] Artifacts persisted into the versioned store alongside the capacity model

## Runnable check

```bash
python -m hydms.surrogate.train --target dH && python -m hydms.surrogate.train --target dS
```

## Traces to

`docs/PRD-inverse-design.md` — S8

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
