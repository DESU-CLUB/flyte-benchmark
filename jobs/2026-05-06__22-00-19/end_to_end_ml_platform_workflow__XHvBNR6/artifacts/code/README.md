# Flyte 2.0 ML Platform Workflow

This project implements an end-to-end ML platform workflow using Flyte 2.0.

## Project Structure

- `workflows/ml_workflow.py`: Contains Flyte tasks and the main workflow.
- `requirements.txt`: Python dependencies.
- `platform_output.json`: Log file containing workflow execution events.

## Workflow Steps

1. **Data Ingestion**: Loads the Iris dataset.
2. **Data Validation**: Checks for null values and logs schema.
3. **Parallel Training**: Trains Logistic Regression and Random Forest models in parallel.
4. **Model Evaluation**: Calculates accuracy for each model.
5. **Best Model Selection**: Selects the model with the highest accuracy.

## How to Run

### Locally
You can run the workflow locally for testing:
```bash
python workflows/ml_workflow.py
```

### On a Flyte Cluster
To register and run on a Flyte cluster:
```bash
pyflyte run --remote workflows/ml_workflow.py ml_pipeline
```
