"""
Standalone Test Script for Flyte 2.0 ML Platform
This script demonstrates the workflow logic without requiring full Flyte installation.
Can be used for testing and development.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import time

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.datasets import make_classification
import pickle

# Constants
PROJECT_DIR = "/home/user/flyte_project"
LOG_FILE = os.path.join(PROJECT_DIR, "platform_output.json")
ARTIFACTS_DIR = "/logs/artifacts"


@dataclass
class ModelMetrics:
    """Data class to hold model evaluation metrics"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_time: float


@dataclass
class ModelResult:
    """Data class to hold model training results"""
    model_name: str
    metrics: ModelMetrics
    model_path: str


@dataclass
class ValidationResult:
    """Data class to hold validation results"""
    is_valid: bool
    issues: List[str]
    statistics: Dict[str, float]


@dataclass
class BestModel:
    """Data class to hold the best model selection result"""
    model_name: str
    metrics: ModelMetrics
    model_path: str
    selection_criteria: str


def log_to_file(data: Dict):
    """Helper function to log data to platform_output.json"""
    try:
        existing_data = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                existing_data = json.load(f)
        
        data['timestamp'] = datetime.now().isoformat()
        existing_data.append(data)
        
        with open(LOG_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)
    except Exception as e:
        print(f"Error logging to file: {e}")


def data_ingestion(
    n_samples: int = 1000,
    n_features: int = 20,
    n_informative: int = 15,
    random_state: int = 42
) -> Tuple[str, str]:
    """
    Ingest and generate synthetic dataset for ML training.
    """
    print(f"Starting data ingestion with {n_samples} samples...")
    
    # Generate synthetic classification dataset
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_informative,
        n_redundant=2,
        n_repeated=0,
        n_classes=2,
        random_state=random_state
    )
    
    # Create DataFrame
    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df['target'] = y
    
    # Split into train and test sets
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=random_state)
    
    # Save to files
    train_path = os.path.join(PROJECT_DIR, "train_data.csv")
    test_path = os.path.join(PROJECT_DIR, "test_data.csv")
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    # Log ingestion
    log_to_file({
        "stage": "data_ingestion",
        "status": "completed",
        "n_samples": n_samples,
        "n_features": n_features,
        "train_size": len(train_df),
        "test_size": len(test_df),
        "train_path": train_path,
        "test_path": test_path
    })
    
    print(f"Data ingestion completed. Train: {len(train_df)} samples, Test: {len(test_df)} samples")
    
    return train_path, test_path


def data_validation(
    train_data: str,
    test_data: str,
    min_samples: int = 100,
    max_missing_ratio: float = 0.1
) -> ValidationResult:
    """
    Validate the ingested data for quality and consistency.
    """
    print("Starting data validation...")
    
    # Load data
    train_df = pd.read_csv(train_data)
    test_df = pd.read_csv(test_data)
    
    issues = []
    is_valid = True
    
    # Check sample size
    if len(train_df) < min_samples:
        issues.append(f"Training set has only {len(train_df)} samples, minimum required: {min_samples}")
        is_valid = False
    
    # Check for missing values
    train_missing = train_df.isnull().sum().sum() / (len(train_df) * len(train_df.columns))
    test_missing = test_df.isnull().sum().sum() / (len(test_df) * len(test_df.columns))
    
    if train_missing > max_missing_ratio:
        issues.append(f"Training set has {train_missing:.2%} missing values, maximum allowed: {max_missing_ratio:.2%}")
        is_valid = False
    
    if test_missing > max_missing_ratio:
        issues.append(f"Test set has {test_missing:.2%} missing values, maximum allowed: {max_missing_ratio:.2%}")
        is_valid = False
    
    # Check for target column
    if 'target' not in train_df.columns:
        issues.append("Training set missing 'target' column")
        is_valid = False
    
    if 'target' not in test_df.columns:
        issues.append("Test set missing 'target' column")
        is_valid = False
    
    # Calculate statistics
    statistics = {
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "train_features": len(train_df.columns) - 1,
        "train_missing_ratio": train_missing,
        "test_missing_ratio": test_missing,
        "target_distribution": train_df['target'].value_counts().to_dict()
    }
    
    # Log validation
    log_to_file({
        "stage": "data_validation",
        "status": "completed",
        "is_valid": is_valid,
        "issues": issues,
        "statistics": statistics
    })
    
    print(f"Data validation completed. Valid: {is_valid}, Issues: {len(issues)}")
    
    return ValidationResult(
        is_valid=is_valid,
        issues=issues,
        statistics=statistics
    )


def train_model(
    train_data: str,
    model_name: str,
    model_type: str,
    random_state: int = 42
) -> ModelResult:
    """
    Train a single ML model.
    """
    print(f"Training {model_name} ({model_type})...")
    
    # Load data
    train_df = pd.read_csv(train_data)
    X_train = train_df.drop('target', axis=1)
    y_train = train_df['target']
    
    # Select model based on type
    start_time = time.time()
    
    if model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=random_state,
            n_jobs=-1
        )
    elif model_type == "gradient_boosting":
        model = GradientBoostingClassifier(
            n_estimators=100,
            random_state=random_state
        )
    elif model_type == "logistic_regression":
        model = LogisticRegression(
            random_state=random_state,
            max_iter=1000
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Train model
    model.fit(X_train, y_train)
    training_time = time.time() - start_time
    
    # Save model
    model_path = os.path.join(PROJECT_DIR, f"{model_name}_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Calculate training metrics
    y_pred_train = model.predict(X_train)
    accuracy = accuracy_score(y_train, y_pred_train)
    precision = precision_score(y_train, y_pred_train, average='weighted')
    recall = recall_score(y_train, y_pred_train, average='weighted')
    f1 = f1_score(y_train, y_pred_train, average='weighted')
    
    # Create metrics
    metrics = ModelMetrics(
        model_name=model_name,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1,
        training_time=training_time
    )
    
    # Log training
    log_to_file({
        "stage": "model_training",
        "status": "completed",
        "model_name": model_name,
        "model_type": model_type,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "training_time": training_time,
        "model_path": model_path
    })
    
    print(f"Model {model_name} trained. Accuracy: {accuracy:.4f}, Time: {training_time:.2f}s")
    
    return ModelResult(
        model_name=model_name,
        metrics=metrics,
        model_path=model_path
    )


def train_models_parallel(
    train_data: str,
    model_configs: List[Dict[str, str]],
    random_state: int = 42
) -> List[ModelResult]:
    """
    Train multiple models in parallel (simulated for standalone execution).
    """
    print(f"Training {len(model_configs)} models...")
    
    results = []
    for config in model_configs:
        result = train_model(
            train_data=train_data,
            model_name=config["name"],
            model_type=config["type"],
            random_state=random_state
        )
        results.append(result)
    
    return results


def evaluate_models(
    model_results: List[ModelResult],
    test_data: str
) -> List[ModelResult]:
    """
    Evaluate trained models on test data.
    """
    print(f"Evaluating {len(model_results)} models...")
    
    # Load test data
    test_df = pd.read_csv(test_data)
    X_test = test_df.drop('target', axis=1)
    y_test = test_df['target']
    
    evaluated_results = []
    
    for result in model_results:
        print(f"Evaluating {result.model_name}...")
        
        # Load model
        with open(result.model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Update metrics
        updated_metrics = ModelMetrics(
            model_name=result.model_name,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            training_time=result.metrics.training_time
        )
        
        updated_result = ModelResult(
            model_name=result.model_name,
            metrics=updated_metrics,
            model_path=result.model_path
        )
        
        evaluated_results.append(updated_result)
        
        # Log evaluation
        log_to_file({
            "stage": "model_evaluation",
            "status": "completed",
            "model_name": result.model_name,
            "test_accuracy": accuracy,
            "test_precision": precision,
            "test_recall": recall,
            "test_f1_score": f1
        })
    
    print("Model evaluation completed")
    
    return evaluated_results


def select_best_model(
    model_results: List[ModelResult],
    selection_metric: str = "f1_score"
) -> BestModel:
    """
    Select the best model based on specified metric.
    """
    print(f"Selecting best model based on {selection_metric}...")
    
    # Sort models by selected metric
    metric_values = []
    for result in model_results:
        metric_value = getattr(result.metrics, selection_metric)
        metric_values.append((result, metric_value))
    
    # Sort in descending order
    metric_values.sort(key=lambda x: x[1], reverse=True)
    
    best_result, best_value = metric_values[0]
    
    # Create BestModel
    best_model = BestModel(
        model_name=best_result.model_name,
        metrics=best_result.metrics,
        model_path=best_result.model_path,
        selection_criteria=selection_metric
    )
    
    # Log selection
    log_to_file({
        "stage": "model_selection",
        "status": "completed",
        "best_model": best_result.model_name,
        "selection_metric": selection_metric,
        "best_value": best_value,
        "all_models": [
            {
                "name": r.model_name,
                selection_metric: getattr(r.metrics, selection_metric)
            }
            for r in model_results
        ]
    })
    
    print(f"Best model selected: {best_model.model_name} with {selection_metric}={best_value:.4f}")
    
    return best_model


def ml_platform_pipeline(
    n_samples: int = 1000,
    n_features: int = 20,
    n_informative: int = 15,
    random_state: int = 42,
    selection_metric: str = "f1_score"
) -> BestModel:
    """
    End-to-end ML platform pipeline.
    """
    print("="*60)
    print("FLYTE 2.0 ML PLATFORM - STANDALONE EXECUTION")
    print("="*60)
    
    # Step 1: Data Ingestion
    print("\n[Step 1/5] Data Ingestion")
    print("-" * 60)
    train_data, test_data = data_ingestion(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_informative,
        random_state=random_state
    )
    
    # Step 2: Data Validation
    print("\n[Step 2/5] Data Validation")
    print("-" * 60)
    validation_result = data_validation(
        train_data=train_data,
        test_data=test_data
    )
    
    if not validation_result.is_valid:
        print("Data validation failed. Please check the issues.")
        return None
    
    # Step 3: Parallel Model Training
    print("\n[Step 3/5] Parallel Model Training")
    print("-" * 60)
    model_configs = [
        {"name": "random_forest", "type": "random_forest"},
        {"name": "gradient_boosting", "type": "gradient_boosting"},
        {"name": "logistic_regression", "type": "logistic_regression"}
    ]
    
    model_results = train_models_parallel(
        train_data=train_data,
        model_configs=model_configs,
        random_state=random_state
    )
    
    # Step 4: Model Evaluation
    print("\n[Step 4/5] Model Evaluation")
    print("-" * 60)
    evaluated_models = evaluate_models(
        model_results=model_results,
        test_data=test_data
    )
    
    # Step 5: Model Selection
    print("\n[Step 5/5] Model Selection")
    print("-" * 60)
    best_model = select_best_model(
        model_results=evaluated_models,
        selection_metric=selection_metric
    )
    
    return best_model


def main():
    """Main entry point for standalone execution"""
    print("\n" + "="*60)
    print("FLYTE 2.0 ML PLATFORM - STANDALONE TEST")
    print("="*60)
    print("\nThis is a standalone version of the Flyte ML Platform")
    print("for testing without full Flyte infrastructure.\n")
    
    # Initialize log file
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    # Run the pipeline
    best_model = ml_platform_pipeline(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        random_state=42,
        selection_metric="f1_score"
    )
    
    if best_model:
        print(f"\n" + "="*60)
        print("ML PLATFORM WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\nBest Model: {best_model.model_name}")
        print(f"Selection Criteria: {best_model.selection_criteria}")
        print(f"\nMetrics:")
        print(f"  Accuracy:  {best_model.metrics.accuracy:.4f}")
        print(f"  Precision: {best_model.metrics.precision:.4f}")
        print(f"  Recall:    {best_model.metrics.recall:.4f}")
        print(f"  F1 Score:  {best_model.metrics.f1_score:.4f}")
        print(f"  Training Time: {best_model.metrics.training_time:.2f}s")
        print(f"\nModel saved to: {best_model.model_path}")
        print(f"Platform output logged to: {LOG_FILE}")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("ML PLATFORM WORKFLOW FAILED")
        print("="*60)


if __name__ == "__main__":
    main()