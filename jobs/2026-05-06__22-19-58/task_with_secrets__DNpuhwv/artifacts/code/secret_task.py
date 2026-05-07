import asyncio
import json
import os

import flyte


env = flyte.TaskEnvironment("secure-env")

API_SECRET = flyte.Secret(key="api_key", group="my-secrets")


@env.task(secret_requests=[API_SECRET])
async def authenticated_call(endpoint: str) -> dict:
    api_key = os.environ.get("MY_SECRETS__API_KEY") or os.environ.get("API_KEY")
    return {
        "endpoint": endpoint,
        "authenticated": api_key is not None and len(api_key) > 0,
        "key_length": len(api_key) if api_key else 0,
    }


@env.task
async def run_secure_pipeline(endpoints: list) -> list:
    results = await asyncio.gather(*[authenticated_call(endpoint) for endpoint in endpoints])
    return list(results)


if __name__ == "__main__":
    os.environ["API_KEY"] = "test-api-key-12345"
    result = asyncio.run(run_secure_pipeline(["/api/v1/data", "/api/v1/models"]))
    with open("/home/user/flyte_project/secure_output.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle)
    print(result)
