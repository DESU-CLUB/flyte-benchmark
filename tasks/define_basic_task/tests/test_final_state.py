import asyncio
import importlib.util
import os
import pytest

PROJECT_DIR = "/home/user/flyte_project"
TASKS_PY = os.path.join(PROJECT_DIR, "tasks.py")
OUTPUT_LOG = os.path.join(PROJECT_DIR, "output.log")


def test_tasks_py_exists():
    """Priority 4 (existence gate): tasks.py must be present before we can import it."""
    assert os.path.isfile(TASKS_PY), (
        f"Expected /home/user/flyte_project/tasks.py to exist, but it was not found."
    )


def _load_tasks_module():
    """Helper: load the agent's tasks.py as a module."""
    spec = importlib.util.spec_from_file_location("tasks", TASKS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_add_function_returns_correct_value():
    """Priority 1: Import the agent's module and assert runtime behaviour of add()."""
    module = _load_tasks_module()

    assert hasattr(module, "add"), (
        "The agent's tasks.py does not define a top-level function named 'add'."
    )

    result = asyncio.run(module.add(3, 4))
    assert result == 7, (
        f"Expected add(3, 4) to return 7, but got: {result!r}"
    )


def test_multiply_function_returns_correct_value():
    """Priority 1: Import the agent's module and assert runtime behaviour of multiply()."""
    module = _load_tasks_module()

    assert hasattr(module, "multiply"), (
        "The agent's tasks.py does not define a top-level function named 'multiply'."
    )

    result = asyncio.run(module.multiply(3, 4))
    assert result == 12, (
        f"Expected multiply(3, 4) to return 12, but got: {result!r}"
    )


def test_output_log_exists():
    """Priority 4 (existence gate): output.log must have been created by running the script."""
    assert os.path.isfile(OUTPUT_LOG), (
        f"Expected /home/user/flyte_project/output.log to exist. "
        "Run `python /home/user/flyte_project/tasks.py > /home/user/flyte_project/output.log` first."
    )
