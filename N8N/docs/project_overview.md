Project Overview
Objective
This project develops a web application to predict the hydrogen storage capacity of hydrides based on chemical composition (e.g., MgH2 in SMILES format) and operating temperature. Users input data via a web interface, and the system processes it using a machine learning model, n8n workflows, and SQLite for data storage.
Components

Frontend: Web interface built with HTML, JavaScript, and Tailwind CSS.
Backend: FastAPI server for model inference using gbr_Basemodel.pkl.
n8n Workflows: Automates feature extraction, model prediction, and data storage.
Database: SQLite with tables:
storage_data: Stores user inputs and predictions.
train_data, validation_data, test_data: Store feature-engineered datasets.


Logs/Data: n8n logs (n8n_workflows/logs/) and data (n8n_workflows/data/) for debugging and analysis.

Technologies

Frontend: HTML, JavaScript, Tailwind CSS
Backend: Python, FastAPI, scikit-learn, RDKit
Workflow: n8n
Database: SQLite
Data Processing: Pandas

Status

Stage 1: Environment setup and folder structure created.
Stage 2: SQLite database implemented with storage_data, train_data, validation_data, and test_data tables. Datasets imported from CSV files.

