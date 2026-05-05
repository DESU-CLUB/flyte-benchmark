import importlib.util
import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
RESOURCE_TASK_PY = os.path.join(PROJECT_DIR, "resource_task.py")
RESULT_JSON = os.path.join(PROJECT_DIR, "result.json")


def test_resource_task_py_exists():
    """Priority 4 (existence gate): resource_task.py must be present before we can run it."""
    assert os.path.isfile(RESOURCE_TASK_PY), (
        f"Expected /home/user/flyte_project/resource_task.py to exist, but it was not found."
    )


def test_resource_task_runs_successfully():
    """Priority 1: Run the agent's resource_task.py and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", RESOURCE_TASK_PY],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"Running resource_task.py failed with returncode {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_result_json_exists():
    """Priority 4 (existence gate): result.json must have been written by the script."""
    assert os.path.isfile(RESULT_JSON), (
        f"Expected /home/user/flyte_project/result.json to exist after running resource_task.py, "
        "but it was not found."
    )


def test_result_json_processed_is_correct():
    """Priority 1: Parse the JSON written by the agent's script and assert processed == 200."""
    with open(RESULT_JSON) as f:
        data = json.load(f)

    assert "processed" in data, (
        f"Expected 'processed' key in result.json, got keys: {list(data.keys())}"
    )
    processed = data["processed"]
    assert int(processed) == 200, (
        f"Expected processed == 200 (batch_size=100 * 2), got: {processed}"
    )


def test_result_json_status_is_complete():
    """Priority 1: Assert status == 'complete' in result.json."""
    with open(RESULT_JSON) as f:
        data = json.load(f)

    assert "status" in data, (
        f"Expected 'status' key in result.json, got keys: {list(data.keys())}"
    )
    assert data["status"] == "complete", (
        f"Expected status == 'complete', got: {data['status']!r}"
    )


def test_env_resources_cpu_and_memory():
    """Priority 1 (module import): Import the agent's module and assert env.resources.cpu==2 and memory=='2Gi'.
    Resources attributes are metadata stored on the TaskEnvironment object; importing the module
    is the only runtime check available for resource configuration correctness."""
    spec = importlib.util.spec_from_file_location("resource_task", RESOURCE_TASK_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "env"), (
        "Expected a module-level variable 'env' (TaskEnvironment) in resource_task.py, but it was not found."
    )
    env = module.env
    assert hasattr(env, "resources"), (
        "Expected 'env.resources' to exist on the TaskEnvironment object, but it was not found."
    )
    resources = env.resources
    assert hasattr(resources, "cpu"), (
        "Expected 'env.resources.cpu' attribute to exist on the Resources object."
    )
    assert int(resources.cpu) == 2, (
        f"Expected env.resources.cpu == 2, got: {resources.cpu!r}"
    )
    assert hasattr(resources, "memory"), (
        "Expected 'env.resources.memory' attribute to exist on the Resources object."
    )
    assert resources.memory == "2Gi", (
        f"Expected env.resources.memory == '2Gi', got: {resources.memory!r}"
    )
