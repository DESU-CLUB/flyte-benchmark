import os
import subprocess
import pytest


PROJECT_DIR = "/home/user/flyte_project"


def test_flyte_importable():
    """Verify the flyte package is installed and importable."""
    result = subprocess.run(
        ["python3", "-c", "import flyte; print(flyte.__version__)"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"'flyte' package is not importable. stderr: {result.stderr}"
    )


def test_project_dir_exists():
    """Verify the project directory exists at the expected path."""
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory does not exist: {PROJECT_DIR}"
    )
