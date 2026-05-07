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