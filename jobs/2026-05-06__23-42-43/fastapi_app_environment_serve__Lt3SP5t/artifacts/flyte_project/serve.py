"""
serve.py — Entry point for the Flyte 2.0 ML Prediction API
============================================================
Start command:  python /home/user/flyte_project/serve.py

This module imports the ``FastAPIAppEnvironment`` (``app_env``) defined in
``app.py`` and serves it locally on port 8000 using Flyte's ``serve``
context manager.

When run directly (not inside the Flyte control-plane) the ``mode="local"``
argument tells Flyte to start the underlying uvicorn/FastAPI server in this
process instead of deploying to a remote cluster.
"""
from __future__ import annotations

import asyncio
import logging

import uvicorn

# Import the FastAPIAppEnvironment and the raw FastAPI instance.
# The TaskEnvironment (env) and predict_task are registered implicitly
# when app.py is imported.
from app import app_env, fastapi_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

PORT: int = 8000
HOST: str = "0.0.0.0"


async def _main() -> None:
    """
    Start the FastAPI server.

    Two strategies are attempted in order:

    1. **Flyte-native serving** — call ``flyte.serve(app_env, mode="local")``
       so that Flyte's ``_fastapi_app_server`` coroutine drives uvicorn.
       This is the idiomatic path when running inside a Flyte app container.

    2. **Direct uvicorn fallback** — if Flyte's local-serve infrastructure is
       unavailable (e.g. missing init config outside of a Flyte cluster), start
       uvicorn directly using the ``fastapi_app`` ASGI application from
       ``FastAPIAppEnvironment.app``.  The port is always taken from
       ``app_env.port.port`` (8000) so both paths bind on the same port.
    """
    port: int = app_env.port.port  # resolves to 8000

    try:
        import flyte

        logger.info(
            "Starting ML Prediction API via flyte.serve (local mode) on port %d …", port
        )
        # flyte.serve returns a _LocalApp handle when mode="local".
        # We keep a reference but don't need to await it here — uvicorn is
        # already running inside a background thread started by flyte.serve.
        local_app = flyte.serve(app_env, mode="local")

        # Block until the server thread exits (Ctrl-C / SIGTERM clean up via
        # Flyte's registered atexit / signal handlers).
        if local_app._thread is not None:
            # Run a simple polling loop so the event loop stays alive for
            # async code that may be scheduled (e.g. lifespan handlers).
            while local_app._thread.is_alive():
                await asyncio.sleep(1)

    except Exception as exc:  # pragma: no cover
        logger.warning(
            "flyte.serve raised %s — falling back to direct uvicorn.", exc
        )
        config = uvicorn.Config(
            app=fastapi_app,
            host=HOST,
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()


if __name__ == "__main__":
    asyncio.run(_main())
