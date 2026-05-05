import asyncio
import json
import os
import flyte
from typing import List, Dict, Any

# 1. Define the TaskEnvironment with appropriate resources and caching
# Flyte 2.0 TaskEnvironment allows setting defaults for all tasks in the environment.
env = flyte.TaskEnvironment(
    name="experiment-tracking-env",
    resources=flyte.Resources(cpu=1, memory="1Gi"),
    cache=flyte.Cache(behavior="auto")
)

# 2. Define the experiment task using the environment's task decorator
@env.task
async def run_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a single ML experiment configuration.
    The results are cached based on the input config and function body.
    """
    name = config.get("name", "unnamed")
    lr = config.get("learning_rate", 0.01)
    epochs = config.get("epochs", 10)
    
    print(f"Running experiment: {name} (LR={lr}, Epochs={epochs})")
    
    # Simulate experiment execution time
    await asyncio.sleep(1)
    
    # Dummy metric calculation logic
    # Higher learning rate and more epochs generally improve accuracy in this simulation
    accuracy = 0.5 + (lr * 2) + (0.005 * epochs)
    accuracy = min(accuracy, 0.99) # Cap at 0.99
    
    result = {
        "experiment_name": name,
        "config": config,
        "metrics": {
            "accuracy": round(accuracy, 4)
        }
    }
    
    print(f"Completed experiment: {name} | Accuracy: {accuracy:.4f}")
    return result

# 3. Define the comparison task
@env.task
async def compare_and_save_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compares multiple experiment results and saves the best one to a JSON file.
    """
    if not results:
        print("No results to compare.")
        return {}

    # Identify the best configuration based on accuracy
    best_exp = max(results, key=lambda x: x["metrics"]["accuracy"])
    
    summary = {
        "best_experiment": best_exp,
        "all_experiments": results,
        "total_experiments": len(results)
    }
    
    # Save results to the specified log file
    log_path = "/home/user/flyte_project/experiment_result.json"
    with open(log_path, "w") as f:
        json.dump(summary, f, indent=4)
    
    print(f"Successfully compared {len(results)} experiments.")
    print(f"Best configuration: {best_exp['experiment_name']} with accuracy {best_exp['metrics']['accuracy']}")
    print(f"Results saved to {log_path}")
    
    return summary

# 4. Main execution logic using asyncio.gather for parallelism
async def run_tracking_system():
    # Define multiple experiment configurations
    experiment_configs = [
        {"name": "baseline", "learning_rate": 0.001, "epochs": 10},
        {"name": "high_lr", "learning_rate": 0.05, "epochs": 10},
        {"name": "long_train", "learning_rate": 0.001, "epochs": 50},
        {"name": "optimized", "learning_rate": 0.02, "epochs": 30},
    ]
    
    print("Starting parallel experiment execution...")
    
    # Run multiple experiment configurations in parallel using asyncio.gather
    results = await asyncio.gather(*[
        run_experiment(config=config) for config in experiment_configs
    ])
    
    print("All experiments completed. Comparing results...")
    
    # Compare and save the results
    await compare_and_save_results(results=results)

if __name__ == "__main__":
    asyncio.run(run_tracking_system())
