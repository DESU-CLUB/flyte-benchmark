import flyte
import json
import asyncio
from typing import List, Dict, Any

# 1. Define Environments with different CPU/memory resources
# Extraction environment: Optimized for I/O, lower resources
extract_env = flyte.TaskEnvironment(
    name="extract-env",
    resources=flyte.Resources(cpu="1", memory="500Mi"),
    # Cache extraction tasks with flyte.Cache
    cache=flyte.Cache(behavior="auto")
)

# Transformation environment: Optimized for compute, higher resources
transform_env = flyte.TaskEnvironment(
    name="transform-env",
    resources=flyte.Resources(cpu="2", memory="2Gi")
)

# 2. Extraction Task
@extract_env.task
async def extract_data(source: str) -> List[Dict[str, Any]]:
    """
    Extracts data from a given source.
    Handles "database", "api", and unknown sources gracefully.
    """
    print(f"Extracting from {source}...")
    
    # Simulate extraction logic
    if source == "database":
        # Simulate successful database extraction
        return [
            {"id": 1, "source": "database", "data": "db_record_1"},
            {"id": 2, "source": "database", "data": "db_record_2"}
        ]
    elif source == "api":
        # Simulate successful API extraction
        return [
            {"id": 3, "source": "api", "data": "api_record_1"},
            {"id": 4, "source": "api", "data": "api_record_2"}
        ]
    elif source == "fail_source":
        # Simulate a source failure
        raise RuntimeError(f"Failed to connect to {source}")
    else:
        # Handle unknown sources gracefully as per requirements
        print(f"Unknown source: {source}. Skipping gracefully.")
        return []

# 3. Transformation Task
@transform_env.task
async def transform_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a single record.
    """
    print(f"Transforming record {record.get('id')} from {record.get('source')}...")
    
    # Simulate transformation logic
    data = record.get("data", "")
    record["transformed_data"] = data.upper()
    record["status"] = "processed"
    
    return record

# 4. Loading Task
@transform_env.task
async def load_data(records: List[Dict[str, Any]], output_path: str):
    """
    Loads the final transformed records into a JSON file.
    """
    print(f"Loading {len(records)} records to {output_path}...")
    try:
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2)
        print("Load successful.")
    except Exception as e:
        print(f"Failed to write output: {e}")
        raise

# 5. ETL Workflow (Entrypoint Task)
@transform_env.task(entrypoint=True)
async def run_etl_pipeline(sources: List[str], output_path: str):
    """
    Orchestrates the ETL pipeline:
    - Extracts from multiple sources in parallel.
    - Handles source failures gracefully.
    - Transforms records in parallel.
    - Loads the result.
    """
    print(f"Starting ETL pipeline for sources: {sources}")
    
    # Step 1: Extract from multiple sources in parallel
    # We use asyncio.gather to run tasks in parallel.
    # We handle source failures gracefully by catching exceptions.
    extraction_tasks = [extract_data(source) for source in sources]
    
    # Using return_exceptions=True to handle failures gracefully
    extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
    
    all_records = []
    for i, result in enumerate(extraction_results):
        if isinstance(result, Exception):
            print(f"Error extracting from source '{sources[i]}': {result}. Skipping source.")
        else:
            all_records.extend(result)
            
    if not all_records:
        print("No records extracted. ETL pipeline finishing early.")
        # Write empty result to output file
        await load_data([], output_path)
        return

    # Step 2: Transform records in parallel
    # Use flyte.map for parallel transformation of records
    print(f"Transforming {len(all_records)} records in parallel...")
    transformed_records = []
    
    # flyte.map.aio returns an async iterator
    async for result in flyte.map.aio(transform_record, all_records):
        # In local mode, result might be a coroutine that needs to be awaited
        if asyncio.iscoroutine(result):
            result = await result
            
        if isinstance(result, Exception):
            print(f"Error transforming a record: {result}. Skipping record.")
        else:
            transformed_records.append(result)
            
    # Step 3: Load the final result
    await load_data(transformed_records, output_path)
    print("ETL pipeline completed successfully.")

if __name__ == "__main__":
    # Run the ETL pipeline locally
    sources = ["database", "api", "unknown_source", "fail_source"]
    output_path = "/home/user/flyte_project/etl_output.json"
    
    print(f"Executing pipeline locally...")
    flyte.run(run_etl_pipeline, sources=sources, output_path=output_path)
    print(f"Pipeline execution finished. Check {output_path} for results.")
