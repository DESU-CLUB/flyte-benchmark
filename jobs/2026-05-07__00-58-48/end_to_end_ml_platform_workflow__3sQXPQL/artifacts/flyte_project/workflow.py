import json
import typing
from flytekit import task, workflow
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Ingest Data
@task
def ingest_data() -> pd.DataFrame:
    # Create some dummy data for classification
    np.random.seed(42)
    X = np.random.rand(1000, 5)
    y = (X[:, 0] + X[:, 1] > 1.0).astype(int)
    
    df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(5)])
    df["target"] = y
    return df

# 2. Validate Data
@task
def validate_data(df: pd.DataFrame) -> bool:
    if df.isnull().values.any():
        raise ValueError("Data contains null values")
    if "target" not in df.columns:
        raise ValueError("Target column missing")
    return True

# 3. Train models in parallel
@task
def train_model_lr(df: pd.DataFrame, is_valid: bool) -> float:
    if not is_valid:
        raise ValueError("Invalid data")
    
    X = df.drop("target", axis=1)
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    return float(accuracy_score(y_test, preds))

@task
def train_model_rf(df: pd.DataFrame, is_valid: bool) -> float:
    if not is_valid:
        raise ValueError("Invalid data")
    
    X = df.drop("target", axis=1)
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    return float(accuracy_score(y_test, preds))

@task
def train_model_svc(df: pd.DataFrame, is_valid: bool) -> float:
    if not is_valid:
        raise ValueError("Invalid data")
    
    X = df.drop("target", axis=1)
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = SVC()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    return float(accuracy_score(y_test, preds))

# 4. Evaluate and 5. Select the best model
@task
def select_best_model(acc_lr: float, acc_rf: float, acc_svc: float) -> str:
    models = {"LogisticRegression": acc_lr, "RandomForest": acc_rf, "SVC": acc_svc}
    best_model = max(models, key=models.get)
    best_acc = models[best_model]
    
    output = {
        "models_evaluated": models,
        "best_model": best_model,
        "best_accuracy": best_acc
    }
    
    # Write to log file
    with open("/home/user/flyte_project/platform_output.json", "w") as f:
        json.dump(output, f, indent=4)
        
    return best_model

@workflow
def ml_platform_workflow() -> str:
    df = ingest_data()
    is_valid = validate_data(df=df)
    
    acc_lr = train_model_lr(df=df, is_valid=is_valid)
    acc_rf = train_model_rf(df=df, is_valid=is_valid)
    acc_svc = train_model_svc(df=df, is_valid=is_valid)
    
    best = select_best_model(acc_lr=acc_lr, acc_rf=acc_rf, acc_svc=acc_svc)
    return best

if __name__ == "__main__":
    best_model = ml_platform_workflow()
    print(f"Workflow completed. Best model: {best_model}")
