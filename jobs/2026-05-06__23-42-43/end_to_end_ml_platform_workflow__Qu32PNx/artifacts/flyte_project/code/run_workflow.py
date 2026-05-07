"""
run_workflow.py
---------------
Local execution driver for the Flyte 2.0 ML Platform workflow.

Runs the entire pipeline, collects outputs, and writes a structured
JSON report to  platform_output.json  in the project directory.

Usage
~~~~~
    python run_workflow.py
"""

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from flytekit.types.file import FlyteFile

# ── project imports ─────────────────────────────────────────────────────────
from data_ingestion import IngestionConfig
from data_validation import ValidationConfig
from model_training import TrainingConfig
from model_selection import SelectionConfig
from workflow import ml_platform_workflow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(val):
    """Recursively make a value JSON-serialisable."""
    if isinstance(val, FlyteFile):
        return f"<FlyteFile path={val.path}>"
    if isinstance(val, bytes):
        return f"<bytes len={len(val)}>"
    if hasattr(val, "__dataclass_fields__"):
        return {k: _safe(getattr(val, k)) for k in val.__dataclass_fields__}
    if isinstance(val, dict):
        return {str(k): _safe(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_safe(v) for v in val]
    if isinstance(val, float):
        return round(val, 6)
    return val


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    project_dir = Path(__file__).parent
    output_path = project_dir / "platform_output.json"

    # ── Configuration ────────────────────────────────────────────────────
    ingestion_cfg = IngestionConfig(
        n_samples=2000,
        n_features=20,
        n_informative=10,
        n_classes=2,
        random_state=42,
        noise_fraction=0.05,
        dataset_name="synthetic_classification_v1",
    )
    validation_cfg = ValidationConfig(
        max_missing_rate=0.15,
        iqr_multiplier=3.0,
        min_class_ratio=0.20,
        imputation_strategy="median",
    )
    training_cfg = TrainingConfig(
        test_size=0.20,
        val_size=0.15,
        random_state=42,
        cv_folds=5,
    )
    selection_cfg = SelectionConfig(
        primary_metric="composite_score",
        min_improvement=0.005,
        require_positive_mcc=True,
    )

    output: dict = {
        "platform": "Flyte 2.0 — End-to-End ML Platform",
        "run_started_at": datetime.now(timezone.utc).isoformat(),
        "run_completed_at": None,
        "elapsed_seconds": None,
        "status": "pending",
        "error": None,
        "configuration": {
            "ingestion": _safe(ingestion_cfg),
            "validation": _safe(validation_cfg),
            "training": _safe(training_cfg),
            "selection": _safe(selection_cfg),
        },
        "pipeline_stages": [
            "1. ingest_data",
            "2. validate_data",
            "3a. train_random_forest   (parallel)",
            "3b. train_gradient_boosting (parallel)",
            "3c. train_logistic_regression (parallel)",
            "4. evaluate_models",
            "5. select_best_model",
        ],
        "selected_model": None,
    }

    t0 = time.perf_counter()
    print("=" * 70)
    print("  Flyte 2.0  —  End-to-End ML Platform Workflow")
    print("=" * 70)

    try:
        # ── Execute workflow ─────────────────────────────────────────────
        selected = ml_platform_workflow(
            ingestion_cfg=ingestion_cfg,
            validation_cfg=validation_cfg,
            training_cfg=training_cfg,
            selection_cfg=selection_cfg,
        )

        elapsed = round(time.perf_counter() - t0, 3)
        output["status"] = "success"
        output["elapsed_seconds"] = elapsed
        output["run_completed_at"] = datetime.now(timezone.utc).isoformat()
        output["selected_model"] = _safe(selected)

        # ── Human-readable summary ────────────────────────────────────────
        print("\n" + "=" * 70)
        print("  PIPELINE COMPLETE")
        print("=" * 70)
        print(f"  Elapsed              : {elapsed}s")
        print(f"  Best model           : {selected.model_name}")
        print(f"  Composite score      : {selected.primary_score:.4f}")
        acc  = selected.test_metrics.get("accuracy", float("nan"))
        f1   = selected.test_metrics.get("f1_weighted", float("nan"))
        auc  = selected.test_metrics.get("roc_auc", float("nan"))
        mcc  = selected.test_metrics.get("mcc", float("nan"))
        ll   = selected.test_metrics.get("log_loss", float("nan"))
        print(f"  Test accuracy        : {acc:.4f}")
        print(f"  ROC-AUC              : {auc:.4f}")
        print(f"  F1 (weighted)        : {f1:.4f}")
        print(f"  MCC                  : {mcc:.4f}")
        print(f"  Log Loss             : {ll:.4f}")
        print(f"  CV accuracy          : {selected.cv_mean_accuracy:.4f} ± {selected.cv_std_accuracy:.4f}")
        print(f"  All composite scores : {selected.all_scores}")
        print(f"  Best hyperparameters : {selected.hyperparameters}")
        print(f"  Selection reason     : {selected.selection_reason}")
        if selected.warnings:
            for w in selected.warnings:
                print(f"  WARN                 : {w}")
        print(f"  Selected at          : {selected.selected_at}")
        print("=" * 70)

    except Exception as exc:
        elapsed = round(time.perf_counter() - t0, 3)
        output["status"] = "failed"
        output["elapsed_seconds"] = elapsed
        output["run_completed_at"] = datetime.now(timezone.utc).isoformat()
        output["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(f"\n[ERROR] Workflow failed: {exc}", file=sys.stderr)
        traceback.print_exc()

    # ── Write JSON output ────────────────────────────────────────────────
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, default=str)

    print(f"\n  Output written → {output_path}")
    return 0 if output["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
