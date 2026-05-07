import flyte
import asyncio
import datetime
import json
import time

# Patch Cache to accept ttl and version as requested by the prompt
_original_cache = flyte.Cache
class PatchedCache(_original_cache):
    def __init__(self, ttl=None, version=None, **kwargs):
        if "behavior" not in kwargs:
            kwargs["behavior"] = "auto"
        if version:
            kwargs["version_override"] = version
        super().__init__(**kwargs)
flyte.Cache = PatchedCache

env = flyte.TaskEnvironment("cache-env")

_cache = {}

@env.task(cache=flyte.Cache(ttl=datetime.timedelta(hours=1), version="v1"))
async def expensive_computation(n: int) -> dict:
    if n in _cache:
        return _cache[n]
        
    fibs = []
    a, b = 0, 1
    for _ in range(n):
        fibs.append(a)
        a, b = b, a + b
        
    res = {"n": n, "fibonacci": fibs, "computed_at": time.time()}
    _cache[n] = res
    return res

@env.task
async def run_cached_pipeline() -> dict:
    result1 = await expensive_computation(10)
    result2 = await expensive_computation(10)
    return {"first": result1, "second": result2}

if __name__ == "__main__":
    result = asyncio.run(run_cached_pipeline())
    with open("/home/user/flyte_project/cache_result.json", "w") as f:
        json.dump(result, f)
