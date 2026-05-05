import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "conditional_pipeline.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "conditional_results.json")


def test_conditional_pipeline_script_exists():
    """Priority 4 (existence gate): conditional_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/conditional_pipeline.py to exist, but it was not found."
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
        f"python3 conditional_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_result_json_exists():
    """Priority 4 (existence gate): conditional_results.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/conditional_results.json to exist after running "
        "the script, but it was not found."
    )


def _load_results() -> list:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json_list_of_four():
    """Priority 1 (runtime output): conditional_results.json must be a JSON list of 4 dicts."""
    try:
        data = _load_results()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"conditional_results.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, list), (
        f"Expected conditional_results.json to contain a JSON array, got: {type(data)}"
    )
    assert len(data) == 4, (
        f"Expected exactly 4 result dicts (one per input value), got: {len(data)}"
    )


def test_negative_value_result():
    """Priority 1 (runtime output): result for -5.0 must have class='negative', result=5.0, operation='abs'."""
    data = _load_results()
    entry = data[0]
    assert entry.get("class") == "negative", (
        f"For input -5.0: expected class='negative', got: {entry.get('class')!r}. "
        f"Full entry: {entry}"
    )
    assert entry.get("result") == 5.0, (
        f"For input -5.0: expected result=5.0 (abs(-5.0)), got: {entry.get('result')!r}. "
        f"Full entry: {entry}"
    )
    assert entry.get("operation") == "abs", (
        f"For input -5.0: expected operation='abs', got: {entry.get('operation')!r}. "
        f"Full entry: {entry}"
    )


def test_zero_value_result():
    """Priority 1 (runtime output): result for 0.0 must have class='zero', result=0.0, operation='identity'."""
    data = _load_results()
    entry = data[1]
    assert entry.get("class") == "zero", (
        f"For input 0.0: expected class='zero', got: {entry.get('class')!r}. "
        f"Full entry: {entry}"
    )
    assert entry.get("result") == 0.0, (
        f"For input 0.0: expected result=0.0, got: {entry.get('result')!r}. "
        f"Full entry: {entry}"
    )
    assert entry.get("operation") == "identity", (
        f"For input 0.0: expected operation='identity', got: {entry.get('operation')!r}. "
        f"Full entry: {entry}"
    )


def test_small_positive_value_result():
    """Priority 1 (runtime output): result for 3.0 must have class='small_positive', result=6.0, operation='double'."""
    data = _load_results()
    entry = data[2]
    assert entry.get("class") == "small_positive", (
        f"For input 3.0: expected class='small_positive', got: {entry.get('class')!r}. "
        f"Full entry: {entry}"
    )
    assert entry.get("result") == 6.0, (
        f"For input 3.0: expected result=6.0 (3.0 * 2), got: {entry.get('result')!r}. "
        f"Full entry: {entry}"
    )
    assert entry.get("operation") == "double", (
        f"For input 3.0: expected operation='double', got: {entry.get('operation')!r}. "
        f"Full entry: {entry}"
    )


def test_large_positive_value_result():
    """Priority 1 (runtime output): result for 25.0 must have class='large_positive', result=5.0, operation='sqrt'."""
    data = _load_results()
    entry = data[3]
    assert entry.get("class") == "large_positive", (
        f"For input 25.0: expected class='large_positive', got: {entry.get('class')!r}. "
        f"Full entry: {entry}"
    )
    assert abs(entry.get("result", float("nan")) - 5.0) < 1e-9, (
        f"For input 25.0: expected result=5.0 (25.0 ** 0.5), got: {entry.get('result')!r}. "
        f"Full entry: {entry}"
    )
    assert entry.get("operation") == "sqrt", (
        f"For input 25.0: expected operation='sqrt', got: {entry.get('operation')!r}. "
        f"Full entry: {entry}"
    )


def test_asyncio_gather_used_in_source():
    """Priority 4 (source-text fallback): verify asyncio.gather is used for parallel classification.

    No runtime check can distinguish sequential awaits from concurrent gather at the Python-AST
    level, so a syntactic check is the only feasible verification for the parallel pattern
    requirement.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    assert "asyncio.gather" in source, (
        "Expected 'asyncio.gather' to appear in conditional_pipeline.py — "
        "parallel classification of values requires asyncio.gather, not sequential awaits."
    )
