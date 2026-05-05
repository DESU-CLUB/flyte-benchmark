# Build a Flyte 2.0 ETL Pipeline with Recovery

Build a production-ready ETL pipeline at `/home/user/flyte_project/` using Flyte 2.0 that extracts data from multiple sources in parallel, transforms it, and loads it into a warehouse. The pipeline must handle source failures gracefully.

## Requirements
- Use two `TaskEnvironment`s with different CPU/memory resources for extraction and transformation
- Extract from "database", "api", and handle unknown sources gracefully
- Transform records in parallel
- Cache extraction tasks with `flyte.Cache`
- Write the final result to `/home/user/flyte_project/etl_output.json`

## Constraints
- Project path: /home/user/flyte_project
- Log file: /home/user/flyte_project/etl_output.json
