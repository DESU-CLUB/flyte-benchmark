# Flyte 2.0 ML Platform

This project defines an end-to-end ML platform workflow with Flyte 2.0. It ingests data, validates it, trains three models in parallel, evaluates them, and selects the best model.

## Workflow

- **Ingest**: Generates a synthetic classification dataset.
- **Validate**: Checks for nulls, class balance, and feature ranges.
- **Train in parallel**: Logistic regression, random forest, and gradient boosting.
- **Evaluate**: Accuracy and F1 score per model.
- **Select best**: Chooses the model with the highest F1 (ties broken by accuracy).
- **Log**: Writes results to `/home/user/flyte_project/platform_output.json`.

## Files

- `workflows.py`: Flyte tasks and workflow definition.
- `requirements.txt`: Python dependencies.
- `platform_output.json`: Output log file written at runtime.

## Run locally (example)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "from workflows import ml_platform_workflow; print(ml_platform_workflow())"
```
