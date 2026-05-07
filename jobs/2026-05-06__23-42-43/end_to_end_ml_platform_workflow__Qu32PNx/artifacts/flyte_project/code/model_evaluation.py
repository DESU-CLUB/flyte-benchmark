"""
model_evaluation.py
-------------------
Flyte 2.0 task: Evaluate all trained model artifacts on a held-out test split.

Metrics computed
~~~~~~~~~~~~~~~~
• Accuracy
• Weighted F1
• Weighted Precision / Recall
• ROC-AUC (binary)
• Matthews Correlation Coefficient
• Log Loss
• Confusion-matrix summary
• Feature importances (where available)
"""

import pickle
import typing
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from flytekit import task
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    matthews_corrcoef,
    log_loss,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split

from data_ingestion import RawDataset
from model_training import ModelArtifact, TrainingConfig


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass
class EvaluationResult:
    model_name: str = ""
    test_metrics: typing.Dict[str, float] = field(default_factory=dict)
    confusion_matrix: typing.List[typing.List[int]] = field(default_factory=list)
    feature_importances: typing.Dict[str, float] = field(default_factory=dict)
    cv_mean_accuracy: float = 0.0
    cv_std_accuracy: float = 0.0
    composite_score: float = 0.0   # weighted aggregate used for ranking


@dataclass
class EvaluationReport:
    results: typing.List[EvaluationResult] = field(default_factory=list)
    ranking: typing.List[str] = field(default_factory=list)   # best → worst
    best_model_name: str = ""


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@task(cache=True, cache_version="v1.0")
def evaluate_models(
    df: pd.DataFrame,
    raw_meta: RawDataset,
    artifacts: typing.List[ModelArtifact],
    train_config: TrainingConfig,
) -> EvaluationReport:
    """
    Evaluate all model artifacts on the same held-out test set.
    """
    # ---- recreate the hold-out test set --------------------------------
    feature_cols = [c for c in df.columns if c != raw_meta.target_column]
    X = df[feature_cols].values
    y = df[raw_meta.target_column].values

    _, X_test, _, y_test = train_test_split(
        X, y,
        test_size=train_config.test_size,
        random_state=train_config.random_state,
        stratify=y,
    )

    results: typing.List[EvaluationResult] = []

    for art in artifacts:
        # Load model from FlyteFile
        with open(art.model_file, "rb") as fh:
            pipeline = pickle.load(fh)

        y_pred = pipeline.predict(X_test)
        y_prob = (
            pipeline.predict_proba(X_test)[:, 1]
            if hasattr(pipeline.named_steps["model"], "predict_proba")
            else None
        )

        # ---- core metrics ----------------------------------------------
        metrics: typing.Dict[str, float] = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "f1_weighted": float(f1_score(y_test, y_pred, average="weighted")),
            "precision_weighted": float(
                precision_score(y_test, y_pred, average="weighted", zero_division=0)
            ),
            "recall_weighted": float(
                recall_score(y_test, y_pred, average="weighted", zero_division=0)
            ),
            "mcc": float(matthews_corrcoef(y_test, y_pred)),
        }
        if y_prob is not None:
            try:
                metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob))
                metrics["log_loss"] = float(log_loss(y_test, y_prob))
            except Exception:
                pass

        # ---- confusion matrix -----------------------------------------
        cm = confusion_matrix(y_test, y_pred).tolist()

        # ---- feature importances (RF / GBM) ----------------------------
        fi: typing.Dict[str, float] = {}
        raw_model = pipeline.named_steps["model"]
        if hasattr(raw_model, "feature_importances_"):
            fi = {
                col: float(imp)
                for col, imp in zip(art.feature_columns, raw_model.feature_importances_)
            }
            fi = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)[:10])
        elif hasattr(raw_model, "coef_"):
            coefs = np.abs(raw_model.coef_[0])
            fi = {
                col: float(v)
                for col, v in zip(art.feature_columns, coefs / coefs.sum())
            }
            fi = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)[:10])

        # ---- composite score: 40% accuracy + 30% F1 + 30% ROC-AUC ----
        composite = (
            0.40 * metrics["accuracy"]
            + 0.30 * metrics["f1_weighted"]
            + 0.30 * metrics.get("roc_auc", metrics["accuracy"])
        )

        cv_mean = float(np.mean(art.cv_scores)) if art.cv_scores else 0.0
        cv_std = float(np.std(art.cv_scores)) if art.cv_scores else 0.0

        res = EvaluationResult(
            model_name=art.model_name,
            test_metrics=metrics,
            confusion_matrix=cm,
            feature_importances=fi,
            cv_mean_accuracy=cv_mean,
            cv_std_accuracy=cv_std,
            composite_score=composite,
        )
        results.append(res)

        print(
            f"[evaluate_models] {art.model_name:25s} "
            f"acc={metrics['accuracy']:.4f}  "
            f"f1={metrics['f1_weighted']:.4f}  "
            f"roc_auc={metrics.get('roc_auc', float('nan')):.4f}  "
            f"composite={composite:.4f}"
        )

    # ---- rank models by composite score --------------------------------
    results.sort(key=lambda r: r.composite_score, reverse=True)
    ranking = [r.model_name for r in results]
    best_name = ranking[0] if ranking else ""

    report = EvaluationReport(results=results, ranking=ranking, best_model_name=best_name)
    print(f"[evaluate_models] Ranking: {ranking}")
    print(f"[evaluate_models] Best model: {best_name}")
    return report
