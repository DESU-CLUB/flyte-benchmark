import importlib.util
import json
import os
import subprocess
import sys
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "ml_pipeline.py")
REPORT_PATH = os.path.join(PROJECT_DIR, "experiment_report.json")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load_report() -> dict:
    """Parse the JSON report file produced by the agent's script."""
    with open(REPORT_PATH) as f:
        return json.load(f)


def _load_module():
    """Import ml_pipeline.py as a module so we can inspect its attributes."""
    spec = importlib.util.spec_from_file_location("ml_pipeline", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Priority 4 (existence gate) — file must exist before we try to run it
# ---------------------------------------------------------------------------

def test_ml_pipeline_script_exists():
    """Priority 4 (existence gate): ml_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/ml_pipeline.py to exist, but it was not found."
    )


# ---------------------------------------------------------------------------
# Priority 1 — execute the agent's script and assert runtime behaviour
# ---------------------------------------------------------------------------

def test_script_runs_without_error():
    """Priority 1: Execute the agent's script and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 ml_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


# ---------------------------------------------------------------------------
# Priority 4 (existence gate) — report file must exist after the run
# ---------------------------------------------------------------------------

def test_experiment_report_exists():
    """Priority 4 (existence gate): experiment_report.json must exist after running the script."""
    assert os.path.isfile(REPORT_PATH), (
        f"Expected /home/user/flyte_project/experiment_report.json to exist after running "
        "ml_pipeline.py, but it was not found."
    )


# ---------------------------------------------------------------------------
# Priority 1 — assert on the runtime-written JSON report
# ---------------------------------------------------------------------------

def test_report_is_valid_json():
    """Priority 1 (runtime output): experiment_report.json must be parseable JSON."""
    try:
        data = _load_report()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"experiment_report.json is not valid JSON: {exc}\n"
            f"Raw content: {open(REPORT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected experiment_report.json to contain a JSON object, got: {type(data)}"
    )


def test_report_type_is_model_selection():
    """Priority 1 (runtime output): report_type must equal 'model_selection'."""
    data = _load_report()
    assert "report_type" in data, (
        f"'report_type' key missing from experiment_report.json. Got keys: {list(data.keys())}"
    )
    assert data["report_type"] == "model_selection", (
        f"Expected report_type == 'model_selection', but got: {data['report_type']!r}"
    )


def test_candidates_evaluated_equals_three():
    """Priority 1 (runtime output): candidates_evaluated must be 3 (lr, rf, nn)."""
    data = _load_report()
    assert "candidates_evaluated" in data, (
        f"'candidates_evaluated' key missing from experiment_report.json. Got keys: {list(data.keys())}"
    )
    assert data["candidates_evaluated"] == 3, (
        f"Expected candidates_evaluated == 3, but got: {data['candidates_evaluated']!r}"
    )


def test_accuracy_in_valid_range():
    """Priority 1 (runtime output): accuracy must be > 0.0 and <= 0.99."""
    data = _load_report()
    assert "accuracy" in data, (
        f"'accuracy' key missing from experiment_report.json. Got keys: {list(data.keys())}"
    )
    acc = data["accuracy"]
    assert isinstance(acc, (int, float)), (
        f"Expected accuracy to be a number, got: {type(acc)} ({acc!r})"
    )
    assert acc > 0.0, (
        f"Expected accuracy > 0.0, but got: {acc}"
    )
    assert acc <= 0.99, (
        f"Expected accuracy <= 0.99 (capped by min(0.99, ...)), but got: {acc}"
    )


def test_winner_is_valid_model_type():
    """Priority 1 (runtime output): winner must be one of ['lr', 'rf', 'nn']."""
    data = _load_report()
    assert "winner" in data, (
        f"'winner' key missing from experiment_report.json. Got keys: {list(data.keys())}"
    )
    assert data["winner"] in ("lr", "rf", "nn"), (
        f"Expected winner to be one of ['lr', 'rf', 'nn'], but got: {data['winner']!r}"
    )


def test_winner_is_rf():
    """Priority 1 (runtime output): winner must be 'rf'.

    Accuracy breakdown:
      lr: 0.01 * 100 * 0.1 = 0.10
      rf: 0.1  *  50 * 0.1 = 0.50  ← highest
      nn: 0.001* 200 * 0.1 = 0.02
    The select_best_model task must pick 'rf'.
    """
    data = _load_report()
    assert data.get("winner") == "rf", (
        f"Expected winner == 'rf' (rf has accuracy 0.5, highest among the three configs), "
        f"but got: {data.get('winner')!r}"
    )


# ---------------------------------------------------------------------------
# Priority 1 — import module and inspect train_model.cache at runtime
# ---------------------------------------------------------------------------

def test_train_model_has_flyte_cache():
    """Priority 1 (runtime import): train_model.cache must be an instance of flyte.Cache.

    The @env.task(cache=flyte.Cache(...)) decorator exposes the cache object on
    the decorated task object so the verifier can confirm it was wired correctly.
    """
    import flyte  # already installed in the environment

    mod = _load_module()
    assert hasattr(mod, "train_model"), (
        "Module ml_pipeline.py does not expose a 'train_model' attribute — "
        "make sure it is defined at module level."
    )
    task_obj = mod.train_model
    assert hasattr(task_obj, "cache"), (
        f"train_model object (type={type(task_obj)}) has no 'cache' attribute — "
        "the @env.task(cache=flyte.Cache(...)) decorator must attach the cache to the task."
    )
    assert isinstance(task_obj.cache, flyte.Cache), (
        f"Expected train_model.cache to be an instance of flyte.Cache, "
        f"but got: {type(task_obj.cache)}"
    )


# ---------------------------------------------------------------------------
# Priority 4 (source-text fallback) — parallel pattern verification
# ---------------------------------------------------------------------------

def test_asyncio_gather_used_in_source():
    """Priority 4 (source-text fallback): verify asyncio.gather is used for parallel training.

    No runtime check can distinguish sequential awaits from concurrent gather at the Python-AST
    level, so a syntactic check is the only feasible verification for the parallel pattern.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    assert "asyncio.gather" in source, (
        "Expected 'asyncio.gather' to appear in ml_pipeline.py — "
        "the parallel model training pattern requires asyncio.gather, not sequential awaits."
    )
