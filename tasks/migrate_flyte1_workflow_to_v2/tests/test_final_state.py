import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
MODERN_SCRIPT = os.path.join(PROJECT_DIR, "modern_workflow.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "migration_result.json")


def test_modern_workflow_script_exists():
    """Priority 4 (existence gate): modern_workflow.py must be present before execution."""
    assert os.path.isfile(MODERN_SCRIPT), (
        f"Expected {MODERN_SCRIPT} to exist, but it was not found. "
        "The agent must create this file as part of the Flyte 2.0 migration."
    )


def test_modern_workflow_runs_without_error():
    """Priority 1: Execute the migrated script and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", MODERN_SCRIPT],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 modern_workflow.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_migration_result_json_exists():
    """Priority 4 (existence gate): migration_result.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected {RESULT_PATH} to exist after running modern_workflow.py, "
        "but it was not found. The __main__ block must write this file."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the migrated script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json():
    """Priority 1 (runtime output): migration_result.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"migration_result.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected migration_result.json to contain a JSON object, got: {type(data)}"
    )


def test_result_equals_55():
    """Priority 1 (runtime output): result must equal 55.

    Sum of squares of [1,2,3,4,5]: 1²+2²+3²+4²+5² = 1+4+9+16+25 = 55.
    """
    data = _load_result()
    assert "result" in data, (
        f"'result' key missing from migration_result.json. Got keys: {list(data.keys())}"
    )
    assert data["result"] == 55, (
        f"Expected result == 55 (1²+2²+3²+4²+5² = 1+4+9+16+25 = 55), "
        f"but got: {data['result']!r}"
    )


def test_input_equals_expected_list():
    """Priority 1 (runtime output): input must equal [1, 2, 3, 4, 5]."""
    data = _load_result()
    assert "input" in data, (
        f"'input' key missing from migration_result.json. Got keys: {list(data.keys())}"
    )
    assert data["input"] == [1, 2, 3, 4, 5], (
        f"Expected input == [1, 2, 3, 4, 5], but got: {data['input']!r}"
    )


def test_modern_workflow_does_not_import_flytekit():
    """Priority 4 (source-text): modern_workflow.py must NOT import the legacy flytekit package."""
    with open(MODERN_SCRIPT) as f:
        source = f.read()
    assert "import flytekit" not in source, (
        "Found 'import flytekit' in modern_workflow.py. "
        "The migrated script must use 'import flyte' (Flyte 2.0), not flytekit (Flyte 1.x)."
    )


def test_modern_workflow_imports_flyte():
    """Priority 4 (source-text): modern_workflow.py must import the new `flyte` package."""
    with open(MODERN_SCRIPT) as f:
        source = f.read()
    assert "import flyte" in source, (
        "Did not find 'import flyte' in modern_workflow.py. "
        "The migrated script must use the Flyte 2.0 package: 'import flyte' or 'from flyte import ...'."
    )


def test_modern_workflow_does_not_use_workflow_decorator():
    """Priority 4 (source-text): modern_workflow.py must NOT contain the legacy @workflow decorator."""
    with open(MODERN_SCRIPT) as f:
        source = f.read()
    assert "@workflow" not in source, (
        "Found '@workflow' in modern_workflow.py. "
        "The @workflow decorator is removed in Flyte 2.0. "
        "Use @env.task for all durable units, including the orchestrating pipeline task."
    )


def test_modern_workflow_uses_asyncio_gather():
    """Priority 4 (source-text): modern_workflow.py must use asyncio.gather for fan-out.

    asyncio.gather replaces flytekit.map_task in Flyte 2.0 for parallel execution over
    a list of inputs. This syntactic check verifies the correct migration pattern is used.
    """
    with open(MODERN_SCRIPT) as f:
        source = f.read()
    assert "asyncio.gather" in source, (
        "Did not find 'asyncio.gather' in modern_workflow.py. "
        "The Flyte 2.0 migration pattern requires asyncio.gather to replace flytekit.map_task. "
        "Example: squared = await asyncio.gather(*[square(n) for n in numbers])"
    )
