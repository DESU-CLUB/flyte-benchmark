import os
import json
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "self_healing.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "experiment_result.json")


def test_self_healing_script_exists():
    """Confirm the agent created self_healing.py at the required path."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"self_healing.py not found at {SCRIPT_PATH}. "
        "The agent must create this file."
    )


def test_script_runs_successfully():
    """Priority 1: Execute the agent's script and assert it exits with code 0."""
    result = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 self_healing.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_experiment_result_json_exists():
    """Confirm that running the script produced experiment_result.json."""
    # Run the script first to ensure the output file is generated
    subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert os.path.isfile(RESULT_PATH), (
        f"experiment_result.json not found at {RESULT_PATH} after running self_healing.py. "
        "The script must write the result to this path."
    )


@pytest.fixture(scope="module")
def experiment_result():
    """Run self_healing.py and parse the resulting JSON once for all tests."""
    run = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert run.returncode == 0, (
        f"self_healing.py failed (exit {run.returncode}).\n"
        f"stdout: {run.stdout}\nstderr: {run.stderr}"
    )
    assert os.path.isfile(RESULT_PATH), (
        f"experiment_result.json was not written to {RESULT_PATH}."
    )
    with open(RESULT_PATH) as f:
        data = json.load(f)
    return data


def test_result_has_large_data_result_key(experiment_result):
    """Confirm top-level key 'large_data_result' is present in the JSON output."""
    assert "large_data_result" in experiment_result, (
        f"Key 'large_data_result' missing from experiment_result.json. Got: {list(experiment_result.keys())}"
    )


def test_result_has_small_data_result_key(experiment_result):
    """Confirm top-level key 'small_data_result' is present in the JSON output."""
    assert "small_data_result" in experiment_result, (
        f"Key 'small_data_result' missing from experiment_result.json. Got: {list(experiment_result.keys())}"
    )


def test_large_data_recovered_is_true(experiment_result):
    """large_data (20 items) exceeds threshold → RuntimeError → fallback used → recovered must be True."""
    large = experiment_result["large_data_result"]
    assert large.get("recovered") is True, (
        f"Expected large_data_result.recovered == True (fallback was triggered), "
        f"but got: {large.get('recovered')}. Full result: {large}"
    )


def test_large_data_model_is_simple_lr(experiment_result):
    """large_data result must use the fallback model 'simple_lr'."""
    large = experiment_result["large_data_result"]
    assert large.get("model") == "simple_lr", (
        f"Expected large_data_result.model == 'simple_lr' (fallback model), "
        f"but got: {large.get('model')}. Full result: {large}"
    )


def test_large_data_env_is_fallback(experiment_result):
    """large_data result must report env == 'fallback'."""
    large = experiment_result["large_data_result"]
    assert large.get("env") == "fallback", (
        f"Expected large_data_result.env == 'fallback', "
        f"but got: {large.get('env')}. Full result: {large}"
    )


def test_small_data_recovered_is_false(experiment_result):
    """small_data (5 items) is within threshold → primary succeeds → recovered must be False."""
    small = experiment_result["small_data_result"]
    assert small.get("recovered") is False, (
        f"Expected small_data_result.recovered == False (primary succeeded), "
        f"but got: {small.get('recovered')}. Full result: {small}"
    )


def test_small_data_model_is_complex_nn(experiment_result):
    """small_data result must use the primary model 'complex_nn'."""
    small = experiment_result["small_data_result"]
    assert small.get("model") == "complex_nn", (
        f"Expected small_data_result.model == 'complex_nn' (primary model), "
        f"but got: {small.get('model')}. Full result: {small}"
    )


def test_small_data_env_is_primary(experiment_result):
    """small_data result must report env == 'primary'."""
    small = experiment_result["small_data_result"]
    assert small.get("env") == "primary", (
        f"Expected small_data_result.env == 'primary', "
        f"but got: {small.get('env')}. Full result: {small}"
    )
