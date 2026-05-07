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
