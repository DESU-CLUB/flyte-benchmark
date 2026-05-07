import asyncio
import json
import logging
import flyte

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Environment definitions ──────────────────────────────────────────────────
primary_env = flyte.TaskEnvironment(
    "primary",
    resources=flyte.Resources(cpu=8, memory="16Gi"),
)
fallback_env = flyte.TaskEnvironment(
    "fallback",
    resources=flyte.Resources(cpu=2, memory="4Gi"),
)


# ── Task: primary_training ───────────────────────────────────────────────────
@primary_env.task
async def primary_training(data: list) -> dict:
    """Attempt resource-heavy training on the primary environment.

    Raises RuntimeError when the dataset is too large to simulate an
    out-of-memory condition on the high-resource environment.
    """
    if len(data) > 10:
        raise RuntimeError("Insufficient memory for primary training")
    return {
        "model": "complex_nn",
        "accuracy": 0.95,
        "env": "primary",
        "data_size": len(data),
    }


# ── Task: fallback_training ──────────────────────────────────────────────────
@fallback_env.task
async def fallback_training(data: list) -> dict:
    """Lightweight training that always succeeds on the fallback environment."""
    return {
        "model": "simple_lr",
        "accuracy": 0.82,
        "env": "fallback",
        "data_size": len(data),
    }


# ── Task: self_healing_train ─────────────────────────────────────────────────
@fallback_env.task
async def self_healing_train(data: list) -> dict:
    """Try primary training; transparently recover via fallback on failure."""
    try:
        result = await primary_training(data)
        result["recovered"] = False
        return result
    except RuntimeError as e:
        logger.warning(
            "Primary training failed: %s. Falling back to fallback environment.", e
        )
        result = await fallback_training(data)
        result["recovered"] = True
        return result


# ── Task: run_experiment ─────────────────────────────────────────────────────
@fallback_env.task
async def run_experiment(large_data: list, small_data: list) -> dict:
    """Run two self-healing training jobs in parallel and collect results."""
    r1, r2 = await asyncio.gather(
        self_healing_train(large_data),
        self_healing_train(small_data),
    )
    return {"large_data_result": r1, "small_data_result": r2}


# ── Entry-point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    large_data = list(range(20))  # 20 items → triggers fallback (len > 10)
    small_data = list(range(5))   # 5 items  → succeeds on primary  (len ≤ 10)

    result = asyncio.run(run_experiment(large_data, small_data))

    output_path = "/home/user/flyte_project/experiment_result.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
