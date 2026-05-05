import flyte
import json
import os
import re

# 1. Use flyte.TaskEnvironment named "agent-env"
env = flyte.TaskEnvironment(name="agent-env")

# 2. Implement add_numbers, multiply_numbers, and divide_numbers as @env.task functions
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

# 3. Implement a tool selection mechanism using @flyte.trace
@flyte.trace
def select_tool(instruction: str):
    instruction = instruction.lower()
    if "add" in instruction or "plus" in instruction or "sum" in instruction:
        return "add"
    elif "multiply" in instruction or "times" in instruction or "product" in instruction:
        return "multiply"
    elif "divide" in instruction or "divided by" in instruction:
        return "divide"
    else:
        return None

@flyte.trace
def extract_numbers(instruction: str):
    # Simple extraction for demo purposes
    # Matches integers and floats
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", instruction)
    return [float(n) for n in nums]

# 4. Build an agent loop that processes a list of instructions and returns results
def run_agent_loop(instructions):
    results = []
    for instruction in instructions:
        tool = select_tool(instruction)
        nums = extract_numbers(instruction)
        
        result_entry = {
            "instruction": instruction,
            "tool_selected": tool,
            "inputs": nums,
            "result": None,
            "error": None
        }
        
        if tool:
            if len(nums) >= 2:
                try:
                    if tool == "add":
                        result_entry["result"] = add_numbers(nums[0], nums[1])
                    elif tool == "multiply":
                        result_entry["result"] = multiply_numbers(nums[0], nums[1])
                    elif tool == "divide":
                        result_entry["result"] = divide_numbers(nums[0], nums[1])
                except Exception as e:
                    result_entry["error"] = str(e)
            else:
                result_entry["error"] = "Insufficient numbers found in instruction"
        else:
            result_entry["error"] = "Could not determine tool from instruction"
            
        results.append(result_entry)
    return results

if __name__ == "__main__":
    instructions = [
        "Add 5 and 10",
        "Multiply 3 by 7",
        "Divide 20 by 4",
        "What is 100 divided by 5?",
        "Sum 1.5 and 2.5",
        "Multiply 10 and 10",
        "Divide 10 by 0"
    ]
    
    print("Starting agent loop...")
    output_results = run_agent_loop(instructions)
    
    # 5. Write output to /home/user/flyte_project/agent_output.json
    output_path = "/home/user/flyte_project/agent_output.json"
    with open(output_path, "w") as f:
        json.dump(output_results, f, indent=4)
    
    print(f"Agent loop completed. Results written to {output_path}")
    for res in output_results:
        status = "Success" if res["error"] is None else f"Error: {res['error']}"
        print(f"Instruction: '{res['instruction']}' -> {status} (Result: {res['result']})")
