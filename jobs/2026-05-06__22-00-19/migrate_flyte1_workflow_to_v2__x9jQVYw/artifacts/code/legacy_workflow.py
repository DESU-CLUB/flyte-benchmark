import flytekit
from flytekit import task, workflow

@task
def square(n: int) -> int:
    return n ** 2

@task
def total(values: list) -> int:
    return sum(values)

@workflow
def compute_sum_of_squares(numbers: list) -> int:
    squared = flytekit.map_task(square)(n=numbers)
    return total(values=squared)

if __name__ == "__main__":
    result = compute_sum_of_squares(numbers=[1, 2, 3, 4, 5])
    print(f"Sum of squares: {result}")
