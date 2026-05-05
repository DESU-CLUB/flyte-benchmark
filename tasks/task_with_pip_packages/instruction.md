# Flyte 2.0 — Task with Pip Packages

## Overview

You have Flyte 2.0 installed in this environment (`pip install flyte`). Your task is to create a Python script that defines a data-summarisation task using Flyte 2.0's `TaskEnvironment` API with a custom image that declares `pandas` and `numpy` as pip dependencies, then runs it locally.

## Requirements

### 1. Create the project file

Create a Python script at `/home/user/flyte_project/data_task.py` that does the following:

- Imports `flyte`, `numpy`, `json`, and `asyncio`.
- Creates a `TaskEnvironment` named `"data-env"` (assign it to a variable called `env`) using a custom image:
  ```python
  env = flyte.TaskEnvironment(
      "data-env",
      image=flyte.Image.from_debian_base().with_pip_packages("pandas", "numpy")
  )
  ```
- Defines a task `summarize_data(values: list) -> dict` decorated with `@env.task` that:
  - Uses `numpy` to compute `mean`, `std`, `min`, and `max` of the values.
  - Returns a `dict` with keys `mean`, `std`, `min`, and `max`.
- In a `if __name__ == "__main__":` block:
  - Calls `asyncio.run(summarize_data([1.0, 2.0, 3.0, 4.0, 5.0]))` and stores the result.
  - Writes the result dict as JSON to `/home/user/flyte_project/summary.json`.

### 2. Run the script

Execute the script:

```bash
python3 /home/user/flyte_project/data_task.py
```

## Key Details

- **Project path**: `/home/user/flyte_project`
- **Log file**: `/home/user/flyte_project/summary.json`
- The `flyte`, `pandas`, and `numpy` packages are already installed — do **not** reinstall them.
- Flyte 2.0 tasks decorated with `@env.task` are `async def` functions; use `await` when calling them from another task and `asyncio.run()` at the top level.
- The `with_pip_packages(...)` call on `flyte.Image` is metadata for remote cluster deployments. When running locally with `python script.py`, the image spec is ignored and the task runs in the current Python environment — so `pandas` and `numpy` must be installed in the host environment (they are).
- There is **no** `@workflow` decorator in Flyte 2.0 — tasks are standalone async functions.

## Expected Behaviour

When the script is run with `values=[1.0, 2.0, 3.0, 4.0, 5.0]`:
- `mean` ≈ 3.0
- `std` ≈ 1.4142 (population std)
- `min` == 1.0
- `max` == 5.0

The file `/home/user/flyte_project/summary.json` should contain a valid JSON object such as:
```json
{"mean": 3.0, "std": 1.4142135623730951, "min": 1.0, "max": 5.0}
```
