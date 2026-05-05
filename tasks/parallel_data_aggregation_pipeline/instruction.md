# Parallel Data Aggregation Pipeline with Flyte 2.0

## Background

Flyte 2.0 introduces a lightweight Python-first task model using `@env.task` async functions, `TaskEnvironment`, and `asyncio.gather` for true parallel execution — no cluster required for local runs. Your goal is to build a multi-file Flyte 2.0 project that fetches data from three simulated sources **in parallel**, normalizes each result **in parallel**, and then aggregates everything into a final JSON report.

## Requirements

Create a two-file Python project under `/home/user/flyte_project/`:

1. **`/home/user/flyte_project/tasks.py`** — defines all Flyte tasks.
2. **`/home/user/flyte_project/main.py`** — entry point that runs the pipeline and writes the report.

### `tasks.py` must define:

- A `TaskEnvironment` named `"aggregation-env"` with `flyte.Resources(cpu=4, memory="8Gi")`.
- **`fetch_source(source_id: str) -> dict`** — an `@env.task` async function that returns hardcoded mock data for each of the three sources:
  - `"source_a"`: `{"source_id": "source_a", "row_count": 100, "total_value": 5000.0}`
  - `"source_b"`: `{"source_id": "source_b", "row_count": 250, "total_value": 12500.0}`
  - `"source_c"`: `{"source_id": "source_c", "row_count": 75, "total_value": 3750.0}`
  - For any unknown source_id, raise a `ValueError`.
- **`normalize_source(raw: dict) -> dict`** — an `@env.task` async function that standardizes the schema, returning `{"id": raw["source_id"], "count": raw["row_count"], "total": raw["total_value"]}`.
- **`compute_aggregate(normalized_list: list) -> dict`** — an `@env.task` async function that returns a summary dict with keys: `grand_total` (sum of all `total`), `max_count` (max of all `count`), `min_count` (min of all `count`), `source_count` (number of sources).
- **`run_pipeline(source_ids: list) -> dict`** — an `@env.task` async function that:
  1. Uses `asyncio.gather` to **fetch all sources in parallel**.
  2. Uses a second `asyncio.gather` to **normalize all fetched results in parallel**.
  3. Calls `compute_aggregate` on the normalized list.
  4. Returns the aggregate dict.

### `main.py` must:

- Import `run_pipeline` from `tasks`.
- Call `asyncio.run(run_pipeline(["source_a", "source_b", "source_c"]))` to execute the pipeline.
- Write the resulting aggregate dict as JSON to `/home/user/flyte_project/aggregate_report.json`.

## Implementation Guide

### Step 1 — Create project directory

```bash
mkdir -p /home/user/flyte_project
```

### Step 2 — Write `tasks.py`

```python
import asyncio
import flyte
from flyte import TaskEnvironment

env = TaskEnvironment("aggregation-env", resources=flyte.Resources(cpu=4, memory="8Gi"))

_MOCK_DATA = {
    "source_a": {"source_id": "source_a", "row_count": 100, "total_value": 5000.0},
    "source_b": {"source_id": "source_b", "row_count": 250, "total_value": 12500.0},
    "source_c": {"source_id": "source_c", "row_count": 75, "total_value": 3750.0},
}

@env.task
async def fetch_source(source_id: str) -> dict:
    if source_id not in _MOCK_DATA:
        raise ValueError(f"Unknown source: {source_id}")
    return _MOCK_DATA[source_id]

@env.task
async def normalize_source(raw: dict) -> dict:
    return {"id": raw["source_id"], "count": raw["row_count"], "total": raw["total_value"]}

@env.task
async def compute_aggregate(normalized_list: list) -> dict:
    return {
        "grand_total": sum(n["total"] for n in normalized_list),
        "max_count": max(n["count"] for n in normalized_list),
        "min_count": min(n["count"] for n in normalized_list),
        "source_count": len(normalized_list),
    }

@env.task
async def run_pipeline(source_ids: list) -> dict:
    # First gather: fetch all sources in parallel
    raw_results = await asyncio.gather(*[fetch_source(sid) for sid in source_ids])
    # Second gather: normalize all in parallel
    normalized = await asyncio.gather(*[normalize_source(r) for r in raw_results])
    # Aggregate
    return await compute_aggregate(list(normalized))
```

### Step 3 — Write `main.py`

```python
import asyncio
import json
from tasks import run_pipeline

if __name__ == "__main__":
    result = asyncio.run(run_pipeline(["source_a", "source_b", "source_c"]))
    with open("/home/user/flyte_project/aggregate_report.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Pipeline complete:", result)
```

### Step 4 — Run the pipeline

```bash
cd /home/user/flyte_project && python3 main.py
```

## Constraints

- Project path: `/home/user/flyte_project`
- Log file: `/home/user/flyte_project/aggregate_report.json`
- Both `tasks.py` and `main.py` must exist under the project path.
- Use `asyncio.gather` **twice** inside `run_pipeline`: once for parallel fetching and once for parallel normalization.
- The `TaskEnvironment` name must be `"aggregation-env"` with `cpu=4` and `memory="8Gi"`.
- Do **not** hardcode the final result in `main.py`; it must be produced by executing `run_pipeline`.
