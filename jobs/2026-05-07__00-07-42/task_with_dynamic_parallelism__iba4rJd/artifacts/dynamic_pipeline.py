import asyncio
import json
import flyte

# Create TaskEnvironment
env = flyte.TaskEnvironment("dynamic-env")


@env.task
async def generate_feature_configs(dataset_size: int) -> list:
    return [
        {"feature": f"feature_{i}", "window": i + 1, "agg": agg}
        for i in range(3)
        for agg in ["mean", "max"]
    ]


@env.task
async def compute_feature(config: dict, data_size: int) -> dict:
    return {
        "feature": config["feature"],
        "agg": config["agg"],
        "window": config["window"],
        "value": data_size / config["window"] * (1.5 if config["agg"] == "mean" else 2.0),
    }


@env.task
async def build_feature_matrix(features: list) -> dict:
    return {
        "n_features": len(features),
        "feature_names": list(set(f["feature"] for f in features)),
        "feature_matrix": features,
    }


@env.task
async def run_feature_pipeline(dataset_size: int) -> dict:
    configs = await generate_feature_configs(dataset_size)
    features = await asyncio.gather(*[compute_feature(cfg, dataset_size) for cfg in configs])
    return await build_feature_matrix(list(features))


if __name__ == "__main__":
    result = asyncio.run(run_feature_pipeline(100))
    with open("/home/user/flyte_project/feature_matrix.json", "w") as f:
        json.dump(result, f)