"""
model_selection.py
------------------
Flyte 2.0 task: Select the best model and produce a deployment-ready artifact.

Selection criteria (configurable)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
• Primary  : composite_score  (accuracy 40% + F1 30% + ROC-AUC 30%)
• Secondary: cv_mean_accuracy  (tie-break)
• Guard    : require_positive_mcc — discard models with MCC ≤ 0

The task also runs a significance check: the winner must outperform the
runner-up by at least `min_improvement`; if not, a warning is emitted.
"""

import typing
from dataclasses import dataclass, field
from datetime import datetime, timezone

from flytekit import task
from flytekit.types.file import FlyteFile

from model_training import ModelArtifact
from model_evaluation import EvaluationReport, EvaluationResult


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass
class SelectionConfig:
    primary_metric: str = "composite_score"
    min_improvement: float = 0.005
    require_positive_mcc: bool = True


@dataclass
class SelectedModel:
    """The winning model with full provenance."""
    model_name: str = ""
    model_file: FlyteFile = field(default_factory=lambda: FlyteFile(path="/dev/null"))
    selection_reason: str = ""
    primary_score: float = 0.0
    all_scores: typing.Dict[str, float] = field(default_factory=dict)
    feature_columns: typing.List[str] = field(default_factory=list)
    target_column: str = "target"
    hyperparameters: typing.Dict[str, str] = field(default_factory=dict)
    test_metrics: typing.Dict[str, float] = field(default_factory=dict)
    confusion_matrix_flat: typing.List[int] = field(default_factory=list)
    feature_importances: typing.Dict[str, float] = field(default_factory=dict)
    cv_mean_accuracy: float = 0.0
    cv_std_accuracy: float = 0.0
    selected_at: str = ""
    warnings: typing.List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@task(cache=True, cache_version="v1.0")
def select_best_model(
    eval_report: EvaluationReport,
    artifacts: typing.List[ModelArtifact],
    config: SelectionConfig,
) -> SelectedModel:
    """
    Choose the winning model from the evaluation report.
    """
    warnings: typing.List[str] = []

    art_map: typing.Dict[str, ModelArtifact] = {a.model_name: a for a in artifacts}

    # ---- filter candidates ---------------------------------------------
    candidates = list(eval_report.results)  # already sorted best→worst

    if config.require_positive_mcc:
        valid = [r for r in candidates if r.test_metrics.get("mcc", 0) > 0]
        if len(valid) < len(candidates):
            excluded = [r.model_name for r in candidates if r not in valid]
            warnings.append(f"Excluded model(s) with MCC ≤ 0: {excluded}")
            candidates = valid

    if not candidates:
        raise RuntimeError("[select_best_model] No valid candidates after filtering.")

    winner: EvaluationResult = candidates[0]
    runner_up: typing.Optional[EvaluationResult] = candidates[1] if len(candidates) > 1 else None

    # ---- significance check --------------------------------------------
    if runner_up is not None:
        margin = winner.composite_score - runner_up.composite_score
        if margin < config.min_improvement:
            warnings.append(
                f"Winner '{winner.model_name}' leads '{runner_up.model_name}' "
                f"by only {margin:.4f} (< {config.min_improvement}). "
                "Consider ensembling or further tuning."
            )

    # ---- selection reason ----------------------------------------------
    reason_parts = [
        f"Ranked #1 by {config.primary_metric} (score={winner.composite_score:.4f})",
    ]
    if runner_up:
        reason_parts.append(
            f"Runner-up '{runner_up.model_name}' scored {runner_up.composite_score:.4f}"
        )
    reason_parts.append(
        f"CV accuracy={winner.cv_mean_accuracy:.4f} ± {winner.cv_std_accuracy:.4f}"
    )
    selection_reason = " | ".join(reason_parts)

    all_scores = {r.model_name: r.composite_score for r in eval_report.results}
    winner_art = art_map[winner.model_name]

    # Flatten confusion matrix for Flyte-serialisable List[int]
    cm_flat: typing.List[int] = []
    for row in winner.confusion_matrix:
        cm_flat.extend(int(v) for v in row)

    selected = SelectedModel(
        model_name=winner.model_name,
        model_file=winner_art.model_file,
        selection_reason=selection_reason,
        primary_score=winner.composite_score,
        all_scores=all_scores,
        feature_columns=winner_art.feature_columns,
        target_column=winner_art.target_column,
        hyperparameters=winner_art.hyperparameters,
        test_metrics=winner.test_metrics,
        confusion_matrix_flat=cm_flat,
        feature_importances=winner.feature_importances,
        cv_mean_accuracy=winner.cv_mean_accuracy,
        cv_std_accuracy=winner.cv_std_accuracy,
        selected_at=datetime.now(timezone.utc).isoformat(),
        warnings=warnings,
    )

    print(f"[select_best_model] ✓ Selected: {winner.model_name}")
    print(f"[select_best_model]   Score  : {winner.composite_score:.4f}")
    print(f"[select_best_model]   Reason : {selection_reason}")
    for w in warnings:
        print(f"[select_best_model]   WARN: {w}")

    return selected
