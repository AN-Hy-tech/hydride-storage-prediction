---
id: 58
status: backlog
priority: Normal
blocked_by: [57]
assignee: "@amirhossein"
tags: [pa, l6, S10]
---

# Streamlit: candidate screening page

**Phase A — Screen-and-Rank** · **L6 Delivery** · Estimate: 2 d

> **Owns (hidden behind this module):** How a non-coding collaborator explores the results.

## Why this exists

User story S10: an experimental collaborator explores results without running code.

Reads the ranked CSV; it does not retrain or re-screen. Every filter verdict is visible per
candidate, because memo 4.2 requires the failure modes to be inspectable — a page that shows
only the winners would hide exactly what needs scrutiny.

Note the app env (`my-env`) currently has Streamlit 1.16.0 from 2022; current is 1.62.0.
Upgrading is part of this ticket.

## Done when

- [ ] Streamlit upgraded and pinned in the environment lockfile
- [ ] Table of ranked candidates with interval, novelty, cost, HHI and every screen verdict
- [ ] Filter controls for family, temperature, AD status and cost ceiling
- [ ] A per-candidate detail view showing all 22 features and the nearest known alloy
- [ ] Reads a published artifact and ranked CSV; performs no training

## Runnable check

```bash
streamlit run app/main.py
```

## Traces to

`docs/PRD-inverse-design.md` — S10

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
