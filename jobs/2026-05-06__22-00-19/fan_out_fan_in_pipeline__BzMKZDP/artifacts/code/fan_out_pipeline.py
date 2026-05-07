import asyncio
import json
import flyte

# Create a TaskEnvironment named "fan-env"
env = flyte.TaskEnvironment("fan-env")

@env.task
async def generate_work_items(n: int) -> list:
    return list(range(n))

@env.task
async def process_item(item: int) -> dict:
    return {"item": item, "squared": item ** 2, "is_even": item % 2 == 0}

@env.task
async def aggregate(results: list) -> dict:
    return {
        "total": len(results),
        "sum_of_squares": sum(r["squared"] for r in results),
        "even_count": sum(1 for r in results if r["is_even"]),
    }

@env.task
async def fan_out_fan_in(n: int) -> dict:
    items = await generate_work_items(n)
    results = await asyncio.gather(*[process_item(item) for item in items])
    return await aggregate(list(results))

if __name__ == "__main__":
    result = asyncio.run(fan_out_fan_in(5))
    with open("/home/user/flyte_project/fan_result.json", "w") as f:
        json.dump(result, f)
