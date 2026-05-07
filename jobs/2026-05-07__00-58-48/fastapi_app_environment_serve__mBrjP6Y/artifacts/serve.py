import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from flyte import TaskEnvironment
from flyte.app.extras import FastAPIAppEnvironment

app = FastAPI()

# Use FastAPIAppEnvironment from flyte.app.extras
fastapi_env = FastAPIAppEnvironment(app=app)

# Use flyte.TaskEnvironment for ML processing tasks
env = TaskEnvironment()

@env.task
def process_features(features: List[float]) -> float:
    """ML processing task to predict based on features."""
    return sum(features) * 2.0

class PredictRequest(BaseModel):
    features: List[float]

@app.post("/predict")
def predict(request: PredictRequest):
    """The /predict endpoint should process a list of features using an @env.task"""
    prediction = process_features(request.features)
    return {"prediction": prediction}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
