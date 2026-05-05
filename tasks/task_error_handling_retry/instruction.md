# Flyte 2.0 — Error Handling & Retry with Try/Except

## Background

Flyte 2.0 introduces a Python-native task model where each task is an `async def` function decorated with `@env.task`, where `env` is a `TaskEnvironment` instance. Error handling is done with standard Python `try/except` blocks, making self-healing pipelines natural to write without any special Flyte-specific constructs.

## Requirements

Create a Flyte 2.0 pipeline script at `/home/user/flyte_project/error_handling.py` that demonstrates:

1. A `TaskEnvironment` named `"robust-env"`.
2. A task `risky_operation(value: int) -> int` that raises `ValueError("Value too large")` when `value > 100`, and returns `value * 2` otherwise.
3. A task `safe_operation(value: int, fallback: int) -> dict` that calls `risky_operation(value)` in a `try/except` block:
   - On success: returns `{"result": result, "status": "success", "used_fallback": False}`
   - On `ValueError`: calls `risky_operation(fallback)` and returns `{"result": fallback_result, "status": "fallback", "used_fallback": True}`
4. A task `run_pipeline() -> list` that runs both:
   - `safe_operation(50, 10)` — succeeds because 50 ≤ 100, result = 100
   - `safe_operation(200, 5)` — triggers fallback because 200 > 100, result = 10
   - Returns a list containing both result dicts.
5. A `__main__` block that calls `asyncio.run(run_pipeline())`, then writes the returned list as JSON to `/home/user/flyte_project/error_results.json`.

## Implementation Guide

1. Install Flyte 2.0:
   ```bash
   pip install flyte
   ```
2. Create the project directory:
   ```bash
   mkdir -p /home/user/flyte_project
   ```
3. Create `/home/user/flyte_project/error_handling.py`:
   ```python
   import asyncio
   import json
   from flyte import TaskEnvironment

   env = TaskEnvironment("robust-env")

   @env.task
   async def risky_operation(value: int) -> int:
       if value > 100:
           raise ValueError("Value too large")
       return value * 2

   @env.task
   async def safe_operation(value: int, fallback: int) -> dict:
       try:
           result = await risky_operation(value)
           return {"result": result, "status": "success", "used_fallback": False}
       except ValueError:
           fallback_result = await risky_operation(fallback)
           return {"result": fallback_result, "status": "fallback", "used_fallback": True}

   @env.task
   async def run_pipeline() -> list:
       r1 = await safe_operation(50, 10)
       r2 = await safe_operation(200, 5)
       return [r1, r2]

   if __name__ == "__main__":
       results = asyncio.run(run_pipeline())
       with open("/home/user/flyte_project/error_results.json", "w") as f:
           json.dump(results, f)
   ```
4. Run the script:
   ```bash
   python3 /home/user/flyte_project/error_handling.py
   ```

## Constraints

- Project path: /home/user/flyte_project
- Log file: /home/user/flyte_project/error_results.json
- Use `flyte` (Flyte 2.0) only — do NOT use `flytekit`.
- The `__main__` block must use `asyncio.run()` to execute `run_pipeline()`.
- Write the results list as JSON to `/home/user/flyte_project/error_results.json`.
