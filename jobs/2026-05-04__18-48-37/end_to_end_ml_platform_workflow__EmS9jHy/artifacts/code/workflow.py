import pandas as pd
from typing import List, Tuple
from flytekit import task, workflow
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.datasets import load_iris
import json
import os
from dataclasses import dataclass

# Define a type for training results
@dataclass
class ModelResult:
    model_name: str
    accuracy: float
    model_path: str

@task
def ingest_data() -> pd.DataFrame:
    """Ingest the Iris dataset."""
    iris = load_iris()
    df = pd.DataFrame(data=iris.data, columns=iris.feature_names)
    df['target'] = iris.target
    print("Data ingested successfully.")
    return df

@task
def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate data for null values and expected columns."""
    if df.isnull().values.any():
        raise ValueError("Data contains null values")
    expected_columns = 5 # 4 features + 1 target
    if len(df.columns) != expected_columns:
        raise ValueError(f"Expected {expected_columns} columns, got {len(df.columns)}")
    print("Data validation passed.")
    return df

@task
def split_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train and test sets."""
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    print(f"Data split: {len(train_df)} train, {len(test_df)} test.")
    return train_df, test_df

@task
def train_model(train_df: pd.DataFrame, test_df: pd.DataFrame, model_type: str) -> ModelResult:
    """Train a model and return its performance."""
    X_train = train_df.drop('target', axis=1)
    y_train = train_df['target']
    X_test = test_df.drop('target', axis=1)
    y_test = test_df['target']
    
    if model_type == "logistic_regression":
        model = LogisticRegression(max_iter=200)
    elif model_type == "random_forest":
        model = RandomForestClassifier(n_estimators=100)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    # Simulated model path
    model_dir = "/home/user/flyte_project/models"
    artifact_dir = "/logs/artifacts/models"
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(artifact_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, f"{model_type}.joblib")
    artifact_model_path = os.path.join(artifact_dir, f"{model_type}.joblib")
    
    # In a real scenario we'd use joblib.dump(model, model_path)
    with open(model_path, "w") as f:
        f.write(f"Model: {model_type}\nAccuracy: {acc}")
    with open(artifact_model_path, "w") as f:
        f.write(f"Model: {model_type}\nAccuracy: {acc}")
    
    print(f"Trained {model_type} with accuracy: {acc}")
    return ModelResult(model_name=model_type, accuracy=acc, model_path=model_path)

@task
def select_best_model(results: List[ModelResult]) -> ModelResult:
    """Select the best performing model."""
    best_result = max(results, key=lambda x: x.accuracy)
    
    output_log = {
        "best_model": best_result.model_name,
        "accuracy": best_result.accuracy,
        "model_path": best_result.model_path,
        "all_results": [
            {"model": r.model_name, "accuracy": r.accuracy} for r in results
        ]
    }
    
    log_path = "/home/user/flyte_project/platform_output.json"
    with open(log_path, "w") as f:
        json.dump(output_log, f, indent=4)
    
    # Save to artifacts
    os.makedirs("/logs/artifacts/reports", exist_ok=True)
    with open("/logs/artifacts/reports/platform_output.json", "w") as f:
        json.dump(output_log, f, indent=4)
    
    print(f"Best model selected: {best_result.model_name} with accuracy {best_result.accuracy}")
    return best_result

@workflow
def ml_platform_workflow() -> ModelResult:
    """Complete ML Platform Workflow."""
    raw_data = ingest_data()
    validated_data = validate_data(df=raw_data)
    train_df, test_df = split_data(df=validated_data)
    
    # Parallel training of multiple models
    lr_result = train_model(train_df=train_df, test_df=test_df, model_type="logistic_regression")
    rf_result = train_model(train_df=train_df, test_df=test_df, model_type="random_forest")
    
    # Selection
    return select_best_model(results=[lr_result, rf_result])

if __name__ == "__main__":
    # Local execution for testing purposes
    print("Running workflow locally...")
    try:
        result = ml_platform_workflow()
        print(f"Workflow finished. Best model: {result.model_name}")
    except Exception as e:
        print(f"Local execution failed: {e}")
        import traceback
        traceback.print_exc()
        print("Note: This script is intended to be run in a Flyte-enabled environment.")
