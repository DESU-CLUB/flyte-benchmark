import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
PIPELINE_PY = os.path.join(PROJECT_DIR, "pipeline.py")
REPORT_JSON = os.path.join(PROJECT_DIR, "report.json")


def test_pipeline_py_exists():
    """Priority 4 (existence gate): pipeline.py must be present before we can run it."""
    assert os.path.isfile(PIPELINE_PY), (
        f"Expected /home/user/flyte_project/pipeline.py to exist, but it was not found."
    )


def test_pipeline_runs_successfully():
    """Priority 1: Run the agent's pipeline.py and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", PIPELINE_PY],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"Running pipeline.py failed with returncode {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_report_json_exists():
    """Priority 4 (existence gate): report.json must have been written by the pipeline."""
    assert os.path.isfile(REPORT_JSON), (
        f"Expected /home/user/flyte_project/report.json to exist after running pipeline.py, "
        "but it was not found."
    )


def test_report_json_is_valid_and_accuracy_in_range():
    """Priority 1: Parse the JSON written by the agent's pipeline and assert accuracy is in [0, 1]."""
    with open(REPORT_JSON) as f:
        data = json.load(f)

    assert "accuracy" in data, (
        f"Expected 'accuracy' key in report.json, got keys: {list(data.keys())}"
    )
    accuracy = data["accuracy"]
    assert isinstance(accuracy, (int, float)), (
        f"Expected 'accuracy' to be a number, got: {type(accuracy).__name__}"
    )
    assert 0.0 <= float(accuracy) <= 1.0, (
        f"Expected 'accuracy' to be between 0.0 and 1.0, got: {accuracy}"
    )


def test_report_json_accuracy_is_correct():
    """Priority 1: Assert accuracy == 0.75 (3 out of 4 correct for predictions=[1,1,0,1], labels=[1,0,0,1])."""
    with open(REPORT_JSON) as f:
        data = json.load(f)

    accuracy = data.get("accuracy")
    assert accuracy is not None, (
        "Expected 'accuracy' key in report.json but it was missing."
    )
    assert abs(float(accuracy) - 0.75) < 1e-9, (
        f"Expected accuracy == 0.75 (3/4 correct predictions), got: {accuracy}"
    )


def test_report_json_loss_is_correct():
    """Priority 1: Assert loss == 0.25 (1.0 - 0.75)."""
    with open(REPORT_JSON) as f:
        data = json.load(f)

    loss = data.get("loss")
    assert loss is not None, (
        "Expected 'loss' key in report.json but it was missing."
    )
    assert abs(float(loss) - 0.25) < 1e-9, (
        f"Expected loss == 0.25 (1.0 - 0.75), got: {loss}"
    )


def test_report_json_epoch_is_correct():
    """Priority 1: Assert epoch == 1."""
    with open(REPORT_JSON) as f:
        data = json.load(f)

    epoch = data.get("epoch")
    assert epoch is not None, (
        "Expected 'epoch' key in report.json but it was missing."
    )
    assert int(epoch) == 1, (
        f"Expected epoch == 1, got: {epoch}"
    )
