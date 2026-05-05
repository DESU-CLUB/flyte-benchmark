import os
import json
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
TASKS_FILE = os.path.join(PROJECT_DIR, "tasks.py")
MAIN_FILE = os.path.join(PROJECT_DIR, "main.py")
REPORT_FILE = os.path.join(PROJECT_DIR, "aggregate_report.json")

EXPECTED_GRAND_TOTAL = 21250.0   # 5000.0 + 12500.0 + 3750.0
EXPECTED_MAX_COUNT = 250          # source_b
EXPECTED_MIN_COUNT = 75           # source_c
EXPECTED_SOURCE_COUNT = 3


def test_tasks_file_exists():
    """Priority 1 prerequisite: tasks.py must exist before the pipeline can run."""
    assert os.path.isfile(TASKS_FILE), (
        f"tasks.py not found at '{TASKS_FILE}'. "
        "The agent must create /home/user/flyte_project/tasks.py."
    )


def test_main_file_exists():
    """Priority 1 prerequisite: main.py must exist before the pipeline can run."""
    assert os.path.isfile(MAIN_FILE), (
        f"main.py not found at '{MAIN_FILE}'. "
        "The agent must create /home/user/flyte_project/main.py."
    )


def test_pipeline_runs_successfully():
    """Priority 1: Execute main.py and assert it exits with returncode 0."""
    result = subprocess.run(
        ["python3", MAIN_FILE],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"'python3 main.py' exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_aggregate_report_exists():
    """Priority 1 (runtime artifact): aggregate_report.json must exist after running main.py."""
    # Run the pipeline first to ensure the report is generated
    subprocess.run(
        ["python3", MAIN_FILE],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert os.path.isfile(REPORT_FILE), (
        f"aggregate_report.json not found at '{REPORT_FILE}'. "
        "main.py must write the aggregate result to this path."
    )


def test_aggregate_report_is_valid_json():
    """Priority 1 (runtime artifact): aggregate_report.json must be parseable as JSON."""
    subprocess.run(
        ["python3", MAIN_FILE],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert os.path.isfile(REPORT_FILE), (
        f"aggregate_report.json missing at '{REPORT_FILE}'."
    )
    try:
        with open(REPORT_FILE) as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"aggregate_report.json is not valid JSON: {exc}. "
            f"File contents: {open(REPORT_FILE).read()[:500]}"
        )


@pytest.fixture(scope="module")
def report_data():
    """Run the pipeline once and return the parsed JSON report."""
    subprocess.run(
        ["python3", MAIN_FILE],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    with open(REPORT_FILE) as f:
        return json.load(f)


def test_source_count(report_data):
    """Priority 1 (runtime value): source_count must equal 3."""
    assert "source_count" in report_data, (
        f"'source_count' key missing from aggregate_report.json. Got keys: {list(report_data.keys())}"
    )
    assert report_data["source_count"] == EXPECTED_SOURCE_COUNT, (
        f"Expected source_count={EXPECTED_SOURCE_COUNT}, "
        f"got {report_data['source_count']}."
    )


def test_grand_total(report_data):
    """Priority 1 (runtime value): grand_total must equal 5000.0 + 12500.0 + 3750.0 = 21250.0."""
    assert "grand_total" in report_data, (
        f"'grand_total' key missing from aggregate_report.json. Got keys: {list(report_data.keys())}"
    )
    assert abs(report_data["grand_total"] - EXPECTED_GRAND_TOTAL) < 1e-6, (
        f"Expected grand_total={EXPECTED_GRAND_TOTAL}, "
        f"got {report_data['grand_total']}."
    )


def test_max_count(report_data):
    """Priority 1 (runtime value): max_count must equal 250 (source_b)."""
    assert "max_count" in report_data, (
        f"'max_count' key missing from aggregate_report.json. Got keys: {list(report_data.keys())}"
    )
    assert report_data["max_count"] == EXPECTED_MAX_COUNT, (
        f"Expected max_count={EXPECTED_MAX_COUNT} (source_b), "
        f"got {report_data['max_count']}."
    )


def test_min_count(report_data):
    """Priority 1 (runtime value): min_count must equal 75 (source_c)."""
    assert "min_count" in report_data, (
        f"'min_count' key missing from aggregate_report.json. Got keys: {list(report_data.keys())}"
    )
    assert report_data["min_count"] == EXPECTED_MIN_COUNT, (
        f"Expected min_count={EXPECTED_MIN_COUNT} (source_c), "
        f"got {report_data['min_count']}."
    )
