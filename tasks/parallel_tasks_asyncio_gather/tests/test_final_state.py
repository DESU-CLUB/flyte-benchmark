import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "parallel_pipeline.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "pipeline_result.json")


def test_parallel_pipeline_script_exists():
    """Priority 4 (existence gate): parallel_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/parallel_pipeline.py to exist, but it was not found."
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
        f"python3 parallel_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_result_json_exists():
    """Priority 4 (existence gate): pipeline_result.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/pipeline_result.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json():
    """Priority 1 (runtime output): pipeline_result.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"pipeline_result.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected pipeline_result.json to contain a JSON object, got: {type(data)}"
    )


def test_total_sources_equals_three():
    """Priority 1 (runtime output): total_sources must be 3 (one per input source)."""
    data = _load_result()
    assert "total_sources" in data, (
        f"'total_sources' key missing from pipeline_result.json. Got keys: {list(data.keys())}"
    )
    assert data["total_sources"] == 3, (
        f"Expected total_sources == 3, but got: {data['total_sources']!r}"
    )


def test_total_records_equals_140():
    """Priority 1 (runtime output): total_records must be 140.

    Breakdown: 'alpha'=5 chars×10=50, 'beta'=4 chars×10=40, 'gamma'=5 chars×10=50 → total=140.
    """
    data = _load_result()
    assert "total_records" in data, (
        f"'total_records' key missing from pipeline_result.json. Got keys: {list(data.keys())}"
    )
    assert data["total_records"] == 140, (
        f"Expected total_records == 140 (alpha=50, beta=40, gamma=50), "
        f"but got: {data['total_records']!r}"
    )


def test_sources_list_contains_all_inputs():
    """Priority 1 (runtime output): sources list must contain 'alpha', 'beta', and 'gamma'."""
    data = _load_result()
    assert "sources" in data, (
        f"'sources' key missing from pipeline_result.json. Got keys: {list(data.keys())}"
    )
    sources = data["sources"]
    for expected in ("alpha", "beta", "gamma"):
        assert expected in sources, (
            f"Expected '{expected}' to be in sources list, but got: {sources!r}"
        )


def test_asyncio_gather_used_in_source():
    """Priority 4 (source-text fallback): verify asyncio.gather is used for parallel execution.

    No runtime check can distinguish sequential awaits from concurrent gather at the AST level,
    so a syntactic check is the only feasible verification for the parallel pattern requirement.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    assert "asyncio.gather" in source, (
        "Expected 'asyncio.gather' to appear in parallel_pipeline.py — "
        "the parallel fan-out pattern requires asyncio.gather, not sequential awaits."
    )
