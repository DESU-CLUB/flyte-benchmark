import asyncio
from flyte import TaskEnvironment

env = TaskEnvironment("basic-env")

@env.task
async def add(a: int, b: int) -> int:
    return a + b

@env.task
async def multiply(a: int, b: int) -> int:
    return a * b

def main():
    add_result = asyncio.run(add(3, 4))
    print(add_result)
    
    multiply_result = asyncio.run(multiply(3, 4))
    print(multiply_result)

if __name__ == "__main__":
    main()
