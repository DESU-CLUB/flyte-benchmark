import flyte
import asyncio

# Create a TaskEnvironment named "basic-env"
env = flyte.TaskEnvironment("basic-env")

# Define the add task
@env.task
async def add(a: int, b: int) -> int:
    return a + b

# Define the multiply task
@env.task
async def multiply(a: int, b: int) -> int:
    return a * b

# Main function to run the tasks
def main():
    # Run add task
    add_result = asyncio.run(add(3, 4))
    print(add_result)

    # Run multiply task
    multiply_result = asyncio.run(multiply(3, 4))
    print(multiply_result)

if __name__ == "__main__":
    main()