from __future__ import annotations

import json
import os
from typing import Dict, List, NamedTuple

import numpy as np
import pandas as pd
from flytekit import task, workflow
from sklearn.datasets import make_classification
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

PLATFORM_LOG_PATH = "/home/user/flyte_project/platform_output.json"


class ModelMetrics(NamedTuple):
    name: str
    accuracy: float
    f1: float


@task
def ingest_data(rows: int = 1000, features: int = 12) -> tuple[pd.DataFrame, pd.Series]:
    data, labels = make_classification(
        n_samples=rows,
        n_features=features,
        n_informative=8,
        n_redundant=2,
        random_state=17,
    )
    feature_columns = [f"feature_{idx}" for idx in range(features)]
    dataframe = pd.DataFrame(data, columns=feature_columns)
    target = pd.Series(labels, name="target")
    return dataframe, target


@task
def validate_data(features: pd.DataFrame, target: pd.Series) -> Dict[str, object]:
    null_count = int(features.isnull().sum().sum()) + int(target.isnull().sum())
    unique_labels = int(target.nunique())
    feature_ranges = {
        column: {
            "min": float(features[column].min()),
            "max": float(features[column].max()),
        }
        for column in features.columns
    }
    if null_count > 0:
        raise ValueError("Input data contains null values.")
    if unique_labels < 2:
        raise ValueError("Target variable needs at least 2 classes.")

    return {
        "rows": int(features.shape[0]),
        "features": int(features.shape[1]),
        "null_count": null_count,
        "label_distribution": target.value_counts(normalize=True).to_dict(),
        "feature_ranges": feature_ranges,
    }


def _train_model(model_name: str, model, features: pd.DataFrame, target: pd.Series) -> ModelMetrics:
    train_x, test_x, train_y, test_y = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    model.fit(train_x, train_y)
    predictions = model.predict(test_x)
    return ModelMetrics(
        name=model_name,
        accuracy=float(accuracy_score(test_y, predictions)),
        f1=float(f1_score(test_y, predictions)),
    )


@task
def train_logistic_regression(features: pd.DataFrame, target: pd.Series) -> ModelMetrics:
    model = LogisticRegression(max_iter=200, n_jobs=1)
    return _train_model("logistic_regression", model, features, target)


@task
def train_random_forest(features: pd.DataFrame, target: pd.Series) -> ModelMetrics:
    model = RandomForestClassifier(n_estimators=250, random_state=10)
    return _train_model("random_forest", model, features, target)


@task
def train_gradient_boosting(features: pd.DataFrame, target: pd.Series) -> ModelMetrics:
    model = GradientBoostingClassifier(random_state=33)
    return _train_model("gradient_boosting", model, features, target)


@task
def select_best_model(metrics: List[ModelMetrics]) -> ModelMetrics:
    if not metrics:
        raise ValueError("No metrics were provided to select_best_model.")
    return sorted(metrics, key=lambda item: (item.f1, item.accuracy), reverse=True)[0]


@task
def log_results(
    validation_report: Dict[str, object],
    metrics: List[ModelMetrics],
    best_model: ModelMetrics,
) -> str:
    payload = {
        "execution_id": os.getenv("FLYTE_INTERNAL_EXECUTION_ID", "local"),
        "validation_report": validation_report,
        "models": [metric._asdict() for metric in metrics],
        "best_model": best_model._asdict(),
    }
    os.makedirs(os.path.dirname(PLATFORM_LOG_PATH), exist_ok=True)
    with open(PLATFORM_LOG_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    return PLATFORM_LOG_PATH


@workflow
def ml_platform_workflow(rows: int = 1000, features: int = 12) -> tuple[ModelMetrics, str]:
    feature_data, target = ingest_data(rows=rows, features=features)
    validation_report = validate_data(features=feature_data, target=target)

    metrics = [
        train_logistic_regression(features=feature_data, target=target),
        train_random_forest(features=feature_data, target=target),
        train_gradient_boosting(features=feature_data, target=target),
    ]

    best_model = select_best_model(metrics=metrics)
    log_path = log_results(
        validation_report=validation_report, metrics=metrics, best_model=best_model
    )
    return best_model, log_path
