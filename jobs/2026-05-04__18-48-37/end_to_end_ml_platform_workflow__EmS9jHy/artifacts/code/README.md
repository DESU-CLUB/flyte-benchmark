# Flyte 2.0 ML Platform Workflow

This project implements an end-to-end ML platform workflow using Flyte 2.0.

## Workflow Steps

1. **Data Ingestion**: Loads the Iris dataset.
2. **Data Validation**: Checks for null values and ensures the correct number of columns.
3. **Data Splitting**: Splits the data into training and testing sets.
4. **Parallel Training**: Trains both Logistic Regression and Random Forest models in parallel.
5. **Model Selection**: Evaluates the models based on accuracy and selects the best one.

## Project Structure

- `workflow.py`: Contains the Flyte tasks and workflow definition.
- `platform_output.json`: Log file containing the results of the workflow execution.
- `requirements.txt`: List of dependencies required to run the workflow.

## Running Locally

To run the workflow locally for testing:

```bash
python workflow.py
```

## Running on Flyte

To register and run on a Flyte cluster:

```bash
pyflyte run --remote workflow.py ml_platform_workflow
```
