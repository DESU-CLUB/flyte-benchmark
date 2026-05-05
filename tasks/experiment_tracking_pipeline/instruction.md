# Flyte 2.0 Experiment Tracking Pipeline

Build a Flyte 2.0 experiment tracking system at `/home/user/flyte_project/experiment_tracker.py` that runs multiple ML experiments in parallel and identifies the best configuration.

## Requirements
- Use `flyte.TaskEnvironment` with appropriate resources
- Run multiple experiment configurations in parallel using `asyncio.gather`
- Cache experiment results with `flyte.Cache`
- Compare experiments and save results

## Constraints
- Project path: /home/user/flyte_project
- Log file: /home/user/flyte_project/experiment_result.json
