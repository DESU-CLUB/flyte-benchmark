from typing import List
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from fastapi import FastAPI
from pydantic import BaseModel

from flytekit import task, workflow
from flytekit.types.schema import FlyteSchema
from flytekit.extras.sqlite3 import SQLite3Config
from flyte.app.extras import FastAPIAppEnvironment, TaskEnvironment


# Initialize FastAPI app
app = FastAPI(title="Flyte 2.0 ML Prediction API", version="2.0.0")

# Initialize Flyte FastAPI App Environment
env = FastAPIAppEnvironment(
    fastapi_app=app,
    task_env=TaskEnvironment()
)


# Data models
class Features(BaseModel):
    features: List[float]


class PredictionResponse(BaseModel):
    prediction: int
    confidence: float
    class_name: str


# Load and train a simple model (Iris dataset)
def get_model():
    iris = load_iris()
    X, y = iris.data, iris.target
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model, iris.target_names


# Global model instance
model, class_names = get_model()


@env.task
def predict_task(features: List[float]) -> dict:
    """
    Flyte task for ML prediction processing.
    
    Args:
        features: List of feature values for prediction
        
    Returns:
        Dictionary containing prediction results
    """
    # Convert to numpy array and reshape
    features_array = np.array(features).reshape(1, -1)
    
    # Make prediction
    prediction = model.predict(features_array)[0]
    probabilities = model.predict_proba(features_array)[0]
    confidence = float(max(probabilities))
    
    return {
        "prediction": int(prediction),
        "confidence": confidence,
        "class_name": str(class_names[prediction])
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "framework": "Flyte 2.0",
        "app": "FastAPI ML Prediction API"
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(features: Features):
    """
    Prediction endpoint that uses Flyte @env.task for ML processing.
    
    Args:
        features: Feature values for prediction
        
    Returns:
        Prediction response with class prediction and confidence
    """
    # Execute the Flyte task for prediction
    result = predict_task(features.features)
    
    return PredictionResponse(
        prediction=result["prediction"],
        confidence=result["confidence"],
        class_name=result["class_name"]
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Flyte 2.0 FastAPI ML Prediction API",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "docs": "/docs"
        }
    }


# Expose the app for Flyte
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)