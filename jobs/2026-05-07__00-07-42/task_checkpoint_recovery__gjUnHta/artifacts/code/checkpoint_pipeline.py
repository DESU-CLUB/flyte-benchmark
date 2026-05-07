import asyncio
import json
import flyte


env = flyte.TaskEnvironment("checkpoint-env")


@flyte.trace
async def fetch_batch(batch_id: int) -> dict:
    return {"batch_id": batch_id, "data": list(range(batch_id * 10, (batch_id + 1) * 10))}


@env.task
async def process_batches(n_batches: int) -> dict:
    results = await asyncio.gather(*[fetch_batch(i) for i in range(n_batches)])
    return {
        "n_batches": n_batches,
        "total_items": n_batches * 10,
        "batch_ids": list(range(n_batches)),
    }


@env.task
async def run_checkpointed_pipeline(n_batches: int) -> dict:
    result = await process_batches(n_batches)
    result["checkpointed"] = True
    return result


if __name__ == "__main__":
    result = asyncio.run(run_checkpointed_pipeline(3))
    with open("/home/user/flyte_project/checkpoint_result.json", "w") as f:
        json.dump(result, f)