import asyncio
import json
import logging
import flyte

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

primary_env = flyte.TaskEnvironment(
    "primary", resources=flyte.Resources(cpu=8, memory="16Gi")
)
fallback_env = flyte.TaskEnvironment(
    "fallback", resources=flyte.Resources(cpu=2, memory="4Gi")
)


@primary_env.task
async def primary_training(data: list) -> dict:
    if len(data) > 10:
        raise RuntimeError("Insufficient memory for primary training")
    return {
        "model": "complex_nn",
        "accuracy": 0.95,
        "env": "primary",
        "data_size": len(data),
    }


@fallback_env.task
async def fallback_training(data: list) -> dict:
    return {
        "model": "simple_lr",
        "accuracy": 0.82,
        "env": "fallback",
        "data_size": len(data),
    }


@fallback_env.task
async def self_healing_train(data: list) -> dict:
    try:
        result = await primary_training(data)
        result["recovered"] = False
        return result
    except RuntimeError as exc:
        logger.warning(
            "Primary training failed: %s. Falling back to fallback environment.",
            exc,
        )
        result = await fallback_training(data)
        result["recovered"] = True
        return result


@fallback_env.task
async def run_experiment(large_data: list, small_data: list) -> dict:
    large_result, small_result = await asyncio.gather(
        self_healing_train(large_data),
        self_healing_train(small_data),
    )
    return {
        "large_data_result": large_result,
        "small_data_result": small_result,
    }


if __name__ == "__main__":
    large_data = list(range(20))
    small_data = list(range(5))
    result = asyncio.run(run_experiment(large_data, small_data))
    with open("/home/user/flyte_project/experiment_result.json", "w") as file:
        json.dump(result, file, indent=2)
    print(json.dumps(result, indent=2))
