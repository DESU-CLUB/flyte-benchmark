import flyte
from dataclasses import dataclass, asdict
import json
import asyncio

# Create a TaskEnvironment named "typed-env"
env = flyte.TaskEnvironment("typed-env")

@dataclass
class ModelMetrics:
    accuracy: float
    loss: float
    epoch: int

@env.task
async def compute_metrics(predictions: list, labels: list) -> ModelMetrics:
    accuracy = sum(p == l for p, l in zip(predictions, labels)) / len(predictions)
    loss = 1.0 - accuracy
    epoch = 1
    return ModelMetrics(accuracy=accuracy, loss=loss, epoch=epoch)

@env.task
async def format_report(metrics: ModelMetrics) -> str:
    # Using asdict to convert dataclass to dictionary for JSON serialization
    return json.dumps(asdict(metrics))

@env.task
async def run_pipeline(predictions: list, labels: list) -> str:
    metrics = await compute_metrics(predictions, labels)
    report = await format_report(metrics)
    return report

if __name__ == "__main__":
    result = asyncio.run(run_pipeline([1, 1, 0, 1], [1, 0, 0, 1]))
    
    with open("/home/user/flyte_project/report.json", "w") as f:
        f.write(result)
    
    print(f"Pipeline completed. Report saved to /home/user/flyte_project/report.json")
    print(f"Result: {result}")
