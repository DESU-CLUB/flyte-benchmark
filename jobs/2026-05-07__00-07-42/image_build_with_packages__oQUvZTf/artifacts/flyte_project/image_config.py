import flyte
import asyncio
import json

# Build a custom image with pip packages and environment variables
image = (
    flyte.Image.from_debian_base()
    .with_pip_packages("pandas", "scikit-learn", "numpy")
    .with_env_vars({"MODEL_ENV": "production"})
)

# Create a TaskEnvironment with the custom image and resources
env = flyte.TaskEnvironment(
    "ml-env",
    image=image,
    resources=flyte.Resources(cpu=4, memory="8Gi")
)

# Define an async task for training a classifier
@env.task
async def train_classifier(features: list, labels: list) -> dict:
    """
    Train a classifier with the given features and labels.
    Returns a model configuration dictionary.
    """
    return {
        "model_type": "logistic_regression",
        "n_features": len(features[0]) if features else 0,
        "n_samples": len(features),
        "model_env": "production"
    }

# Define an async task for running the ML pipeline
@env.task
async def run_ml_pipeline(n_samples: int, n_features: int) -> dict:
    """
    Generate mock data and run the ML pipeline.
    """
    # Generate mock feature data
    features = [[float(i + j) for j in range(n_features)] for i in range(n_samples)]
    
    # Generate mock labels (alternating 0 and 1)
    labels = [i % 2 for i in range(n_samples)]
    
    # Call the train_classifier task
    result = await train_classifier(features, labels)
    return result

# Main execution block
if __name__ == "__main__":
    # Run the pipeline with 100 samples and 5 features
    result = asyncio.run(run_ml_pipeline(100, 5))
    
    # Write the result to a JSON file
    with open("/home/user/flyte_project/model_config.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Pipeline completed. Result written to model_config.json")
    print(f"Result: {result}")