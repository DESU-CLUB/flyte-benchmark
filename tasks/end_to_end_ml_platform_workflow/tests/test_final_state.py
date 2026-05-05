import importlib.util
import json
import os
import subprocess
import sys

import pytest


PROJECT_DIR = "/home/user/flyte_project"
OUTPUT_FILE = os.path.join(PROJECT_DIR, "platform_output.json")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load_module(name: str, filepath: str):
    """Load a Python source file as a module without executing __main__."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Priority 3: file-existence checks (no CLI can verify file presence)
# ---------------------------------------------------------------------------

def test_config_py_exists():
    path = os.path.join(PROJECT_DIR, "config.py")
    assert os.path.isfile(path), f"config.py not found at {path}"


def test_data_tasks_py_exists():
    path = os.path.join(PROJECT_DIR, "data_tasks.py")
    assert os.path.isfile(path), f"data_tasks.py not found at {path}"


def test_model_tasks_py_exists():
    path = os.path.join(PROJECT_DIR, "model_tasks.py")
    assert os.path.isfile(path), f"model_tasks.py not found at {path}"


def test_orchestrator_py_exists():
    path = os.path.join(PROJECT_DIR, "orchestrator.py")
    assert os.path.isfile(path), f"orchestrator.py not found at {path}"


def test_main_py_exists():
    path = os.path.join(PROJECT_DIR, "main.py")
    assert os.path.isfile(path), f"main.py not found at {path}"


# ---------------------------------------------------------------------------
# Priority 1: run main.py and assert on runtime behaviour
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pipeline_output():
    """Run main.py once for the whole module and return the parsed JSON output."""
    result = subprocess.run(
        ["python3", os.path.join(PROJECT_DIR, "main.py")],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 main.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert os.path.isfile(OUTPUT_FILE), (
        f"platform_output.json was not created at {OUTPUT_FILE}"
    )
    with open(OUTPUT_FILE) as f:
        return json.load(f)


def test_output_file_exists(pipeline_output):
    """platform_output.json must be present after running main.py."""
    assert os.path.isfile(OUTPUT_FILE), (
        f"platform_output.json not found at {OUTPUT_FILE}"
    )


def test_pipeline_complete(pipeline_output):
    assert pipeline_output.get("pipeline_complete") is True, (
        f"Expected pipeline_complete==True, got: {pipeline_output.get('pipeline_complete')}"
    )


def test_sources_ingested(pipeline_output):
    assert pipeline_output.get("sources_ingested") == 2, (
        f"Expected sources_ingested==2, got: {pipeline_output.get('sources_ingested')}"
    )


def test_models_trained(pipeline_output):
    assert pipeline_output.get("models_trained") == 2, (
        f"Expected models_trained==2, got: {pipeline_output.get('models_trained')}"
    )


def test_total_samples(pipeline_output):
    assert pipeline_output.get("total_samples") == 200, (
        f"Expected total_samples==200 (100 per source × 2 sources), "
        f"got: {pipeline_output.get('total_samples')}"
    )


def test_best_model_present(pipeline_output):
    best = pipeline_output.get("best_model")
    assert best is not None, "Expected 'best_model' to be present in output, got None"
    assert "model_type" in best, (
        f"Expected 'model_type' field in best_model, got keys: {list(best.keys())}"
    )


# ---------------------------------------------------------------------------
# Priority 1: import config.py and inspect live objects
# ---------------------------------------------------------------------------

def test_config_data_env_cpu():
    """data_env.resources.cpu must equal 2."""
    config = _load_module("config", os.path.join(PROJECT_DIR, "config.py"))
    assert hasattr(config, "data_env"), "config.py must define 'data_env'"
    cpu = config.data_env.resources.cpu
    assert cpu == 2, (
        f"Expected data_env.resources.cpu==2, got: {cpu}"
    )


def test_config_model_env_cpu():
    """model_env.resources.cpu must equal 8."""
    config = _load_module("config", os.path.join(PROJECT_DIR, "config.py"))
    assert hasattr(config, "model_env"), "config.py must define 'model_env'"
    cpu = config.model_env.resources.cpu
    assert cpu == 8, (
        f"Expected model_env.resources.cpu==8, got: {cpu}"
    )


# ---------------------------------------------------------------------------
# Priority 1: import data_tasks.py and inspect ingest_data.cache
# ---------------------------------------------------------------------------

def test_ingest_data_cache_is_flyte_cache():
    """ingest_data.cache must be an instance of flyte.Cache."""
    import flyte  # already installed in the image

    # Ensure PROJECT_DIR is on sys.path so relative imports inside the module work
    if PROJECT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_DIR)

    data_tasks = _load_module(
        "data_tasks", os.path.join(PROJECT_DIR, "data_tasks.py")
    )
    assert hasattr(data_tasks, "ingest_data"), (
        "data_tasks.py must define 'ingest_data'"
    )
    cache_attr = getattr(data_tasks.ingest_data, "cache", None)
    assert cache_attr is not None, (
        "ingest_data must have a 'cache' attribute set to a flyte.Cache instance"
    )
    assert isinstance(cache_attr, flyte.Cache), (
        f"Expected ingest_data.cache to be flyte.Cache, got: {type(cache_attr)}"
    )
