import asyncio
import json

import flyte
import numpy as np


env = flyte.TaskEnvironment(
    "data-env",
    image=flyte.Image.from_debian_base().with_pip_packages("pandas", "numpy"),
)


@env.task
async def summarize_data(values: list) -> dict:
    array = np.array(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "std": float(array.std()),
        "min": float(array.min()),
        "max": float(array.max()),
    }


if __name__ == "__main__":
    result = asyncio.run(summarize_data([1.0, 2.0, 3.0, 4.0, 5.0]))
    with open("/home/user/flyte_project/summary.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle)
