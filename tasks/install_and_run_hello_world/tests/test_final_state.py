import asyncio
import importlib.util
import os
import pytest

PROJECT_DIR = "/home/user/flyte_project"
HELLO_PY = os.path.join(PROJECT_DIR, "hello.py")
OUTPUT_LOG = os.path.join(PROJECT_DIR, "output.log")


def test_hello_py_exists():
    """Priority 4 (existence gate): hello.py must be present before we can import it."""
    assert os.path.isfile(HELLO_PY), (
        f"Expected /home/user/flyte_project/hello.py to exist, but it was not found."
    )


def test_greet_function_returns_correct_value():
    """Priority 1: Import the agent's module and assert runtime behaviour of greet()."""
    spec = importlib.util.spec_from_file_location("hello", HELLO_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "greet"), (
        "The agent's hello.py does not define a top-level function named 'greet'."
    )

    result = asyncio.run(module.greet("World"))
    assert result == "Hello, World!", (
        f"Expected greet('World') to return 'Hello, World!', but got: {result!r}"
    )


def test_output_log_exists():
    """Priority 4 (existence gate): output.log must have been created by running the script."""
    assert os.path.isfile(OUTPUT_LOG), (
        f"Expected /home/user/flyte_project/output.log to exist. "
        "Run `python /home/user/flyte_project/hello.py > /home/user/flyte_project/output.log` first."
    )


def test_output_log_contains_hello():
    """Priority 1 (runtime output): the log produced by executing hello.py must contain 'Hello'."""
    with open(OUTPUT_LOG, "r") as f:
        content = f.read()
    assert "Hello" in content, (
        f"Expected /home/user/flyte_project/output.log to contain 'Hello', "
        f"but got: {content!r}"
    )
