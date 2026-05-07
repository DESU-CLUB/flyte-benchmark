# Flyte 2.0 FastAPI ML Prediction API

A machine learning prediction API built with Flyte 2.0 and FastAPI, featuring `FastAPIAppEnvironment` and `@env.task` for ML processing.

## Features

- **FastAPI Integration**: RESTful API with automatic OpenAPI documentation
- **Flyte 2.0 Integration**: Uses `FastAPIAppEnvironment` for seamless Flyte integration
- **ML Prediction**: Built-in RandomForest model trained on Iris dataset
- **Task-based Processing**: Uses `@env.task` decorator for ML prediction tasks

## Project Structure

```
flyte_project/
├── __init__.py          # Package initialization
├── app.py               # Main FastAPI app with Flyte integration
├── serve.py             # Startup script
├── requirements.txt     # Python dependencies
└── README.md           # Documentation
```

## Installation

```bash
cd /home/user/flyte_project
pip install -r requirements.txt
```

## Running the Server

```bash
python /home/user/flyte_project/serve.py
```

The server will start on `http://0.0.0.0:8000`

## API Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "framework": "Flyte 2.0",
  "app": "FastAPI ML Prediction API"
}
```

### POST /predict
Make predictions using the trained ML model.

**Request Body:**
```json
{
  "features": [5.1, 3.5, 1.4, 0.2]
}
```

**Response:**
```json
{
  "prediction": 0,
  "confidence": 1.0,
  "class_name": "setosa"
}
```

### GET /
Root endpoint with API information.

## Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Flyte Integration

This project demonstrates Flyte 2.0's `FastAPIAppEnvironment`:

- Uses `flyte.app.extras.FastAPIAppEnvironment` for FastAPI integration
- Implements ML processing with `@env.task` decorator
- Leverages `flyte.TaskEnvironment` for task execution

## Model

The API uses a RandomForest classifier trained on the Iris dataset with 4 features:
- Sepal length
- Sepal width
- Petal length
- Petal width

The model predicts one of three iris classes:
- setosa (0)
- versicolor (1)
- virginica (2)