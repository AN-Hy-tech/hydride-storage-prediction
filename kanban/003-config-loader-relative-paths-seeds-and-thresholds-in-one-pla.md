---
id: 3
status: done
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

- [x] `hydms/config/pipeline.yaml` holds every path (relative to repo root), RNG seed and threshold
- [x] `hydms.config.load()` returns a validated typed object; unknown keys raise
- [x] No absolute path literals remain in `hydms/`
- [x] Paths resolve correctly when the repo is cloned to a different directory

## Runnable check

```bash
python -m pytest tests/config -q && ! grep -rn 'D:\\' hydms/
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-05: Implemented. `hydms/config/pipeline.yaml` is now the single owner of every path,
  seed and threshold; `hydms.config.load()` reads it and returns a frozen, typed `Config`
  (`Paths`/`Seeds`/`Splits`/`Thresholds`). Design notes and decisions taken:

  - **The schema is the contract.** Validation is structural, not a separate schema file: the
    frozen dataclasses in `__init__.py` *are* the allowed shape, and `_build()` rejects any YAML
    key that is not a declared field (`ConfigError`, naming the dotted path — e.g.
    `seeds.extra`) and any required field that is absent. So a typo fails loudly at load time
    rather than being silently dropped downstream. Adding a knob to the YAML means adding its
    typed field here too — that coupling is deliberate.

  - **Repo root comes from `__file__`, not `cwd`.** `_REPO_ROOT = parents[2]` of this module,
    so relative paths resolve correctly no matter where the repo is cloned or what directory the
    process runs from. `load(root=...)` overrides it, which is how the relocation test stages a
    fake clone under `tmp_path` and confirms every path follows the new root.

  - **`global` keyword.** The seed key is `global` in YAML (readable) but `global_` on the
    dataclass (Python keyword); a single alias in `_KEY_ALIASES` maps between them, and the
    error/`missing`-key messages translate back so users see the YAML spelling.

  - **Scope held to what is known now.** Paths name the two archival raw inputs that exist
    (`raw_capacity`, `raw_thermo`) plus `artifacts_root`; the layout *beneath* that root is left
    to the artifact store (card #4), which this module only locates. Thresholds carry the
    selection knobs (`variance` 0.001, `mutual_info` 0.001, `vif` 30.0) and CleanLab's
    `outlier_residual_sigma` (3.0); split fractions (test 0.20, val 0.10) match the legacy
    `split_data.py`, with `train_fraction` a derived property so the three can never contradict.
    Values were taken from the legacy scripts, not invented.

  - **Input existence is validated; outputs are not.** `raw_*` must already exist (they are
    read-only archival data), so a missing or mis-pointed input fails at load; `artifacts_root`
    is a run output and need not exist yet.

  - **PyYAML only.** No pydantic — the pinned `Project` env has PyYAML and nothing new was
    pulled in (invariant: adding a package invalidates the lock files). The one `yaml` import
    carries a `type: ignore[import-untyped]` rather than adding `types-PyYAML` as a dependency.

  Verified: `python -m pytest tests/config -q` → 13 passed; `ruff` and `mypy hydms/config`
  both clean; the card's runnable check (`pytest tests/config && ! grep -rn 'D:\' hydms/`)
  passes. Note for later cards: the runnable check greps `hydms/` for the Windows drive-path
  literal, so even a *comment* containing it fails the gate — the YAML refers to "absolute
  Windows drive paths" in prose instead. (by @assistant)
