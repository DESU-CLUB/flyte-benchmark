import json
import re

try:
    import flyte
except ImportError:
    # Mock flyte for execution if not installed
    class MockEnv:
        def __init__(self, name):
            self.name = name
        def task(self, fn):
            return fn
            
    class MockFlyte:
        TaskEnvironment = MockEnv
        @staticmethod
        def trace(fn):
            return fn
            
    flyte = MockFlyte()

env = flyte.TaskEnvironment(name="agent-env")

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
def select_tool_and_execute(instruction: str):
    """
    Parses the natural language instruction to select the right tool
    and extracts the numbers to perform the operation.
    """
    instruction_lower = instruction.lower()
    
    # Extract numbers from the instruction
    numbers = [float(x) for x in re.findall(r'-?\d+\.?\d*', instruction)]
    
    if len(numbers) < 2:
        return {"error": f"Need at least two numbers in instruction: '{instruction}'"}
    
    a, b = numbers[0], numbers[1]
    
    if "add" in instruction_lower or "plus" in instruction_lower or "+" in instruction_lower:
        return add_numbers(a=a, b=b)
    elif "multiply" in instruction_lower or "times" in instruction_lower or "*" in instruction_lower:
        return multiply_numbers(a=a, b=b)
    elif "divide" in instruction_lower or "/" in instruction_lower:
        return divide_numbers(a=a, b=b)
    else:
        return {"error": f"Could not determine operation for instruction: '{instruction}'"}

def agent_loop(instructions: list) -> list:
    results = []
    for instr in instructions:
        res = select_tool_and_execute(instr)
        results.append({
            "instruction": instr,
            "result": res
        })
    return results

if __name__ == "__main__":
    instructions = [
        "Add 5 and 3",
        "Multiply 4 by 2.5",
        "Divide 10 by 2",
        "What is 100 plus 200?"
    ]
    
    results = agent_loop(instructions)
    
    output_path = "/home/user/flyte_project/agent_output.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"Agent loop finished. Results written to {output_path}")
