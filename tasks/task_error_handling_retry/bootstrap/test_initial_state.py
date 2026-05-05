import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"


def test_flyte_importable():
    """Verify that the `flyte` package is installed and importable."""
    result = subprocess.run(
        ["python3", "-c", "import flyte; print(flyte.__version__)"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`import flyte` failed — flyte package is not installed or not importable. "
        f"stderr: {result.stderr.strip()}"
    )


def test_project_directory_exists():
    """Verify that the project directory /home/user/flyte_project exists."""
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist. "
        "It should be created as part of the initial environment setup."
    )
