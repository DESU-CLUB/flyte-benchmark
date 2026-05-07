"""
Flyte 2.0 Experiment Tracking Pipeline
=======================================
Runs multiple ML experiment configurations in parallel, caches results,
compares all runs, and writes the best configuration to a JSON log file.

Local execution (no Flyte cluster needed):
    python3 experiment_tracker.py

Design notes
------------
* ``@task`` with ``requests``/``limits`` (``Resources``) stands in for the
  conceptual ``TaskEnvironment`` that Flyte 2.0 surfaces through the same
  ``resources=`` / ``requests=`` / ``limits=`` kwargs on ``@task``.
* ``Cache(version=...)`` gives each task deterministic caching semantics that
  a real Flyte backend would honour; locally the cache is simulated via an
  in-process ``diskcache.Cache``.
* ``asyncio.gather`` drives the parallel fan-out of experiment tasks.
* Results are persisted to ``experiment_result.json``.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ── flytekit imports ──────────────────────────────────────────────────────────
import flytekit
from flytekit import Cache, Resources, task, workflow
from flytekit.core.context_manager import FlyteContextManager, ExecutionState

# ── constants ─────────────────────────────────────────────────────────────────
LOG_PATH = Path("/home/user/flyte_project/experiment_result.json")
RANDOM_SEED = 42


# ─────────────────────────────────────────────────────────────────────────────
# Data-model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExperimentConfig:
    """Hyper-parameter bundle for one experiment run."""
    experiment_id: str
    learning_rate: float
    batch_size: int
    num_epochs: int
    dropout_rate: float
    optimizer: str          # "adam" | "sgd" | "rmsprop"
    hidden_units: int


@dataclass
class ExperimentResult:
    """Metrics produced by a single experiment run."""
    experiment_id: str
    config: Dict
    train_loss: float
    val_loss: float
    train_accuracy: float
    val_accuracy: float
    duration_seconds: float
    timestamp: str
    status: str             # "success" | "failed"
    error_message: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# TaskEnvironment helper
# ─────────────────────────────────────────────────────────────────────────────

class TaskEnvironment:
    """
    Lightweight wrapper that bundles resource requirements and environment
    variables for a group of related tasks – mirrors the *Flyte 2.0*
    ``TaskEnvironment`` concept.

    Usage::

        env = TaskEnvironment(
            name="ml-experiment",
            cpu="2",
            memory="4Gi",
            env_vars={"EXPERIMENT_MODE": "parallel"},
        )
        requests, limits, env_vars = env.resources()
    """

    def __init__(
        self,
        name: str,
        cpu: str = "2",
        memory: str = "4Gi",
        gpu: str = "0",
        ephemeral_storage: str = "20Gi",
        env_vars: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.cpu = cpu
        self.memory = memory
        self.gpu = gpu
        self.ephemeral_storage = ephemeral_storage
        self.env_vars: Dict[str, str] = env_vars or {}

    def requests(self) -> Resources:
        """Return a ``flytekit.Resources`` object for *requests*."""
        return Resources(
            cpu=self.cpu,
            mem=self.memory,
            gpu=self.gpu if self.gpu != "0" else None,
            ephemeral_storage=self.ephemeral_storage,
        )

    def limits(self) -> Resources:
        """Return a ``flytekit.Resources`` object for *limits* (2× requests)."""
        # Simple heuristic: limits = 2× requests
        cpu_limit = str(int(self.cpu) * 2) if self.cpu.isdigit() else self.cpu
        return Resources(
            cpu=cpu_limit,
            mem=self.memory,
            gpu=self.gpu if self.gpu != "0" else None,
        )

    def apply_env_vars(self) -> None:
        """Inject environment variables into the current process."""
        for key, value in self.env_vars.items():
            os.environ[key] = value

    def __repr__(self) -> str:
        return (
            f"TaskEnvironment(name={self.name!r}, cpu={self.cpu}, "
            f"memory={self.memory}, gpu={self.gpu})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Define shared TaskEnvironment instances
# ─────────────────────────────────────────────────────────────────────────────

# Standard environment for individual experiment tasks
EXPERIMENT_ENV = TaskEnvironment(
    name="ml-experiment-worker",
    cpu="2",
    memory="4Gi",
    env_vars={
        "EXPERIMENT_MODE": "parallel",
        "ML_FRAMEWORK": "simulated",
        "LOG_LEVEL": "INFO",
    },
)

# Heavier environment reserved for the aggregation / comparison task
AGGREGATION_ENV = TaskEnvironment(
    name="ml-experiment-aggregator",
    cpu="4",
    memory="8Gi",
    env_vars={"AGGREGATION_MODE": "best_val_accuracy"},
)


# ─────────────────────────────────────────────────────────────────────────────
# In-process cache (simulates Flyte's distributed cache locally)
# ─────────────────────────────────────────────────────────────────────────────

import diskcache

_CACHE_DIR = Path("/tmp/flyte_experiment_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_LOCAL_CACHE: diskcache.Cache = diskcache.Cache(str(_CACHE_DIR))


def _cache_key(cfg: ExperimentConfig) -> str:
    """Deterministic cache key derived from all hyper-parameters."""
    return (
        f"exp:{cfg.learning_rate}:{cfg.batch_size}:{cfg.num_epochs}:"
        f"{cfg.dropout_rate}:{cfg.optimizer}:{cfg.hidden_units}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core simulation logic (pure Python – no ML framework required)
# ─────────────────────────────────────────────────────────────────────────────

def _simulate_training(cfg: ExperimentConfig) -> Dict:
    """
    Simulate a training loop and return scalar metrics.

    The formulas are designed so that:
    * lower learning-rate ≈ lower loss (within reason)
    * smaller dropout ≈ higher accuracy
    * more epochs ≈ converges further
    * optimizer quality: adam > rmsprop > sgd
    """
    rng = random.Random(RANDOM_SEED + hash(cfg.experiment_id) % 1_000)
    t0 = time.perf_counter()

    optimizer_bonus = {"adam": 0.05, "rmsprop": 0.02, "sgd": 0.00}.get(
        cfg.optimizer, 0.0
    )
    lr_penalty = abs(math.log10(max(cfg.learning_rate, 1e-8))) * 0.02
    dropout_penalty = cfg.dropout_rate * 0.15
    epoch_bonus = min(cfg.num_epochs / 100.0, 0.10)
    hidden_bonus = min(cfg.hidden_units / 1024.0, 0.05)

    base_accuracy = 0.70 + optimizer_bonus - dropout_penalty + epoch_bonus + hidden_bonus
    base_accuracy = max(0.50, min(0.99, base_accuracy + rng.gauss(0, 0.02)))

    base_loss = 1.0 - base_accuracy + lr_penalty + rng.gauss(0, 0.01)
    base_loss = max(0.01, base_loss)

    # Slight overfitting: val is a little worse than train
    overfit_gap = rng.uniform(0.005, 0.03)
    train_acc = min(0.995, base_accuracy + overfit_gap / 2)
    val_acc   = max(0.50,  base_accuracy - overfit_gap / 2)
    train_loss = max(0.005, base_loss - overfit_gap / 2)
    val_loss   = base_loss + overfit_gap / 2

    # Simulate wall-clock time (scaled down for demo purposes)
    simulated_ms = (
        cfg.num_epochs * cfg.hidden_units / cfg.batch_size * 0.0001
        + rng.uniform(0.005, 0.015)
    )
    time.sleep(simulated_ms)          # tiny real sleep to make parallelism visible
    duration = time.perf_counter() - t0

    return dict(
        train_loss=round(train_loss, 6),
        val_loss=round(val_loss, 6),
        train_accuracy=round(train_acc, 6),
        val_accuracy=round(val_acc, 6),
        duration_seconds=round(duration, 4),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Flyte tasks
# ─────────────────────────────────────────────────────────────────────────────

@task(
    cache=Cache(version="v1.0.0", serialize=True),
    requests=EXPERIMENT_ENV.requests(),
    limits=EXPERIMENT_ENV.limits(),
    environment=EXPERIMENT_ENV.env_vars,
    retries=2,
)
def run_experiment(
    experiment_id: str,
    learning_rate: float,
    batch_size: int,
    num_epochs: int,
    dropout_rate: float,
    optimizer: str,
    hidden_units: int,
) -> Dict:
    """
    Flyte task: train (simulate) one ML model and return metric dict.

    The ``cache=Cache(version='v1.0.0', serialize=True)`` annotation ensures
    that Flyte caches results keyed on input values; ``serialize=True`` prevents
    redundant parallel executions for identical inputs.
    """
    cfg = ExperimentConfig(
        experiment_id=experiment_id,
        learning_rate=learning_rate,
        batch_size=batch_size,
        num_epochs=num_epochs,
        dropout_rate=dropout_rate,
        optimizer=optimizer,
        hidden_units=hidden_units,
    )

    cache_key = _cache_key(cfg)
    if cache_key in _LOCAL_CACHE:
        print(f"  [cache HIT]  {experiment_id}")
        return _LOCAL_CACHE[cache_key]

    print(f"  [running]    {experiment_id}  lr={learning_rate}  opt={optimizer}")
    EXPERIMENT_ENV.apply_env_vars()

    try:
        metrics = _simulate_training(cfg)
        metrics["experiment_id"] = experiment_id
        metrics["config"] = asdict(cfg)
        metrics["status"] = "success"
        metrics["error_message"] = None
        metrics["timestamp"] = datetime.utcnow().isoformat() + "Z"
        _LOCAL_CACHE[cache_key] = metrics
        return metrics
    except Exception as exc:  # pragma: no cover
        error_result: Dict = {
            "experiment_id": experiment_id,
            "config": asdict(cfg),
            "train_loss": float("inf"),
            "val_loss": float("inf"),
            "train_accuracy": 0.0,
            "val_accuracy": 0.0,
            "duration_seconds": 0.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "failed",
            "error_message": str(exc),
        }
        return error_result


@task(
    requests=AGGREGATION_ENV.requests(),
    limits=AGGREGATION_ENV.limits(),
    environment=AGGREGATION_ENV.env_vars,
)
def compare_experiments(results: List[Dict]) -> Dict:
    """
    Flyte task: compare all experiment results and return a summary dict
    that includes the best configuration ranked by validation accuracy.
    """
    AGGREGATION_ENV.apply_env_vars()

    successful = [r for r in results if r.get("status") == "success"]
    failed     = [r for r in results if r.get("status") != "success"]

    if not successful:
        return {
            "best_experiment": None,
            "summary": {"total": len(results), "successful": 0, "failed": len(results)},
            "ranked_experiments": [],
            "analysis": {},
        }

    # Rank by validation accuracy (descending), then by val_loss (ascending)
    ranked = sorted(
        successful,
        key=lambda r: (-r["val_accuracy"], r["val_loss"]),
    )

    best = ranked[0]

    # Aggregate statistics across all successful runs
    val_accs  = [r["val_accuracy"]  for r in successful]
    val_losses = [r["val_loss"]     for r in successful]
    durations  = [r["duration_seconds"] for r in successful]

    def _mean(xs: List[float]) -> float:
        return sum(xs) / len(xs)

    analysis = {
        "val_accuracy": {
            "best": max(val_accs),
            "worst": min(val_accs),
            "mean": round(_mean(val_accs), 6),
        },
        "val_loss": {
            "best": min(val_losses),
            "worst": max(val_losses),
            "mean": round(_mean(val_losses), 6),
        },
        "duration_seconds": {
            "total": round(sum(durations), 4),
            "mean": round(_mean(durations), 4),
            "max": max(durations),
        },
        "optimizer_breakdown": {
            opt: round(
                _mean([r["val_accuracy"] for r in successful if r["config"]["optimizer"] == opt]),
                6,
            )
            for opt in {"adam", "sgd", "rmsprop"}
            if any(r["config"]["optimizer"] == opt for r in successful)
        },
    }

    summary = {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "failed_ids": [r["experiment_id"] for r in failed],
    }

    return {
        "best_experiment": best,
        "summary": summary,
        "ranked_experiments": ranked,
        "analysis": analysis,
    }


@task(
    requests=AGGREGATION_ENV.requests(),
    limits=AGGREGATION_ENV.limits(),
)
def save_results(comparison: Dict, log_path: str) -> str:
    """
    Flyte task: persist the full comparison report to *log_path* as JSON
    and return a human-readable one-line summary.
    """
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    report = {
        "pipeline": "flyte-experiment-tracker",
        "version": "2.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "flytekit_version": flytekit.__version__,
        **comparison,
    }

    with open(log_path, "w") as fh:
        json.dump(report, fh, indent=2)

    best = comparison.get("best_experiment") or {}
    best_id  = best.get("experiment_id", "N/A")
    best_acc = best.get("val_accuracy", 0.0)
    best_loss = best.get("val_loss", float("inf"))

    summary_line = (
        f"Best experiment: {best_id} | "
        f"val_accuracy={best_acc:.4f} | "
        f"val_loss={best_loss:.4f} | "
        f"results → {log_path}"
    )
    print(f"\n{'='*70}")
    print(summary_line)
    print(f"{'='*70}\n")
    return summary_line


# ─────────────────────────────────────────────────────────────────────────────
# Workflow
# ─────────────────────────────────────────────────────────────────────────────

# Grid of experiment configurations to sweep
EXPERIMENT_CONFIGS: List[ExperimentConfig] = [
    ExperimentConfig("exp_01", learning_rate=0.001,  batch_size=32,  num_epochs=50,  dropout_rate=0.1,  optimizer="adam",    hidden_units=256),
    ExperimentConfig("exp_02", learning_rate=0.001,  batch_size=64,  num_epochs=100, dropout_rate=0.2,  optimizer="adam",    hidden_units=512),
    ExperimentConfig("exp_03", learning_rate=0.01,   batch_size=32,  num_epochs=50,  dropout_rate=0.3,  optimizer="sgd",     hidden_units=256),
    ExperimentConfig("exp_04", learning_rate=0.01,   batch_size=128, num_epochs=75,  dropout_rate=0.1,  optimizer="sgd",     hidden_units=128),
    ExperimentConfig("exp_05", learning_rate=0.005,  batch_size=64,  num_epochs=100, dropout_rate=0.2,  optimizer="rmsprop", hidden_units=512),
    ExperimentConfig("exp_06", learning_rate=0.0001, batch_size=32,  num_epochs=200, dropout_rate=0.05, optimizer="adam",    hidden_units=1024),
    ExperimentConfig("exp_07", learning_rate=0.005,  batch_size=128, num_epochs=50,  dropout_rate=0.4,  optimizer="adam",    hidden_units=256),
    ExperimentConfig("exp_08", learning_rate=0.001,  batch_size=256, num_epochs=150, dropout_rate=0.15, optimizer="rmsprop", hidden_units=512),
    ExperimentConfig("exp_09", learning_rate=0.1,    batch_size=32,  num_epochs=30,  dropout_rate=0.5,  optimizer="sgd",     hidden_units=64),
    ExperimentConfig("exp_10", learning_rate=0.0005, batch_size=64,  num_epochs=200, dropout_rate=0.1,  optimizer="adam",    hidden_units=768),
]


@workflow
def experiment_tracking_workflow(log_path: str = str(LOG_PATH)) -> str:
    """
    Flyte workflow that:
    1. Launches all experiment tasks (fan-out).
    2. Aggregates / compares results.
    3. Saves the best configuration report to *log_path*.
    """
    results: List[Dict] = [
        run_experiment(
            experiment_id=cfg.experiment_id,
            learning_rate=cfg.learning_rate,
            batch_size=cfg.batch_size,
            num_epochs=cfg.num_epochs,
            dropout_rate=cfg.dropout_rate,
            optimizer=cfg.optimizer,
            hidden_units=cfg.hidden_units,
        )
        for cfg in EXPERIMENT_CONFIGS
    ]

    comparison = compare_experiments(results=results)
    summary    = save_results(comparison=comparison, log_path=log_path)
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Async parallel local runner (asyncio.gather fan-out)
# ─────────────────────────────────────────────────────────────────────────────

async def _run_experiment_async(cfg: ExperimentConfig) -> Dict:
    """
    Coroutine wrapper: executes ``run_experiment`` in a thread-pool so that
    asyncio.gather() achieves true I/O-bound parallelism locally.
    """
    loop = asyncio.get_running_loop()
    result: Dict = await loop.run_in_executor(
        None,  # use default ThreadPoolExecutor
        lambda: run_experiment(
            experiment_id=cfg.experiment_id,
            learning_rate=cfg.learning_rate,
            batch_size=cfg.batch_size,
            num_epochs=cfg.num_epochs,
            dropout_rate=cfg.dropout_rate,
            optimizer=cfg.optimizer,
            hidden_units=cfg.hidden_units,
        ),
    )
    return result


async def run_pipeline_async(log_path: str = str(LOG_PATH)) -> str:
    """
    Local async entry-point.

    Uses ``asyncio.gather`` to fan-out all experiment tasks in parallel,
    then compares results and saves the report.
    """
    print(f"\n{'='*70}")
    print("  Flyte 2.0 Experiment Tracking Pipeline")
    print(f"  flytekit {flytekit.__version__}")
    print(f"  {len(EXPERIMENT_CONFIGS)} experiments  |  parallel execution via asyncio.gather")
    print(f"{'='*70}\n")

    print("Phase 1 ── Launching experiments in parallel …")
    t_start = time.perf_counter()

    # ── asyncio.gather fan-out ────────────────────────────────────────────────
    raw_results: List[Dict] = await asyncio.gather(
        *[_run_experiment_async(cfg) for cfg in EXPERIMENT_CONFIGS]
    )

    elapsed = time.perf_counter() - t_start
    print(f"\nPhase 1 complete in {elapsed:.3f}s  "
          f"({sum(1 for r in raw_results if r['status']=='success')} succeeded, "
          f"{sum(1 for r in raw_results if r['status']!='success')} failed)\n")

    print("Phase 2 ── Comparing experiments …")
    comparison = compare_experiments(results=raw_results)

    print("Phase 3 ── Saving results …")
    summary = save_results(comparison=comparison, log_path=log_path)

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Entrypoint.

    * When running against a live Flyte cluster use ``pyflyte run`` or
      ``FlyteRemote`` – the ``@workflow`` declaration above is what Flyte
      serialises and executes on the cluster.

    * Locally (no cluster) we bypass the Flyte execution engine and drive
      tasks directly via the async runner so that ``asyncio.gather`` provides
      genuine parallel execution.
    """
    print("\nStarting Flyte 2.0 Experiment Tracking Pipeline (local execution)")
    print(f"TaskEnvironment  → {EXPERIMENT_ENV}")
    print(f"Aggregation env  → {AGGREGATION_ENV}")
    print(f"Cache backend    → {_CACHE_DIR}")
    print(f"Output log       → {LOG_PATH}\n")

    summary = asyncio.run(run_pipeline_async(log_path=str(LOG_PATH)))

    # Also print the Flyte workflow declaration for reference
    print("\nFlyte workflow registered as: experiment_tracking_workflow")
    print("To execute on a cluster:")
    print("  pyflyte run experiment_tracker.py experiment_tracking_workflow\n")
    print("Summary:", summary)


if __name__ == "__main__":
    main()
