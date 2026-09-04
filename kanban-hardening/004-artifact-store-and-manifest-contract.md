---
id: 4
status: done
priority: High
blocked_by: [2, 3]
assignee: "@amirhossein"
tags: [p0, l0, S1, AC-1]
---

# Artifact store and manifest contract

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** What a trained artifact is, where it lives, and what is recorded alongside it.

## Why this exists

The audit's first finding: **no trained artifacts exist on disk**. The model, the fitted
scaler and the splits were never persisted, so Architecture A's 'load the fitted scaler, do
not refit' step had nothing to load.

An artifact version is this project's equivalent of a deployment environment: `v1` is
promoted to by passing gates, and later phases pin the version they consume.

## Done when

- [x] `artifacts/v{N}/` layout defined and documented — `hydms/artifacts/store.py`'s module
      docstring and `docs/PHASE-H-RUNBOOK.md` §2. One `manifest.json` and one `<name>.joblib`
      per saved object; `current.json` beside the version directories, and the standalone
      `gate-results.json` the harness already wrote
- [x] `manifest.json` records git SHA, all seeds, resolved package versions, the feature list and gate results
- [x] `hydms.artifacts.save(...)` / `.load(version)` are the only ways in and out
- [x] Loading a version whose gate results are incomplete raises rather than returning a model

- [x] **The feature contract's manifest payload already exists; embedding it is this card's
      (from #19).** `hydms.descriptors.contract.FeatureContract.as_manifest()` returns JSON-safe
      data — one entry per feature with its statistic, table, property and dtype, plus a
      SHA-256 digest over the names, their order and their dtype — and `from_manifest()` refuses
      a payload whose digest no longer matches. Store it under the model's manifest so a stored
      model records what it expects; a model fed a matrix built to a different contract returns
      plausible, wrong numbers, which is what AC-4 exists to catch

- [x] **A version is written once.** `save` stages the directory under `.v{N}.partial` and renames
      it into place, refuses an existing version, and never re-uses a number left behind by a run
      that died — two different artifacts under one name is worse than a gap in the sequence
- [x] **Every payload carries a SHA-256.** A truncated or edited `model.joblib` otherwise unpickles
      into something that still predicts. `load` re-hashes and raises `PayloadCorrupt`

## Runnable check

```bash
conda run -n Project python -m pytest tests/artifacts -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-04: Landed ahead of S4, because #23 is blocked by it and S4 is a thirteen-card chain
  that starts there. `hydms/artifacts/` is two modules — `manifest.py` owns what is recorded,
  `store.py` owns the layout and the two doors — and 68 tests. Four things worth keeping:

  **The gate report is embedded, not re-formatted.** `hydms/gates/_report.py` already wrote the
  run as JSON behind a versioned `schema` key, and its own comment said it did so *for this
  card*. So `save(gates=report)` stores that object unmodified. The dependency is one-way:
  `hydms.gates` writes into the artifacts directory, so `hydms.artifacts` importing it would
  close a cycle. `GATE_SCHEMA` is therefore restated in `manifest.py`, and
  `test_the_embedded_gate_schema_is_the_harnesss` asserts it still equals the harness's own
  constant — the restatement is only safe while that test exists.

  **The harness's own `ok` flag is not consulted, and that is the whole of the fourth box.**
  `GateReport.ok` tolerates a `SKIPPED` gate under a broad selection, deliberately: CI that is
  red for the length of the phase is CI nobody reads (card #5's reasoning, and it is right for a
  CI log). An artifact somebody is about to load into a prediction path is exactly where that
  leniency must not apply, so `Manifest.unestablished()` recomputes the verdict from the
  per-gate statuses and treats `SKIPPED` exactly as it treats `FAILED`. A version saved today
  therefore cannot load or be promoted, which is correct — #34 is blocked on #31/#32/#33 for the
  same reason. `require_gates=False` is the escape, and it is a keyword at the call site
  precisely so it is visible in a diff.

  **The manifest is not self-digested, and does not need to be.** Editing `manifest.json` by
  hand is caught where it is dangerous: the feature contract carries its own SHA-256 over the
  names, their order and their dtype (#19), and every payload carries one over its bytes.
  `test_an_edited_feature_list_is_caught_by_the_contracts_own_digest` swaps two features in a
  saved manifest, loads the bundle successfully — the payload files are untouched — and then
  gets a `ContractError` from `bundle.contract()`. That is the AC-4 failure mode, caught.

  **`RECORDED_PACKAGES` is tested against `pyproject.toml`, not maintained by memory.** A
  CatBoost or scikit-learn upgrade can change a fit from the same seed, which is the failure
  AC-1 exists to detect; a new core dependency that nothing records would leave "it used to
  reproduce" as the only evidence. `test_recorded_packages_covers_every_core_runtime_dependency`
  parses the `[project] dependencies` block and fails if one is missing. An absent package is
  recorded as `null` rather than omitted — reading an old manifest must be able to tell "mapie
  was not installed" from "this store did not yet record mapie".

  Two smaller findings. `joblib` needed a `[[tool.mypy.overrides]]` entry: it ships neither
  inline types nor a `py.typed` marker, and the conda-free lint lane does not install it. And
  `versions()` sorts numerically, never lexicographically — a string sort puts `v10` before `v9`
  and promotes the wrong artifact on the tenth retrain, which is one test and one `int()` away
  from being a real incident. Suite 661 green, ruff and mypy clean, `run --fast` exits 0.
  (by @assistant)
