import json
import os
import subprocess
import pytest

PROJECT_DIR = "/home/user/flyte_project"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "trace_pipeline.py")
RESULT_PATH = os.path.join(PROJECT_DIR, "trace_result.json")


def test_trace_pipeline_script_exists():
    """Priority 4 (existence gate): trace_pipeline.py must be present before execution."""
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected /home/user/flyte_project/trace_pipeline.py to exist, but it was not found."
    )


def test_script_runs_without_error():
    """Priority 1: Execute the agent's script and assert it exits cleanly."""
    result = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )
    assert result.returncode == 0, (
        f"python3 trace_pipeline.py exited with code {result.returncode}.\n"
        f"stdout: {result.stdout.strip()}\n"
        f"stderr: {result.stderr.strip()}"
    )


def test_trace_result_json_exists():
    """Priority 4 (existence gate): trace_result.json must exist after running the script."""
    assert os.path.isfile(RESULT_PATH), (
        f"Expected /home/user/flyte_project/trace_result.json to exist after running the script, "
        "but it was not found."
    )


def _load_result() -> dict:
    """Helper: parse the JSON result file produced by the agent's script."""
    with open(RESULT_PATH) as f:
        return json.load(f)


def test_result_is_valid_json():
    """Priority 1 (runtime output): trace_result.json must be parseable JSON."""
    try:
        data = _load_result()
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"trace_result.json is not valid JSON: {exc}\n"
            f"Raw content: {open(RESULT_PATH).read()!r}"
        )
    assert isinstance(data, dict), (
        f"Expected trace_result.json to contain a JSON object, got: {type(data)}"
    )


def test_total_prompts_equals_three():
    """Priority 1 (runtime output): total_prompts must be 3."""
    data = _load_result()
    assert "total_prompts" in data, (
        f"'total_prompts' key missing from trace_result.json. Got keys: {list(data.keys())}"
    )
    assert data["total_prompts"] == 3, (
        f"Expected total_prompts == 3 (3 prompts provided), but got: {data['total_prompts']!r}"
    )


def test_valid_count_equals_three():
    """Priority 1 (runtime output): valid_count must be 3 (all prompts validated successfully)."""
    data = _load_result()
    assert "valid_count" in data, (
        f"'valid_count' key missing from trace_result.json. Got keys: {list(data.keys())}"
    )
    assert data["valid_count"] == 3, (
        f"Expected valid_count == 3 (all 3 responses valid), but got: {data['valid_count']!r}"
    )


def test_traced_calls_equals_six():
    """Priority 1 (runtime output): traced_calls must be 6 (3 prompts × 2 @flyte.trace functions)."""
    data = _load_result()
    assert "traced_calls" in data, (
        f"'traced_calls' key missing from trace_result.json. Got keys: {list(data.keys())}"
    )
    assert data["traced_calls"] == 6, (
        f"Expected traced_calls == 6 (3 prompts × 2 traced functions: simulate_llm_call + validate_response), "
        f"but got: {data['traced_calls']!r}"
    )


def test_results_is_list_of_three():
    """Priority 1 (runtime output): results must be a list of exactly 3 items."""
    data = _load_result()
    assert "results" in data, (
        f"'results' key missing from trace_result.json. Got keys: {list(data.keys())}"
    )
    results = data["results"]
    assert isinstance(results, list), (
        f"Expected 'results' to be a list, got: {type(results)}"
    )
    assert len(results) == 3, (
        f"Expected results to contain exactly 3 items (one per prompt), "
        f"but got {len(results)} items."
    )


def test_all_results_are_valid():
    """Priority 1 (runtime output): every result item must have valid == True."""
    data = _load_result()
    results = data.get("results", [])
    for i, item in enumerate(results):
        assert "valid" in item, (
            f"'valid' field missing from result item at index {i}: {item!r}"
        )
        assert item["valid"] is True, (
            f"Expected result[{i}]['valid'] == True, but got: {item['valid']!r}. "
            f"Full item: {item!r}"
        )


def test_flyte_trace_decorator_appears_at_least_twice():
    """Priority 4 (source-text fallback): @flyte.trace must appear at least twice in trace_pipeline.py.

    No runtime check can distinguish a @flyte.trace-decorated function from a plain async def at
    execution time in local mode, so a syntactic check is the only feasible way to verify that the
    agent actually applied the decorator rather than writing plain async functions.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    count = source.count("@flyte.trace")
    assert count >= 2, (
        f"Expected '@flyte.trace' to appear at least 2 times in trace_pipeline.py "
        f"(once for simulate_llm_call, once for validate_response), "
        f"but found {count} occurrence(s)."
    )


def test_simulate_llm_call_decorated_with_flyte_trace():
    """Priority 4 (source-text fallback): @flyte.trace must appear before simulate_llm_call definition.

    Local execution of @flyte.trace functions is identical to plain async functions, so there is
    no runtime behavioral difference to assert on — only the decorator presence can be checked.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    # Check that @flyte.trace appears before 'async def simulate_llm_call'
    trace_idx = source.find("@flyte.trace")
    func_idx = source.find("async def simulate_llm_call")
    assert trace_idx != -1, (
        "Expected '@flyte.trace' to appear in trace_pipeline.py but it was not found."
    )
    assert func_idx != -1, (
        "Expected 'async def simulate_llm_call' to appear in trace_pipeline.py but it was not found."
    )
    # Find the last @flyte.trace before simulate_llm_call
    trace_positions = []
    search_start = 0
    while True:
        idx = source.find("@flyte.trace", search_start)
        if idx == -1:
            break
        trace_positions.append(idx)
        search_start = idx + 1
    decorated = any(pos < func_idx and source[pos:func_idx].strip().startswith("@flyte.trace") or
                    (pos < func_idx and func_idx - pos < 200)
                    for pos in trace_positions)
    assert decorated, (
        "Expected 'simulate_llm_call' to be decorated with '@flyte.trace' immediately before its definition. "
        "Ensure '@flyte.trace' appears directly above 'async def simulate_llm_call'."
    )


def test_validate_response_decorated_with_flyte_trace():
    """Priority 4 (source-text fallback): @flyte.trace must appear before validate_response definition.

    Local execution of @flyte.trace functions is identical to plain async functions, so there is
    no runtime behavioral difference to assert on — only the decorator presence can be checked.
    """
    with open(SCRIPT_PATH) as f:
        source = f.read()
    func_idx = source.find("async def validate_response")
    assert func_idx != -1, (
        "Expected 'async def validate_response' to appear in trace_pipeline.py but it was not found."
    )
    # Find @flyte.trace occurrences before validate_response
    trace_positions = []
    search_start = 0
    while True:
        idx = source.find("@flyte.trace", search_start)
        if idx == -1:
            break
        trace_positions.append(idx)
        search_start = idx + 1
    decorated = any(pos < func_idx and (func_idx - pos) < 200 for pos in trace_positions)
    assert decorated, (
        "Expected 'validate_response' to be decorated with '@flyte.trace' immediately before its definition. "
        "Ensure '@flyte.trace' appears directly above 'async def validate_response'."
    )
