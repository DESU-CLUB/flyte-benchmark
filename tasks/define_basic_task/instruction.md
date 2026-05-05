# Flyte 2.0 — Define Basic Tasks

## Overview

You have Flyte 2.0 installed in this environment (`pip install flyte`). Your task is to create a Python script that defines two arithmetic tasks using Flyte 2.0's `TaskEnvironment` API and runs them locally.

## Requirements

### 1. Create the project file

Create a Python script at `/home/user/flyte_project/tasks.py` that does the following:

- Imports the `flyte` package and `asyncio`.
- Creates a `TaskEnvironment` named `"basic-env"` (assign it to a variable called `env`).
- Defines a task function `add(a: int, b: int) -> int` decorated with `@env.task` that returns `a + b`.
- Defines a task function `multiply(a: int, b: int) -> int` decorated with `@env.task` that returns `a * b`.
- Defines a `main()` function that:
  - Calls `asyncio.run(add(3, 4))`, stores the result, and prints it.
  - Calls `asyncio.run(multiply(3, 4))`, stores the result, and prints it.
- In a `if __name__ == "__main__":` block, calls `main()`.

### 2. Run the script and capture output

Execute the script and save its output:

```bash
python /home/user/flyte_project/tasks.py > /home/user/flyte_project/output.log
```

## Key Details

- **Project path**: `/home/user/flyte_project/tasks.py`
- **Log file**: `/home/user/flyte_project/output.log`
- The `flyte` package is already installed — do **not** reinstall it.
- Flyte 2.0 tasks decorated with `@env.task` are `async def` functions; use `asyncio.run()` to call them.
- There is **no** `@workflow` decorator in Flyte 2.0 — tasks are standalone async functions.

## Expected Behaviour

When the script is run, it should print the results of both operations:

```
7
12
```

This output must be captured in `/home/user/flyte_project/output.log`.
