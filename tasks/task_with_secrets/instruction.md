# Flyte 2.0 Task with Secrets

## Background

Flyte 2.0 provides a `Secret` primitive that lets you declare secret dependencies at the task level using `@env.task(secret_requests=[...])`. In a local execution context, secrets are resolved from environment variables following the convention `<GROUP>__<KEY>` (upper-cased, hyphens replaced by underscores), or a plain fallback variable name. This task walks you through building a pipeline that reads an API key from the environment, uses it to simulate authenticated HTTP calls, and writes results to disk.

## Requirements

- Create `/home/user/flyte_project/secret_task.py` that:
  1. Creates a `TaskEnvironment` named `"secure-env"`.
  2. Declares a module-level `Secret`: `API_SECRET = flyte.Secret(key="api_key", group="my-secrets")`.
  3. Defines an async task `authenticated_call(endpoint: str) -> dict` decorated with `@env.task(secret_requests=[API_SECRET])` that:
     - Reads the API key from env var `MY_SECRETS__API_KEY` (Flyte local convention) or `API_KEY` as a fallback.
     - Returns `{"endpoint": endpoint, "authenticated": api_key is not None and len(api_key) > 0, "key_length": len(api_key) if api_key else 0}`.
  4. Defines an async task `run_secure_pipeline(endpoints: list) -> list` that calls `authenticated_call` for each endpoint using `asyncio.gather`.
  5. In `__main__`, sets `os.environ["API_KEY"] = "test-api-key-12345"`, calls `asyncio.run(run_secure_pipeline(["/api/v1/data", "/api/v1/models"]))`, and writes the result to `/home/user/flyte_project/secure_output.json`.

## Implementation Guide

### Step 1 — Install Flyte 2.0

```bash
pip install flyte
```

### Step 2 — Create `/home/user/flyte_project/secret_task.py`

```python
import asyncio
import json
import os
import flyte

# 1. Create the task environment
env = flyte.TaskEnvironment("secure-env")

# 2. Declare the Secret
API_SECRET = flyte.Secret(key="api_key", group="my-secrets")

# 3. Authenticated call task
@env.task(secret_requests=[API_SECRET])
async def authenticated_call(endpoint: str) -> dict:
    # Flyte local convention: GROUP__KEY (uppercased, hyphens replaced by underscores)
    api_key = os.environ.get("MY_SECRETS__API_KEY") or os.environ.get("API_KEY")
    return {
        "endpoint": endpoint,
        "authenticated": api_key is not None and len(api_key) > 0,
        "key_length": len(api_key) if api_key else 0,
    }

# 4. Pipeline task
@env.task
async def run_secure_pipeline(endpoints: list) -> list:
    results = await asyncio.gather(*[authenticated_call(ep) for ep in endpoints])
    return list(results)

if __name__ == "__main__":
    os.environ["API_KEY"] = "test-api-key-12345"
    result = asyncio.run(run_secure_pipeline(["/api/v1/data", "/api/v1/models"]))
    with open("/home/user/flyte_project/secure_output.json", "w") as f:
        json.dump(result, f)
    print(result)
```

### Step 3 — Run the script

```bash
API_KEY="test-api-key-12345" python3 /home/user/flyte_project/secret_task.py
```

The script writes results to `/home/user/flyte_project/secure_output.json`.

## Constraints

- Project path: `/home/user/flyte_project`
- Log file: `/home/user/flyte_project/secure_output.json`
- Use `pip install flyte` (Flyte 2.0 package name).
- Do NOT use the old `flytekit` API — use `flyte` (the new package).
- Tasks must be `async def` decorated with `@env.task`.
- For local execution, the API key is provided via the `API_KEY` environment variable (or `MY_SECRETS__API_KEY`).
- The `run_secure_pipeline` task must call `authenticated_call` for each endpoint concurrently using `asyncio.gather`.
