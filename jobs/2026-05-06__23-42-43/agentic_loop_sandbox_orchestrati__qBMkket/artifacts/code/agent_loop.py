"""
Flyte 2.0 Agentic Loop
======================
Processes natural-language math instructions through a traced tool-selection
mechanism backed by Flyte TaskEnvironment tasks, then writes results to
agent_output.json.

Architecture
------------
1.  ``env = flyte.TaskEnvironment(name="agent-env")`` — shared execution env.
2.  Three ``@env.task`` functions implement arithmetic operations:
      • add_numbers(a, b)      → a + b
      • multiply_numbers(a, b) → a × b
      • divide_numbers(a, b)   → a ÷ b  (raises ZeroDivisionError when b == 0)
3.  ``select_tool`` — ``@flyte.trace``-decorated **async** function that parses
    an instruction string and returns the tool name plus extracted operands.
    Being async avoids the syncify-thread deadlock that a sync traced function
    would create when called from inside an async task.
4.  ``agent_loop`` — ``@env.task`` that iterates over instructions, calls
    ``select_tool``, dispatches to the correct math task via ``flyte.run.aio()``,
    and collects typed ``StepResult`` dataclass instances.
5.  ``main()`` — invokes ``agent_loop`` locally (no remote cluster needed),
    builds a JSON summary, and writes it to ``/home/user/flyte_project/agent_output.json``.
"""

from __future__ import annotations

import dataclasses
import json
import re
import time
from pathlib import Path
from typing import Optional

import flyte
from flyte.errors import RuntimeUserError

# ---------------------------------------------------------------------------
# TaskEnvironment
# ---------------------------------------------------------------------------

env = flyte.TaskEnvironment(name="agent-env")

# ---------------------------------------------------------------------------
# Result dataclass  (Flyte serialises dataclasses via msgpack / JSON schema)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class StepResult:
    """Structured result for a single instruction in the agentic loop."""

    step: int
    """1-based position in the instruction list."""

    instruction: str
    """Original natural-language instruction."""

    tool: str
    """Name of the math task that was selected (or '' on parse failure)."""

    a: float
    """First operand extracted from the instruction."""

    b: float
    """Second operand extracted from the instruction."""

    result: Optional[float]
    """Numeric result, or None when an error occurred."""

    status: str
    """'success' | 'error'"""

    error: str
    """Error message, or '' when status is 'success'."""

    timestamp: str
    """ISO-8601 UTC timestamp of when this step was processed."""


# ---------------------------------------------------------------------------
# Math tasks
# ---------------------------------------------------------------------------


@env.task
async def add_numbers(a: float, b: float) -> float:
    """Return the sum of *a* and *b*."""
    result = a + b
    flyte.logger.info(f"add_numbers({a}, {b}) = {result}")
    return result


@env.task
async def multiply_numbers(a: float, b: float) -> float:
    """Return the product of *a* and *b*."""
    result = a * b
    flyte.logger.info(f"multiply_numbers({a}, {b}) = {result}")
    return result


@env.task
async def divide_numbers(a: float, b: float) -> float:
    """Return *a* divided by *b*.

    Raises
    ------
    ZeroDivisionError
        When *b* equals zero.
    """
    if b == 0:
        raise ZeroDivisionError("Division by zero is undefined.")
    result = a / b
    flyte.logger.info(f"divide_numbers({a}, {b}) = {result}")
    return result


# ---------------------------------------------------------------------------
# Tool-selection helper  —  decorated with @flyte.trace
#
# @flyte.trace records timing and I/O for every call into the Flyte action
# trace, giving full observability in the Flyte UI.  The function must be
# **async** so the trace wrapper uses wrapper_async (not wrapper_sync), which
# avoids the syncify-thread deadlock that occurs when a sync traced function is
# called from inside an already-running async task.
# ---------------------------------------------------------------------------

# Keyword patterns that map an instruction to a tool name.
# Order matters: divide first (it's more specific), then multiply, then add.
# Each pattern uses word-boundary anchors and partial-word prefixes so that
# inflected forms ("divides", "multiplied", "adds") are also matched.
_TOOL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # divide / divided / divides / division / over / quotient / ratio
    (
        re.compile(r"\b(divid\w*|over|quotient|ratio)\b", re.IGNORECASE),
        "divide_numbers",
    ),
    # multiply / multiplied / multiplies / times / product
    (
        re.compile(r"\b(multipl\w*|times|product)\b", re.IGNORECASE),
        "multiply_numbers",
    ),
    # add / added / addition / plus / sum / and
    (
        re.compile(r"\b(add\w*|plus|sum|and)\b", re.IGNORECASE),
        "add_numbers",
    ),
]

# Regex that captures the first two numeric tokens (integers or decimals)
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _pick_tool(instruction: str) -> str:
    """Return the best-matching tool name for *instruction*.

    Scans keyword patterns in priority order: add → multiply → divide.
    Falls back to ``"add_numbers"`` when no keyword matches.
    """
    for pattern, tool_name in _TOOL_PATTERNS:
        if pattern.search(instruction):
            return tool_name
    return "add_numbers"


def _parse_numbers(instruction: str) -> tuple[float, float]:
    """Extract the first two numbers from *instruction*.

    Raises
    ------
    ValueError
        When fewer than two numeric tokens are found.
    """
    matches = _NUMBER_RE.findall(instruction)
    if len(matches) < 2:
        raise ValueError(
            f"Could not find two numbers in instruction: {instruction!r}"
        )
    return float(matches[0]), float(matches[1])


@flyte.trace
async def select_tool(instruction: str) -> dict:
    """Parse *instruction* and return a tool-call descriptor dict.

    The returned dict has the shape::

        {
            "tool":   "<tool_name>",
            "a":      <float>,
            "b":      <float>,
            "reason": "<explanation>",
        }

    Decorated with ``@flyte.trace`` so every invocation is recorded in the
    parent task's action trace (timing, inputs, outputs).
    """
    tool_name = _pick_tool(instruction)
    a, b = _parse_numbers(instruction)
    return {
        "tool": tool_name,
        "a": a,
        "b": b,
        "reason": (
            f"Matched '{tool_name}' from keyword scan; "
            f"extracted operands a={a}, b={b}."
        ),
    }


# ---------------------------------------------------------------------------
# Agent loop task
# ---------------------------------------------------------------------------

_TOOL_MAP = {
    "add_numbers": add_numbers,
    "multiply_numbers": multiply_numbers,
    "divide_numbers": divide_numbers,
}


@env.task
async def agent_loop(instructions: list[str]) -> list[StepResult]:
    """Process each natural-language math instruction and return results.

    For every instruction the loop:

    1. Calls ``select_tool`` (``@flyte.trace``) to choose a math task.
    2. Dispatches to the chosen task via ``await flyte.run.aio()``.
    3. Retrieves the numeric output via ``await run.outputs.aio()``.
    4. Packages everything into a ``StepResult`` dataclass.

    Parameters
    ----------
    instructions:
        Natural-language math strings, e.g. ``"Add 3 and 5"``.

    Returns
    -------
    list[StepResult]
        One result per instruction, in order.
    """
    results: list[StepResult] = []

    for idx, instruction in enumerate(instructions, start=1):
        flyte.logger.info(f"[{idx}/{len(instructions)}] {instruction!r}")
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Default values filled in on error paths
        tool_name = ""
        a: float = 0.0
        b: float = 0.0
        value: Optional[float] = None
        status = "error"
        error_msg = ""

        try:
            # ── Step 1: tool selection (traced) ──────────────────────────────
            tool_call: dict = await select_tool(instruction)
            tool_name = tool_call["tool"]
            a = tool_call["a"]
            b = tool_call["b"]
            flyte.logger.info(f"  → tool={tool_name}  a={a}  b={b}")

            # ── Step 2: execute the chosen task ──────────────────────────────
            task_fn = _TOOL_MAP[tool_name]
            run = await flyte.run.aio(task_fn, a, b)
            outputs = await run.outputs.aio()
            value = outputs.o0

            status = "success"
            flyte.logger.info(f"  ✓ result={value}")

        except ZeroDivisionError as exc:
            error_msg = f"ZeroDivisionError: {exc}"
            flyte.logger.warning(f"  ✗ {error_msg}")

        except RuntimeUserError as exc:
            # Flyte wraps task-level exceptions in RuntimeUserError when a
            # sub-task raises (e.g. ZeroDivisionError inside divide_numbers).
            error_msg = f"RuntimeUserError: {exc}"
            flyte.logger.warning(f"  ✗ {error_msg}")

        except ValueError as exc:
            error_msg = f"ValueError: {exc}"
            flyte.logger.warning(f"  ✗ {error_msg}")

        except Exception as exc:  # pragma: no cover – unexpected failures
            error_msg = f"{type(exc).__name__}: {exc}"
            flyte.logger.error(f"  ✗ Unexpected: {error_msg}")

        results.append(
            StepResult(
                step=idx,
                instruction=instruction,
                tool=tool_name,
                a=a,
                b=b,
                result=value,
                status=status,
                error=error_msg,
                timestamp=ts,
            )
        )

    return results


# ---------------------------------------------------------------------------
# Instructions & output path
# ---------------------------------------------------------------------------

INSTRUCTIONS: list[str] = [
    "Add 15 and 27",
    "Multiply 8 by 9",
    "Divide 100 by 4",
    "What is the sum of 42 and 58?",
    "Calculate the product of 12 and 7",
    "Divide 50 by 0",        # intentional ZeroDivisionError
    "Multiply 3.5 times 2.0",
    "Add 1000 and 999",
    "Divide 81 by 9",
    "What is 6 plus 14?",
]

OUTPUT_PATH = Path("/home/user/flyte_project/agent_output.json")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the agent loop locally and write results to *OUTPUT_PATH*."""
    print("=" * 62)
    print("  Flyte 2.0 Agentic Loop  —  starting")
    print(f"  Processing {len(INSTRUCTIONS)} instructions …")
    print("=" * 62)

    # ── Run the top-level agent_loop task locally ────────────────────────────
    run = flyte.run(agent_loop, INSTRUCTIONS)
    outputs = run.outputs()
    step_results: list[StepResult] = outputs.o0

    # ── Build JSON payload ───────────────────────────────────────────────────
    n_ok = sum(1 for r in step_results if r.status == "success")
    n_err = sum(1 for r in step_results if r.status == "error")

    payload = {
        "run_metadata": {
            "flyte_version": flyte.__version__,
            "environment": env.name,
            "total_instructions": len(INSTRUCTIONS),
            "succeeded": n_ok,
            "failed": n_err,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "results": [
            {
                "step": r.step,
                "instruction": r.instruction,
                "tool": r.tool,
                "operands": {"a": r.a, "b": r.b},
                "result": r.result,
                "status": r.status,
                "error": r.error,
                "timestamp": r.timestamp,
            }
            for r in step_results
        ],
    }

    # ── Write JSON output ────────────────────────────────────────────────────
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"\n{'=' * 62}")
    print(f"  Done.  {n_ok} succeeded, {n_err} failed.")
    print(f"  Results written → {OUTPUT_PATH}")
    print("=" * 62)

    # ── Pretty-print summary table ───────────────────────────────────────────
    print(
        f"\n{'Step':<5} {'Tool':<20} {'a':>8} {'b':>8}  "
        f"{'Result':>12}  {'Status'}"
    )
    print("-" * 70)
    for r in step_results:
        result_str = f"{r.result:>12.4f}" if r.result is not None else f"{'—':>12}"
        print(
            f"{r.step:<5} {r.tool or '—':<20} {r.a:>8.2f} {r.b:>8.2f}  "
            f"{result_str}  {r.status}"
            + (f"  [{r.error}]" if r.error else "")
        )


if __name__ == "__main__":
    main()
