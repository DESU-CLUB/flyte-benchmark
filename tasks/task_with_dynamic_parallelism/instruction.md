# Flyte 2.0 — Dynamic Parallelism Feature Engineering Pipeline

## Background

Flyte 2.0 embraces native Python async primitives for parallelism. Instead of a `@workflow` decorator or `flytekit.map`, you compose parallel execution using `asyncio.gather`. Tasks are `async def` functions decorated with `@env.task` from a `TaskEnvironment`, and you run them with `asyncio.run()`.

Dynamic parallelism means the number of parallel tasks is computed at runtime — the task arguments (configs) are generated dynamically based on input parameters, not hardcoded at the call site.

## Requirements

Create the file `/home/user/flyte_project/dynamic_pipeline.py` implementing a dynamically parallel feature engineering pipeline.

### 1. Setup

- Import `asyncio`, `json`, and `flyte`.
- Create a `TaskEnvironment` named `"dynamic-env"` (assign it to a variable named `env`).

### 2. Task: `generate_feature_configs`

Define an async task:

```python
@env.task
async def generate_feature_configs(dataset_size: int) -> list:
    return [
        {"feature": f"feature_{i}", "window": i + 1, "agg": agg}
        for i in range(3)
        for agg in ["mean", "max"]
    ]
```

This returns 6 configs (3 features × 2 aggregations). The `dataset_size` parameter determines the scope at runtime — this is the dynamic aspect.

### 3. Task: `compute_feature`

Define an async task:

```python
@env.task
async def compute_feature(config: dict, data_size: int) -> dict:
    return {
        "feature": config["feature"],
        "agg": config["agg"],
        "window": config["window"],
        "value": data_size / config["window"] * (1.5 if config["agg"] == "mean" else 2.0),
    }
```

### 4. Task: `build_feature_matrix`

Define an async task:

```python
@env.task
async def build_feature_matrix(features: list) -> dict:
    return {
        "n_features": len(features),
        "feature_names": list(set(f["feature"] for f in features)),
        "feature_matrix": features,
    }
```

### 5. Task: `run_feature_pipeline`

Define an async task that:
- Accepts `dataset_size: int`
- Generates configs: `configs = await generate_feature_configs(dataset_size)`
- Computes ALL features in parallel: `features = await asyncio.gather(*[compute_feature(cfg, dataset_size) for cfg in configs])`
- Builds and returns the feature matrix: `return await build_feature_matrix(list(features))`

```python
@env.task
async def run_feature_pipeline(dataset_size: int) -> dict:
    configs = await generate_feature_configs(dataset_size)
    features = await asyncio.gather(*[compute_feature(cfg, dataset_size) for cfg in configs])
    return await build_feature_matrix(list(features))
```

### 6. `__main__` block

In the `if __name__ == "__main__":` block:

- Call `asyncio.run(run_feature_pipeline(100))`
- Write the returned dict as JSON to `/home/user/flyte_project/feature_matrix.json`

```python
if __name__ == "__main__":
    result = asyncio.run(run_feature_pipeline(100))
    with open("/home/user/flyte_project/feature_matrix.json", "w") as f:
        json.dump(result, f)
```

## Implementation Guide

1. Do **not** use `@workflow` or `flytekit.map` — they do not exist in Flyte 2.0.
2. Parallelism is **dynamic**: the list of `compute_feature` coroutines is generated at runtime from the configs returned by `generate_feature_configs`.
3. All task functions must be `async def` and decorated with `@env.task`.
4. Running the script with `python3 /home/user/flyte_project/dynamic_pipeline.py` must:
   - Execute without errors
   - Produce `/home/user/flyte_project/feature_matrix.json`

## Constraints

- **Project path**: `/home/user/flyte_project`
- **Script**: `/home/user/flyte_project/dynamic_pipeline.py`
- **Result file**: `/home/user/flyte_project/feature_matrix.json`
- The `flyte` package is already installed — do **not** reinstall it.
- Use only the standard library plus `flyte`.
