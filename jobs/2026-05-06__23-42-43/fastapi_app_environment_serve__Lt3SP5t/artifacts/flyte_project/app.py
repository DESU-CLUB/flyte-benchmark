"""
Flyte 2.0 ML Prediction API
============================
Defines:
  - A ``TaskEnvironment`` (env) that owns the ``@env.task`` ML processing task.
  - A ``FastAPIAppEnvironment`` (app_env) that wraps a FastAPI application
    and exposes ``POST /predict`` and ``GET /health`` endpoints.

The ``predict_task`` runs inside Flyte's task infrastructure; the FastAPI app
delegates prediction requests to it and returns the result to the caller.
"""
from __future__ import annotations

from typing import List

import flyte
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from flyte.app.extras import FastAPIAppEnvironment

# ---------------------------------------------------------------------------
# 1.  TaskEnvironment — owns ML processing tasks
# ---------------------------------------------------------------------------
env = flyte.TaskEnvironment(
    name="ml-prediction-env",
    image="auto",
    resources=flyte.Resources(cpu="1", memory="512Mi"),
)


# ---------------------------------------------------------------------------
# 2.  ML prediction task decorated with @env.task
# ---------------------------------------------------------------------------
@env.task
async def predict_task(features: List[float]) -> dict:
    """
    Perform ML inference on a flat list of numerical features.

    This is a placeholder model: it computes a weighted sum of the input
    features as the predicted value, simulating what a real model (e.g.
    scikit-learn, PyTorch, XGBoost) would do.

    :param features: 1-D list of numerical feature values.
    :returns: A dict containing the prediction result and feature metadata.
    :raises ValueError: When the feature list is empty.
    """
    if not features:
        raise ValueError("features must not be empty")

    n = len(features)
    # Simulated model weights (1 / position index, 1-based)
    weights = [1.0 / (i + 1) for i in range(n)]
    score = sum(w * f for w, f in zip(weights, features))

    return {
        "prediction": round(score, 6),
        "num_features": n,
        "model": "weighted-sum-v1",
    }


# ---------------------------------------------------------------------------
# 3.  FastAPI application
# ---------------------------------------------------------------------------
fastapi_app = FastAPI(
    title="Flyte ML Prediction API",
    description="Flyte 2.0 FastAPI app — POST features to /predict, check /health.",
    version="1.0.0",
)


class PredictRequest(BaseModel):
    features: List[float] = Field(
        ...,
        min_length=1,
        description="Non-empty list of numerical feature values for inference.",
        examples=[[1.0, 2.0, 3.0, 4.0]],
    )


class PredictResponse(BaseModel):
    prediction: float
    num_features: int
    model: str


@fastapi_app.get("/health", tags=["ops"])
async def health() -> JSONResponse:
    """Liveness / readiness probe — returns 200 OK when the server is up."""
    return JSONResponse(content={"status": "ok"})


@fastapi_app.post("/predict", response_model=PredictResponse, tags=["ml"])
async def predict(request: PredictRequest) -> PredictResponse:
    """
    Run ML inference on the supplied feature vector.

    Delegates to the Flyte ``predict_task`` (a ``@env.task``-decorated
    coroutine) and returns the structured prediction result.

    Inside a Flyte task context ``predict_task(...)`` submits the task to the
    Flyte controller.  Outside a task context (local / serve mode) it calls
    the underlying function directly, which is the correct behaviour for an
    API server — the task logic runs in-process on every request.
    """
    try:
        # predict_task(...) returns a coroutine outside a Flyte task context
        # because the underlying function is declared `async def`.
        result = await predict_task(features=request.features)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    return PredictResponse(**result)


# ---------------------------------------------------------------------------
# 4.  FastAPIAppEnvironment — wraps the FastAPI app for Flyte serving
# ---------------------------------------------------------------------------
app_env = FastAPIAppEnvironment(
    name="ml-prediction-api",
    app=fastapi_app,
    port=8000,
    image="auto",
    requires_auth=False,
    depends_on=[env],
)
