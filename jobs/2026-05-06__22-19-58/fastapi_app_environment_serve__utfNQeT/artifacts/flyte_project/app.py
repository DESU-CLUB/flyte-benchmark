from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field

from flyte import TaskEnvironment
from flyte.app.extras import FastAPIAppEnvironment

app = FastAPI(title="Flyte 2.0 Prediction API")


class PredictRequest(BaseModel):
    features: List[float] = Field(..., min_items=1, description="Input feature values")


class PredictResponse(BaseModel):
    prediction: float


ml_env = TaskEnvironment(name="ml-processing")


@ml_env.task
def normalize_features(features: List[float]) -> List[float]:
    max_value = max((abs(value) for value in features), default=1.0) or 1.0
    return [value / max_value for value in features]


env = FastAPIAppEnvironment(app)


@env.task
def predict_task(features: List[float]) -> float:
    normalized = normalize_features(features=features)
    return float(sum(normalized))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    prediction = predict_task(features=request.features)
    return PredictResponse(prediction=prediction)
