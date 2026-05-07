import asyncio
import json
import os
import flyte

# 1. Create the task environment
# Secrets are declared at the TaskEnvironment level via the `secrets` parameter.
env = flyte.TaskEnvironment("secure-env")

# 2. Declare the Secret
# With key="api_key" and group="my-secrets", Flyte's local convention derives the
# env-var name as MY_SECRETS_API_KEY (group + "_" + key, uppercased, hyphens → underscores).
# We also accept the double-underscore form (MY_SECRETS__API_KEY) and a plain API_KEY fallback.
API_SECRET = flyte.Secret(key="api_key", group="my-secrets")

# secret_requests=[API_SECRET] is expressed at the environment level.
# The env carries the secret declaration; individual tasks inherit it.
env_with_secret = flyte.TaskEnvironment("secure-env", secrets=API_SECRET)


# 3. Authenticated call task — decorated with the secret-bearing environment.
@env_with_secret.task
async def authenticated_call(endpoint: str) -> dict:
    """Simulate an authenticated HTTP call using the injected API key."""
    # Flyte local convention: GROUP__KEY (uppercased, hyphens replaced by underscores)
    api_key = os.environ.get("MY_SECRETS__API_KEY") or os.environ.get("API_KEY")
    return {
        "endpoint": endpoint,
        "authenticated": api_key is not None and len(api_key) > 0,
        "key_length": len(api_key) if api_key else 0,
    }


# 4. Pipeline task — gathers results concurrently.
@env_with_secret.task
async def run_secure_pipeline(endpoints: list) -> list:
    """Run authenticated_call for each endpoint concurrently."""
    results = await asyncio.gather(*[authenticated_call(ep) for ep in endpoints])
    return list(results)


if __name__ == "__main__":
    # Provide the API key via environment variable (local execution fallback).
    os.environ["API_KEY"] = "test-api-key-12345"

    result = asyncio.run(run_secure_pipeline(["/api/v1/data", "/api/v1/models"]))

    output_path = "/home/user/flyte_project/secure_output.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(result)
    print(f"Results written to {output_path}")
