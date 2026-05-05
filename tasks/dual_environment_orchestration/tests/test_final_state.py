import os
import json
import subprocess
import importlib.util
import sys
import pytest


PROJECT_DIR = "/home/user/flyte_project"
PIPELINE_SCRIPT = os.path.join(PROJECT_DIR, "dual_env_pipeline.py")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "pipeline_output.json")


def test_pipeline_script_exists():
    """Priority 4 (file existence): Verify dual_env_pipeline.py was created by the agent."""
    assert os.path.isfile(PIPELINE_SCRIPT), (
        f"Pipeline script not found at {PIPELINE_SCRIPT}"
    )


def test_pipeline_script_runs_successfully():
    """Priority 1: Run the agent's pipeline script and assert it exits with code 0."""
    result = subprocess.run(
        ["python3", PIPELINE_SCRIPT],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 dual_env_pipeline.py failed with returncode {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_output_file_exists_and_is_valid_json():
    """Priority 1 (runtime artifact): Verify pipeline_output.json exists and is valid JSON."""
    assert os.path.isfile(OUTPUT_FILE), (
        f"Output file not found at {OUTPUT_FILE}. "
        "The pipeline script must write results to this path."
    )
    with open(OUTPUT_FILE) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f"pipeline_output.json is not valid JSON: {exc}")
    assert isinstance(data, dict), (
        f"pipeline_output.json must contain a JSON object (dict), got {type(data)}"
    )


def test_output_model_name_is_linear():
    """Priority 1 (runtime artifact): Assert model_name == 'linear' in the output JSON."""
    with open(OUTPUT_FILE) as f:
        data = json.load(f)
    assert "model_name" in data, (
        f"Key 'model_name' missing from pipeline_output.json. Got keys: {list(data.keys())}"
    )
    assert data["model_name"] == "linear", (
        f"Expected model_name == 'linear', got: {data['model_name']!r}"
    )


def test_output_accuracy_in_valid_range():
    """Priority 1 (runtime artifact): Assert accuracy > 0.0 and <= 0.99."""
    with open(OUTPUT_FILE) as f:
        data = json.load(f)
    assert "accuracy" in data, (
        f"Key 'accuracy' missing from pipeline_output.json. Got keys: {list(data.keys())}"
    )
    accuracy = data["accuracy"]
    assert accuracy > 0.0, (
        f"Expected accuracy > 0.0, got: {accuracy}"
    )
    assert accuracy <= 0.99, (
        f"Expected accuracy <= 0.99, got: {accuracy}"
    )


def test_output_accuracy_exact_value():
    """Priority 1 (runtime artifact): Assert accuracy == 0.15 for input [Alice, None, BOB, charlie, None]."""
    with open(OUTPUT_FILE) as f:
        data = json.load(f)
    accuracy = data.get("accuracy")
    # Input: ["Alice", None, "BOB", "charlie", None]
    # After clean_data: ["alice", "bob", "charlie"] -> 3 data_points
    # accuracy = min(0.99, 3 * 0.05) = 0.15
    assert accuracy == pytest.approx(0.15, abs=1e-9), (
        f"Expected accuracy == 0.15 (3 data_points * 0.05), got: {accuracy}"
    )


def _load_pipeline_module():
    """Helper: import the agent's dual_env_pipeline module via importlib."""
    spec = importlib.util.spec_from_file_location(
        "dual_env_pipeline", PIPELINE_SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    # Guard against re-executing __main__ block
    original_name = getattr(mod, "__name__", None)
    # We load without executing __main__; importlib sets __name__ to the given name
    spec.loader.exec_module(mod)
    return mod


def test_cpu_env_resources():
    """Priority 1 (module import): Assert cpu_env has cpu=2 and memory='4Gi'."""
    mod = _load_pipeline_module()
    cpu_env = mod.cpu_env
    assert cpu_env.resources.cpu == 2, (
        f"Expected cpu_env.resources.cpu == 2, got: {cpu_env.resources.cpu}"
    )
    assert cpu_env.resources.memory == "4Gi", (
        f"Expected cpu_env.resources.memory == '4Gi', got: {cpu_env.resources.memory!r}"
    )


def test_gpu_env_resources():
    """Priority 1 (module import): Assert gpu_env has cpu=8 and memory='16Gi'."""
    mod = _load_pipeline_module()
    gpu_env = mod.gpu_env
    assert gpu_env.resources.cpu == 8, (
        f"Expected gpu_env.resources.cpu == 8, got: {gpu_env.resources.cpu}"
    )
    assert gpu_env.resources.memory == "16Gi", (
        f"Expected gpu_env.resources.memory == '16Gi', got: {gpu_env.resources.memory!r}"
    )
