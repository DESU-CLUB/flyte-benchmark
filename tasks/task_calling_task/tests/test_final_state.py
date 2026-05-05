import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "chained_tasks.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "analysis.json")


def test_chained_tasks_script_exists():
    """Priority 4 (existence gate): chained_tasks.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/chained_tasks.py to exist, but it was not found."
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
        f"python3 chained_tasks.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_analysis_json_exists():
    """Priority 4 (existence gate): analysis.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/analysis.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json():
    """Priority 1 (runtime output): analysis.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"analysis.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected analysis.json to contain a JSON object, got: {type(data)}"
    )


def test_token_count_equals_five():
    """Priority 1 (runtime output): token_count must be 5.

    Input 'Hello World Hello Flyte World' normalizes to
    'hello world hello flyte world', which splits into 5 tokens.
    """
    data = _load_result()
    assert "token_count" in data, (
        f"'token_count' key missing from analysis.json. Got keys: {list(data.keys())}"
    )
    assert data["token_count"] == 5, (
        f"Expected token_count == 5 ('hello world hello flyte world' → 5 tokens), "
        f"but got: {data['token_count']!r}"
    )


def test_unique_count_equals_three():
    """Priority 1 (runtime output): unique_count must be 3.

    The 5 tokens ['hello', 'world', 'hello', 'flyte', 'world'] have
    3 distinct values: 'hello', 'world', 'flyte'.
    """
    data = _load_result()
    assert "unique_count" in data, (
        f"'unique_count' key missing from analysis.json. Got keys: {list(data.keys())}"
    )
    assert data["unique_count"] == 3, (
        f"Expected unique_count == 3 (hello, world, flyte are 3 unique tokens), "
        f"but got: {data['unique_count']!r}"
    )
