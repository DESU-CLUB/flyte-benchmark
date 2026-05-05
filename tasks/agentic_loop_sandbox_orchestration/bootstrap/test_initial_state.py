import os
import subprocess
import pytest


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


def test_flyte_trace_accessible():
    """Verify that `flyte.trace` is accessible (decorator for tracking agent steps)."""
    result = subprocess.run(
        ["python3", "-c", "import flyte; assert callable(flyte.trace), 'flyte.trace is not callable'"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`flyte.trace` is not accessible or not callable. "
        f"stderr: {result.stderr.strip()}"
    )


def test_flyte_project_directory_exists():
    """Verify the /home/user/flyte_project directory exists."""
    assert os.path.isdir("/home/user/flyte_project"), (
        "Expected directory /home/user/flyte_project to exist, but it was not found."
    )
