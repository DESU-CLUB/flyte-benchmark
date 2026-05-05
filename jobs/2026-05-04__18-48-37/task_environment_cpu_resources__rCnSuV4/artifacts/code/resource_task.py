import flyte
import json
import asyncio

# Create a TaskEnvironment with explicit CPU and memory resource constraints
env = flyte.TaskEnvironment("cpu-env", resources=flyte.Resources(cpu=2, memory="2Gi"))

@env.task
async def process_batch(batch_size: int) -> dict:
    """
    A batch-processing task that returns a summary dict.
    """
    return {
        "batch_size": batch_size,
        "processed": batch_size * 2,
        "status": "complete"
    }

if __name__ == "__main__":
    # Run the async task
    result = asyncio.run(process_batch(100))
    
    # Print the result as JSON
    json_result = json.dumps(result)
    print(json_result)
    
    # Write the result as JSON to result.json
    with open("/home/user/flyte_project/result.json", "w") as f:
        f.write(json_result)
