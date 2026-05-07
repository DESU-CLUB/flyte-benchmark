import asyncio
import flyte


env = flyte.TaskEnvironment(name="basic-env")


@env.task
async def add(a: int, b: int) -> int:
    return a + b


@env.task
async def multiply(a: int, b: int) -> int:
    return a * b


def main() -> None:
    add_result = asyncio.run(add(3, 4))
    print(add_result)
    multiply_result = asyncio.run(multiply(3, 4))
    print(multiply_result)


if __name__ == "__main__":
    main()
