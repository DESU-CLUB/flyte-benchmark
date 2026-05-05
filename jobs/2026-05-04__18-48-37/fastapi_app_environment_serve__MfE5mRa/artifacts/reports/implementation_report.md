# Flyte 2.0 FastAPI Prediction API

This project implements a Flyte 2.0 machine learning prediction API using `FastAPIAppEnvironment` and `@env.task`.

## Components

- **TaskEnvironment**: Used to define the ML processing environment.
- **FastAPIAppEnvironment**: Used to wrap the FastAPI application and serve it via Flyte.
- **@env.task**: Used to define the `predict_task` which handles the ML logic.

## Endpoints

- `POST /predict`: Accepts a list of features and returns a prediction.
- `GET /health`: Returns the health status of the API.

## Usage

To start the API:
```bash
python /home/user/flyte_project/serve.py
```

The API will be available at `http://0.0.0.0:8000`.
