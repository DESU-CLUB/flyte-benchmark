import importlib.util
import json
import os
import subprocess
import sys
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "checkpoint_pipeline.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "checkpoint_result.json")


def test_checkpoint_pipeline_script_exists():
    """Priority 4 (existence gate): checkpoint_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/checkpoint_pipeline.py to exist, but it was not found."
    )


def test_script_runs_without_error():
    """Priority 1: Execute the agent's script and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 checkpoint_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_result_json_exists():
    """Priority 4 (existence gate): checkpoint_result.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/checkpoint_result.json to exist after running the "
        "script, but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json():
    """Priority 1 (runtime output): checkpoint_result.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"checkpoint_result.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected checkpoint_result.json to contain a JSON object, got: {type(data)}"
    )


def test_n_batches_equals_three():
    """Priority 1 (runtime output): n_batches must be 3."""
    data = _load_result()
    assert "n_batches" in data, (
        f"'n_batches' key missing from checkpoint_result.json. Got keys: {list(data.keys())}"
    )
    assert data["n_batches"] == 3, (
        f"Expected n_batches == 3, but got: {data['n_batches']!r}"
    )


def test_total_items_equals_thirty():
    """Priority 1 (runtime output): total_items must be 30 (3 batches × 10 items each)."""
    data = _load_result()
    assert "total_items" in data, (
        f"'total_items' key missing from checkpoint_result.json. Got keys: {list(data.keys())}"
    )
    assert data["total_items"] == 30, (
        f"Expected total_items == 30 (3 batches × 10 items), but got: {data['total_items']!r}"
    )


def test_checkpointed_flag_is_true():
    """Priority 1 (runtime output): checkpointed must be True in the result."""
    data = _load_result()
    assert "checkpointed" in data, (
        f"'checkpointed' key missing from checkpoint_result.json. Got keys: {list(data.keys())}"
    )
    assert data["checkpointed"] is True, (
        f"Expected checkpointed == True, but got: {data['checkpointed']!r}"
    )


def test_batch_ids_correct():
    """Priority 1 (runtime output): batch_ids must be [0, 1, 2]."""
    data = _load_result()
    assert "batch_ids" in data, (
        f"'batch_ids' key missing from checkpoint_result.json. Got keys: {list(data.keys())}"
    )
    assert data["batch_ids"] == [0, 1, 2], (
        f"Expected batch_ids == [0, 1, 2], but got: {data['batch_ids']!r}"
    )


def test_fetch_batch_has_trace_decoration():
    """Priority 1 / Priority 4 fallback: verify fetch_batch is decorated with @flyte.trace.

    First attempts to import the module and check for __wrapped__ (set by functools.wraps-based
    decorators). Falls back to source-text check if __wrapped__ is absent, since @flyte.trace
    may not expose __wrapped__ in all versions.
    """
    spec = importlib.util.spec_from_file_location("checkpoint_pipeline", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        fetch_batch_fn = getattr(module, "fetch_batch", None)
        assert fetch_batch_fn is not None, (
            "Expected 'fetch_batch' to be defined in checkpoint_pipeline.py, but it was not found."
        )
        if hasattr(fetch_batch_fn, "__wrapped__"):
            # __wrapped__ is present — decoration confirmed via introspection.
            return
    except Exception:
        # If module import fails for any reason, fall through to source-text check.
        pass

    # Priority 4 fallback: no runtime introspection available; check source text.
    # @flyte.trace is the sole Flyte 2.0 checkpoint primitive and has no CLI inspector.
    with open(SCRIPT_PATH) as f:
        source = f.read()
    assert "@flyte.trace" in source, (
        "Expected '@flyte.trace' decorator to appear in checkpoint_pipeline.py — "
        "this is the Flyte 2.0 primitive required for checkpointing fetch_batch."
    )
