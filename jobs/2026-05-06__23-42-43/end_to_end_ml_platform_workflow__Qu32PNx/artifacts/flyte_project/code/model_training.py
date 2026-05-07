"""
model_training.py
-----------------
Flyte 2.0 tasks: Train multiple ML models in parallel.

Models
~~~~~~
1. RandomForestClassifier
2. GradientBoostingClassifier
3. LogisticRegression

Each training task:
  • Splits data into train / validation sets
  • Scales features
  • Trains the model with a manual hyper-parameter grid search
  • Returns a FlyteFile-backed model artifact + training metadata
"""

import os
import pickle
import tempfile
import typing
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from flytekit import task
from flytekit.types.file import FlyteFile
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data_ingestion import RawDataset


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    test_size: float = 0.20
    val_size: float = 0.15
    random_state: int = 42
    cv_folds: int = 5


@dataclass
class ModelArtifact:
    """Trained model artifact stored as a FlyteFile (pickle)."""
    model_name: str = ""
    model_file: FlyteFile = field(default_factory=lambda: FlyteFile(path="/dev/null"))
    hyperparameters: typing.Dict[str, str] = field(default_factory=dict)
    train_metrics: typing.Dict[str, float] = field(default_factory=dict)
    val_metrics: typing.Dict[str, float] = field(default_factory=dict)
    cv_scores: typing.List[float] = field(default_factory=list)
    feature_columns: typing.List[str] = field(default_factory=list)
    target_column: str = "target"
    training_config: typing.Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _split_xy(
    df: pd.DataFrame,
    feature_cols: typing.List[str],
    target_col: str,
    test_size: float,
    val_size: float,
    random_state: int,
):
    X = df[feature_cols].values
    y = df[target_col].values

    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    relative_val = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp,
        test_size=relative_val,
        random_state=random_state,
        stratify=y_temp,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def _compute_metrics(pipeline, X, y) -> typing.Dict[str, float]:
    from sklearn.metrics import (
        accuracy_score, f1_score, roc_auc_score, precision_score, recall_score
    )
    y_pred = pipeline.predict(X)
    y_prob = (
        pipeline.predict_proba(X)[:, 1]
        if hasattr(pipeline.named_steps["model"], "predict_proba")
        else None
    )
    metrics = {
        "accuracy": float(accuracy_score(y, y_pred)),
        "f1": float(f1_score(y, y_pred, average="weighted")),
        "precision": float(precision_score(y, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y, y_pred, average="weighted", zero_division=0)),
    }
    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y, y_prob))
        except Exception:
            pass
    return metrics


def _save_pipeline(pipeline) -> FlyteFile:
    """Pickle a sklearn pipeline into a temp file and return a FlyteFile."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pkl", delete=False)
    pickle.dump(pipeline, tmp)
    tmp.close()
    return FlyteFile(path=tmp.name)


# ---------------------------------------------------------------------------
# Task 1 — Random Forest
# ---------------------------------------------------------------------------

@task(cache=True, cache_version="v1.0")
def train_random_forest(
    df: pd.DataFrame,
    raw_meta: RawDataset,
    config: TrainingConfig,
) -> ModelArtifact:
    """Train a Random Forest classifier."""
    feature_cols = [c for c in df.columns if c != raw_meta.target_column]
    X_train, X_val, X_test, y_train, y_val, y_test = _split_xy(
        df, feature_cols, raw_meta.target_column,
        config.test_size, config.val_size, config.random_state,
    )

    best_val_acc, best_hp, best_pipeline = -1.0, {}, None
    for n_est in [100, 200]:
        for max_depth in [None, 10, 20]:
            hp = {"n_estimators": n_est, "max_depth": max_depth}
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("model", RandomForestClassifier(
                    random_state=config.random_state, n_jobs=-1, **hp
                )),
            ])
            pipe.fit(X_train, y_train)
            val_acc = pipe.score(X_val, y_val)
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_hp = hp
                best_pipeline = pipe

    cv_scores = cross_val_score(
        best_pipeline, X_train, y_train, cv=config.cv_folds, scoring="accuracy"
    )

    artifact = ModelArtifact(
        model_name="RandomForest",
        model_file=_save_pipeline(best_pipeline),
        hyperparameters={k: str(v) for k, v in best_hp.items()},
        train_metrics=_compute_metrics(best_pipeline, X_train, y_train),
        val_metrics=_compute_metrics(best_pipeline, X_val, y_val),
        cv_scores=cv_scores.tolist(),
        feature_columns=feature_cols,
        target_column=raw_meta.target_column,
        training_config={"test_size": str(config.test_size), "cv_folds": str(config.cv_folds)},
    )

    print(f"[train_random_forest] Best HP: {best_hp}")
    print(f"[train_random_forest] Val accuracy: {best_val_acc:.4f}")
    print(f"[train_random_forest] CV mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    return artifact


# ---------------------------------------------------------------------------
# Task 2 — Gradient Boosting
# ---------------------------------------------------------------------------

@task(cache=True, cache_version="v1.0")
def train_gradient_boosting(
    df: pd.DataFrame,
    raw_meta: RawDataset,
    config: TrainingConfig,
) -> ModelArtifact:
    """Train a Gradient Boosting classifier."""
    feature_cols = [c for c in df.columns if c != raw_meta.target_column]
    X_train, X_val, X_test, y_train, y_val, y_test = _split_xy(
        df, feature_cols, raw_meta.target_column,
        config.test_size, config.val_size, config.random_state,
    )

    best_val_acc, best_hp, best_pipeline = -1.0, {}, None
    for lr in [0.05, 0.1]:
        for n_est in [100, 200]:
            hp = {"learning_rate": lr, "n_estimators": n_est, "max_depth": 4}
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("model", GradientBoostingClassifier(
                    random_state=config.random_state, **hp
                )),
            ])
            pipe.fit(X_train, y_train)
            val_acc = pipe.score(X_val, y_val)
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_hp = hp
                best_pipeline = pipe

    cv_scores = cross_val_score(
        best_pipeline, X_train, y_train, cv=config.cv_folds, scoring="accuracy"
    )

    artifact = ModelArtifact(
        model_name="GradientBoosting",
        model_file=_save_pipeline(best_pipeline),
        hyperparameters={k: str(v) for k, v in best_hp.items()},
        train_metrics=_compute_metrics(best_pipeline, X_train, y_train),
        val_metrics=_compute_metrics(best_pipeline, X_val, y_val),
        cv_scores=cv_scores.tolist(),
        feature_columns=feature_cols,
        target_column=raw_meta.target_column,
        training_config={"test_size": str(config.test_size), "cv_folds": str(config.cv_folds)},
    )

    print(f"[train_gradient_boosting] Best HP: {best_hp}")
    print(f"[train_gradient_boosting] Val accuracy: {best_val_acc:.4f}")
    print(f"[train_gradient_boosting] CV mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    return artifact


# ---------------------------------------------------------------------------
# Task 3 — Logistic Regression
# ---------------------------------------------------------------------------

@task(cache=True, cache_version="v1.0")
def train_logistic_regression(
    df: pd.DataFrame,
    raw_meta: RawDataset,
    config: TrainingConfig,
) -> ModelArtifact:
    """Train a Logistic Regression classifier."""
    feature_cols = [c for c in df.columns if c != raw_meta.target_column]
    X_train, X_val, X_test, y_train, y_val, y_test = _split_xy(
        df, feature_cols, raw_meta.target_column,
        config.test_size, config.val_size, config.random_state,
    )

    best_val_acc, best_hp, best_pipeline = -1.0, {}, None
    for C in [0.01, 0.1, 1.0, 10.0]:
        for solver in ["lbfgs", "saga"]:
            hp = {"C": C, "solver": solver, "max_iter": 1000}
            try:
                pipe = Pipeline([
                    ("scaler", StandardScaler()),
                    ("model", LogisticRegression(
                        random_state=config.random_state, **hp
                    )),
                ])
                pipe.fit(X_train, y_train)
                val_acc = pipe.score(X_val, y_val)
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    best_hp = hp
                    best_pipeline = pipe
            except Exception as exc:
                print(f"[train_logistic_regression] Skipped {hp}: {exc}")

    cv_scores = cross_val_score(
        best_pipeline, X_train, y_train, cv=config.cv_folds, scoring="accuracy"
    )

    artifact = ModelArtifact(
        model_name="LogisticRegression",
        model_file=_save_pipeline(best_pipeline),
        hyperparameters={k: str(v) for k, v in best_hp.items()},
        train_metrics=_compute_metrics(best_pipeline, X_train, y_train),
        val_metrics=_compute_metrics(best_pipeline, X_val, y_val),
        cv_scores=cv_scores.tolist(),
        feature_columns=feature_cols,
        target_column=raw_meta.target_column,
        training_config={"test_size": str(config.test_size), "cv_folds": str(config.cv_folds)},
    )

    print(f"[train_logistic_regression] Best HP: {best_hp}")
    print(f"[train_logistic_regression] Val accuracy: {best_val_acc:.4f}")
    print(f"[train_logistic_regression] CV mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    return artifact
