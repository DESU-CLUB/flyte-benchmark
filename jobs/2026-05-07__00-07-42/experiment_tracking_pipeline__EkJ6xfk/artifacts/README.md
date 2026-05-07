# Flyte 2.0 Experiment Tracking Pipeline

A comprehensive experiment tracking system built with Flyte 2.0 that runs multiple ML experiments in parallel, caches results, and identifies the best configuration.

## Features

- **Parallel Execution**: Runs multiple experiments concurrently using `asyncio.gather`
- **Result Caching**: Implements `flyte.Cache` for efficient experiment reuse
- **Resource Management**: Uses `flyte.TaskEnvironment` with appropriate resource allocations
- **Automatic Comparison**: Identifies the best configuration based on specified metrics
- **Result Persistence**: Saves all experiment results to JSON for analysis

## Requirements

- Python 3.8+
- Flytekit 2.0+
- pandas
- numpy

## Installation

```bash
pip install flytekit pandas numpy
```

## Usage

### Basic Workflow Execution

```python
from experiment_tracker import experiment_tracking_workflow

# Run 8 experiments in parallel
result_path = experiment_tracking_workflow(
    num_experiments=8,
    metric="accuracy",
    random_seed=42
)

print(f"Results saved to: {result_path}")
```

### Custom Experiment Configurations

```python
from experiment_tracker import create_experiment_configs, ExperimentConfig

# Create custom configurations
custom_configs = [
    {
        "experiment_id": "custom_001",
        "learning_rate": 0.01,
        "batch_size": 64,
        "epochs": 100,
        "optimizer": "adam",
        "dropout_rate": 0.2
    },
    {
        "experiment_id": "custom_002",
        "learning_rate": 0.001,
        "batch_size": 128,
        "epochs": 200,
        "optimizer": "sgd",
        "dropout_rate": 0.1
    }
]

configs = create_experiment_configs(custom_configs=custom_configs)
```

### Running with Flyte

```bash
# Register the workflow
pyflyte register experiment_tracker.py -e my_project -d development

# Execute the workflow
pyflyte run experiment_tracker.py experiment_tracking_workflow \
    --num_experiments 10 \
    --metric accuracy \
    --random_seed 42
```

## Architecture

### Tasks

1. **generate_synthetic_data**: Creates synthetic training data for experiments
   - Resources: 2 CPU, 4Gi memory
   - Cached for 1 hour

2. **run_single_experiment**: Executes a single ML experiment
   - Resources: 2 CPU, 4Gi memory
   - Async function for parallel execution
   - Cached for 1 hour

3. **run_parallel_experiments**: Orchestrates parallel experiment execution
   - Resources: 4 CPU, 8Gi memory
   - Uses `asyncio.gather` for concurrent execution
   - Cached for 1 hour

4. **compare_experiments**: Analyzes and ranks experiment results
   - Resources: 1 CPU, 2Gi memory
   - Supports accuracy and loss metrics
   - Cached for 1 hour

5. **save_experiment_results**: Persists results to JSON
   - Resources: 0.5 CPU, 1Gi memory
   - Outputs to `/home/user/flyte_project/experiment_result.json`

### Data Structures

**ExperimentConfig**
```python
@dataclass
class ExperimentConfig:
    experiment_id: str
    learning_rate: float
    batch_size: int
    epochs: int
    optimizer: str
    dropout_rate: float
```

**ExperimentResult**
```python
@dataclass
class ExperimentResult:
    experiment_id: str
    accuracy: float
    loss: float
    training_time: float
    config: ExperimentConfig
    timestamp: str
```

## Output Format

Results are saved to `/home/user/flyte_project/experiment_result.json`:

```json
{
  "timestamp": "2026-05-07T07:21:04.000000",
  "total_experiments": 8,
  "best_experiment": {
    "experiment_id": "exp_003",
    "accuracy": 0.8765,
    "loss": 0.1234,
    "training_time": 1.5,
    "config": {
      "experiment_id": "exp_003",
      "learning_rate": 0.01,
      "batch_size": 64,
      "epochs": 100,
      "optimizer": "adam",
      "dropout_rate": 0.2
    }
  },
  "all_results": [...]
}
```

## Resource Configuration

All tasks use the following environment:

```python
task_env = {
    "cpu": "2",
    "memory": "4Gi",
    "gpu": "0"
}
```

Individual task specifications:
- **Data Generation**: 2 CPU, 4Gi memory
- **Single Experiment**: 2 CPU, 4Gi memory
- **Parallel Execution**: 4 CPU, 8Gi memory
- **Comparison**: 1 CPU, 2Gi memory
- **Save Results**: 0.5 CPU, 1Gi memory

## Caching Strategy

All tasks implement caching with:
- Version: "1.0"
- Max age: 3600 seconds (1 hour)
- Cache key based on input parameters

This allows efficient reuse of experiment results when running with the same configurations.

## Metrics

Supported comparison metrics:
- **accuracy**: Higher is better (default)
- **loss**: Lower is better

## Best Practices

1. **Reproducibility**: Always use the same `random_seed` for comparable results
2. **Resource Planning**: Adjust `num_experiments` based on available resources
3. **Metric Selection**: Choose appropriate metric based on your use case
4. **Configuration Space**: Use `create_experiment_configs()` for systematic exploration

## Example Output

```
Running 8 experiments in parallel...
Completed 8 experiments

================================================================================
EXPERIMENT COMPARISON SUMMARY (sorted by accuracy)
================================================================================
ID              LR         Batch      Epochs     Accuracy    Loss        
--------------------------------------------------------------------------------
exp_003         0.0100     64         100        0.8765      0.1234     
exp_007         0.1000     128        50         0.8543      0.1456     
exp_001         0.0010     32         50         0.8234      0.1765     
...

🏆 Best Experiment: exp_003
   Accuracy: 0.8765
   Configuration: LR=0.01, Batch=64, Epochs=100
================================================================================

Results saved to: /home/user/flyte_project/experiment_result.json
```

## License

MIT License