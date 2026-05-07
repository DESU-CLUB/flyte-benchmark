import flyte
from flyte import TaskEnvironment
from flyte.app.extras import FastAPIAppEnvironment
from fastapi import FastAPI, Body
from typing import List
import uvicorn

# 1. Use flyte.TaskEnvironment for ML processing tasks
# The name must be snake_case or kebab-case.
env = TaskEnvironment(name="ml-processing-env")

# 2. Define an @env.task for ML processing
# The /predict endpoint should process a list of features using an @env.task
@env.task
def compute_prediction(features: List[float]) -> List[float]:
    """
    ML processing task that processes a list of features.
    This is a placeholder for actual model inference logic.
    """
    return [f * 2.0 for f in features]

# 3. Create a FastAPI app with POST /predict and GET /health endpoints
app = FastAPI()

@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

@app.post("/predict")
async def predict(features: List[float] = Body(..., embed=True)):
    """
    The /predict endpoint receives a list of features and uses the @env.task for processing.
    """
    # Call the Flyte task for processing
    prediction = compute_prediction(features)
    return {"prediction": prediction}

# 4. Use FastAPIAppEnvironment from flyte.app.extras
app_env = FastAPIAppEnvironment(
    name="prediction-api-app",
    app=app,
    port=8000,
    depends_on=[env]
)

if __name__ == "__main__":
    # Start command: python /home/user/flyte_project/serve.py
    # Port: 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
