import asyncio
import json
from flyte import TaskEnvironment

env = TaskEnvironment("robust-env")

@env.task
async def risky_operation(value: int) -> int:
    if value > 100:
        raise ValueError("Value too large")
    return value * 2

@env.task
async def safe_operation(value: int, fallback: int) -> dict:
    try:
        result = await risky_operation(value)
        return {"result": result, "status": "success", "used_fallback": False}
    except ValueError:
        fallback_result = await risky_operation(fallback)
        return {"result": fallback_result, "status": "fallback", "used_fallback": True}

@env.task
async def run_pipeline() -> list:
    r1 = await safe_operation(50, 10)
    r2 = await safe_operation(200, 5)
    return [r1, r2]

if __name__ == "__main__":
    results = asyncio.run(run_pipeline())
    with open("/home/user/flyte_project/error_results.json", "w") as f:
        json.dump(results, f)