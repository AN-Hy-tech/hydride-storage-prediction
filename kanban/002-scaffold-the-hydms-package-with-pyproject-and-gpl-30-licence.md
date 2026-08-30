---
id: 2
status: done
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

- [x] `hydms/` exists with `__init__.py` and 12 layer subpackages
- [x] `pyproject.toml` declares the package, dependencies and `license = "GPL-3.0-or-later"`
- [x] `LICENSE` contains the GPL-3.0 text (35,150 bytes, canonical)
- [x] `pip install -e .` succeeds inside the `Project` env — and installs *only* `hydms`
- [x] `Machine_Model/src/` is unmodified (`git diff --stat Machine_Model/` is empty)

## Runnable check

```bash
pip install -e . && python -c "import hydms; print(hydms.__file__)" && git diff --stat Machine_Model/
```

## Traces to

`docs/PRD-inverse-design.md` — S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-08-30: **Licence resolved: GPL-3.0-or-later, confirmed by @amirhossein.** The root
  `LICENSE` had been MIT (added via the GitHub web UI on 2026-06-21) which contradicted this
  card's title. Replaced with the canonical GPL-3.0 text and the README licence line updated to
  match. Two caveats worth recording rather than discovering later:

  1. The repository was **public under MIT from June until 2026-08-30**. Anyone who obtained a
     copy in that window keeps MIT rights *to those commits* — a licence already granted cannot
     be revoked. The change binds everything from here on. As sole copyright holder this is
     @amirhossein's to make; no third-party contributions needed re-consenting.
  2. GPL-3.0 is copyleft. If a journal or collaborator later wants permissive terms for the
     featuriser, relicensing is easy *now* and hard once outside contributors exist.

- 2026-08-30: **Dependency design — core deps deliberately exclude what is not yet installed.**
  The obvious reading of this card is to declare everything the project will eventually need.
  That would have been actively harmful: `mapie`, `pymoo`, `streamlit` and `ElMD` are absent from
  the `Project` env, so `pip install -e .` would have downloaded them *into* it and invalidated
  the `environment.lock.yml` / `requirements-lock.txt` pair that card #1 had just verified.

  So `dependencies` lists only packages already present and already pinned, and the decided-but-
  unused ones sit in optional groups (`uq`, `search`, `novelty`, `app`) to be installed by the
  card that first needs them. Verified: the install reported `Installing collected packages:
  hydms` and nothing else, and a re-check of every pinned version afterwards showed no drift.

  `CBFV` is in a `parity` extra and **must never become a runtime dependency** — it is unlicensed
  (all rights reserved by default), which is the entire reason the descriptor layer is being
  reimplemented. It is present only so gate AC-2 has something to diff against.

- 2026-08-30: Subpackage names were derived from the cards, not invented — the `tests/<layer>/`
  paths and the `python -m hydms.<module>` invocations already written into cards 3-67 name
  twelve: config, artifacts, gates, data, descriptors, surrogate, thermo, screens, search,
  delivery, figures, pipeline. Each `__init__.py` carries a docstring stating what that layer
  owns, so the boundary is legible before any implementation exists. Also noted in
  `docs/ENVIRONMENT.md`: after an editable install `pip freeze` reports `hydms` as a git URL, and
  that line must be stripped from any regenerated lock file or the environment would depend on
  cloning itself. (by @assistant)
