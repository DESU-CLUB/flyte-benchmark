import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from flytekit import task
from typing import List
import json
import os
from datetime import datetime

# Define the log file path
LOG_FILE = "/home/user/flyte_project/platform_output.json"

def log_event(event_type, message, data=None):
    log_entry = {
        "event": event_type,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    # Ensure directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    # Append to log file
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

@task
def ingest_data() -> pd.DataFrame:
    """Ingests data from the Iris dataset."""
    data = load_iris(as_frame=True)
    df = data.frame
    log_event("ingestion", "Data ingested successfully", {"rows": len(df)})
    return df

@task
def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validates the ingested data."""
    if df.isnull().values.any():
        log_event("validation_failed", "Data contains null values")
        raise ValueError("Data contains null values")
    log_event("validation", "Data validation passed", {"columns": list(df.columns)})
    return df

@task
def train_model(df: pd.DataFrame, model_type: str) -> dict:
    """Trains a specific type of model and returns its performance."""
    X = df.drop(columns="target")
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if model_type == "logistic_regression":
        model = LogisticRegression(max_iter=200)
    elif model_type == "random_forest":
        model = RandomForestClassifier(n_estimators=100)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    result = {"model_type": model_type, "accuracy": float(accuracy)}
    log_event("training", f"Model trained: {model_type}", result)
    return result

@task
def select_best_model(results: List[dict]) -> dict:
    """Selects the best model based on accuracy."""
    best_model = max(results, key=lambda x: x["accuracy"])
    log_event("selection", "Best model selected", best_model)
    return best_model
