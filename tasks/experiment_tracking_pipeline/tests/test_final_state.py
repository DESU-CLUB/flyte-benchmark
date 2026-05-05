import importlib.util
import json
import os
import subprocess
import sys
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "experiment_tracker.py")
LOG_PATH = os.path.join(PROJECT_DIR, "experiment_log.json")
RESULT_PATH = os.path.join(PROJECT_DIR, "experiment_result.json")


def test_experiment_tracker_script_exists():
    """Priority 4 (existence gate): experiment_tracker.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/experiment_tracker.py to exist, but it was not found."
    )


def test_script_runs_without_error():
    """Priority 1: Execute the agent's script and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 experiment_tracker.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_experiment_log_json_exists():
    """Priority 4 (existence gate): experiment_log.json must exist after running the script."""
    assert os.path.isfile(LOG_PATH), (
        f"Expected /home/user/flyte_project/experiment_log.json to exist after running the script, "
        "but it was not found."
    )


def test_experiment_result_json_exists():
    """Priority 4 (existence gate): experiment_result.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/experiment_result.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json_object():
    """Priority 1 (runtime output): experiment_result.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"experiment_result.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected experiment_result.json to contain a JSON object, got: {type(data)}"
    )


def test_experiments_run_equals_three():
    """Priority 1 (runtime output): experiments_run must be 3 (one per config)."""
    data = _load_result()
    assert "experiments_run" in data, (
        f"'experiments_run' key missing from experiment_result.json. Got keys: {list(data.keys())}"
    )
    assert data["experiments_run"] == 3, (
        f"Expected experiments_run == 3, but got: {data['experiments_run']!r}"
    )


def test_best_experiment_is_fast_lr():
    """Priority 1 (runtime output): best_experiment must be 'fast_lr'.

    fast_lr achieves accuracy = min(0.99, 0.01 * 1000 / 1000) = 0.01, which is the highest
    among the three configs (baseline=0.001, fast_lr=0.01, high_epochs=0.002).
    """
    data = _load_result()
    assert "best_experiment" in data, (
        f"'best_experiment' key missing from experiment_result.json. Got keys: {list(data.keys())}"
    )
    assert data["best_experiment"] == "fast_lr", (
        f"Expected best_experiment == 'fast_lr', but got: {data['best_experiment']!r}"
    )


def test_best_accuracy_approximately_0_01():
    """Priority 1 (runtime output): best_accuracy must be approximately 0.01 (±0.001).

    fast_lr: accuracy = min(0.99, 0.01 * 1000 / 1000) = 0.01.
    """
    data = _load_result()
    assert "best_accuracy" in data, (
        f"'best_accuracy' key missing from experiment_result.json. Got keys: {list(data.keys())}"
    )
    actual = data["best_accuracy"]
    assert abs(actual - 0.01) <= 0.001, (
        f"Expected best_accuracy ≈ 0.01 (±0.001), but got: {actual!r}"
    )


def _load_module():
    """Helper: import the agent's experiment_tracker.py as a module without running __main__."""
    spec = importlib.util.spec_from_file_location("experiment_tracker", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    # Prevent __main__ block from executing on import
    original_name = getattr(module, "__name__", None)
    module.__name__ = "experiment_tracker"
    spec.loader.exec_module(module)
    return module


def test_run_experiment_has_cache_attribute():
    """Priority 1 (module inspection): run_experiment must have a .cache attribute that is a flyte.Cache instance."""
    import flyte
    module = _load_module()
    task_fn = getattr(module, "run_experiment", None)
    assert task_fn is not None, (
        "Expected 'run_experiment' to be defined in experiment_tracker.py, but it was not found."
    )
    assert hasattr(task_fn, "cache"), (
        f"Expected run_experiment to have a 'cache' attribute (set via @env.task(cache=...)), "
        f"but the attribute was not found. Available attributes: {[a for a in dir(task_fn) if not a.startswith('__')]}"
    )
    assert isinstance(task_fn.cache, flyte.Cache), (
        f"Expected run_experiment.cache to be an instance of flyte.Cache, "
        f"got: {type(task_fn.cache)}"
    )
