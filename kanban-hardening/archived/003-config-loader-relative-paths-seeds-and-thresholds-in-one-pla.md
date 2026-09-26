---
id: 3
status: done
priority: High
blocked_by: [2]
assignee: "@amirhossein"
tags: [p0, l0, S1, AC-1]
---

# Config loader: relative paths, seeds and thresholds in one place

**Stage S2 — Data layer** · **L0 Foundation** · Estimate: 1 d

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

- [x] `hydms/config/pipeline.yaml` holds every path (relative to repo root), RNG seed and threshold
- [x] `hydms.config.load()` returns a validated typed object; unknown **and missing** keys raise,
      in both directions, and the result is frozen
- [x] No absolute path literals remain in `hydms/` — asserted by a test, not by a grep
- [x] Paths resolve correctly when the repo is cloned to a different directory, and `HYDMS_ROOT`
      overrides discovery for an installed package

## Runnable check

```bash
python -m pytest tests/config -q && ! grep -rn 'D:\\' hydms/
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Done. Three decisions worth recording.

  **Root discovery raises rather than falling back to the working directory.** It looks for the
  nearest ancestor holding both `pyproject.toml` and `hydms/`, with `HYDMS_ROOT` as an explicit
  override. A path silently resolved against wherever the user happened to be standing is the exact
  class of bug this module exists to remove, so there is no quiet default.

  **Missing keys raise as loudly as unknown ones.** The card asked only for unknown keys, but the
  same drift happens in reverse: a field added to the dataclass and forgotten in the YAML would
  otherwise surface as a bare `TypeError` naming an argument rather than the file it should have come
  from. The loader now refuses drift in both directions. A section whose last key is deleted parses as
  `None`, not `{}` — that is handled explicitly so the error names the missing key instead of
  reporting `got NoneType`.

  **Every value in `pipeline.yaml` is traced to the archival code or to a measurement**, and where it
  contradicts `REPORT.md` the comment says so. Two contradictions are now pinned here: the split
  fractions are 0.20 / 0.10, not the 70/15/15 that REPORT 2.6 and the README both claim; and the
  variance threshold is 0.001 while `Boruta_FeatEng.py`'s own comment beside it says 0.01.

  The quantile list is range-checked for order and uniqueness, not merely for membership of (0, 1),
  because CatBoost identifies quantiles by column position alone — an unsorted list means the column
  the code calls P90 is not the one the model wrote. (by @assistant)
