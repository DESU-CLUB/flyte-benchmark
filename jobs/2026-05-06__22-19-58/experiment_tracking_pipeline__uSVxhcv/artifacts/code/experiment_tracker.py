from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from flyte import Cache, TaskEnvironment, task, workflow
from flyte.types import Resources

LOG_PATH = Path("/home/user/flyte_project/experiment_result.json")


@dataclass(frozen=True)
class ExperimentConfig:
    learning_rate: float
    num_layers: int
    batch_size: int


@dataclass
class ExperimentResult:
    config: ExperimentConfig
    accuracy: float
    loss: float


DEFAULT_ENV = TaskEnvironment(
    resources=Resources(cpu="1", mem="1Gi"),
)


@task(
    environment=DEFAULT_ENV,
    cache=Cache(version="1", serialize=True),
)
def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    """Simulated experiment run.

    Replace this with real training and evaluation logic.
    """
    accuracy = max(
        0.0,
        min(
            1.0,
            0.6
            + (0.05 * config.num_layers)
            - (0.1 * abs(config.learning_rate - 0.01))
            - (0.01 * (config.batch_size / 32.0)),
        ),
    )
    loss = 1.0 - accuracy
    return ExperimentResult(config=config, accuracy=accuracy, loss=loss)


@task(environment=DEFAULT_ENV)
async def run_experiments_parallel(configs: List[ExperimentConfig]) -> List[ExperimentResult]:
    tasks = [asyncio.to_thread(run_experiment, config) for config in configs]
    return list(await asyncio.gather(*tasks))


@task(environment=DEFAULT_ENV)
def select_best(results: List[ExperimentResult]) -> ExperimentResult:
    return max(results, key=lambda result: result.accuracy)


@task(environment=DEFAULT_ENV)
def persist_results(results: List[ExperimentResult], best: ExperimentResult) -> str:
    payload: Dict[str, object] = {
        "results": [
            {
                "config": {
                    "learning_rate": result.config.learning_rate,
                    "num_layers": result.config.num_layers,
                    "batch_size": result.config.batch_size,
                },
                "accuracy": result.accuracy,
                "loss": result.loss,
            }
            for result in results
        ],
        "best": {
            "config": {
                "learning_rate": best.config.learning_rate,
                "num_layers": best.config.num_layers,
                "batch_size": best.config.batch_size,
            },
            "accuracy": best.accuracy,
            "loss": best.loss,
        },
    }
    LOG_PATH.write_text(json.dumps(payload, indent=2))
    return str(LOG_PATH)


@workflow
async def experiment_tracking_workflow() -> str:
    configs = [
        ExperimentConfig(learning_rate=0.01, num_layers=2, batch_size=32),
        ExperimentConfig(learning_rate=0.005, num_layers=3, batch_size=64),
        ExperimentConfig(learning_rate=0.02, num_layers=4, batch_size=16),
        ExperimentConfig(learning_rate=0.015, num_layers=5, batch_size=32),
    ]
    results = await run_experiments_parallel(configs=configs)
    best = select_best(results=results)
    return persist_results(results=results, best=best)


if __name__ == "__main__":
    output_path = asyncio.run(experiment_tracking_workflow())
    print(f"Results saved to {output_path}")
