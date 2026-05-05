"""
Final state tests for the Flyte 2.0 full ETL pipeline with recovery task.
Verifies that the agent correctly implemented the pipeline and produced expected output.
"""
import json
import os
import subprocess
import sys


PROJECT_DIR = "/home/user/flyte_project"
ETL_PIPELINE_FILE = os.path.join(PROJECT_DIR, "etl_pipeline.py")
MAIN_FILE = os.path.join(PROJECT_DIR, "main.py")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "etl_output.json")


# ---------------------------------------------------------------------------
# Priority 1: File existence
# ---------------------------------------------------------------------------

def test_etl_pipeline_file_exists():
    """etl_pipeline.py must exist in the project directory."""
    assert os.path.isfile(ETL_PIPELINE_FILE), (
        f"Expected '{ETL_PIPELINE_FILE}' to exist, but it was not found."
    )


def test_main_file_exists():
    """main.py must exist in the project directory."""
    assert os.path.isfile(MAIN_FILE), (
        f"Expected '{MAIN_FILE}' to exist, but it was not found."
    )


# ---------------------------------------------------------------------------
# Priority 1: Execution
# ---------------------------------------------------------------------------

def test_main_runs_successfully():
    """Running main.py with python3 must exit with returncode 0."""
    result = subprocess.run(
        ["python3", MAIN_FILE],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"main.py exited with code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Priority 1: Output file and content
# ---------------------------------------------------------------------------

def _load_output() -> dict:
    assert os.path.isfile(OUTPUT_FILE), (
        f"Expected output file '{OUTPUT_FILE}' to exist after running main.py."
    )
    with open(OUTPUT_FILE, "r") as f:
        return json.load(f)


def test_output_file_exists():
    """etl_output.json must be created after running the pipeline."""
    assert os.path.isfile(OUTPUT_FILE), (
        f"Expected '{OUTPUT_FILE}' to exist, but it was not found."
    )


def test_warehouse_status_loaded():
    """The output must contain warehouse_status == 'loaded'."""
    data = _load_output()
    assert "warehouse_status" in data, (
        f"'warehouse_status' key missing from output. Got keys: {list(data.keys())}"
    )
    assert data["warehouse_status"] == "loaded", (
        f"Expected warehouse_status='loaded', got: {data['warehouse_status']!r}"
    )


def test_sources_contain_database_and_api():
    """The output sources list must include 'database' and 'api'."""
    data = _load_output()
    assert "sources" in data, (
        f"'sources' key missing from output. Got keys: {list(data.keys())}"
    )
    sources = data["sources"]
    assert "database" in sources, (
        f"Expected 'database' in sources, got: {sources}"
    )
    assert "api" in sources, (
        f"Expected 'api' in sources, got: {sources}"
    )


def test_total_records_is_twelve():
    """total_records must equal 12 (7 from database + 5 from api)."""
    data = _load_output()
    assert "total_records" in data, (
        f"'total_records' key missing from output. Got keys: {list(data.keys())}"
    )
    assert data["total_records"] == 12, (
        f"Expected total_records=12, got: {data['total_records']}.\n"
        "Breakdown: database has 10 records but 3 are inactive (ids 3,6,9), "
        "leaving 7 active; api has 5 records all active. 7+5=12."
    )
