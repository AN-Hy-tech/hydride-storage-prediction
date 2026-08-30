---
id: 3
status: backlog
priority: High
blocked_by: [2]
assignee: "@amirhossein"
tags: [p0, l0, S1, AC-1]
---

# Config loader: relative paths, seeds and thresholds in one place

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** Every path, seed and threshold. Nothing else may hard-code them.

## Job story

When I move the repository or change where data lives, I want to edit one file, so I can avoid hunting hard-coded paths across nine scripts.

## Why this exists

The audit found six data directory names (`raw/ database/ processed/ processed_data/
splits/ augmented/`) and absolute `D:\...` paths throughout, with two scripts reading
directories nothing writes.

**Information-hiding check:** after this lands, changing where data lives must require
editing one YAML file and nothing else.

## Done when

- [ ] `hydms/config/pipeline.yaml` holds every path (relative to repo root), RNG seed and threshold
- [ ] `hydms.config.load()` returns a validated typed object; unknown keys raise
- [ ] No absolute path literals remain in `hydms/`
- [ ] Paths resolve correctly when the repo is cloned to a different directory

## Runnable check

```bash
python -m pytest tests/config -q && ! grep -rn 'D:\\' hydms/
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
