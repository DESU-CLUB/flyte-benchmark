import importlib.util
import json
import os
import subprocess
import sys
import pytest

PROJECT_DIR = "/home/user/flyte_project"
IMAGE_CONFIG_PY = os.path.join(PROJECT_DIR, "image_config.py")
MODEL_CONFIG_JSON = os.path.join(PROJECT_DIR, "model_config.json")


def test_image_config_py_exists():
    """Priority 4 (existence gate): image_config.py must be present before we can run it."""
    assert os.path.isfile(IMAGE_CONFIG_PY), (
        f"Expected /home/user/flyte_project/image_config.py to exist, but it was not found."
    )


def test_image_config_runs_successfully():
    """Priority 1: Run the agent's image_config.py and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", IMAGE_CONFIG_PY],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"Running image_config.py failed with returncode {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_model_config_json_exists():
    """Priority 4 (existence gate): model_config.json must have been written by the script."""
    assert os.path.isfile(MODEL_CONFIG_JSON), (
        f"Expected /home/user/flyte_project/model_config.json to exist after running "
        "image_config.py, but it was not found."
    )


def test_model_type_is_logistic_regression():
    """Priority 1: Parse JSON output and assert model_type == 'logistic_regression'."""
    with open(MODEL_CONFIG_JSON) as f:
        data = json.load(f)

    model_type = data.get("model_type")
    assert model_type == "logistic_regression", (
        f"Expected model_type == 'logistic_regression', got: {model_type!r}"
    )


def test_n_samples_is_100():
    """Priority 1: Parse JSON output and assert n_samples == 100."""
    with open(MODEL_CONFIG_JSON) as f:
        data = json.load(f)

    n_samples = data.get("n_samples")
    assert n_samples == 100, (
        f"Expected n_samples == 100, got: {n_samples!r}"
    )


def test_n_features_is_5():
    """Priority 1: Parse JSON output and assert n_features == 5."""
    with open(MODEL_CONFIG_JSON) as f:
        data = json.load(f)

    n_features = data.get("n_features")
    assert n_features == 5, (
        f"Expected n_features == 5, got: {n_features!r}"
    )


def test_model_env_is_production():
    """Priority 1: Parse JSON output and assert model_env == 'production'."""
    with open(MODEL_CONFIG_JSON) as f:
        data = json.load(f)

    model_env = data.get("model_env")
    assert model_env == "production", (
        f"Expected model_env == 'production', got: {model_env!r}"
    )


def _load_image_config_module():
    """Helper: load image_config.py as a module without executing __main__ block."""
    spec = importlib.util.spec_from_file_location("image_config", IMAGE_CONFIG_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_env_image_is_not_none():
    """Priority 1: Import image_config module and assert env.image is not None."""
    mod = _load_image_config_module()
    env = getattr(mod, "env", None)
    assert env is not None, (
        "Expected module-level variable 'env' (TaskEnvironment) to be defined in image_config.py."
    )
    image = getattr(env, "image", None)
    assert image is not None, (
        "Expected env.image to be set (not None) — the TaskEnvironment must have an image configured."
    )


def test_image_has_pandas_and_sklearn_pip_packages():
    """Priority 1: Import image_config module and assert image has 'pandas' and 'scikit-learn'
    in its pip packages via env.image._pip_packages.
    Priority 4 fallback (source text): used when _pip_packages attribute is unavailable."""
    mod = _load_image_config_module()
    env = getattr(mod, "env", None)
    assert env is not None, (
        "Expected module-level variable 'env' (TaskEnvironment) to be defined in image_config.py."
    )
    image = getattr(env, "image", None)
    assert image is not None, (
        "Expected env.image to be set (not None)."
    )

    pip_packages = getattr(image, "_pip_packages", None)
    if pip_packages is not None:
        # Runtime attribute check: verify pip packages are declared on the Image object
        assert "pandas" in pip_packages, (
            f"Expected 'pandas' in env.image._pip_packages, got: {pip_packages}"
        )
        assert "scikit-learn" in pip_packages, (
            f"Expected 'scikit-learn' in env.image._pip_packages, got: {pip_packages}"
        )
    else:
        # Priority 4 fallback: _pip_packages attribute is not available on this Image implementation;
        # fall back to source-text inspection as the only remaining option.
        with open(IMAGE_CONFIG_PY) as f:
            source = f.read()
        assert "pandas" in source, (
            "Expected 'pandas' to appear in image_config.py (pip package declaration)."
        )
        assert "scikit-learn" in source, (
            "Expected 'scikit-learn' to appear in image_config.py (pip package declaration)."
        )
