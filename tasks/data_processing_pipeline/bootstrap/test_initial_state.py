import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"


def test_flyte_importable():
    result = subprocess.run(
        ["python3", "-c", "import flyte; print(flyte.__version__)"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"'flyte' package is not importable. stderr: {result.stderr}"
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )
