import json
from typing import Callable, Dict, List, Tuple

import flyte


env = flyte.TaskEnvironment("agent-env")


@env.task
def add_numbers(a: float, b: float) -> float:
    return a + b


@env.task
def multiply_numbers(a: float, b: float) -> float:
    return a * b


@env.task
def divide_numbers(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@flyte.trace
def select_tool(instruction: str) -> Tuple[Callable[[float, float], float], Tuple[float, float]]:
    lowered = instruction.lower()
    numbers = [float(token) for token in lowered.replace("by", " ").replace("and", " ").split() if token.replace(".", "", 1).isdigit()]
    if len(numbers) != 2:
        raise ValueError(f"Expected two numbers in instruction: {instruction}")
    a, b = numbers

    if "add" in lowered or "sum" in lowered:
        return add_numbers, (a, b)
    if "multiply" in lowered or "product" in lowered:
        return multiply_numbers, (a, b)
    if "divide" in lowered or "quotient" in lowered:
        return divide_numbers, (a, b)

    raise ValueError(f"Unsupported instruction: {instruction}")


def run_agent_loop(instructions: List[str]) -> List[Dict[str, float]]:
    results: List[Dict[str, float]] = []
    for instruction in instructions:
        tool, args = select_tool(instruction)
        result = tool(*args)
        results.append({"instruction": instruction, "result": result})
    return results


def write_results(path: str, payload: List[Dict[str, float]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


if __name__ == "__main__":
    instruction_list = [
        "add 3 and 5",
        "multiply 4 by 6",
        "divide 20 by 4",
    ]
    output = run_agent_loop(instruction_list)
    write_results("/home/user/flyte_project/agent_output.json", output)
