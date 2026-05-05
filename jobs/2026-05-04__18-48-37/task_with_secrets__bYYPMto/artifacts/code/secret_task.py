import asyncio
import json
import os
import flyte

# 2. Declare the Secret
API_SECRET = flyte.Secret(key="api_key", group="my-secrets")

# 1. Create the task environment with the secret
env = flyte.TaskEnvironment("secure-env", secrets=[API_SECRET])

# 3. Authenticated call task
@env.task
async def authenticated_call(endpoint: str) -> dict:
    # Flyte local convention: GROUP__KEY (uppercased, hyphens replaced by underscores)
    api_key = os.environ.get("MY_SECRETS__API_KEY") or os.environ.get("API_KEY")
    return {
        "endpoint": endpoint,
        "authenticated": api_key is not None and len(api_key) > 0,
        "key_length": len(api_key) if api_key else 0,
    }

# 4. Pipeline task
@env.task
async def run_secure_pipeline(endpoints: list) -> list:
    results = await asyncio.gather(*[authenticated_call(ep) for ep in endpoints])
    return list(results)

if __name__ == "__main__":
    os.environ["API_KEY"] = "test-api-key-12345"
    result = asyncio.run(run_secure_pipeline(["/api/v1/data", "/api/v1/models"]))
    with open("/home/user/flyte_project/secure_output.json", "w") as f:
        json.dump(result, f)
    print(result)
