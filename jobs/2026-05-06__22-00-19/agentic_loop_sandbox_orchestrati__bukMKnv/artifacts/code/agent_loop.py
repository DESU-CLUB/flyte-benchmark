import flyte
import json
import asyncio
import re
import os

# 1. Use flyte.TaskEnvironment named "agent-env"
env = flyte.TaskEnvironment(name="agent-env")

# 2. Implement add_numbers, multiply_numbers, and divide_numbers as @env.task functions
@env.task
async def add_numbers(a: float, b: float) -> float:
    return a + b

@env.task
async def multiply_numbers(a: float, b: float) -> float:
    return a * b

@env.task
async def divide_numbers(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# 3. Implement a tool selection mechanism using @flyte.trace
@flyte.trace
def select_tool(instruction: str):
    """
    Selects the appropriate tool and extracts numbers from the instruction.
    """
    instruction_lower = instruction.lower()
    
    # Simple regex to find numbers
    numbers = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", instruction)]
    
    if "add" in instruction_lower or "plus" in instruction_lower or "sum" in instruction_lower:
        return "add", numbers
    elif "multiply" in instruction_lower or "times" in instruction_lower or "product" in instruction_lower:
        return "multiply", numbers
    elif "divide" in instruction_lower or "ratio" in instruction_lower:
        return "divide", numbers
    else:
        return None, numbers

# 4. Build an agent loop that processes a list of instructions and returns results
async def agent_loop(instructions: list[str]):
    results = []
    for instruction in instructions:
        tool_name, args = select_tool(instruction)
        
        result_entry = {
            "instruction": instruction,
            "tool": tool_name,
            "result": None,
            "error": None
        }
        
        try:
            if tool_name == "add":
                if len(args) >= 2:
                    result_entry["result"] = await add_numbers(a=args[0], b=args[1])
                else:
                    result_entry["error"] = "Insufficient arguments for addition"
            elif tool_name == "multiply":
                if len(args) >= 2:
                    result_entry["result"] = await multiply_numbers(a=args[0], b=args[1])
                else:
                    result_entry["error"] = "Insufficient arguments for multiplication"
            elif tool_name == "divide":
                if len(args) >= 2:
                    result_entry["result"] = await divide_numbers(a=args[0], b=args[1])
                else:
                    result_entry["error"] = "Insufficient arguments for division"
            else:
                result_entry["error"] = f"No tool found for instruction: {instruction}"
        except Exception as e:
            result_entry["error"] = str(e)
            
        results.append(result_entry)
        
    return results

# 5. Write output to /home/user/flyte_project/agent_output.json
async def main():
    instructions = [
        "Add 5 and 10",
        "Multiply 3 by 4",
        "Divide 20 by 5",
        "What is the sum of 100 and 200?",
        "Divide 10 by 0",
        "Multiply 7 and 6",
        "Just a random sentence with no math."
    ]
    
    print("Starting agent loop...")
    results = await agent_loop(instructions)
    
    output_path = "/home/user/flyte_project/agent_output.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"Results written to {output_path}")
    for res in results:
        status = "SUCCESS" if res["error"] is None else "FAILED"
        print(f"[{status}] {res['instruction']} -> {res['result'] if res['error'] is None else res['error']}")

if __name__ == "__main__":
    asyncio.run(main())
