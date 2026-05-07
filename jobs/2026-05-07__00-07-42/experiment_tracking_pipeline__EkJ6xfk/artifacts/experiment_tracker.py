"""
Flyte 2.0 Experiment Tracking Pipeline

This module implements a parallel experiment tracking system that runs multiple
ML experiments concurrently, caches results, and identifies the best configuration.
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

from flytekit import task, workflow, Resources, Cache, CacheVersion
from flytekit.types.file import FlyteFile
from flytekit.types.schema import FlyteSchema
import pandas as pd


@dataclass
class ExperimentConfig:
    """Configuration for a single ML experiment."""
    experiment_id: str
    learning_rate: float
    batch_size: int
    epochs: int
    optimizer: str
    dropout_rate: float


@dataclass
class ExperimentResult:
    """Results from a single ML experiment."""
    experiment_id: str
    accuracy: float
    loss: float
    training_time: float
    config: ExperimentConfig
    timestamp: str


# Define task environment with appropriate resources
task_env = {
    "cpu": "2",
    "memory": "4Gi",
    "gpu": "0"
}


@task(
    cache=Cache(
        version=CacheVersion("1.0"),
        max_age_seconds=3600  # Cache for 1 hour
    ),
    limits=Resources(cpu="2", mem="4Gi"),
    requests=Resources(cpu="1", mem="2Gi"),
    environment=task_env
)
def generate_synthetic_data(
    num_samples: int = 1000,
    num_features: int = 20,
    random_seed: int = 42
) -> FlyteFile:
    """
    Generate synthetic training data for experiments.
    
    Args:
        num_samples: Number of samples to generate
        num_features: Number of features per sample
        random_seed: Random seed for reproducibility
        
    Returns:
        Path to the generated data file
    """
    import numpy as np
    
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    # Generate synthetic data
    X = np.random.randn(num_samples, num_features)
    y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(num_samples) * 0.1 > 0).astype(int)
    
    # Save to file
    output_path = "/tmp/synthetic_data.csv"
    df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(num_features)])
    df["target"] = y
    df.to_csv(output_path, index=False)
    
    return FlyteFile(path=output_path)


@task(
    cache=Cache(
        version=CacheVersion("1.0"),
        max_age_seconds=3600
    ),
    limits=Resources(cpu="2", mem="4Gi"),
    requests=Resources(cpu="1", mem="2Gi"),
    environment=task_env
)
async def run_single_experiment(
    config: ExperimentConfig,
    data_file: FlyteFile,
    random_seed: int = 42
) -> ExperimentResult:
    """
    Run a single ML experiment with the given configuration.
    
    Args:
        config: Experiment configuration
        data_file: Path to training data
        random_seed: Random seed for reproducibility
        
    Returns:
        ExperimentResult containing metrics and configuration
    """
    import numpy as np
    import time
    
    # Simulate experiment execution
    await asyncio.sleep(0.5)  # Simulate some async work
    
    random.seed(random_seed + hash(config.experiment_id))
    np.random.seed(random_seed + hash(config.experiment_id))
    
    # Load data
    df = pd.read_csv(data_file.path)
    X = df.drop("target", axis=1).values
    y = df["target"].values
    
    start_time = time.time()
    
    # Simulate model training (simplified for demo)
    # In real scenario, this would train an actual model
    learning_factor = config.learning_rate * 100
    batch_factor = np.log(config.batch_size) / 10
    epoch_factor = config.epochs / 100
    
    # Simulate accuracy based on hyperparameters
    base_accuracy = 0.75
    accuracy = base_accuracy + (learning_factor * 0.1) + (batch_factor * 0.05) + (epoch_factor * 0.03)
    accuracy = min(0.95, max(0.5, accuracy + (random.random() - 0.5) * 0.1))
    
    # Simulate loss
    loss = 1.0 - accuracy + (random.random() * 0.1)
    
    training_time = start_time - time.time() + (config.epochs * 0.01)
    
    result = ExperimentResult(
        experiment_id=config.experiment_id,
        accuracy=round(accuracy, 4),
        loss=round(loss, 4),
        training_time=round(abs(training_time), 2),
        config=config,
        timestamp=datetime.now().isoformat()
    )
    
    return result


@task(
    cache=Cache(
        version=CacheVersion("1.0"),
        max_age_seconds=3600
    ),
    limits=Resources(cpu="4", mem="8Gi"),
    requests=Resources(cpu="2", mem="4Gi"),
    environment=task_env
)
async def run_parallel_experiments(
    configs: List[ExperimentConfig],
    data_file: FlyteFile,
    random_seed: int = 42
) -> List[ExperimentResult]:
    """
    Run multiple experiments in parallel using asyncio.gather.
    
    Args:
        configs: List of experiment configurations
        data_file: Path to training data
        random_seed: Random seed for reproducibility
        
    Returns:
        List of experiment results
    """
    print(f"Running {len(configs)} experiments in parallel...")
    
    # Create tasks for all experiments
    tasks = [
        run_single_experiment(config=config, data_file=data_file, random_seed=random_seed)
        for config in configs
    ]
    
    # Run all experiments in parallel
    results = await asyncio.gather(*tasks)
    
    print(f"Completed {len(results)} experiments")
    return results


@task(
    cache=Cache(
        version=CacheVersion("1.0"),
        max_age_seconds=3600
    ),
    limits=Resources(cpu="1", mem="2Gi"),
    requests=Resources(cpu="0.5", mem="1Gi"),
    environment=task_env
)
def compare_experiments(
    results: List[ExperimentResult],
    metric: str = "accuracy"
) -> Tuple[ExperimentResult, List[ExperimentResult]]:
    """
    Compare experiments and identify the best configuration.
    
    Args:
        results: List of experiment results
        metric: Metric to use for comparison (accuracy or loss)
        
    Returns:
        Tuple of (best_result, sorted_results)
    """
    print(f"\nComparing {len(results)} experiments by {metric}...")
    
    # Sort results by the specified metric
    if metric == "accuracy":
        sorted_results = sorted(results, key=lambda x: x.accuracy, reverse=True)
    elif metric == "loss":
        sorted_results = sorted(results, key=lambda x: x.loss)
    else:
        sorted_results = results
    
    best_result = sorted_results[0]
    
    # Print comparison summary
    print(f"\n{'='*80}")
    print(f"EXPERIMENT COMPARISON SUMMARY (sorted by {metric})")
    print(f"{'='*80}")
    print(f"{'ID':<15} {'LR':<10} {'Batch':<10} {'Epochs':<10} {'Accuracy':<12} {'Loss':<12}")
    print(f"{'-'*80}")
    
    for result in sorted_results:
        config = result.config
        print(f"{result.experiment_id:<15} {config.learning_rate:<10.4f} "
              f"{config.batch_size:<10} {config.epochs:<10} "
              f"{result.accuracy:<12.4f} {result.loss:<12.4f}")
    
    print(f"\n🏆 Best Experiment: {best_result.experiment_id}")
    print(f"   {metric.capitalize()}: {getattr(best_result, metric):.4f}")
    print(f"   Configuration: LR={best_result.config.learning_rate}, "
          f"Batch={best_result.config.batch_size}, "
          f"Epochs={best_result.config.epochs}")
    print(f"{'='*80}\n")
    
    return best_result, sorted_results


@task(
    cache=Cache(
        version=CacheVersion("1.0"),
        max_age_seconds=3600
    ),
    limits=Resources(cpu="1", mem="2Gi"),
    requests=Resources(cpu="0.5", mem="1Gi"),
    environment=task_env
)
def save_experiment_results(
    results: List[ExperimentResult],
    best_result: ExperimentResult,
    output_path: str = "/home/user/flyte_project/experiment_result.json"
) -> str:
    """
    Save experiment results to a JSON file.
    
    Args:
        results: List of experiment results
        best_result: Best experiment result
        output_path: Path to save results
        
    Returns:
        Path to the saved results file
    """
    # Convert results to serializable format
    results_dict = {
        "timestamp": datetime.now().isoformat(),
        "total_experiments": len(results),
        "best_experiment": {
            "experiment_id": best_result.experiment_id,
            "accuracy": best_result.accuracy,
            "loss": best_result.loss,
            "training_time": best_result.training_time,
            "config": asdict(best_result.config)
        },
        "all_results": [
            {
                "experiment_id": r.experiment_id,
                "accuracy": r.accuracy,
                "loss": r.loss,
                "training_time": r.training_time,
                "config": asdict(r.config),
                "timestamp": r.timestamp
            }
            for r in results
        ]
    }
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    print(f"Results saved to: {output_path}")
    
    return output_path


@workflow
def experiment_tracking_workflow(
    num_experiments: int = 8,
    metric: str = "accuracy",
    random_seed: int = 42
) -> str:
    """
    Main workflow for parallel experiment tracking.
    
    Args:
        num_experiments: Number of experiments to run
        metric: Metric to use for comparison
        random_seed: Random seed for reproducibility
        
    Returns:
        Path to the saved results file
    """
    # Generate experiment configurations
    configs = []
    learning_rates = [0.001, 0.01, 0.1]
    batch_sizes = [32, 64, 128]
    epochs_options = [50, 100]
    optimizers = ["adam", "sgd"]
    dropout_rates = [0.1, 0.2, 0.5]
    
    for i in range(num_experiments):
        config = ExperimentConfig(
            experiment_id=f"exp_{i+1:03d}",
            learning_rate=random.choice(learning_rates),
            batch_size=random.choice(batch_sizes),
            epochs=random.choice(epochs_options),
            optimizer=random.choice(optimizers),
            dropout_rate=random.choice(dropout_rates)
        )
        configs.append(config)
    
    # Generate synthetic data
    data_file = generate_synthetic_data(
        num_samples=1000,
        num_features=20,
        random_seed=random_seed
    )
    
    # Run experiments in parallel
    results = run_parallel_experiments(
        configs=configs,
        data_file=data_file,
        random_seed=random_seed
    )
    
    # Compare experiments
    best_result, sorted_results = compare_experiments(
        results=results,
        metric=metric
    )
    
    # Save results
    output_path = save_experiment_results(
        results=sorted_results,
        best_result=best_result
    )
    
    return output_path


def create_experiment_configs(
    num_configs: int = 8,
    custom_configs: Optional[List[Dict]] = None
) -> List[ExperimentConfig]:
    """
    Create experiment configurations programmatically.
    
    Args:
        num_configs: Number of configurations to generate
        custom_configs: Optional list of custom config dictionaries
        
    Returns:
        List of ExperimentConfig objects
    """
    if custom_configs:
        return [ExperimentConfig(**config) for config in custom_configs]
    
    configs = []
    learning_rates = [0.001, 0.005, 0.01, 0.05, 0.1]
    batch_sizes = [16, 32, 64, 128, 256]
    epochs_options = [25, 50, 100, 200]
    optimizers = ["adam", "sgd", "rmsprop", "adagrad"]
    dropout_rates = [0.0, 0.1, 0.2, 0.3, 0.5]
    
    for i in range(num_configs):
        config = ExperimentConfig(
            experiment_id=f"exp_{i+1:03d}",
            learning_rate=random.choice(learning_rates),
            batch_size=random.choice(batch_sizes),
            epochs=random.choice(epochs_options),
            optimizer=random.choice(optimizers),
            dropout_rate=random.choice(dropout_rates)
        )
        configs.append(config)
    
    return configs


if __name__ == "__main__":
    # Example usage
    print("Flyte 2.0 Experiment Tracking Pipeline")
    print("=" * 80)
    
    # Run the workflow
    result_path = experiment_tracking_workflow(
        num_experiments=8,
        metric="accuracy",
        random_seed=42
    )
    
    print(f"\nExperiment tracking completed!")
    print(f"Results saved to: {result_path}")
    
    # Display results
    with open(result_path, 'r') as f:
        results = json.load(f)
    
    print(f"\nTotal experiments run: {results['total_experiments']}")
    print(f"Best experiment: {results['best_experiment']['experiment_id']}")
    print(f"Best accuracy: {results['best_experiment']['accuracy']:.4f}")