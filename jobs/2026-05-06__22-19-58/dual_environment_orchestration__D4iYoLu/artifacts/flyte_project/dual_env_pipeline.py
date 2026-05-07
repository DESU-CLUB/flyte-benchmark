import asyncio
import json
import flyte

cpu_env = flyte.TaskEnvironment("cpu-env", resources=flyte.Resources(cpu=2, memory="4Gi"))
gpu_env = flyte.TaskEnvironment("gpu-env", resources=flyte.Resources(cpu=8, memory="16Gi"))


@cpu_env.task
async def clean_data(raw: list) -> list:
    """Filter out None values and convert strings to lowercase."""
    return [item.lower() for item in raw if item is not None]


@gpu_env.task
async def train_model(data: list) -> dict:
    """Simulate model training; return model metadata."""
    return {
        "model": "linear",
        "data_points": len(data),
        "weights": [len(data) * 0.1, len(data) * 0.01],
    }


@cpu_env.task
async def evaluate_model(model: dict) -> dict:
    """Evaluate a trained model and return accuracy metrics."""
    return {
        "accuracy": min(0.99, model["data_points"] * 0.05),
        "model_name": model["model"],
    }


@cpu_env.task
async def ml_pipeline(raw_data: list) -> dict:
    """Chain clean → train → evaluate."""
    cleaned = await clean_data(raw_data)
    model = await train_model(cleaned)
    result = await evaluate_model(model)
    return result


if __name__ == "__main__":
    result = asyncio.run(ml_pipeline(["Alice", None, "BOB", "charlie", None]))
    with open("/home/user/flyte_project/pipeline_output.json", "w") as f:
        json.dump(result, f)
    print(result)
