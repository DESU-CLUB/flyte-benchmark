# Flyte 2.0 — Fine-Grained Checkpointing with `@flyte.trace`

## Background

Flyte 2.0 introduces `@flyte.trace`, a decorator for `async def` functions that enables **fine-grained sub-task recovery and automated checkpointing**. When an expensive operation (such as an LLM API call) is wrapped with `@flyte.trace`, Flyte can individually track, checkpoint, and recover that operation without re-running the entire pipeline from scratch. This is critical for LLM pipelines where each API call is costly and failures should not trigger a full retry.

The `@flyte.trace` decorator marks async functions as individually recoverable units inside `@env.task` functions. For local execution, `@flyte.trace` functions behave like normal async functions, but in production Flyte environments they enable sub-task-level checkpointing and replay.

## Requirements

Create the file `/home/user/flyte_project/trace_pipeline.py` that:

1. Creates a `TaskEnvironment` named `"trace-env"`.
2. Defines a `@flyte.trace`-decorated async function `simulate_llm_call` that simulates an expensive LLM API call.
3. Defines a `@flyte.trace`-decorated async function `validate_response` that validates the LLM response.
4. Defines `@env.task` functions `process_prompts` and `llm_pipeline` that orchestrate the traced calls.
5. In `__main__`, runs `llm_pipeline` with a fixed set of prompts and writes the result to `/home/user/flyte_project/trace_result.json`.

## Implementation Guide

### 1. Setup

```python
import asyncio
import json
import flyte
from flyte import TaskEnvironment

env = TaskEnvironment("trace-env")
```

### 2. `@flyte.trace` on `simulate_llm_call`

```python
@flyte.trace
async def simulate_llm_call(prompt: str, call_id: int) -> dict:
    """Simulate an expensive LLM API call — marked for individual checkpointing."""
    return {
        "call_id": call_id,
        "prompt": prompt,
        "response": f"Response to: {prompt}",
        "tokens_used": len(prompt.split()) * 10,
    }
```

`@flyte.trace` is the **key API** here. It wraps the async function to enable Flyte's checkpointing mechanism so that if the pipeline fails mid-execution, individual `simulate_llm_call` invocations that already completed do not need to be re-run.

### 3. `@flyte.trace` on `validate_response`

```python
@flyte.trace
async def validate_response(response: dict) -> dict:
    """Validate the LLM response — individually checkpointed via @flyte.trace."""
    return {
        "call_id": response["call_id"],
        "valid": True,
        "quality_score": min(1.0, response["tokens_used"] / 100),
    }
```

### 4. `process_prompts` task

```python
@env.task
async def process_prompts(prompts: list) -> list:
    results = []
    for i, prompt in enumerate(prompts):
        response = await simulate_llm_call(prompt, i)
        validation = await validate_response(response)
        results.append(validation)
    return results
```

### 5. `llm_pipeline` task

```python
@env.task
async def llm_pipeline(prompts: list) -> dict:
    results = await process_prompts(prompts)
    return {
        "total_prompts": len(prompts),
        "valid_count": sum(1 for r in results if r["valid"]),
        "results": results,
        "traced_calls": len(prompts) * 2,
    }
```

### 6. `__main__` block

```python
if __name__ == "__main__":
    prompts = ["Hello world", "What is Flyte", "Explain async python"]
    result = asyncio.run(llm_pipeline(prompts))
    with open("/home/user/flyte_project/trace_result.json", "w") as f:
        json.dump(result, f)
```

## Constraints

- **Project path**: `/home/user/flyte_project`
- **Script**: `/home/user/flyte_project/trace_pipeline.py`
- **Log file**: `/home/user/flyte_project/trace_result.json`
- Use `@flyte.trace` (not `@env.task`) on `simulate_llm_call` and `validate_response` — these are the checkpointed sub-operations, not top-level tasks.
- Use `@env.task` on `process_prompts` and `llm_pipeline`.
- The `flyte` package is already installed — do **not** reinstall it.
- Use only the standard library plus `flyte`.
