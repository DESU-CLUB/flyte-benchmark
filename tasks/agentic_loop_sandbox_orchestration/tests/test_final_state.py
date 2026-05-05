import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "agent_loop.py")
OUTPUT_PATH = os.path.join(PROJECT_DIR, "agent_output.json")


def test_agent_loop_script_exists():
    """Priority 4 (existence gate): agent_loop.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/agent_loop.py to exist, but it was not found."
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
        f"python3 agent_loop.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_agent_output_json_exists():
    """Priority 4 (existence gate): agent_output.json must exist after running the script."""
    assert os.path.isfile(OUTPUT_PATH), (
        f"Expected /home/user/flyte_project/agent_output.json to exist after running the script, "
        "but it was not found."
    )


def _load_output() -> dict:
    """Helper: parse the JSON output file produced by the agent's script."""
    with open(OUTPUT_PATH) as f:
        return json.load(f)


def test_output_is_valid_json():
    """Priority 1 (runtime output): agent_output.json must be parseable JSON containing a dict."""
    try:
        data = _load_output()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"agent_output.json is not valid JSON: {exc}\n"
            f"Raw content: {open(OUTPUT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected agent_output.json to contain a JSON object, got: {type(data)}"
    )


def test_steps_completed_equals_two():
    """Priority 1 (runtime output): steps_completed must be 2 (two instructions were processed)."""
    data = _load_output()
    assert "steps_completed" in data, (
        f"'steps_completed' key missing from agent_output.json. Got keys: {list(data.keys())}"
    )
    assert data["steps_completed"] == 2, (
        f"Expected steps_completed == 2 (two instructions processed), "
        f"but got: {data['steps_completed']!r}"
    )


def test_results_is_list_of_two():
    """Priority 1 (runtime output): results must be a list with exactly 2 items."""
    data = _load_output()
    assert "results" in data, (
        f"'results' key missing from agent_output.json. Got keys: {list(data.keys())}"
    )
    results = data["results"]
    assert isinstance(results, list), (
        f"Expected 'results' to be a list, got: {type(results)}"
    )
    assert len(results) == 2, (
        f"Expected 'results' to have 2 items (one per instruction), "
        f"but got: {len(results)}"
    )


def test_first_result_is_add_8():
    """Priority 1 (runtime output): first result must be 8.0 (add 5.0 + 3.0)."""
    data = _load_output()
    results = data["results"]
    assert len(results) >= 1, "results list must have at least 1 item"
    first = results[0]
    assert isinstance(first, dict), (
        f"Expected results[0] to be a dict, got: {type(first)}"
    )
    assert "result" in first, (
        f"Expected 'result' key in results[0], got keys: {list(first.keys())}"
    )
    assert first["result"] == pytest.approx(8.0), (
        f"Expected results[0]['result'] == 8.0 (add 5.0 + 3.0), "
        f"but got: {first['result']!r}"
    )


def test_second_result_is_multiply_28():
    """Priority 1 (runtime output): second result must be 28.0 (multiply 4.0 * 7.0)."""
    data = _load_output()
    results = data["results"]
    assert len(results) >= 2, "results list must have at least 2 items"
    second = results[1]
    assert isinstance(second, dict), (
        f"Expected results[1] to be a dict, got: {type(second)}"
    )
    assert "result" in second, (
        f"Expected 'result' key in results[1], got keys: {list(second.keys())}"
    )
    assert second["result"] == pytest.approx(28.0), (
        f"Expected results[1]['result'] == 28.0 (multiply 4.0 * 7.0), "
        f"but got: {second['result']!r}"
    )
