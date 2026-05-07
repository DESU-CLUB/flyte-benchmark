"""
workflow.py
-----------
Flyte 2.0 — End-to-End ML Platform Workflow

Pipeline stages
~~~~~~~~~~~~~~~
  1. ingest_data          — generate / load raw dataset
  2. validate_data        — quality checks, imputation, outlier clipping
  3. train_random_forest  ─┐
     train_gradient_boost ─┼─ parallel fan-out
     train_logistic_regr  ─┘
  4. evaluate_models      — uniform hold-out evaluation
  5. select_best_model    — rank and pick winner

                    ┌──────────────────────────────────┐
                    │         ml_platform_workflow      │
                    └──────────────────────────────────┘
                               │
               ┌───────────────▼──────────────────┐
               │          ingest_data              │
               └───────────────┬──────────────────┘
                               │
               ┌───────────────▼──────────────────┐
               │          validate_data            │
               └───────┬───────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      train_RF    train_GBM    train_LR
          └────────────┼────────────┘
                       │
               ┌───────▼──────────────┐
               │    evaluate_models   │
               └───────┬──────────────┘
                       │
               ┌───────▼──────────────┐
               │   select_best_model  │
               └──────────────────────┘
"""

import typing
from flytekit import workflow

from data_ingestion import ingest_data, IngestionConfig
from data_validation import validate_data, ValidationConfig
from model_training import (
    train_random_forest,
    train_gradient_boosting,
    train_logistic_regression,
    TrainingConfig,
    ModelArtifact,
)
from model_evaluation import evaluate_models
from model_selection import select_best_model, SelectionConfig, SelectedModel


@workflow
def ml_platform_workflow(
    ingestion_cfg: IngestionConfig = IngestionConfig(),
    validation_cfg: ValidationConfig = ValidationConfig(),
    training_cfg: TrainingConfig = TrainingConfig(),
    selection_cfg: SelectionConfig = SelectionConfig(),
) -> SelectedModel:
    """
    Full end-to-end ML platform workflow.

    Parameters
    ----------
    ingestion_cfg  : Dataset generation / ingestion settings
    validation_cfg : Data quality thresholds and cleaning strategy
    training_cfg   : Train/val/test split sizes, CV folds
    selection_cfg  : Model selection criteria

    Returns
    -------
    SelectedModel — the best trained model with full provenance
    """

    # ── Stage 1: Ingest ──────────────────────────────────────────────────
    raw_df, raw_meta = ingest_data(config=ingestion_cfg)

    # ── Stage 2: Validate & Clean ─────────────────────────────────────────
    clean_df, val_report = validate_data(
        df=raw_df,
        raw_meta=raw_meta,
        config=validation_cfg,
    )

    # ── Stage 3: Parallel Model Training ─────────────────────────────────
    rf_artifact = train_random_forest(
        df=clean_df,
        raw_meta=raw_meta,
        config=training_cfg,
    )
    gbm_artifact = train_gradient_boosting(
        df=clean_df,
        raw_meta=raw_meta,
        config=training_cfg,
    )
    lr_artifact = train_logistic_regression(
        df=clean_df,
        raw_meta=raw_meta,
        config=training_cfg,
    )

    # Collect artifacts into a list for downstream tasks
    all_artifacts: typing.List[ModelArtifact] = [rf_artifact, gbm_artifact, lr_artifact]

    # ── Stage 4: Evaluate ─────────────────────────────────────────────────
    eval_report = evaluate_models(
        df=clean_df,
        raw_meta=raw_meta,
        artifacts=all_artifacts,
        train_config=training_cfg,
    )

    # ── Stage 5: Select Best ──────────────────────────────────────────────
    best_model = select_best_model(
        eval_report=eval_report,
        artifacts=all_artifacts,
        config=selection_cfg,
    )

    return best_model
