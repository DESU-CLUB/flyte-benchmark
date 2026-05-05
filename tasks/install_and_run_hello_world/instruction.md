# Flyte 2.0 Hello World

## Overview

You have Flyte 2.0 installed in this environment (`pip install flyte`). Your task is to create a simple Flyte task that greets a user by name and run it locally.

## Requirements

### 1. Create the project file

Create a Python script at `/home/user/flyte_project/hello.py` that does the following:

- Imports the `flyte` package.
- Creates a `TaskEnvironment` named `"local-env"` (assign it to a variable called `env`).
- Defines a task function `greet(name: str) -> str` decorated with `@env.task` that returns `f"Hello, {name}!"`.
- In a `if __name__ == "__main__":` block, calls `greet` with the argument `"World"` using `asyncio.run()` and prints the result.

### 2. Run the script and capture output

Execute the script and save its output:

```bash
python /home/user/flyte_project/hello.py > /home/user/flyte_project/output.log
```

## Key Details

- **Project path**: `/home/user/flyte_project/hello.py`
- **Log file path**: `/home/user/flyte_project/output.log`
- The `flyte` package is already installed — do **not** reinstall it.
- Flyte 2.0 tasks decorated with `@env.task` are async functions; use `asyncio.run()` to call them.
- There is **no** `@workflow` decorator in Flyte 2.0 — workflows are just tasks that call other tasks.

## Expected Behaviour

When the script is run, it should print:

```
Hello, World!
```

This output must be captured in `/home/user/flyte_project/output.log`.
