import flyte
import numpy
import json
import asyncio

env = flyte.TaskEnvironment(
    "data-env",
    image=flyte.Image.from_debian_base().with_pip_packages("pandas", "numpy")
)

@env.task
async def summarize_data(values: list) -> dict:
    arr = numpy.array(values)
    return {
        "mean": numpy.mean(arr),
        "std": numpy.std(arr),
        "min": numpy.min(arr),
        "max": numpy.max(arr)
    }

if __name__ == "__main__":
    result = asyncio.run(summarize_data([1.0, 2.0, 3.0, 4.0, 5.0]))
    with open("/home/user/flyte_project/summary.json", "w") as f:
        json.dump(result, f)