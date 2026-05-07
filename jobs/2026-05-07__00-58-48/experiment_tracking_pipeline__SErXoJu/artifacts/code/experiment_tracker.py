import asyncio
import json
import flyte

@flyte.TaskEnvironment(cpu=2, memory="4Gi")
@flyte.Cache(version="1.0")
async def run_experiment(config):
    """Run a single experiment with the given configuration."""
    # Simulate experiment duration
    await asyncio.sleep(0.5)
    
    # Simulate a metric (e.g., accuracy) based on config
    lr = config.get("learning_rate", 0.01)
    bs = config.get("batch_size", 32)
    accuracy = 0.9 - abs(0.005 - lr) * 10 - (bs * 0.0001)
    
    return {
        "config": config,
        "accuracy": accuracy
    }

async def main():
    """Run multiple experiments in parallel and find the best one."""
    configs = [
        {"learning_rate": 0.01, "batch_size": 32},
        {"learning_rate": 0.005, "batch_size": 16},
        {"learning_rate": 0.001, "batch_size": 64},
        {"learning_rate": 0.005, "batch_size": 32},
    ]
    
    # Run multiple experiment configurations in parallel using asyncio.gather
    results = await asyncio.gather(*(run_experiment(cfg) for cfg in configs))
    
    # Compare experiments and identify the best configuration
    best_experiment = max(results, key=lambda x: x["accuracy"])
    
    output = {
        "experiments": results,
        "best_experiment": best_experiment
    }
    
    # Save results to the specified log file
    log_file_path = "/home/user/flyte_project/experiment_result.json"
    with open(log_file_path, "w") as f:
        json.dump(output, f, indent=4)
        
    print(f"Experiment tracking complete. Results saved to {log_file_path}")

if __name__ == "__main__":
    asyncio.run(main())
