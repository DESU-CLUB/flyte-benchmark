import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
LEGACY_SCRIPT = os.path.join(PROJECT_DIR, "legacy_workflow.py")


def test_flyte_package_importable():
    """Verify the `flyte` (Flyte 2.0) pip package is installed and importable."""
    result = subprocess.run(
        ["python3", "-c", "import flyte"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`import flyte` failed — the Flyte 2.0 package does not appear to be installed. "
        f"stderr: {result.stderr.strip()}"
    )


def test_flyte_project_directory_exists():
    """Verify the /home/user/flyte_project directory was pre-created in the environment."""
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected directory {PROJECT_DIR} to exist, but it was not found. "
        "The Dockerfile should create this directory."
    )


def test_legacy_workflow_file_exists():
    """Verify the legacy Flyte 1.0 script was pre-created in the environment."""
    assert os.path.isfile(LEGACY_SCRIPT), (
        f"Expected {LEGACY_SCRIPT} to exist, but it was not found. "
        "The Dockerfile should create the legacy_workflow.py file."
    )


def test_legacy_workflow_contains_workflow_decorator():
    """Verify legacy_workflow.py contains the @workflow decorator (a Flyte 1.0 artifact)."""
    with open(LEGACY_SCRIPT) as f:
        source = f.read()
    assert "@workflow" in source, (
        f"Expected legacy_workflow.py to contain '@workflow' (Flyte 1.0 decorator), "
        f"but it was not found. File contents:\n{source}"
    )


def test_legacy_workflow_contains_map_task():
    """Verify legacy_workflow.py uses flytekit.map_task (a Flyte 1.0 API)."""
    with open(LEGACY_SCRIPT) as f:
        source = f.read()
    assert "map_task" in source, (
        f"Expected legacy_workflow.py to contain 'map_task' (Flyte 1.0 API), "
        f"but it was not found. File contents:\n{source}"
    )
