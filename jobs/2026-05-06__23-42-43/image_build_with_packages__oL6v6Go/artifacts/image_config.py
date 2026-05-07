import asyncio
import json

import flyte

# Build a custom image with pip packages and an environment variable
image = (
    flyte.Image.from_debian_base()
    .with_pip_packages("pandas", "scikit-learn", "numpy")
    .with_env_vars({"MODEL_ENV": "production"})
)

# Create a TaskEnvironment using the custom image and resource spec
env = flyte.TaskEnvironment(
    "ml-env",
    image=image,
    resources=flyte.Resources(cpu=4, memory="8Gi")
)


@env.task
async def train_classifier(features: list, labels: list) -> dict:
    """Train a mock classifier and return the model configuration."""
    return {
        "model_type": "logistic_regression",
        "n_features": len(features[0]) if features else 0,
        "n_samples": len(features),
        "model_env": "production",
    }


@env.task
async def run_ml_pipeline(n_samples: int, n_features: int) -> dict:
    """Generate mock data and run the ML training pipeline."""
    # Generate mock feature matrix: n_samples rows, n_features columns
    features = [[float(i + j) for j in range(n_features)] for i in range(n_samples)]

    # Generate mock binary labels alternating 0 and 1
    labels = [i % 2 for i in range(n_samples)]

    result = await train_classifier(features, labels)
    return result


if __name__ == "__main__":
    result = asyncio.run(run_ml_pipeline(100, 5))
    print(json.dumps(result, indent=2))

    output_path = "/home/user/flyte_project/model_config.json"
    with open(output_path, "w") as f:
        json.dump(result, f)

    print(f"\nModel config written to {output_path}")
