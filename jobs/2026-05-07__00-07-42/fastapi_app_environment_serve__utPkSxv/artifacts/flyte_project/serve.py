"""
FastAPI server startup script for Flyte 2.0 ML Prediction API.
"""
import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )