import asyncio
import json
import flyte

env = flyte.TaskEnvironment("parallel-env")


@env.task
async def fetch_data(source: str) -> dict:
    return {"source": source, "records": len(source) * 10}


@env.task
async def aggregate_results(results: list) -> dict:
    return {
        "total_sources": len(results),
        "total_records": sum(r["records"] for r in results),
        "sources": [r["source"] for r in results],
    }


@env.task
async def run_parallel_pipeline(sources: list) -> dict:
    results = await asyncio.gather(*[fetch_data(s) for s in sources])
    return await aggregate_results(list(results))


if __name__ == "__main__":
    result = asyncio.run(run_parallel_pipeline(["alpha", "beta", "gamma"]))
    with open("/home/user/flyte_project/pipeline_result.json", "w") as f:
        json.dump(result, f)
