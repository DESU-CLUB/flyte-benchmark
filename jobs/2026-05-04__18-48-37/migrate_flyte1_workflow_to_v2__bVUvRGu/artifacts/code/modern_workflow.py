import asyncio
import json
from flyte import TaskEnvironment

# Create a TaskEnvironment named "migrate-env"
env = TaskEnvironment("migrate-env")

@env.task
async def square(n: int) -> int:
    return n ** 2

@env.task
async def total(values: list) -> int:
    return sum(values)

@env.task
async def compute_sum_of_squares(numbers: list) -> int:
    # Use asyncio.gather to compute squares in parallel, replacing flytekit.map_task
    squared = await asyncio.gather(*[square(n) for n in numbers])
    # Call total to sum the results
    return await total(values=list(squared))

if __name__ == "__main__":
    # Call asyncio.run to execute the entry point task
    result = asyncio.run(compute_sum_of_squares([1, 2, 3, 4, 5]))
    
    # Write the result to migration_result.json
    output_path = "/home/user/flyte_project/migration_result.json"
    with open(output_path, "w") as f:
        json.dump({"result": result, "input": [1, 2, 3, 4, 5]}, f)
    
    print(f"Sum of squares: {result}")
    print(f"Result written to {output_path}")
