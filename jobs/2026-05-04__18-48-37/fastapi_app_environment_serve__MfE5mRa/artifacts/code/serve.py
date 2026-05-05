import flyte
from flyte.app.extras import FastAPIAppEnvironment
from fastapi import FastAPI
from typing import List
from pydantic import BaseModel

# Use TaskEnvironment for ML processing tasks
env = flyte.TaskEnvironment(name="ml-processing")

# The /predict endpoint should process a list of features using an @env.task
@env.task
async def predict_task(features: List[float]) -> float:
    """
    ML processing task to predict based on features.
    For this example, we return the sum of features.
    """
    return sum(features)

# Create a FastAPI app
app = FastAPI()

class PredictionRequest(BaseModel):
    features: List[float]

class PredictionResponse(BaseModel):
    prediction: float

# POST /predict endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    # Call the ML task
    result = await predict_task(features=request.features)
    return PredictionResponse(prediction=result)

# GET /health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# FastAPIAppEnvironment from flyte.app.extras
app_env = FastAPIAppEnvironment(
    name="prediction-api",
    app=app,
    port=8000
)

if __name__ == "__main__":
    # Start the Flyte application
    flyte.serve(app_env)
