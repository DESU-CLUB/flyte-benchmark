import asyncio
import flyte

env = flyte.TaskEnvironment("basic-env")


@env.task
async def add(a: int, b: int) -> int:
    return a + b


@env.task
async def multiply(a: int, b: int) -> int:
    return a * b


def main():
    result = asyncio.run(add(3, 4))
    print(result)

    result = asyncio.run(multiply(3, 4))
    print(result)


if __name__ == "__main__":
    main()
