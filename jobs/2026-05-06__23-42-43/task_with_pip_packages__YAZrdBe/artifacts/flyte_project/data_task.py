import asyncio
import json

import flyte
import numpy

# Define the task environment with a custom image that declares pip dependencies.
# When running locally, the image spec is metadata only — the host environment
# (where numpy/pandas are already installed) is used instead.
env = flyte.TaskEnvironment(
    "data-env",
    image=flyte.Image.from_debian_base().with_pip_packages("pandas", "numpy"),
)


@env.task
async def summarize_data(values: list) -> dict:
    """Compute basic descriptive statistics for a list of numeric values."""
    arr = numpy.array(values, dtype=float)
    return {
        "mean": float(numpy.mean(arr)),
        "std": float(numpy.std(arr)),   # population std (ddof=0)
        "min": float(numpy.min(arr)),
        "max": float(numpy.max(arr)),
    }


if __name__ == "__main__":
    result = asyncio.run(summarize_data([1.0, 2.0, 3.0, 4.0, 5.0]))
    print("Result:", result)

    output_path = "/home/user/flyte_project/summary.json"
    with open(output_path, "w") as f:
        json.dump(result, f)
    print(f"Written to {output_path}")
