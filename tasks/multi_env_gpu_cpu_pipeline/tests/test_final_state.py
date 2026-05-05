import importlib.util
import json
import os
import subprocess
import sys
import pytest

PROJECT_DIR = "/home/user/flyte_project"
ENVIRONMENTS_PATH = os.path.join(PROJECT_DIR, "environments.py")
PIPELINE_PATH = os.path.join(PROJECT_DIR, "pipeline.py")
MAIN_PATH = os.path.join(PROJECT_DIR, "main.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "training_result.json")


# ---------------------------------------------------------------------------
# File existence checks
# ---------------------------------------------------------------------------


def test_environments_py_exists():
    """Confirm the agent created environments.py at the required path."""
    assert os.path.isfile(ENVIRONMENTS_PATH), (
        f"environments.py not found at {ENVIRONMENTS_PATH}. "
        "The agent must create this file."
    )


def test_pipeline_py_exists():
    """Confirm the agent created pipeline.py at the required path."""
    assert os.path.isfile(PIPELINE_PATH), (
        f"pipeline.py not found at {PIPELINE_PATH}. "
        "The agent must create this file."
    )


def test_main_py_exists():
    """Confirm the agent created main.py at the required path."""
    assert os.path.isfile(MAIN_PATH), (
        f"main.py not found at {MAIN_PATH}. "
        "The agent must create this file."
    )


# ---------------------------------------------------------------------------
# Runtime execution check
# ---------------------------------------------------------------------------


def test_main_runs_successfully():
    """Priority 1: Execute main.py and assert it exits with code 0."""
    result = subprocess.run(
        ["python3", MAIN_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 main.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Result JSON checks
# ---------------------------------------------------------------------------


def test_training_result_json_exists():
    """Confirm that running main.py produced training_result.json."""
    subprocess.run(
        ["python3", MAIN_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert os.path.isfile(RESULT_PATH), (
        f"training_result.json not found at {RESULT_PATH} after running main.py. "
        "The script must write the result to this path."
    )


@pytest.fixture(scope="module")
def training_result():
    """Run main.py and parse the resulting JSON once for all data-driven tests."""
    run = subprocess.run(
        ["python3", MAIN_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert run.returncode == 0, (
        f"main.py failed (exit {run.returncode}).\n"
        f"stdout: {run.stdout}\nstderr: {run.stderr}"
    )
    assert os.path.isfile(RESULT_PATH), (
        f"training_result.json was not written to {RESULT_PATH}."
    )
    with open(RESULT_PATH) as f:
        data = json.load(f)
    return data


def test_result_has_preprocessing_key(training_result):
    """Confirm top-level key 'preprocessing' is present in the JSON output."""
    assert "preprocessing" in training_result, (
        f"Key 'preprocessing' missing from training_result.json. Got: {list(training_result.keys())}"
    )


def test_result_has_model_key(training_result):
    """Confirm top-level key 'model' is present in the JSON output."""
    assert "model" in training_result, (
        f"Key 'model' missing from training_result.json. Got: {list(training_result.keys())}"
    )


def test_result_has_evaluation_key(training_result):
    """Confirm top-level key 'evaluation' is present in the JSON output."""
    assert "evaluation" in training_result, (
        f"Key 'evaluation' missing from training_result.json. Got: {list(training_result.keys())}"
    )


def test_evaluation_accuracy_positive(training_result):
    """evaluation.accuracy must be greater than 0.0."""
    accuracy = training_result["evaluation"].get("accuracy")
    assert isinstance(accuracy, (int, float)) and accuracy > 0.0, (
        f"Expected evaluation.accuracy > 0.0, but got: {accuracy}"
    )


def test_evaluation_eval_env_is_cpu(training_result):
    """evaluation.eval_env must equal 'cpu'."""
    eval_env = training_result["evaluation"].get("eval_env")
    assert eval_env == "cpu", (
        f"Expected evaluation.eval_env == 'cpu', but got: {eval_env!r}. "
        f"Full evaluation: {training_result['evaluation']}"
    )


def test_model_training_env_is_gpu(training_result):
    """model.training_env must equal 'gpu'."""
    training_env = training_result["model"].get("training_env")
    assert training_env == "gpu", (
        f"Expected model.training_env == 'gpu', but got: {training_env!r}. "
        f"Full model: {training_result['model']}"
    )


def test_preprocessing_env_is_cpu(training_result):
    """preprocessing.preprocessing_env must equal 'cpu'."""
    preprocessing_env = training_result["preprocessing"].get("preprocessing_env")
    assert preprocessing_env == "cpu", (
        f"Expected preprocessing.preprocessing_env == 'cpu', but got: {preprocessing_env!r}. "
        f"Full preprocessing: {training_result['preprocessing']}"
    )


def test_preprocessing_n_samples_is_five(training_result):
    """preprocessing.n_samples must equal 5 (the 5 non-None values in train_data)."""
    n_samples = training_result["preprocessing"].get("n_samples")
    assert n_samples == 5, (
        f"Expected preprocessing.n_samples == 5 (non-None values from [1.0, None, 2.0, 3.0, None, 4.0, 5.0]), "
        f"but got: {n_samples}. Full preprocessing: {training_result['preprocessing']}"
    )


# ---------------------------------------------------------------------------
# environments.py module introspection
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def environments_module():
    """Import environments.py as a module for attribute inspection."""
    spec = importlib.util.spec_from_file_location("environments", ENVIRONMENTS_PATH)
    module = importlib.util.module_from_spec(spec)
    # Ensure PROJECT_DIR is on the path so relative imports inside environments.py work
    if PROJECT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_DIR)
    spec.loader.exec_module(module)
    return module


def test_cpu_env_resources_cpu(environments_module):
    """cpu_env must be configured with cpu=4."""
    cpu = environments_module.cpu_env.resources.cpu
    assert cpu == 4, (
        f"Expected cpu_env.resources.cpu == 4, but got: {cpu}. "
        "Check the TaskEnvironment definition in environments.py."
    )


def test_gpu_env_resources_cpu(environments_module):
    """gpu_env must be configured with cpu=8."""
    cpu = environments_module.gpu_env.resources.cpu
    assert cpu == 8, (
        f"Expected gpu_env.resources.cpu == 8, but got: {cpu}. "
        "Check the TaskEnvironment definition in environments.py."
    )


def test_eval_env_resources_cpu(environments_module):
    """eval_env must be configured with cpu=2."""
    cpu = environments_module.eval_env.resources.cpu
    assert cpu == 2, (
        f"Expected eval_env.resources.cpu == 2, but got: {cpu}. "
        "Check the TaskEnvironment definition in environments.py."
    )
