import asyncio
import datetime
import json
import time

import flyte


env = flyte.TaskEnvironment(name="cache-env")


@env.task(cache=flyte.Cache(ttl=datetime.timedelta(hours=1), version="v1"))
async def expensive_computation(n: int) -> dict:
    fibs = []
    a, b = 0, 1
    for _ in range(n):
        fibs.append(a)
        a, b = b, a + b
    return {"n": n, "fibonacci": fibs, "computed_at": time.time()}


@env.task
async def run_cached_pipeline() -> dict:
    result1 = await expensive_computation(10)
    result2 = await expensive_computation(10)
    return {"first": result1, "second": result2}


if __name__ == "__main__":
    result = asyncio.run(run_cached_pipeline())
    with open("/home/user/flyte_project/cache_result.json", "w") as f:
        json.dump(result, f)
