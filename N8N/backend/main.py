from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import sqlite3
from database.db_utils import add_storage_data, check_storage_data, check_dataset_data

app = FastAPI(title="Discover the groundbreaking Hydrogen Storage Material Capacity Prediction API! Unlock the future of energy with precise forecasts for material capacity.")

# Load models
try:
    models = {
        "gbr": joblib.load("backend/gbr_Basemodel_NoHRatio.pkl"),
        "catboost": joblib.load("backend/Catboost_best_model_NoHRatio.pkl")
    }
except Exception as e:
    models = None
    print(f"Failed to load models: {str(e)}")

# Define input schema
class PredictionInput(BaseModel):
    composition: str
    temperature: float
    model_type: str = "gbr"  # Default to GBR model

# Placeholder for feature extraction (to be implemented in Stage 4)
def extract_features(composition: str, temperature: float) -> list:
    # TODO: Implement feature extraction using MatMiner, Miedema, WenAlloys, Magpie
    # This is a placeholder returning dummy features
    return [100.0, 50.0, 300.0]  # Replace with actual feature extraction

@app.post("/predict", response_model=dict)
async def predict_capacity(input_data: PredictionInput):
    try:
        # Validate model type
        if input_data.model_type not in models:
            raise HTTPException(status_code=400, detail="Invalid model_type. Choose 'gbr' or 'catboost'.")

        # Check if prediction exists in storage_data
        features, stored_capacity = check_storage_data(input_data.composition, input_data.temperature)
        if stored_capacity is not None:
            # Check dataset for real capacity
            real_capacity = check_dataset_data(input_data.composition, input_data.temperature)
            # Predict new capacity
            features = extract_features(input_data.composition, input_data.temperature)
            features_array = np.array([features])
            model = models[input_data.model_type]
            predicted_capacity = model.predict(features_array)[0]
            
            response = {
                "composition": input_data.composition,
                "temperature": input_data.temperature,
                "real_capacity": float(real_capacity) if real_capacity is not None else None,
                "predicted_capacity": float(predicted_capacity),
                "model_type": input_data.model_type
            }
            return response

        # Check dataset for real capacity
        real_capacity = check_dataset_data(input_data.composition, input_data.temperature)

        # Extract features and predict
        features = extract_features(input_data.composition, input_data.temperature)
        features_array = np.array([features])
        model = models[input_data.model_type]
        predicted_capacity = model.predict(features_array)[0]

        # Store in storage_data
        add_storage_data(input_data.composition, input_data.temperature, features, predicted_capacity)

        response = {
            "composition": input_data.composition,
            "temperature": input_data.temperature,
            "real_capacity": float(real_capacity) if real_capacity is not None else None,
            "predicted_capacity": float(predicted_capacity),
            "model_type": input_data.model_type
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/health")
async def health_check():
    health_status = {"status": "healthy", "details": {}}

    # Check models
    if models is None:
        health_status["status"] = "unhealthy"
        health_status["details"]["models"] = "Failed to load models"
    else:
        health_status["details"]["models"] = "Models loaded successfully"

    # Check database connection
    try:
        conn = sqlite3.connect("database/storage.db")
        conn.execute("SELECT 1 FROM storage_data LIMIT 1")
        conn.close()
        health_status["details"]["database"] = "Database connection successful"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["details"]["database"] = f"Database connection failed: {str(e)}"

    return health_status