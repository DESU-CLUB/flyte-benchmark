import os
import json
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "error_handling.py")
RESULTS_PATH = os.path.join(PROJECT_DIR, "error_results.json")


def test_error_handling_script_exists():
    """Verify that the agent created error_handling.py in the project directory."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Script {SCRIPT_PATH} does not exist. "
        "The agent must create error_handling.py inside /home/user/flyte_project."
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
        f"python3 error_handling.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_results_file_exists():
    """Verify that running the script produced error_results.json."""
    assert os.path.isfile(RESULTS_PATH), (
        f"Output file {RESULTS_PATH} does not exist after running the script. "
        "The __main__ block must write results to /home/user/flyte_project/error_results.json."
    )


def test_results_is_valid_json_list_of_two():
    """Parse error_results.json and assert it is a list of exactly 2 dicts."""
    with open(RESULTS_PATH, "r") as f:
        data = json.load(f)
    assert isinstance(data, list), (
        f"error_results.json must be a JSON list, got {type(data).__name__}."
    )
    assert len(data) == 2, (
        f"error_results.json must contain exactly 2 result dicts, got {len(data)}."
    )
    for i, item in enumerate(data):
        assert isinstance(item, dict), (
            f"results[{i}] must be a dict, got {type(item).__name__}."
        )


def test_first_result_success():
    """Assert results[0] reflects a successful call: result=100, status='success', used_fallback=False."""
    with open(RESULTS_PATH, "r") as f:
        data = json.load(f)
    first = data[0]
    assert first.get("result") == 100, (
        f"results[0]['result'] must be 100 (safe_operation(50,10) → risky_operation(50) → 50*2), "
        f"got {first.get('result')!r}."
    )
    assert first.get("status") == "success", (
        f"results[0]['status'] must be 'success', got {first.get('status')!r}."
    )
    assert first.get("used_fallback") is False, (
        f"results[0]['used_fallback'] must be False, got {first.get('used_fallback')!r}."
    )


def test_second_result_fallback():
    """Assert results[1] reflects a fallback call: result=10, status='fallback', used_fallback=True."""
    with open(RESULTS_PATH, "r") as f:
        data = json.load(f)
    second = data[1]
    assert second.get("result") == 10, (
        f"results[1]['result'] must be 10 (safe_operation(200,5) → fallback risky_operation(5) → 5*2), "
        f"got {second.get('result')!r}."
    )
    assert second.get("status") == "fallback", (
        f"results[1]['status'] must be 'fallback', got {second.get('status')!r}."
    )
    assert second.get("used_fallback") is True, (
        f"results[1]['used_fallback'] must be True, got {second.get('used_fallback')!r}."
    )
