import asyncio
import json
from flyte import TaskEnvironment

env = TaskEnvironment("migrate-env")

@env.task
async def square(n: int) -> int:
    return n ** 2

@env.task
async def total(values: list) -> int:
    return sum(values)

@env.task
async def compute_sum_of_squares(numbers: list) -> int:
    squared = await asyncio.gather(*[square(n) for n in numbers])
    return await total(values=list(squared))

if __name__ == "__main__":
    result = asyncio.run(compute_sum_of_squares([1, 2, 3, 4, 5]))
    with open("/home/user/flyte_project/migration_result.json", "w") as f:
        json.dump({"result": result, "input": [1, 2, 3, 4, 5]}, f)
    print(f"Sum of squares: {result}")
