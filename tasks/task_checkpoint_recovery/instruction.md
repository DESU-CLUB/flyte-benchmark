# Flyte 2.0 — Task Checkpoint Recovery

## Background

Flyte 2.0 provides `@flyte.trace` as the key primitive for fine-grained, sub-task level checkpointing. By decorating an async function with `@flyte.trace`, Flyte can checkpoint expensive operations so that on failure the pipeline can resume from the last successful checkpoint rather than restarting from scratch.

## Requirements

Create the file `/home/user/flyte_project/checkpoint_pipeline.py` with the following:

### 1. Setup

- Import `asyncio`, `json`, and `flyte`.
- Create a `TaskEnvironment` named `"checkpoint-env"` (assign it to a variable named `env`).

### 2. Traced function: `fetch_batch`

Define a `@flyte.trace` decorated async function:

```python
@flyte.trace
async def fetch_batch(batch_id: int) -> dict:
    return {"batch_id": batch_id, "data": list(range(batch_id * 10, (batch_id + 1) * 10))}
```

This simulates fetching a batch of data. The `@flyte.trace` decorator enables checkpointing so that if the pipeline is interrupted, already-fetched batches do not need to be re-fetched.

### 3. Task: `process_batches`

Define an async task:

```python
@env.task
async def process_batches(n_batches: int) -> dict:
    results = await asyncio.gather(*[fetch_batch(i) for i in range(n_batches)])
    return {
        "n_batches": n_batches,
        "total_items": n_batches * 10,
        "batch_ids": list(range(n_batches)),
    }
```

### 4. Task: `run_checkpointed_pipeline`

Define an async task that calls `process_batches` and adds a `"checkpointed": True` flag to the result:

```python
@env.task
async def run_checkpointed_pipeline(n_batches: int) -> dict:
    result = await process_batches(n_batches)
    result["checkpointed"] = True
    return result
```

### 5. `__main__` block

In the `if __name__ == "__main__":` block:

- Call `asyncio.run(run_checkpointed_pipeline(3))`
- Write the returned dict as JSON to `/home/user/flyte_project/checkpoint_result.json`

```python
if __name__ == "__main__":
    result = asyncio.run(run_checkpointed_pipeline(3))
    with open("/home/user/flyte_project/checkpoint_result.json", "w") as f:
        json.dump(result, f)
```

## Implementation Guide

1. `@flyte.trace` is the Flyte 2.0 primitive for checkpointing — apply it to `fetch_batch`.
2. Tasks (`process_batches`, `run_checkpointed_pipeline`) must be `async def` and decorated with `@env.task`.
3. Use `asyncio.gather` inside `process_batches` to invoke all `fetch_batch` calls concurrently.
4. Running the script with `python3 /home/user/flyte_project/checkpoint_pipeline.py` must:
   - Execute without errors
   - Produce `/home/user/flyte_project/checkpoint_result.json`

## Constraints

- **Project path**: `/home/user/flyte_project`
- **Script**: `/home/user/flyte_project/checkpoint_pipeline.py`
- **Result file**: `/home/user/flyte_project/checkpoint_result.json`
- The `flyte` package is already installed — do **not** reinstall it.
- Use only the standard library plus `flyte`.
