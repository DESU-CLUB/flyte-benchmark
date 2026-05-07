import asyncio
import json
import flyte

env = flyte.TaskEnvironment("chain-env")


@env.task
async def normalize_text(text: str) -> str:
    return text.lower().strip()


@env.task
async def tokenize(text: str) -> list:
    return text.split(" ")


@env.task
async def count_tokens(tokens: list) -> dict:
    return {"token_count": len(tokens), "unique_count": len(set(tokens))}


@env.task
async def text_analysis_pipeline(raw_text: str) -> dict:
    normalized = await normalize_text(raw_text)
    tokens = await tokenize(normalized)
    counts = await count_tokens(tokens)
    return counts


if __name__ == "__main__":
    result = asyncio.run(text_analysis_pipeline("Hello World Hello Flyte World"))
    with open("/home/user/flyte_project/analysis.json", "w") as f:
        json.dump(result, f)
