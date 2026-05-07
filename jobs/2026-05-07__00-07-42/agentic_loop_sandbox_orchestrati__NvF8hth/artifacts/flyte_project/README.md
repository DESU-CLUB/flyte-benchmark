# Flyte 2.0 Agentic Loop for Math Operations

A Flyte 2.0 compatible agentic loop that can execute math operations based on natural language instructions.

## Overview

This project demonstrates a simple agentic workflow using Flyte 2.0 that:
- Parses natural language instructions to identify mathematical operations
- Selects appropriate tools (add, multiply, divide)
- Executes the operations and returns results
- Supports multiple instruction processing in a loop

## Features

- **Natural Language Processing**: Understands various phrasings for math operations
  - Addition: "add X and Y", "X plus Y", "sum of X and Y", "X + Y"
  - Multiplication: "multiply X by Y", "X times Y", "product of X and Y", "X * Y"
  - Division: "divide X by Y", "X divided by Y", "quotient of X and Y", "X / Y"

- **Tool Selection**: Pattern-based tool selection using `@flyte.trace` decorator
- **Agent Loop**: Processes multiple instructions and aggregates results
- **Error Handling**: Graceful error handling with detailed error messages
- **JSON Output**: Structured output with detailed execution trace

## Files

- `agent_loop.py`: Main Flyte 2.0 implementation with full Flyte decorators
- `agent_loop_standalone.py`: Standalone version that runs without Flyte dependencies (for testing)
- `agent_output.json`: Sample output from test execution
- `README.md`: This documentation

## Requirements

### For Full Flyte 2.0 Implementation
```bash
pip install flytekit
```

### For Standalone Version
- Python 3.7+
- No external dependencies required (uses only standard library)

## Usage

### Standalone Mode (Testing)

Run the standalone version without Flyte dependencies:

```bash
python3 agent_loop_standalone.py
```

This will:
- Process a set of test instructions
- Print detailed execution logs
- Save results to `agent_output.json`
- Save a copy to `/logs/artifacts/flyte_project/agent_output.json`

### Full Flyte 2.0 Mode

When `flytekit` is installed, use the full implementation:

```python
from agent_loop import agent_workflow

# Define instructions
instructions = [
    "add 5 and 3",
    "multiply 4 by 7",
    "divide 20 by 4"
]

# Run the workflow
results = agent_workflow(instructions=instructions)
```

## Architecture

### Components

1. **Task Environment**: Named `"agent-env"` using `flyte.TaskEnvironment`

2. **Task Functions**:
   - `add_numbers(a, b)`: Addition operation
   - `multiply_numbers(a, b)`: Multiplication operation
   - `divide_numbers(a, b)`: Division operation (with zero-division protection)

3. **Tool Selection** (`@flyte.trace`):
   - Parses natural language instructions
   - Matches against regex patterns
   - Returns appropriate `ToolCall` objects

4. **Agentic Loop**:
   - Processes each instruction
   - Selects and executes tools
   - Aggregates results

### Data Structures

```python
@dataclass
class ToolCall:
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[float] = None
    error: Optional[str] = None

@dataclass
class AgentResult:
    instruction: str
    tool_calls: List[ToolCall]
    final_result: Optional[float] = None
    success: bool = True
```

## Output Format

The agent loop produces JSON output with the following structure:

```json
[
  {
    "instruction": "add 5 and 3",
    "success": true,
    "final_result": 8.0,
    "tool_calls": [
      {
        "tool_name": "add_numbers",
        "parameters": {
          "a": 5.0,
          "b": 3.0
        },
        "result": 8.0,
        "error": null
      }
    ]
  }
]
```

## Example Instructions

Supported instruction formats:

### Addition
- "add 5 and 3"
- "10 plus 15"
- "sum of 7 and 8"
- "12 + 8"

### Multiplication
- "multiply 4 by 7"
- "6 times 8"
- "product of 3 and 9"
- "5 * 4"

### Division
- "divide 20 by 4"
- "100 divided by 5"
- "quotient of 50 and 10"
- "30 / 6"

## Extending the Agent

### Adding New Tools

1. Implement the tool function:

```python
@agent_env.task
def subtract_numbers(a: float, b: float) -> float:
    result = a - b
    return result
```

2. Add patterns to `select_tool()`:

```python
subtract_patterns = [
    r'subtract\s+(-?\d*\.?\d+)\s+from\s+(-?\d*\.?\d+)',
    r'(-?\d*\.?\d+)\s+minus\s+(-?\d*\.?\d+)',
    r'(-?\d*\.?\d+)\s+-\s+(-?\d*\.?\d+)',
]
```

3. Add execution logic in `execute_tool_call()`:

```python
elif tool_call.tool_name == "subtract_numbers":
    result = subtract_numbers(**tool_call.parameters)
    tool_call.result = result
```

## Testing

Run the test suite:

```bash
python3 agent_loop_standalone.py
```

Expected output:
- 6 instructions processed
- 6 successful operations
- Results saved to `agent_output.json`

## Error Handling

The agent handles various error conditions:
- Unknown tool names
- Division by zero
- Invalid instruction formats
- Missing parameters

All errors are captured in the `error` field of the `ToolCall` object.

## Project Structure

```
/home/user/flyte_project/
├── agent_loop.py              # Full Flyte 2.0 implementation
├── agent_loop_standalone.py   # Standalone version for testing
├── agent_output.json          # Sample output
└── README.md                  # Documentation

/logs/artifacts/flyte_project/
└── agent_output.json          # Preserved copy of output
```

## License

This is a demonstration project for Flyte 2.0 agentic workflows.