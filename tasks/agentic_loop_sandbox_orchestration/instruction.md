# Build a Flyte 2.0 Agentic Loop

Build a simple Flyte 2.0 agentic loop at `/home/user/flyte_project/agent_loop.py` that can execute math operations based on natural language instructions.

## Requirements
- Use `flyte.TaskEnvironment` named `"agent-env"`
- Implement `add_numbers`, `multiply_numbers`, and `divide_numbers` as `@env.task` functions
- Implement a tool selection mechanism using `@flyte.trace`
- Build an agent loop that processes a list of instructions and returns results
- Write output to `/home/user/flyte_project/agent_output.json`

## Constraints
- Project path: `/home/user/flyte_project`
- Output file: `/home/user/flyte_project/agent_output.json`
