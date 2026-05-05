"""
Initial state tests for the Flyte 2.0 distributed map-reduce pipeline task.
Verifies that the environment is correctly set up before the agent begins.
"""
import os
import subprocess


def test_flyte_importable():
    """Verify that the flyte package can be imported."""
    try:
        import flyte  # noqa: F401
    except ImportError as e:
        raise AssertionError(f"flyte is not importable: {e}")


def test_project_directory_exists():
    """Verify that the project directory exists."""
    project_dir = "/home/user/flyte_project"
    assert os.path.isdir(project_dir), (
        f"Expected project directory '{project_dir}' to exist, but it does not."
    )
