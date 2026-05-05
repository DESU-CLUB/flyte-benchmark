import asyncio
import json
from dataclasses import dataclass, asdict
from typing import List
from flyte import TaskEnvironment

# Create TaskEnvironment
env = TaskEnvironment(name="typed-env")

@dataclass
class ModelMetrics:
    accuracy: float
    loss: float
    epoch: int

@env.task
async def compute_metrics(predictions: List[int], labels: List[int]) -> ModelMetrics:
    if not predictions:
        return ModelMetrics(accuracy=0.0, loss=1.0, epoch=1)
    
    accuracy = sum(p == l for p, l in zip(predictions, labels)) / len(predictions)
    loss = 1.0 - accuracy
    epoch = 1
    return ModelMetrics(accuracy=accuracy, loss=loss, epoch=epoch)

@env.task
async def format_report(metrics: ModelMetrics) -> str:
    return json.dumps(asdict(metrics))

@env.task
async def run_pipeline(predictions: List[int], labels: List[int]) -> str:
    metrics = await compute_metrics(predictions, labels)
    report = await format_report(metrics)
    return report

if __name__ == "__main__":
    predictions = [1, 1, 0, 1]
    labels = [1, 0, 0, 1]
    
    result = asyncio.run(run_pipeline(predictions, labels))
    
    with open("/home/user/flyte_project/report.json", "w") as f:
        f.write(result)
    
    print(f"Report generated: {result}")
