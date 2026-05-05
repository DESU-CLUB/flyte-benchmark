import os
import json
import signal
import socket
import subprocess
import time
import urllib.request
import urllib.error
import pytest

PROJECT_DIR = "/home/user/flyte_project"
APP_PY = os.path.join(PROJECT_DIR, "app.py")
SERVE_PY = os.path.join(PROJECT_DIR, "serve.py")
PORT = 8000
SERVER_URL = f"http://localhost:{PORT}"


def wait_for_port(port: int, timeout: int = 30) -> bool:
    """Poll localhost:port until it accepts connections or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex(("localhost", port)) == 0:
                return True
        time.sleep(0.5)
    return False


def http_get(path: str) -> tuple[int, dict]:
    """Perform a GET request; return (status_code, parsed_json_body)."""
    req = urllib.request.Request(f"{SERVER_URL}{path}", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode()) if exc.fp else {}
        return exc.code, body


def http_post_json(path: str, payload: dict) -> tuple[int, dict]:
    """Perform a POST request with a JSON body; return (status_code, parsed_json_body)."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{SERVER_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode()) if exc.fp else {}
        return exc.code, body


@pytest.fixture(scope="module")
def running_server():
    """Start serve.py and wait for port 8000 to be ready, then yield; shut down after."""
    assert os.path.isfile(APP_PY), f"app.py not found at {APP_PY}"
    assert os.path.isfile(SERVE_PY), f"serve.py not found at {SERVE_PY}"

    proc = subprocess.Popen(
        ["python3", SERVE_PY],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    if not wait_for_port(PORT, timeout=30):
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
        stdout = proc.stdout.read().decode() if proc.stdout else ""
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        pytest.fail(
            f"Server did not start on port {PORT} within 30 seconds.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    yield proc

    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


# ── File existence ─────────────────────────────────────────────────────────────

def test_app_py_exists():
    """app.py must exist in the project directory."""
    assert os.path.isfile(APP_PY), f"Expected app.py at {APP_PY}, but it was not found."


def test_serve_py_exists():
    """serve.py must exist in the project directory."""
    assert os.path.isfile(SERVE_PY), f"Expected serve.py at {SERVE_PY}, but it was not found."


# ── Runtime: health endpoint ───────────────────────────────────────────────────

def test_health_returns_200(running_server):
    """GET /health must return HTTP 200."""
    status, _ = http_get("/health")
    assert status == 200, f"Expected HTTP 200 from GET /health, got {status}."


def test_health_response_status_healthy(running_server):
    """GET /health response body must contain status=='healthy'."""
    _, body = http_get("/health")
    assert body.get("status") == "healthy", (
        f"Expected {{\"status\": \"healthy\"}} in /health response, got: {body}"
    )


def test_health_response_service_name(running_server):
    """GET /health response body must contain service=='flyte-ml-api'."""
    _, body = http_get("/health")
    assert body.get("service") == "flyte-ml-api", (
        f"Expected {{\"service\": \"flyte-ml-api\"}} in /health response, got: {body}"
    )


# ── Runtime: predict endpoint — five features ──────────────────────────────────

def test_predict_five_features_returns_200(running_server):
    """POST /predict with five features must return HTTP 200."""
    status, _ = http_post_json("/predict", {"features": [1.0, 2.0, 3.0, 4.0, 5.0]})
    assert status == 200, f"Expected HTTP 200 from POST /predict, got {status}."


def test_predict_five_features_prediction(running_server):
    """POST /predict [1,2,3,4,5] → prediction must equal 3.0."""
    _, body = http_post_json("/predict", {"features": [1.0, 2.0, 3.0, 4.0, 5.0]})
    prediction = body.get("prediction")
    assert prediction == pytest.approx(3.0), (
        f"Expected prediction==3.0 for features [1,2,3,4,5], got: {prediction}. Full body: {body}"
    )


def test_predict_five_features_n_features(running_server):
    """POST /predict [1,2,3,4,5] → n_features must equal 5."""
    _, body = http_post_json("/predict", {"features": [1.0, 2.0, 3.0, 4.0, 5.0]})
    n_features = body.get("n_features")
    assert n_features == 5, (
        f"Expected n_features==5 for features [1,2,3,4,5], got: {n_features}. Full body: {body}"
    )


def test_predict_five_features_status(running_server):
    """POST /predict [1,2,3,4,5] → status must equal 'processed'."""
    _, body = http_post_json("/predict", {"features": [1.0, 2.0, 3.0, 4.0, 5.0]})
    status_val = body.get("status")
    assert status_val == "processed", (
        f"Expected status=='processed', got: {status_val}. Full body: {body}"
    )


# ── Runtime: predict endpoint — two features ───────────────────────────────────

def test_predict_two_features_returns_200(running_server):
    """POST /predict with two features must return HTTP 200."""
    status, _ = http_post_json("/predict", {"features": [10.0, 20.0]})
    assert status == 200, f"Expected HTTP 200 from POST /predict (two features), got {status}."


def test_predict_two_features_prediction(running_server):
    """POST /predict [10, 20] → prediction must equal 15.0."""
    _, body = http_post_json("/predict", {"features": [10.0, 20.0]})
    prediction = body.get("prediction")
    assert prediction == pytest.approx(15.0), (
        f"Expected prediction==15.0 for features [10,20], got: {prediction}. Full body: {body}"
    )


def test_predict_two_features_n_features(running_server):
    """POST /predict [10, 20] → n_features must equal 2."""
    _, body = http_post_json("/predict", {"features": [10.0, 20.0]})
    n_features = body.get("n_features")
    assert n_features == 2, (
        f"Expected n_features==2 for features [10,20], got: {n_features}. Full body: {body}"
    )
