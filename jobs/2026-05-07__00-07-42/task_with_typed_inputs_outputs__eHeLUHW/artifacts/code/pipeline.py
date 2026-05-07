import flyte
import dataclasses
import json
import asyncio

# Create TaskEnvironment
env = flyte.TaskEnvironment("typed-env")

# Define ModelMetrics dataclass
@dataclasses.dataclass
class ModelMetrics:
    accuracy: float
    loss: float
    epoch: int

# Define compute_metrics task
@env.task
async def compute_metrics(predictions: list, labels: list) -> ModelMetrics:
    accuracy = sum(p == l for p, l in zip(predictions, labels)) / len(predictions)
    loss = 1.0 - accuracy
    epoch = 1
    return ModelMetrics(accuracy=accuracy, loss=loss, epoch=epoch)

# Define format_report task
@env.task
async def format_report(metrics: ModelMetrics) -> str:
    report = {
        "accuracy": metrics.accuracy,
        "loss": metrics.loss,
        "epoch": metrics.epoch
    }
    return json.dumps(report)

# Define run_pipeline task
@env.task
async def run_pipeline(predictions: list, labels: list) -> str:
    metrics = await compute_metrics(predictions, labels)
    report = await format_report(metrics)
    return report

# Main execution
if __name__ == "__main__":
    result = asyncio.run(run_pipeline([1, 1, 0, 1], [1, 0, 0, 1]))
    with open("/home/user/flyte_project/report.json", "w") as f:
        f.write(result)