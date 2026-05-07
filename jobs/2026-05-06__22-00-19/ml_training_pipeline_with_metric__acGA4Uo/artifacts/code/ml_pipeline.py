import asyncio
import datetime
import json
import flyte

# 1. Setup
env = flyte.TaskEnvironment("ml-training", resources=flyte.Resources(cpu=4, memory="8Gi"))

# 2. Task: generate_dataset
@env.task
async def generate_dataset(n_samples: int, n_features: int) -> dict:
    return {
        "X": [[float(i + j) for j in range(n_features)] for i in range(n_samples)],
        "y": [i % 2 for i in range(n_samples)],
        "n_samples": n_samples,
        "n_features": n_features,
    }

# 3. Task: train_model (with cache)
@env.task(cache=flyte.Cache(behavior="override", version_override="v1"))
async def train_model(config: dict, dataset: dict) -> dict:
    accuracy = min(0.99, config["learning_rate"] * config["epochs"] * 0.1)
    loss = max(0.01, 1.0 - config["learning_rate"] * config["epochs"] * 0.1)
    return {
        "config": config,
        "accuracy": accuracy,
        "loss": loss,
        "n_samples": dataset["n_samples"],
    }

# 4. Task: select_best_model
@env.task
async def select_best_model(models: list) -> dict:
    best = max(models, key=lambda m: m["accuracy"])
    return {"best_model": best, "n_candidates": len(models), "best_accuracy": best["accuracy"]}

# 5. Task: generate_report
@env.task
async def generate_report(best: dict) -> dict:
    return {
        "report_type": "model_selection",
        "winner": best["best_model"]["config"]["model_type"],
        "accuracy": best["best_accuracy"],
        "candidates_evaluated": best["n_candidates"],
    }

# 6. Task: run_ml_experiment
@env.task
async def run_ml_experiment(n_samples: int, n_features: int) -> dict:
    dataset = await generate_dataset(n_samples, n_features)
    configs = [
        {"model_type": "lr",  "learning_rate": 0.01,  "epochs": 100},
        {"model_type": "rf",  "learning_rate": 0.1,   "epochs": 50},
        {"model_type": "nn",  "learning_rate": 0.001, "epochs": 200},
    ]
    trained = await asyncio.gather(*[train_model(cfg, dataset) for cfg in configs])
    best = await select_best_model(list(trained))
    report = await generate_report(best)
    return report

# 7. __main__ block
if __name__ == "__main__":
    report = asyncio.run(run_ml_experiment(1000, 10))
    with open("/home/user/flyte_project/experiment_report.json", "w") as f:
        json.dump(report, f, indent=4)
