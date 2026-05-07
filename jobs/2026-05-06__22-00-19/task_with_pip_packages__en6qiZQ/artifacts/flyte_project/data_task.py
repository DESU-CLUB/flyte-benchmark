import flyte
import numpy
import json
import asyncio

# Create a TaskEnvironment named "data-env" using a custom image
env = flyte.TaskEnvironment(
    "data-env",
    image=flyte.Image.from_debian_base().with_pip_packages("pandas", "numpy")
)

@env.task
async def summarize_data(values: list) -> dict:
    """
    Summarizes the input values using numpy.
    """
    arr = numpy.array(values)
    summary = {
        "mean": float(numpy.mean(arr)),
        "std": float(numpy.std(arr)),
        "min": float(numpy.min(arr)),
        "max": float(numpy.max(arr))
    }
    return summary

if __name__ == "__main__":
    # Execute the task locally
    result = asyncio.run(summarize_data([1.0, 2.0, 3.0, 4.0, 5.0]))
    
    # Write the result to summary.json
    output_path = "/home/user/flyte_project/summary.json"
    with open(output_path, "w") as f:
        json.dump(result, f)
    
    print(f"Summary saved to {output_path}")
    print(json.dumps(result, indent=2))
