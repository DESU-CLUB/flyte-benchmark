import flyte
import numpy as np
import json
import asyncio

env = flyte.TaskEnvironment(
    "data-env",
    image=flyte.Image.from_debian_base().with_pip_packages("pandas", "numpy")
)

@env.task
async def summarize_data(values: list) -> dict:
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr))
    }

if __name__ == "__main__":
    result = asyncio.run(summarize_data([1.0, 2.0, 3.0, 4.0, 5.0]))
    with open("/home/user/flyte_project/summary.json", "w") as f:
        json.dump(result, f)
