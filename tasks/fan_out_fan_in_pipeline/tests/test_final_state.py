import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "fan_out_pipeline.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "fan_result.json")


def test_fan_out_pipeline_script_exists():
    """Priority 4 (existence gate): fan_out_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/fan_out_pipeline.py to exist, but it was not found."
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
        f"python3 fan_out_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_result_json_exists():
    """Priority 4 (existence gate): fan_result.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/fan_result.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json():
    """Priority 1 (runtime output): fan_result.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"fan_result.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected fan_result.json to contain a JSON object, got: {type(data)}"
    )


def test_total_equals_five():
    """Priority 1 (runtime output): total must be 5 (one entry per work item)."""
    data = _load_result()
    assert "total" in data, (
        f"'total' key missing from fan_result.json. Got keys: {list(data.keys())}"
    )
    assert data["total"] == 5, (
        f"Expected total == 5 (n=5 items), but got: {data['total']!r}"
    )


def test_sum_of_squares_equals_30():
    """Priority 1 (runtime output): sum_of_squares must be 30.

    Breakdown: 0²+1²+2²+3²+4² = 0+1+4+9+16 = 30.
    """
    data = _load_result()
    assert "sum_of_squares" in data, (
        f"'sum_of_squares' key missing from fan_result.json. Got keys: {list(data.keys())}"
    )
    assert data["sum_of_squares"] == 30, (
        f"Expected sum_of_squares == 30 (0+1+4+9+16), but got: {data['sum_of_squares']!r}"
    )


def test_even_count_equals_three():
    """Priority 1 (runtime output): even_count must be 3.

    Items [0,1,2,3,4]: 0, 2, and 4 are even → count = 3.
    """
    data = _load_result()
    assert "even_count" in data, (
        f"'even_count' key missing from fan_result.json. Got keys: {list(data.keys())}"
    )
    assert data["even_count"] == 3, (
        f"Expected even_count == 3 (items 0, 2, 4 are even), but got: {data['even_count']!r}"
    )


def test_asyncio_gather_used_in_source():
    """Priority 4 (source-text fallback): verify asyncio.gather is used for fan-out.

    No runtime check can distinguish sequential awaits from concurrent gather at the AST level,
    so a syntactic check is the only feasible verification for the fan-out pattern requirement.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    assert "asyncio.gather" in source, (
        "Expected 'asyncio.gather' to appear in fan_out_pipeline.py — "
        "the fan-out pattern requires asyncio.gather, not sequential awaits."
    )
