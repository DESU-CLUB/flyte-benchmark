import importlib.util
import json
import os
import subprocess
import pytest


PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "secret_task.py")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "secure_output.json")

# API key used for local testing (len == 18)
TEST_API_KEY = "test-api-key-12345"


def test_secret_task_script_exists():
    """Priority 4 (file existence): Verify secret_task.py was created by the agent."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Script not found at {SCRIPT_PATH}. "
        "The agent must create /home/user/flyte_project/secret_task.py."
    )


def test_script_runs_successfully():
    """Priority 1: Run the agent's script with API_KEY set and assert returncode == 0."""
    env = {
        "API_KEY": TEST_API_KEY,
        "PATH": os.environ.get("PATH", ""),
    }
    result = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        env=env,
    )
    assert result.returncode == 0, (
        f"python3 secret_task.py failed with returncode {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_output_file_exists():
    """Priority 1 (runtime artifact): Verify secure_output.json exists after script execution."""
    assert os.path.isfile(OUTPUT_FILE), (
        f"Output file not found at {OUTPUT_FILE}. "
        "The script must write results to /home/user/flyte_project/secure_output.json."
    )


def _load_output():
    """Helper: parse and return the JSON output file."""
    with open(OUTPUT_FILE) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f"secure_output.json is not valid JSON: {exc}")


def test_output_is_list_of_two_items():
    """Priority 1 (runtime artifact): Assert output is a JSON list with exactly 2 items."""
    data = _load_output()
    assert isinstance(data, list), (
        f"secure_output.json must be a JSON array (list), got {type(data).__name__}"
    )
    assert len(data) == 2, (
        f"Expected exactly 2 items in secure_output.json, got {len(data)}: {data}"
    )


def test_both_items_authenticated():
    """Priority 1 (runtime artifact): Assert both result items have authenticated == True."""
    data = _load_output()
    for i, item in enumerate(data):
        assert "authenticated" in item, (
            f"Item {i} missing 'authenticated' key. Got keys: {list(item.keys())}"
        )
        assert item["authenticated"] is True, (
            f"Item {i} has authenticated == {item['authenticated']!r}, expected True. "
            f"Ensure API_KEY env var is set when running the script."
        )


def test_both_items_key_length_18():
    """Priority 1 (runtime artifact): Assert both items have key_length == 18 (len('test-api-key-12345'))."""
    data = _load_output()
    for i, item in enumerate(data):
        assert "key_length" in item, (
            f"Item {i} missing 'key_length' key. Got keys: {list(item.keys())}"
        )
        assert item["key_length"] == 18, (
            f"Item {i} has key_length == {item['key_length']}, expected 18 "
            f"(len('test-api-key-12345') == 18)."
        )


def test_output_contains_both_endpoints():
    """Priority 1 (runtime artifact): Assert items contain endpoints '/api/v1/data' and '/api/v1/models'."""
    data = _load_output()
    endpoints = {item.get("endpoint") for item in data}
    assert "/api/v1/data" in endpoints, (
        f"Expected endpoint '/api/v1/data' in output, got endpoints: {endpoints}"
    )
    assert "/api/v1/models" in endpoints, (
        f"Expected endpoint '/api/v1/models' in output, got endpoints: {endpoints}"
    )


def _load_module():
    """Helper: import secret_task module via importlib without re-running __main__."""
    spec = importlib.util.spec_from_file_location("secret_task", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_api_secret_key_attribute():
    """Priority 1 (module import): Assert API_SECRET.key == 'api_key'."""
    mod = _load_module()
    assert hasattr(mod, "API_SECRET"), (
        "Module secret_task does not define 'API_SECRET' at module level."
    )
    assert mod.API_SECRET.key == "api_key", (
        f"Expected API_SECRET.key == 'api_key', got: {mod.API_SECRET.key!r}"
    )


def test_api_secret_group_attribute():
    """Priority 1 (module import): Assert API_SECRET.group == 'my-secrets'."""
    mod = _load_module()
    assert hasattr(mod, "API_SECRET"), (
        "Module secret_task does not define 'API_SECRET' at module level."
    )
    assert mod.API_SECRET.group == "my-secrets", (
        f"Expected API_SECRET.group == 'my-secrets', got: {mod.API_SECRET.group!r}"
    )
