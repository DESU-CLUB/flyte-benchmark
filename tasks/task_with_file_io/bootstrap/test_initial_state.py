import os
import subprocess
import pytest


PROJECT_DIR = "/home/user/flyte_project"
INPUT_CSV = "/home/user/flyte_project/input.csv"


def test_flyte_package_importable():
    """Verify the `flyte` pip package is installed and importable."""
    result = subprocess.run(
        ["python3", "-c", "import flyte"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`import flyte` failed — the flyte package does not appear to be installed. "
        f"stderr: {result.stderr.strip()}"
    )


def test_flyte_project_directory_exists():
    """Verify the /home/user/flyte_project directory exists."""
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected directory {PROJECT_DIR} to exist, but it was not found."
    )


def test_input_csv_exists():
    """Verify the pre-created input.csv file exists in the project directory."""
    assert os.path.isfile(INPUT_CSV), (
        f"Expected pre-created input CSV file at {INPUT_CSV} to exist, but it was not found."
    )
