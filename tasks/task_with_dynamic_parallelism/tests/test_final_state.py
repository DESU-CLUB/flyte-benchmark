import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "dynamic_pipeline.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "feature_matrix.json")


def test_dynamic_pipeline_script_exists():
    """Priority 4 (existence gate): dynamic_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/dynamic_pipeline.py to exist, but it was not found."
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
        f"python3 dynamic_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_feature_matrix_json_exists():
    """Priority 4 (existence gate): feature_matrix.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/feature_matrix.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json():
    """Priority 1 (runtime output): feature_matrix.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"feature_matrix.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected feature_matrix.json to contain a JSON object, got: {type(data)}"
    )


def test_n_features_equals_six():
    """Priority 1 (runtime output): n_features must be 6 (3 features × 2 aggregations)."""
    data = _load_result()
    assert "n_features" in data, (
        f"'n_features' key missing from feature_matrix.json. Got keys: {list(data.keys())}"
    )
    assert data["n_features"] == 6, (
        f"Expected n_features == 6 (3 features × 2 aggregations = 6 configs), "
        f"but got: {data['n_features']!r}"
    )


def test_feature_names_contains_exactly_three_features():
    """Priority 1 (runtime output): feature_names must contain exactly feature_0, feature_1, feature_2."""
    data = _load_result()
    assert "feature_names" in data, (
        f"'feature_names' key missing from feature_matrix.json. Got keys: {list(data.keys())}"
    )
    feature_names = set(data["feature_names"])
    expected = {"feature_0", "feature_1", "feature_2"}
    assert feature_names == expected, (
        f"Expected feature_names to be exactly {expected}, but got: {feature_names!r}"
    )


def test_feature_matrix_has_six_entries():
    """Priority 1 (runtime output): feature_matrix list must have exactly 6 entries."""
    data = _load_result()
    assert "feature_matrix" in data, (
        f"'feature_matrix' key missing from feature_matrix.json. Got keys: {list(data.keys())}"
    )
    matrix = data["feature_matrix"]
    assert isinstance(matrix, list), (
        f"Expected 'feature_matrix' to be a list, got: {type(matrix)}"
    )
    assert len(matrix) == 6, (
        f"Expected feature_matrix to contain 6 entries (3 features × 2 aggregations), "
        f"but got {len(matrix)} entries."
    )


def test_feature0_mean_value_is_150():
    """Priority 1 (runtime output): feature_0/mean value must be 150.0 (100 / 1 * 1.5)."""
    data = _load_result()
    matrix = data.get("feature_matrix", [])
    matches = [
        entry for entry in matrix
        if entry.get("feature") == "feature_0" and entry.get("agg") == "mean"
    ]
    assert len(matches) == 1, (
        f"Expected exactly one entry with feature='feature_0' and agg='mean', "
        f"found {len(matches)}: {matches!r}"
    )
    entry = matches[0]
    assert entry["value"] == pytest.approx(150.0), (
        f"Expected feature_0/mean value == 150.0 (dataset_size=100, window=1, factor=1.5), "
        f"but got: {entry['value']!r}"
    )


def test_feature0_max_value_is_200():
    """Priority 1 (runtime output): feature_0/max value must be 200.0 (100 / 1 * 2.0)."""
    data = _load_result()
    matrix = data.get("feature_matrix", [])
    matches = [
        entry for entry in matrix
        if entry.get("feature") == "feature_0" and entry.get("agg") == "max"
    ]
    assert len(matches) == 1, (
        f"Expected exactly one entry with feature='feature_0' and agg='max', "
        f"found {len(matches)}: {matches!r}"
    )
    entry = matches[0]
    assert entry["value"] == pytest.approx(200.0), (
        f"Expected feature_0/max value == 200.0 (dataset_size=100, window=1, factor=2.0), "
        f"but got: {entry['value']!r}"
    )


def test_asyncio_gather_used_in_source():
    """Priority 4 (source-text fallback): verify asyncio.gather is used for dynamic parallel execution.

    No runtime check can distinguish sequential awaits from concurrent gather at the AST level,
    so a syntactic check is the only feasible verification for the dynamic parallel pattern requirement.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    assert "asyncio.gather" in source, (
        "Expected 'asyncio.gather' to appear in dynamic_pipeline.py — "
        "the dynamic parallel fan-out pattern requires asyncio.gather, not sequential awaits."
    )
