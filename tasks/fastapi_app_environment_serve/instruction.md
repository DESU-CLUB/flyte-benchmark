# Flyte 2.0 FastAPI App Environment

Create a Flyte 2.0 machine learning prediction API at `/home/user/flyte_project/` using `FastAPIAppEnvironment` and `@env.task`.

## Requirements
- Use `flyte.TaskEnvironment` for ML processing tasks
- Create a FastAPI app with `POST /predict` and `GET /health` endpoints
- Use `FastAPIAppEnvironment` from `flyte.app.extras`
- The `/predict` endpoint should process a list of features using an `@env.task`

## Constraints
- Project path: /home/user/flyte_project
- Start command: python /home/user/flyte_project/serve.py
- Port: 8000
