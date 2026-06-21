# Hydride Hydrogen Storage Capacity Prediction

A machine learning project for predicting the hydrogen storage capacity (wt%) of hydride materials based on chemical composition and operating temperature.

## Project Structure

```
Hydride_Machine_learning_project/
├── Machine_Model/      # ML training & evaluation pipeline
└── N8N/                # FastAPI web application for serving predictions
```

## Components

### Machine_Model
End-to-end ML pipeline covering data ingestion, featurization, model benchmarking, hyperparameter optimization, and analysis. Trained on the HyStor and ML-HYDPARK datasets.

See [Machine_Model/README.md](Machine_Model/README.md) for full details.

### N8N
FastAPI backend that serves the trained model via a REST API. Accepts a chemical formula and temperature, runs feature extraction, and returns a predicted storage capacity. Uses SQLite to log predictions and an n8n workflow for automation.

See [N8N/docs/project_overview.md](N8N/docs/project_overview.md) for full details.

## Quickstart

### 1. Set up the ML environment

```bash
cd Machine_Model
pip install -r requirements.txt
```

> Some packages (`matminer`, `pymatgen`, `rdkit`) are best installed via conda:
> ```bash
> conda install -c conda-forge matminer pymatgen rdkit
> ```

### 2. Run the pipeline

Work through the notebooks in order:

```
notebooks/Raw_Data_Analysis.ipynb
notebooks/data_preprocessed_matminer.ipynb
notebooks/Preprocessed_Data_Analysis.ipynb
notebooks/identify_extream_outliers.ipynb
notebooks/optimize_catboost_model.ipynb
```

Or run the source scripts directly from `Machine_Model/src/`.

### 3. Start the API server

```bash
cd N8N
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Datasets

| File | Description |
|------|-------------|
| `Machine_Model/data/raw/hydride_data.csv` | Primary hydride dataset |
| `Machine_Model/data/raw/ML-HYDPARK_v0.0.5.csv` | ML-HYDPARK benchmark dataset |
| `Machine_Model/data/raw/HyStor_27_7_24 (1).xlsx` | HyStor experimental database |

## Key Results

- Best model: **CatBoost** (Optuna-optimized), stacked ensemble
- Features extracted via: Matminer, CBFV, JARVIS descriptors
- Target: H₂ storage capacity (wt%)
