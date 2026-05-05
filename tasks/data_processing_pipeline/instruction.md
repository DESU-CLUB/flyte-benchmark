# Flyte 2.0 Data Processing Pipeline

## Background
Flyte 2.0 introduces a new `@env.task` decorator pattern for defining async tasks within a `TaskEnvironment`. In this task you will use Flyte 2.0 to build a multi-stage data processing pipeline that loads several CSV datasets concurrently, computes per-dataset statistics in parallel, and merges the results into a summary report.

## Requirements
- Create a script `/home/user/flyte_project/data_pipeline.py` that implements all pipeline stages below using Flyte 2.0.
- The pipeline must process multiple datasets in parallel using `asyncio.gather`.
- Final merged statistics must be written to `/home/user/flyte_project/pipeline_stats.json`.

## Implementation Guide

### 1. Install Flyte 2.0
```bash
pip install flyte
```

### 2. Create `/home/user/flyte_project/data_pipeline.py`

```python
import asyncio
import json
from flyte import TaskEnvironment

env = TaskEnvironment("data-pipeline-env")

@env.task
async def load_dataset(name: str) -> dict:
    if name == "sales":
        return {"name": "sales", "rows": [{"product": "A", "qty": 100, "price": 10.0}, {"product": "B", "qty": 50, "price": 20.0}]}
    elif name == "inventory":
        return {"name": "inventory", "rows": [{"product": "A", "stock": 500}, {"product": "B", "stock": 200}]}
    else:
        return {"name": name, "rows": []}

@env.task
async def compute_dataset_stats(dataset: dict) -> dict:
    return {"name": dataset["name"], "row_count": len(dataset["rows"]), "has_data": len(dataset["rows"]) > 0}

@env.task
async def merge_stats(stats_list: list) -> dict:
    return {
        "total_datasets": len(stats_list),
        "total_rows": sum(s["row_count"] for s in stats_list),
        "datasets": [s["name"] for s in stats_list]
    }

@env.task
async def run_data_pipeline(dataset_names: list) -> dict:
    datasets = await asyncio.gather(*[load_dataset(n) for n in dataset_names])
    stats = await asyncio.gather(*[compute_dataset_stats(d) for d in datasets])
    return await merge_stats(list(stats))

if __name__ == "__main__":
    result = asyncio.run(run_data_pipeline(["sales", "inventory", "returns"]))
    with open("/home/user/flyte_project/pipeline_stats.json", "w") as f:
        json.dump(result, f)
```

### 3. Run the pipeline
```bash
python3 /home/user/flyte_project/data_pipeline.py
```

## Constraints
- Project path: /home/user/flyte_project
- Log file: /home/user/flyte_project/pipeline_stats.json
- Use `flyte` (Flyte 2.0) package installed via `pip install flyte`.
- Use `TaskEnvironment("data-pipeline-env")` and `@env.task` async functions.
- Use `asyncio.gather` for all parallel stages.
- Do not use external services; all data is mocked inline.
