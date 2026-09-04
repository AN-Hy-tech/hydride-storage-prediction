---
id: 48
status: backlog
priority: High
blocked_by: [30, 44]
assignee: "@amirhossein"
tags: [pa, l4, S4, AC-8, R1]
---

# Applicability-domain ceiling

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** How far from known chemistry a prediction may be trusted.

## Why this exists

The Beltrame result means a candidate from an unfamiliar corner of composition space is
not merely uncertain — it is **out of scope**. Those are different things and the glossary
(35) keeps them distinct.

The ceiling is set from the leave-one-alloy-class-out result (30): the distance at which
measured cross-family performance degrades past what the thesis is willing to claim. It is
the primary structural mitigation for risk R1.

## Done when

- [ ] Ceiling derived from the LOCO result, not chosen arbitrarily; the derivation is documented
- [ ] Candidates beyond it are flagged `OUT_OF_DOMAIN`, distinct from `HIGH_UNCERTAINTY`
- [ ] Ceiling is a config value so risk-R1 iterations can tighten it and re-run
- [ ] Alloy-class assignability checked as a second, independent domain signal
- [ ] **The ceiling is a `Screen` (#44) and it declares its own vocabulary.** `OUT_OF_DOMAIN` and
      `HIGH_UNCERTAINTY` are entries in `reasons`; `hydms.screens.apply_screens` refuses a code no
      screen declared, which is what lets #75 enumerate every refusal the API can emit rather than
      maintaining a second list. The shared `INDETERMINATE` is a **rejection**: a ceiling that could
      not be computed for a candidate must not admit it. Return the distance and the ceiling as
      extra columns — the runner prefixes and carries them as `<screen>.<column>`.

## Runnable check

```bash
python -m pytest tests/screens/test_applicability.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S4, AC-8, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: #44 landed the contract this card implements. The vocabulary is declared per screen
  and enforced by the runner, so `OUT_OF_DOMAIN` vs `HIGH_UNCERTAINTY` stops being a naming
  convention and becomes something a test can assert. `temperature_window()` is the worked example
  of the config-driven threshold this card's third box asks for — and is explicitly *not* an
  applicability domain: it is the outer bound, and the AD ceiling is what this card adds. (by @assistant)
