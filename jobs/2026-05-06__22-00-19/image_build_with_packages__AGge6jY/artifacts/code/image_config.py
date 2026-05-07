import flyte
import asyncio
import json

# Create custom flyte.Image
image = (
    flyte.Image.from_debian_base()
    .with_pip_packages("pandas", "scikit-learn", "numpy")
    .with_env_vars({"MODEL_ENV": "production"})
)

# Create TaskEnvironment
env = flyte.TaskEnvironment(
    "ml-env",
    image=image,
    resources=flyte.Resources(cpu=4, memory="8Gi")
)

@env.task
async def train_classifier(features: list, labels: list) -> dict:
    """
    Mock training task.
    """
    return {
        "model_type": "logistic_regression",
        "n_features": len(features[0]) if features else 0,
        "n_samples": len(features),
        "model_env": "production"
    }

@env.task
async def run_ml_pipeline(n_samples: int, n_features: int) -> dict:
    """
    ML Pipeline task that generates data and calls training.
    """
    # Generate mock feature data
    features = [[float(i + j) for j in range(n_features)] for i in range(n_samples)]
    # Generate mock labels
    labels = [i % 2 for i in range(n_samples)]
    
    # Call the training task
    result = await train_classifier(features, labels)
    return result

if __name__ == "__main__":
    # Run the pipeline locally
    result = asyncio.run(run_ml_pipeline(100, 5))
    
    # Write result to JSON
    output_path = "/home/user/flyte_project/model_config.json"
    with open(output_path, "w") as f:
        json.dump(result, f)
    
    print(f"Result written to {output_path}")
