import flyte
import numpy as np
import json
import asyncio

# Creates a TaskEnvironment named "data-env" using a custom image
env = flyte.TaskEnvironment(
    "data-env",
    image=flyte.Image.from_debian_base().with_pip_packages("pandas", "numpy")
)

@env.task
async def summarize_data(values: list) -> dict:
    """
    Uses numpy to compute mean, std, min, and max of the values.
    Returns a dict with keys mean, std, min, and max.
    """
    data = np.array(values)
    summary = {
        "mean": float(np.mean(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data))
    }
    return summary

async def main():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = await summarize_data(values)
    
    output_path = "/home/user/flyte_project/summary.json"
    with open(output_path, "w") as f:
        json.dump(result, f)
    
    print(f"Summary saved to {output_path}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
