# HydMS — Hydrogen Storage Capacity Prediction via Machine Learning

> **Master's Thesis Project** · Faculty of Metallurgical and Materials Engineering · Shiraz University
Researcher: Amirhossein Nasiri
---

## What is this?

Metal hydrides store hydrogen inside their crystal lattice, a path toward solid-state hydrogen
storage. Measuring storage capacity experimentally is slow and expensive. HydMS predicts the
**maximum material H₂ storage capacity (wt%)** of a hydride alloy from its **chemical formula and
temperature alone**, and extends that forward model to the inverse question: which alloys should
we make?

A prediction from HydMS is never a bare number. Every answer carries a **conformal prediction
interval** and an **applicability-domain verdict**, and a composition outside the domain is
refused with a stated reason rather than answered. Validation groups rows by canonical composition
and holds out whole alloy families, so the reported scores say how well the model transfers, not
how well it remembers.

**Status.** The project is in Phase H (hardening). Work outside it is frozen; see
[docs/FREEZE.md](docs/FREEZE.md) and [docs/PHASE-H-FINDINGS.md](docs/PHASE-H-FINDINGS.md).

## Results

This README quotes no scores: each number has one owner, and a copy here would go stale.

| What | Where it lives |
|---|---|
| Current numbers, in prose, each with its evidence | [docs/chapter1-revision.md](docs/chapter1-revision.md) |
| Grouped-CV fit, held-out evaluation, conformal coverage | [reports/model/](reports/model/) — summary in [evaluation.md](reports/model/evaluation.md) |
| Leave-one-alloy-class-out transfer | [reports/loco/](reports/loco/) — summary in [loco.md](reports/loco/loco.md) |
| Feature selection inside the folds | [reports/feature_selection/](reports/feature_selection/) |
| The model card a running service reports | `GET /v1/model` and `GET /v1/evidence` ([docs/API.md](docs/API.md)) |

The first version of this work published higher scores from an earlier pipeline. Those scores
were not reproducible and are withdrawn; [docs/archive/REPORT-RECONCILIATION.md](docs/archive/REPORT-RECONCILIATION.md)
records why. The old pipeline and its report are kept, unedited, at git tag
`machine-model-archive`.

---

## Project Structure

```
hydride-storage-prediction/
├── hydms/                  # The project package
│   ├── data/               # Loaders, curation, canonical composition keys
│   ├── descriptors/        # Composition featuriser (element tables ship in the package)
│   ├── surrogate/          # Fit, calibrate, evaluate, LOACO, promote, predict
│   ├── screens/            # Applicability domain and physics screens
│   ├── search/             # Inverse-design search seam (frozen programme; not yet built)
│   ├── delivery/           # HTTP API, refusals, model card
│   ├── gates/              # Executable acceptance gates (AC-*, HG-*)
│   └── evidence/, figures/, thermo/, qa/, pipeline/, artifacts/, config/
├── app/                    # Streamlit client of the HTTP API
├── data/raw/               # HyStor + ML-HydPARK raw data
├── reports/                # Committed evidence tables (model/, loco/, feature_selection/)
├── tests/                  # The test suite
├── docs/                   # Runbook, API, environment, ADRs, findings
├── kanban-hardening/       # The active board (Phase H)
└── kanban/                 # The frozen inverse-design board
```

---

## Quickstart

### Step 1 — Environment

Use the conda environment `Project` (Python 3.10, NumPy 1.x). The machine's default Python will
not work. Rebuild instructions and why the pins matter: [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).

```bash
conda env create -f environment.lock.yml -n Project
conda run -n Project python -m pip install -e .
```

### Step 2 — Fit the model

The fit is several hours and its operator steps are ordered; follow
[docs/RUNNING-THE-FIT.md](docs/RUNNING-THE-FIT.md). In outline:

```bash
conda run -n Project python -m hydms.surrogate.train --target capacity      # grouped-CV fit
conda run -n Project python -m hydms.surrogate.calibrate --target capacity --save
conda run -n Project python -m hydms.surrogate.evaluate --emit              # intervals and coverage
conda run -n Project python -m hydms.surrogate.promote --dry-run            # gate check before promotion
```

`artifacts/` is gitignored, so a fresh clone has no promoted model and the service below refuses
to start until you have run these steps.

### Step 3 — Serve and use it

```bash
conda run -n Project uvicorn hydms.delivery.api:app --port 8000
conda run -n Project streamlit run app/main.py
```

The HTTP contract is [docs/API.md](docs/API.md); every refusal sentence is in
[docs/REFUSALS.md](docs/REFUSALS.md).

### Checks

```bash
conda run -n Project python -m hydms.gates list
conda run -n Project python -m pytest -m "not slow" -q
```

---

## Datasets

| File | Description |
|------|-------------|
| `data/raw/hydride_data.csv` | Primary merged hydride dataset |
| `data/raw/ML-HYDPARK_v0.0.5.csv` | ML-HydPARK benchmark dataset |
| `data/raw/HyStor_27_7_24 (1).xlsx` | HyStor experimental database |
| `data/raw/hydride_prefeaturizing.csv` | The same rows with the target log1p-transformed; a test fixture, never a source |

---

## About

This project was developed as a **Master's thesis** in the **Department of Metallurgy and
Materials Engineering** at **Shiraz University**. Terms used across the repository are defined in
[CONTEXT.md](CONTEXT.md); the thesis statement is [docs/PRD-inverse-design.md](docs/PRD-inverse-design.md) §4.

---

Copyright © 2026 Amirhossein Nasiri. Licensed under the [GNU General Public License v3.0 or later](LICENSE).
