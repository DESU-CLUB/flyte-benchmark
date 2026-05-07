import asyncio
import json

import flyte

try:
    image = (
        flyte.Image.from_debian_base()
        .with_pip_packages("pandas", "scikit-learn", "numpy")
        .with_env_vars(MODEL_ENV="production")
    )
except TypeError:
    image = (
        flyte.Image.from_debian_base()
        .with_pip_packages("pandas", "scikit-learn", "numpy")
        .with_env_vars({"MODEL_ENV": "production"})
    )

env = flyte.TaskEnvironment(
    "ml-env",
    image=image,
    resources=flyte.Resources(cpu=4, memory="8Gi"),
)


@env.task
async def train_classifier(features: list, labels: list) -> dict:
    return {
        "model_type": "logistic_regression",
        "n_features": len(features[0]) if features else 0,
        "n_samples": len(features),
        "model_env": "production",
    }


@env.task
async def run_ml_pipeline(n_samples: int, n_features: int) -> dict:
    features = [
        [float(i + j) for j in range(n_features)] for i in range(n_samples)
    ]
    labels = [i % 2 for i in range(n_samples)]
    return await train_classifier(features, labels)


if __name__ == "__main__":
    result = asyncio.run(run_ml_pipeline(100, 5))
    with open("/home/user/flyte_project/model_config.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle)
