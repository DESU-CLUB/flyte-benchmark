import flyte
import asyncio

env = flyte.TaskEnvironment(name="basic-env")

@env.task
async def add(a: int, b: int) -> int:
    return a + b

@env.task
async def multiply(a: int, b: int) -> int:
    return a * b

def main():
    res_add = asyncio.run(add(3, 4))
    print(res_add)
    res_mul = asyncio.run(multiply(3, 4))
    print(res_mul)

if __name__ == "__main__":
    main()
