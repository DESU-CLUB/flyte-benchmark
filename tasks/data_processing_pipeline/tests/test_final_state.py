import os
import subprocess
import json
import pytest

PROJECT_DIR = "/home/user/flyte_project"
PIPELINE_SCRIPT = os.path.join(PROJECT_DIR, "data_pipeline.py")
OUTPUT_JSON = os.path.join(PROJECT_DIR, "pipeline_stats.json")


def test_data_pipeline_script_exists():
    assert os.path.isfile(PIPELINE_SCRIPT), (
        f"data_pipeline.py not found at {PIPELINE_SCRIPT}"
    )


def test_pipeline_runs_successfully():
    """Priority 1: Execute the agent's script and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", PIPELINE_SCRIPT],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 data_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_pipeline_stats_json_exists():
    """Priority 1: Confirm the output JSON file was written by the script."""
    assert os.path.isfile(OUTPUT_JSON), (
        f"pipeline_stats.json not found at {OUTPUT_JSON}. "
        "The script must write results to this path."
    )


def test_pipeline_stats_total_datasets():
    """Priority 1: Parse the runtime-produced JSON and check total_datasets == 3."""
    with open(OUTPUT_JSON) as f:
        stats = json.load(f)
    assert stats.get("total_datasets") == 3, (
        f"Expected total_datasets == 3, got {stats.get('total_datasets')}. "
        f"Full stats: {stats}"
    )


def test_pipeline_stats_total_rows():
    """Priority 1: Assert total_rows == 4 (sales:2 + inventory:2 + returns:0)."""
    with open(OUTPUT_JSON) as f:
        stats = json.load(f)
    assert stats.get("total_rows") == 4, (
        f"Expected total_rows == 4 (sales:2 + inventory:2 + returns:0), "
        f"got {stats.get('total_rows')}. Full stats: {stats}"
    )


def test_pipeline_stats_datasets_names():
    """Priority 1: Assert the datasets list contains sales, inventory, and returns."""
    with open(OUTPUT_JSON) as f:
        stats = json.load(f)
    datasets = stats.get("datasets", [])
    for expected in ["sales", "inventory", "returns"]:
        assert expected in datasets, (
            f"Expected '{expected}' in datasets list, got: {datasets}"
        )
    assert len(datasets) == 3, (
        f"Expected exactly 3 dataset names, got {len(datasets)}: {datasets}"
    )
