# Flyte 2.0 — Conditional Branching with Python if/elif/else

## Background

Flyte 2.0 has removed `flytekit.conditional` — the old Flyte 1.x DSL-level conditional construct no longer exists. In Flyte 2.0, conditional branching is expressed using **standard Python `if/elif/else`** (or `try/except`) directly inside `@env.task` async functions. Parallelism is achieved via `asyncio.gather`.

## Requirements

Create the file `/home/user/flyte_project/conditional_pipeline.py` with the following:

### 1. Setup

- Import `asyncio`, `json`, and `flyte`.
- Create a `TaskEnvironment` named `"branching-env"` (assign it to a variable named `env`).

### 2. Task: `classify_input`

Define an async task that classifies a float value into one of four categories:

```python
@env.task
async def classify_input(value: float) -> str:
    if value < 0:
        return "negative"
    elif value == 0.0:
        return "zero"
    elif value < 10:
        return "small_positive"
    else:
        return "large_positive"
```

### 3. Task: `process_by_class`

Define an async task that applies a class-specific operation:

```python
@env.task
async def process_by_class(value: float, classification: str) -> dict:
    if classification == "negative":
        return {"class": "negative", "result": abs(value), "operation": "abs"}
    elif classification == "zero":
        return {"class": "zero", "result": 0.0, "operation": "identity"}
    elif classification == "small_positive":
        return {"class": "small_positive", "result": value * 2, "operation": "double"}
    else:
        return {"class": "large_positive", "result": value ** 0.5, "operation": "sqrt"}
```

### 4. Task: `conditional_pipeline`

Define an async task that:
- Accepts `values: list`
- Classifies all values **in parallel** using `asyncio.gather` on the `classify_input` calls
- Processes each value with its classification (sequentially or with `asyncio.gather`) using `process_by_class`
- Returns a list of result dicts in the same order as the input

```python
@env.task
async def conditional_pipeline(values: list) -> list:
    classifications = await asyncio.gather(*[classify_input(v) for v in values])
    results = await asyncio.gather(*[process_by_class(v, c) for v, c in zip(values, classifications)])
    return list(results)
```

### 5. `__main__` block

In the `if __name__ == "__main__":` block:

- Call `asyncio.run(conditional_pipeline([-5.0, 0.0, 3.0, 25.0]))`
- Write the returned list as JSON to `/home/user/flyte_project/conditional_results.json`

```python
if __name__ == "__main__":
    results = asyncio.run(conditional_pipeline([-5.0, 0.0, 3.0, 25.0]))
    with open("/home/user/flyte_project/conditional_results.json", "w") as f:
        json.dump(results, f)
```

## Implementation Guide

1. **Do NOT use `flytekit.conditional`** — it is removed in Flyte 2.0. Use standard Python `if/elif/else` inside your `@env.task` functions.
2. Do **not** use `@workflow` — it does not exist in Flyte 2.0.
3. All task functions must be `async def` decorated with `@env.task`.
4. Parallelism is achieved via `asyncio.gather`, which runs multiple async task coroutines concurrently and **preserves input order** in the results.
5. Running the script with `python3 /home/user/flyte_project/conditional_pipeline.py` must:
   - Execute without errors
   - Produce `/home/user/flyte_project/conditional_results.json`

## Constraints

- **Project path**: `/home/user/flyte_project`
- **Script**: `/home/user/flyte_project/conditional_pipeline.py`
- **Log file**: `/home/user/flyte_project/conditional_results.json`
- The `flyte` package is already installed — do **not** reinstall it.
- Use only the standard library plus `flyte`.
