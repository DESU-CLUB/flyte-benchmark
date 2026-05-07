"""
Flyte 2.0 Agentic Loop for Math Operations (Standalone Version)

This module implements an agentic loop that can execute math operations
based on natural language instructions. This standalone version can run
without Flyte dependencies for testing purposes.

The structure is Flyte 2.0 compatible and can be easily converted to
use actual Flyte task decorators when flytekit is available.
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


# Check if flytekit is available
try:
    import flytekit
    from flytekit.types.json import JSON
    FLYTEKIT_AVAILABLE = True
except ImportError:
    FLYTEKIT_AVAILABLE = False
    print("Warning: flytekit not available. Running in standalone mode.")


@dataclass
class ToolCall:
    """Represents a tool call with its parameters and result."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[float] = None
    error: Optional[str] = None


@dataclass
class AgentResult:
    """Represents the result of processing an instruction."""
    instruction: str
    tool_calls: List[ToolCall]
    final_result: Optional[float] = None
    success: bool = True


# Task implementations
def add_numbers(a: float, b: float) -> float:
    """
    Add two numbers together.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    result = a + b
    print(f"add_numbers({a}, {b}) = {result}")
    return result


def multiply_numbers(a: float, b: float) -> float:
    """
    Multiply two numbers together.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Product of a and b
    """
    result = a * b
    print(f"multiply_numbers({a}, {b}) = {result}")
    return result


def divide_numbers(a: float, b: float) -> float:
    """
    Divide two numbers.
    
    Args:
        a: Numerator
        b: Denominator
    
    Returns:
        Quotient of a and b
    
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    result = a / b
    print(f"divide_numbers({a}, {b}) = {result}")
    return result


def select_tool(instruction: str) -> List[ToolCall]:
    """
    Select and parse tools from a natural language instruction.
    
    This function uses pattern matching to identify which math operations
    are needed and extracts the parameters.
    
    Args:
        instruction: Natural language instruction describing the operation
    
    Returns:
        List of ToolCall objects representing the operations to perform
    """
    tool_calls = []
    
    # Normalize instruction
    instruction_lower = instruction.lower()
    
    # Pattern for addition: "add X and Y" or "X plus Y" or "sum of X and Y"
    add_patterns = [
        r'add\s+(-?\d*\.?\d+)\s+and\s+(-?\d*\.?\d+)',
        r'(-?\d*\.?\d+)\s+plus\s+(-?\d*\.?\d+)',
        r'sum\s+of\s+(-?\d*\.?\d+)\s+and\s+(-?\d*\.?\d+)',
        r'(-?\d*\.?\d+)\s+\+\s+(-?\d*\.?\d+)',
    ]
    
    # Pattern for multiplication: "multiply X by Y" or "X times Y" or "product of X and Y"
    multiply_patterns = [
        r'multiply\s+(-?\d*\.?\d+)\s+by\s+(-?\d*\.?\d+)',
        r'(-?\d*\.?\d+)\s+times\s+(-?\d*\.?\d+)',
        r'product\s+of\s+(-?\d*\.?\d+)\s+and\s+(-?\d*\.?\d+)',
        r'(-?\d*\.?\d+)\s+\*\s+(-?\d*\.?\d+)',
    ]
    
    # Pattern for division: "divide X by Y" or "X divided by Y" or "quotient of X and Y"
    divide_patterns = [
        r'divide\s+(-?\d*\.?\d+)\s+by\s+(-?\d*\.?\d+)',
        r'(-?\d*\.?\d+)\s+divided\s+by\s+(-?\d*\.?\d+)',
        r'quotient\s+of\s+(-?\d*\.?\d+)\s+and\s+(-?\d*\.?\d+)',
        r'(-?\d*\.?\d+)\s+/\s+(-?\d*\.?\d+)',
    ]
    
    # Try to match addition patterns
    for pattern in add_patterns:
        match = re.search(pattern, instruction_lower)
        if match:
            a = float(match.group(1))
            b = float(match.group(2))
            tool_calls.append(ToolCall(
                tool_name="add_numbers",
                parameters={"a": a, "b": b}
            ))
            break
    
    # Try to match multiplication patterns
    for pattern in multiply_patterns:
        match = re.search(pattern, instruction_lower)
        if match:
            a = float(match.group(1))
            b = float(match.group(2))
            tool_calls.append(ToolCall(
                tool_name="multiply_numbers",
                parameters={"a": a, "b": b}
            ))
            break
    
    # Try to match division patterns
    for pattern in divide_patterns:
        match = re.search(pattern, instruction_lower)
        if match:
            a = float(match.group(1))
            b = float(match.group(2))
            tool_calls.append(ToolCall(
                tool_name="divide_numbers",
                parameters={"a": a, "b": b}
            ))
            break
    
    return tool_calls


def execute_tool_call(tool_call: ToolCall) -> ToolCall:
    """
    Execute a single tool call.
    
    Args:
        tool_call: ToolCall object representing the operation to perform
    
    Returns:
        ToolCall object with the result populated
    """
    try:
        if tool_call.tool_name == "add_numbers":
            result = add_numbers(**tool_call.parameters)
            tool_call.result = result
        elif tool_call.tool_name == "multiply_numbers":
            result = multiply_numbers(**tool_call.parameters)
            tool_call.result = result
        elif tool_call.tool_name == "divide_numbers":
            result = divide_numbers(**tool_call.parameters)
            tool_call.result = result
        else:
            tool_call.error = f"Unknown tool: {tool_call.tool_name}"
            tool_call.success = False
    except Exception as e:
        tool_call.error = str(e)
        tool_call.success = False
    
    return tool_call


def process_instruction(instruction: str) -> AgentResult:
    """
    Process a single instruction through the agentic loop.
    
    This function:
    1. Selects the appropriate tool(s) for the instruction
    2. Executes the tool(s)
    3. Returns the result
    
    Args:
        instruction: Natural language instruction
    
    Returns:
        AgentResult containing the tool calls and final result
    """
    print(f"Processing instruction: {instruction}")
    
    # Step 1: Select tools
    tool_calls = select_tool(instruction)
    
    if not tool_calls:
        return AgentResult(
            instruction=instruction,
            tool_calls=[],
            success=False
        )
    
    # Step 2: Execute tool calls
    executed_calls = []
    for tool_call in tool_calls:
        executed_call = execute_tool_call(tool_call)
        executed_calls.append(executed_call)
    
    # Step 3: Determine final result
    final_result = None
    success = True
    
    if executed_calls:
        last_call = executed_calls[-1]
        if last_call.error:
            success = False
        else:
            final_result = last_call.result
    else:
        success = False
    
    return AgentResult(
        instruction=instruction,
        tool_calls=executed_calls,
        final_result=final_result,
        success=success
    )


def agent_loop(instructions: List[str]) -> List[Dict[str, Any]]:
    """
    Main agentic loop that processes multiple instructions.
    
    This workflow processes each instruction through the agentic loop
    and collects all results.
    
    Args:
        instructions: List of natural language instructions to process
    
    Returns:
        List of result dictionaries
    """
    results = []
    
    for instruction in instructions:
        result = process_instruction(instruction=instruction)
        
        # Convert result to dict for JSON serialization
        result_dict = {
            "instruction": result.instruction,
            "success": result.success,
            "final_result": result.final_result,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "parameters": tc.parameters,
                    "result": tc.result,
                    "error": tc.error
                }
                for tc in result.tool_calls
            ]
        }
        results.append(result_dict)
    
    return results


def save_results_to_json(results: List[Dict[str, Any]], output_path: str):
    """
    Save results to a JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


def run_agent_loop_locally(instructions: List[str], output_path: str = None):
    """
    Run the agent loop locally.
    
    This is useful for testing and development.
    
    Args:
        instructions: List of natural language instructions to process
        output_path: Optional path to save results as JSON
    
    Returns:
        List of result dictionaries
    """
    results = []
    
    for instruction in instructions:
        print(f"\n{'='*60}")
        print(f"Instruction: {instruction}")
        print('='*60)
        
        # Process the instruction
        result = process_instruction(instruction=instruction)
        
        # Convert to dict
        result_dict = {
            "instruction": result.instruction,
            "success": result.success,
            "final_result": result.final_result,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "parameters": tc.parameters,
                    "result": tc.result,
                    "error": tc.error
                }
                for tc in result.tool_calls
            ]
        }
        results.append(result_dict)
        
        # Print result summary
        if result.success:
            print(f"✓ Success: {result.final_result}")
        else:
            print("✗ Failed: Could not process instruction")
        
        for tc in result.tool_calls:
            print(f"  - {tc.tool_name}({tc.parameters}) = {tc.result}")
    
    # Save to JSON if output path provided
    if output_path:
        save_results_to_json(results, output_path)
    
    return results


if __name__ == "__main__":
    # Example usage
    test_instructions = [
        "add 5 and 3",
        "multiply 4 by 7",
        "divide 20 by 4",
        "10 plus 15",
        "6 times 8",
        "100 divided by 5",
    ]
    
    # Run locally and save results
    output_file = "/home/user/flyte_project/agent_output.json"
    results = run_agent_loop_locally(test_instructions, output_file)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Processed {len(results)} instructions")
    successful = sum(1 for r in results if r["success"])
    print(f"Successful: {successful}/{len(results)}")
    
    # Also save a copy to artifacts
    import shutil
    artifacts_dir = "/logs/artifacts/flyte_project"
    import os
    os.makedirs(artifacts_dir, exist_ok=True)
    save_results_to_json(results, f"{artifacts_dir}/agent_output.json")