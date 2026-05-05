# Multi-Environment GPU/CPU ML Training Pipeline with Flyte 2.0

## Background

Flyte 2.0 introduces a Python-native task execution model where tasks are defined using `@env.task` decorators on async functions. A key capability is defining **multiple `TaskEnvironment`s** with different compute resources — CPU-only environments for lightweight preprocessing and evaluation, and GPU-enabled environments for heavy model training — all as plain Python code without a separate `@workflow` decorator.

In this task you will implement a complete multi-environment ML training system split across three files: `environments.py` (resource definitions), `pipeline.py` (task implementations), and `main.py` (entry point).

## Requirements

Create the following three files inside `/home/user/flyte_project/`:

### File 1 — `/home/user/flyte_project/environments.py`

Define three `TaskEnvironment` objects:

```python
import flyte

cpu_env = flyte.TaskEnvironment("cpu-preprocessing", resources=flyte.Resources(cpu=4, memory="8Gi"))
gpu_env = flyte.TaskEnvironment("gpu-training", resources=flyte.Resources(cpu=8, memory="32Gi"))
eval_env = flyte.TaskEnvironment("cpu-evaluation", resources=flyte.Resources(cpu=2, memory="4Gi"))
```

### File 2 — `/home/user/flyte_project/pipeline.py`

Import the three environments from `environments.py` and implement four tasks:

1. **`preprocess(raw_data: list) -> dict`** — decorated with `@cpu_env.task`:
   - Remove `None` values and convert remaining items to `float`
   - Return `{"data": cleaned, "n_samples": len(cleaned), "preprocessing_env": "cpu"}`

2. **`train(preprocessed: dict) -> dict`** — decorated with `@gpu_env.task`:
   - Return:
     ```python
     {
         "model_weights": [0.1 * i for i in range(5)],
         "n_samples_trained": preprocessed["n_samples"],
         "training_env": "gpu",
         "loss": max(0.01, 1.0 / preprocessed["n_samples"])
     }
     ```

3. **`evaluate(model: dict, test_data: list) -> dict`** — decorated with `@eval_env.task`:
   - Return:
     ```python
     {
         "accuracy": min(0.99, model["n_samples_trained"] * 0.05),
         "loss": model["loss"],
         "test_samples": len(test_data),
         "eval_env": "cpu"
     }
     ```

4. **`full_pipeline(train_data: list, test_data: list) -> dict`** — decorated with `@cpu_env.task`:
   - Chain: `preprocess(train_data)` → `train(preprocessed)` → `evaluate(model, test_data)`
   - Return `{"preprocessing": preprocessed, "model": model, "evaluation": eval_result}`

### File 3 — `/home/user/flyte_project/main.py`

```python
import asyncio
import json
from pipeline import full_pipeline

if __name__ == "__main__":
    train_data = [1.0, None, 2.0, 3.0, None, 4.0, 5.0]
    test_data = [0.5, 1.5, 2.5]
    result = asyncio.run(full_pipeline(train_data, test_data))
    with open("/home/user/flyte_project/training_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
```

## Implementation Guide

1. Install Flyte 2.0: `pip install flyte`
2. Create the project directory: `mkdir -p /home/user/flyte_project`
3. Create `environments.py`, `pipeline.py`, and `main.py` as described above.
4. Run: `cd /home/user/flyte_project && python3 main.py`

## Expected Behaviour

- `train_data = [1.0, None, 2.0, 3.0, None, 4.0, 5.0]` → after removing `None`: `[1.0, 2.0, 3.0, 4.0, 5.0]` → `n_samples = 5`
- `loss = max(0.01, 1.0 / 5) = 0.2`
- `accuracy = min(0.99, 5 * 0.05) = 0.25`
- The result JSON must contain three top-level keys: `preprocessing`, `model`, `evaluation`
- `preprocessing.preprocessing_env` == `"cpu"`, `preprocessing.n_samples` == `5`
- `model.training_env` == `"gpu"`
- `evaluation.eval_env` == `"cpu"`, `evaluation.accuracy` == `0.25`

## Constraints
- Project path: `/home/user/flyte_project`
- Result file: `/home/user/flyte_project/training_result.json`
- Use `flyte` (Flyte 2.0) — install with `pip install flyte`
- No `@workflow` decorator — Flyte 2.0 uses `TaskEnvironment` and `@env.task` async functions
- Environments must be defined in `environments.py` and imported into `pipeline.py`
