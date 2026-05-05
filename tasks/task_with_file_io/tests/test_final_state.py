import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "file_pipeline.py")
OUTPUT_PATH = os.path.join(PROJECT_DIR, "filtered.json")


def test_file_pipeline_script_exists():
    """Priority 4 (existence gate): file_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/file_pipeline.py to exist, but it was not found."
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
        f"python3 file_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_filtered_json_exists():
    """Priority 4 (existence gate): filtered.json must exist after running the script."""
    assert os.path.isfile(OUTPUT_PATH), (
        f"Expected /home/user/flyte_project/filtered.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> list:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(OUTPUT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json_array():
    """Priority 1 (runtime output): filtered.json must be a parseable JSON array."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"filtered.json is not valid JSON: {exc}\n"
            f"Raw content: {open(OUTPUT_PATH).read()!r}"
        )
    assert isinstance(data, list), (
        f"Expected filtered.json to contain a JSON array, got: {type(data)}"
    )


def test_filtered_records_count_is_two():
    """Priority 1 (runtime output): exactly 2 records must pass the score > 80 filter.

    alice (85 > 80) and bob (92 > 80) qualify; charlie (78 <= 80) does not.
    """
    data = _load_result()
    assert len(data) == 2, (
        f"Expected exactly 2 filtered records (alice and bob), but got {len(data)}. "
        f"Records: {data}"
    )


def test_alice_record_present():
    """Priority 1 (runtime output): a record with name 'alice' must be in the output."""
    data = _load_result()
    names = [r.get("name") for r in data]
    assert "alice" in names, (
        f"Expected a record with name 'alice' in filtered.json (score 85 > 80), "
        f"but got names: {names}"
    )


def test_bob_record_present():
    """Priority 1 (runtime output): a record with name 'bob' must be in the output."""
    data = _load_result()
    names = [r.get("name") for r in data]
    assert "bob" in names, (
        f"Expected a record with name 'bob' in filtered.json (score 92 > 80), "
        f"but got names: {names}"
    )


def test_charlie_record_absent():
    """Priority 1 (runtime output): charlie (score 78) must NOT appear in the output."""
    data = _load_result()
    names = [r.get("name") for r in data]
    assert "charlie" not in names, (
        f"Expected 'charlie' to be filtered out (score 78 <= 80), "
        f"but found charlie in filtered records: {data}"
    )


def test_alice_score_correct():
    """Priority 1 (runtime output): alice's score field must be '85' (as read from CSV)."""
    data = _load_result()
    alice = next((r for r in data if r.get("name") == "alice"), None)
    assert alice is not None, "Record for 'alice' not found in filtered.json."
    assert str(alice.get("score")) == "85", (
        f"Expected alice's score to be '85', got: {alice.get('score')!r}"
    )


def test_bob_score_correct():
    """Priority 1 (runtime output): bob's score field must be '92' (as read from CSV)."""
    data = _load_result()
    bob = next((r for r in data if r.get("name") == "bob"), None)
    assert bob is not None, "Record for 'bob' not found in filtered.json."
    assert str(bob.get("score")) == "92", (
        f"Expected bob's score to be '92', got: {bob.get('score')!r}"
    )
