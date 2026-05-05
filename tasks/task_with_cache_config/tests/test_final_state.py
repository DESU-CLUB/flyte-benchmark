import importlib.util
import json
import os
import subprocess
import sys
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "cached_pipeline.py")
OUTPUT_PATH = os.path.join(PROJECT_DIR, "cache_result.json")

EXPECTED_FIBONACCI_10 = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def test_cached_pipeline_script_exists():
    """Priority 4 (existence gate): cached_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/cached_pipeline.py to exist, but it was not found."
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
        f"python3 cached_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_cache_result_json_exists():
    """Priority 4 (existence gate): cache_result.json must exist after running the script."""
    assert os.path.isfile(OUTPUT_PATH), (
        f"Expected /home/user/flyte_project/cache_result.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(OUTPUT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json_object():
    """Priority 1 (runtime output): cache_result.json must be a parseable JSON object."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"cache_result.json is not valid JSON: {exc}\n"
            f"Raw content: {open(OUTPUT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected cache_result.json to contain a JSON object, got: {type(data)}"
    )


def test_first_result_fibonacci_correct():
    """Priority 1 (runtime output): 'first' result must have fibonacci=[0,1,1,2,3,5,8,13,21,34]."""
    data = _load_result()
    assert "first" in data, (
        f"Expected 'first' key in cache_result.json, got keys: {list(data.keys())}"
    )
    first = data["first"]
    assert "fibonacci" in first, (
        f"Expected 'fibonacci' key in first result, got keys: {list(first.keys())}"
    )
    assert first["fibonacci"] == EXPECTED_FIBONACCI_10, (
        f"Expected fibonacci sequence {EXPECTED_FIBONACCI_10} for n=10, "
        f"but got: {first['fibonacci']}"
    )


def test_second_result_fibonacci_correct():
    """Priority 1 (runtime output): 'second' result must have fibonacci=[0,1,1,2,3,5,8,13,21,34]."""
    data = _load_result()
    assert "second" in data, (
        f"Expected 'second' key in cache_result.json, got keys: {list(data.keys())}"
    )
    second = data["second"]
    assert "fibonacci" in second, (
        f"Expected 'fibonacci' key in second result, got keys: {list(second.keys())}"
    )
    assert second["fibonacci"] == EXPECTED_FIBONACCI_10, (
        f"Expected fibonacci sequence {EXPECTED_FIBONACCI_10} for n=10, "
        f"but got: {second['fibonacci']}"
    )


def test_first_result_n_is_ten():
    """Priority 1 (runtime output): 'first' result must have n=10."""
    data = _load_result()
    first = data.get("first", {})
    assert first.get("n") == 10, (
        f"Expected 'n' == 10 in first result, got: {first.get('n')!r}"
    )


def test_second_result_n_is_ten():
    """Priority 1 (runtime output): 'second' result must have n=10."""
    data = _load_result()
    second = data.get("second", {})
    assert second.get("n") == 10, (
        f"Expected 'n' == 10 in second result, got: {second.get('n')!r}"
    )


def _load_module():
    """Helper: import the agent's cached_pipeline.py as a module."""
    spec = importlib.util.spec_from_file_location("cached_pipeline", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_expensive_computation_has_cache_attribute():
    """Priority 1 (module inspection): expensive_computation must have a .cache attribute."""
    import flyte
    module = _load_module()
    task_fn = getattr(module, "expensive_computation", None)
    assert task_fn is not None, (
        "Expected 'expensive_computation' to be defined in cached_pipeline.py, but it was not found."
    )
    assert hasattr(task_fn, "cache"), (
        f"Expected expensive_computation to have a 'cache' attribute (set via @env.task(cache=...)), "
        f"but the attribute was not found. Available attributes: {[a for a in dir(task_fn) if not a.startswith('__')]}"
    )
    assert isinstance(task_fn.cache, flyte.Cache), (
        f"Expected expensive_computation.cache to be an instance of flyte.Cache, "
        f"got: {type(task_fn.cache)}"
    )


def test_cache_version_is_v1():
    """Priority 1 (module inspection): cache version must be 'v1'."""
    module = _load_module()
    task_fn = getattr(module, "expensive_computation", None)
    assert task_fn is not None, (
        "Expected 'expensive_computation' to be defined in cached_pipeline.py."
    )
    assert hasattr(task_fn, "cache"), (
        "Expected expensive_computation to have a 'cache' attribute."
    )
    actual_version = task_fn.cache.version
    assert actual_version == "v1", (
        f"Expected expensive_computation.cache.version == 'v1', got: {actual_version!r}"
    )
