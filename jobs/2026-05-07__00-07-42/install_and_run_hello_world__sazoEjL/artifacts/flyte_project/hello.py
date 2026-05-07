import asyncio
from flyte import TaskEnvironment

env = TaskEnvironment("local-env")

@env.task
async def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    result = asyncio.run(greet("World"))
    print(result)