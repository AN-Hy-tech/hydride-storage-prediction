# HydMS — Hydrogen Storage Capacity Prediction

> **Master's Thesis Project** · Faculty of Metallurgical and Materials Engineering · Shiraz University
> Researcher: Amirhossein Nasiri

HydMS predicts the **maximum gravimetric hydrogen storage capacity (wt%)** of a metal-hydride alloy
from its **chemical formula and temperature**. Every prediction comes with an interval and a domain
verdict, and the model refuses to answer when a formula is outside what it was trained on.

All code is in the `hydms/` package. An HTTP service and a Streamlit app sit on top of it.

---

## Results

Every number in this project is produced by code and written to `reports/`; a test asserts that each
committed summary is exactly what the code produces from the committed tables.

| Question | Where the answer is |
| --- | --- |
| How well does the training procedure predict unseen rows? (out-of-fold, with 95% intervals) | [reports/model/evaluation.md](reports/model/evaluation.md) |
| How well does it transfer to an alloy family it has never seen? (leave-one-alloy-class-out) | [reports/loco/loco.md](reports/loco/loco.md) |
| Which features are used, and how stable is the selection? | [reports/feature_selection/](reports/feature_selection/) |

Read the two together: the model interpolates well within known alloy families and transfers
poorly to new ones. Both numbers are shown on the app's model-card page.

---

## Quickstart

Requires Python 3.10–3.12.

```bash
pip install -e ".[dev,uq,novelty,api,figures]"

python -m pytest                       # the test suite
python -m hydms.pipeline.smoke         # end-to-end smoke run on a committed fixture
python -m hydms.gates list             # the executable quality gates
```

The pinned Windows environment is in `environment.lock.yml` / `requirements-lock.txt`; see
[docs/ENVIRONMENT.md](docs/ENVIRONMENT.md).

### Train, then serve

A fresh clone has no trained model (`artifacts/` is not committed), so the service will not start
until one is built. [docs/RUNNING-THE-FIT.md](docs/RUNNING-THE-FIT.md) gives the commands in order.
Then:

```bash
uvicorn hydms.delivery.api:app --port 8000   # the HTTP service — contract in docs/API.md
streamlit run app/main.py                    # the app: single prediction, model card, batch screening
```

---

## Project structure

```text
hydms/          the package: data, descriptors, surrogate, screens, delivery, gates
app/            Streamlit app (a client of the HTTP service)
data/raw/       the source datasets (read-only)
reports/        generated results tables and summaries
tests/          the test suite
docs/           API contract, environment, operator guide, decisions (docs/adr/)
scripts/        CI checks
```

## Datasets

| File | Description |
| --- | --- |
| `data/raw/hydride_data.csv` | The curated dataset the model is trained on (1279 rows) |
| `data/raw/hydride_prefeaturizing.csv` | The same rows with the target log-transformed |
| `data/raw/ML-HYDPARK_v0.0.5.csv` | The upstream ML-HydPARK release |
| `data/raw/HyStor_27_7_24 (1).xlsx` | The HyStor experimental database |

## History

An earlier pipeline (`Machine_Model/`) and the report built on it (`REPORT.md`) published scores
that its own committed results did not reproduce. Both were removed; they remain available at the
git tag `machine-model-archive` for anyone tracing that history. Do not quote their numbers.

---

Copyright © 2026 Amirhossein Nasiri. Licensed under the [GNU General Public License v3.0 or later](LICENSE).
