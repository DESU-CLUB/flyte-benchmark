import flyte
import json
import asyncio

env = flyte.TaskEnvironment("cpu-env", resources=flyte.Resources(cpu=2, memory="2Gi"))

@env.task
async def process_batch(batch_size: int) -> dict:
    return {
        "batch_size": batch_size,
        "processed": batch_size * 2,
        "status": "complete"
    }

if __name__ == "__main__":
    result = asyncio.run(process_batch(100))
    print(json.dumps(result))
    
    with open("/home/user/flyte_project/result.json", "w") as f:
        json.dump(result, f)
