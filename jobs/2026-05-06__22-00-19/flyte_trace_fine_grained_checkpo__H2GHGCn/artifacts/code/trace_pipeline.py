import asyncio
import json
import flyte
from flyte import TaskEnvironment

env = TaskEnvironment("trace-env")

@flyte.trace
async def simulate_llm_call(prompt: str, call_id: int) -> dict:
    """Simulate an expensive LLM API call — marked for individual checkpointing."""
    return {
        "call_id": call_id,
        "prompt": prompt,
        "response": f"Response to: {prompt}",
        "tokens_used": len(prompt.split()) * 10,
    }

@flyte.trace
async def validate_response(response: dict) -> dict:
    """Validate the LLM response — individually checkpointed via @flyte.trace."""
    return {
        "call_id": response["call_id"],
        "valid": True,
        "quality_score": min(1.0, response["tokens_used"] / 100),
    }

@env.task
async def process_prompts(prompts: list) -> list:
    results = []
    for i, prompt in enumerate(prompts):
        response = await simulate_llm_call(prompt, i)
        validation = await validate_response(response)
        results.append(validation)
    return results

@env.task
async def llm_pipeline(prompts: list) -> dict:
    results = await process_prompts(prompts)
    return {
        "total_prompts": len(prompts),
        "valid_count": sum(1 for r in results if r["valid"]),
        "results": results,
        "traced_calls": len(prompts) * 2,
    }

if __name__ == "__main__":
    prompts = ["Hello world", "What is Flyte", "Explain async python"]
    result = asyncio.run(llm_pipeline(prompts))
    with open("/home/user/flyte_project/trace_result.json", "w") as f:
        json.dump(result, f, indent=4)
