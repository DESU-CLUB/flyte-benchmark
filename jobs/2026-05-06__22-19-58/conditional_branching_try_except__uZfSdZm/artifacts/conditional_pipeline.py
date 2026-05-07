import asyncio
import json
import flyte

env = flyte.TaskEnvironment(name="branching-env")


@env.task
async def classify_input(value: float) -> str:
    if value < 0:
        return "negative"
    elif value == 0.0:
        return "zero"
    elif value < 10:
        return "small_positive"
    else:
        return "large_positive"


@env.task
async def process_by_class(value: float, classification: str) -> dict:
    if classification == "negative":
        return {"class": "negative", "result": abs(value), "operation": "abs"}
    elif classification == "zero":
        return {"class": "zero", "result": 0.0, "operation": "identity"}
    elif classification == "small_positive":
        return {
            "class": "small_positive",
            "result": value * 2,
            "operation": "double",
        }
    else:
        return {
            "class": "large_positive",
            "result": value ** 0.5,
            "operation": "sqrt",
        }


@env.task
async def conditional_pipeline(values: list) -> list:
    classifications = await asyncio.gather(*[classify_input(v) for v in values])
    results = await asyncio.gather(
        *[process_by_class(v, c) for v, c in zip(values, classifications)]
    )
    return list(results)


if __name__ == "__main__":
    results = asyncio.run(conditional_pipeline([-5.0, 0.0, 3.0, 25.0]))
    with open("/home/user/flyte_project/conditional_results.json", "w") as f:
        json.dump(results, f)
