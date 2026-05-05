# Flyte 2.0 — Fan-Out / Fan-In Pipeline

## Background

Flyte 2.0 uses native Python async primitives for parallelism. The classic fan-out/fan-in pattern — generate a list of work items, process each item concurrently, then aggregate the results — maps cleanly onto `asyncio.gather`. Tasks are `async def` functions decorated with `@env.task` from a `TaskEnvironment`, and the pipeline is launched with `asyncio.run()`.

## Requirements

Create the file `/home/user/flyte_project/fan_out_pipeline.py` implementing the following fan-out/fan-in data processing pipeline.

### 1. Setup

- Import `asyncio`, `json`, and `flyte`.
- Create a `TaskEnvironment` named `"fan-env"` (assign it to a variable named `env`).

### 2. Task: `generate_work_items`

```python
@env.task
async def generate_work_items(n: int) -> list:
    return list(range(n))
```

### 3. Task: `process_item`

```python
@env.task
async def process_item(item: int) -> dict:
    return {"item": item, "squared": item ** 2, "is_even": item % 2 == 0}
```

### 4. Task: `aggregate`

```python
@env.task
async def aggregate(results: list) -> dict:
    return {
        "total": len(results),
        "sum_of_squares": sum(r["squared"] for r in results),
        "even_count": sum(1 for r in results if r["is_even"]),
    }
```

### 5. Task: `fan_out_fan_in`

Define an async task that:
- Accepts `n: int`
- Calls `generate_work_items(n)` to get items
- Uses `asyncio.gather(*[process_item(item) for item in items])` to process all items in parallel
- Calls `aggregate(list(results))` and returns the aggregated dict

```python
@env.task
async def fan_out_fan_in(n: int) -> dict:
    items = await generate_work_items(n)
    results = await asyncio.gather(*[process_item(item) for item in items])
    return await aggregate(list(results))
```

### 6. `__main__` block

In the `if __name__ == "__main__":` block:

- Call `asyncio.run(fan_out_fan_in(5))`
- Write the returned dict as JSON to `/home/user/flyte_project/fan_result.json`

```python
if __name__ == "__main__":
    result = asyncio.run(fan_out_fan_in(5))
    with open("/home/user/flyte_project/fan_result.json", "w") as f:
        json.dump(result, f)
```

## Implementation Guide

1. Do **not** use `@workflow` or `flytekit.map` — they do not exist in Flyte 2.0.
2. Fan-out is achieved via `asyncio.gather`, which runs multiple async task coroutines concurrently.
3. All task functions must be `async def` and decorated with `@env.task`.
4. Running `python3 /home/user/flyte_project/fan_out_pipeline.py` must:
   - Execute without errors
   - Produce `/home/user/flyte_project/fan_result.json`

## Constraints

- **Project path**: `/home/user/flyte_project`
- **Script**: `/home/user/flyte_project/fan_out_pipeline.py`
- **Log file**: `/home/user/flyte_project/fan_result.json`
- The `flyte` package is already installed — do **not** reinstall it.
- Use only the standard library plus `flyte`.
