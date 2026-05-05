import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
DATA_TASK_PY = os.path.join(PROJECT_DIR, "data_task.py")
SUMMARY_JSON = os.path.join(PROJECT_DIR, "summary.json")


def test_data_task_py_exists():
    """Priority 4 (existence gate): data_task.py must be present before we can run it."""
    assert os.path.isfile(DATA_TASK_PY), (
        f"Expected /home/user/flyte_project/data_task.py to exist, but it was not found."
    )


def test_data_task_runs_successfully():
    """Priority 1: Run the agent's data_task.py and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", DATA_TASK_PY],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"Running data_task.py failed with returncode {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_summary_json_exists():
    """Priority 4 (existence gate): summary.json must have been written by the script."""
    assert os.path.isfile(SUMMARY_JSON), (
        f"Expected /home/user/flyte_project/summary.json to exist after running data_task.py, "
        "but it was not found."
    )


def test_summary_json_has_required_keys():
    """Priority 1: Parse the JSON written by the agent's script and assert all required keys are present."""
    with open(SUMMARY_JSON) as f:
        data = json.load(f)

    for key in ("mean", "std", "min", "max"):
        assert key in data, (
            f"Expected key '{key}' in summary.json, got keys: {list(data.keys())}"
        )


def test_summary_json_mean_is_correct():
    """Priority 1: Assert mean ≈ 3.0 for values [1.0, 2.0, 3.0, 4.0, 5.0]."""
    with open(SUMMARY_JSON) as f:
        data = json.load(f)

    mean = data.get("mean")
    assert mean is not None, "Expected 'mean' key in summary.json but it was missing."
    assert abs(float(mean) - 3.0) < 1e-9, (
        f"Expected mean == 3.0 for values [1, 2, 3, 4, 5], got: {mean}"
    )


def test_summary_json_min_is_correct():
    """Priority 1: Assert min == 1.0 for values [1.0, 2.0, 3.0, 4.0, 5.0]."""
    with open(SUMMARY_JSON) as f:
        data = json.load(f)

    min_val = data.get("min")
    assert min_val is not None, "Expected 'min' key in summary.json but it was missing."
    assert abs(float(min_val) - 1.0) < 1e-9, (
        f"Expected min == 1.0 for values [1, 2, 3, 4, 5], got: {min_val}"
    )


def test_summary_json_max_is_correct():
    """Priority 1: Assert max == 5.0 for values [1.0, 2.0, 3.0, 4.0, 5.0]."""
    with open(SUMMARY_JSON) as f:
        data = json.load(f)

    max_val = data.get("max")
    assert max_val is not None, "Expected 'max' key in summary.json but it was missing."
    assert abs(float(max_val) - 5.0) < 1e-9, (
        f"Expected max == 5.0 for values [1, 2, 3, 4, 5], got: {max_val}"
    )
