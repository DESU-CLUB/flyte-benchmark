import flyte
import json
import asyncio
from typing import List, Dict, Any

# Define TaskEnvironments with different resources
# Extraction environment: Lower CPU/Memory, Caching enabled
extract_env = flyte.TaskEnvironment(
    name="extract-env",
    resources=flyte.Resources(cpu="1", memory="500Mi"),
    cache=flyte.Cache(behavior="auto")
)

# Transformation environment: Higher CPU/Memory
transform_env = flyte.TaskEnvironment(
    name="transform-env",
    resources=flyte.Resources(cpu="2", memory="1Gi")
)

@extract_env.task
async def extract_data(source: str) -> List[Dict[str, Any]]:
    """
    Extracts data from a given source.
    Handles 'database', 'api' and handles unknown sources gracefully.
    """
    print(f"Extracting from {source}...")
    
    # Simulate extraction logic
    try:
        if source == "database":
            return [
                {"id": 1, "source": "database", "data": "db_record_1"},
                {"id": 2, "source": "database", "data": "db_record_2"}
            ]
        elif source == "api":
            return [
                {"id": 3, "source": "api", "data": "api_record_1"},
                {"id": 4, "source": "api", "data": "api_record_2"}
            ]
        elif source == "failed_source":
            # Simulate a failure
            raise Exception("Connection failed to failed_source")
        else:
            # Handle unknown sources gracefully
            print(f"Warning: Unknown source '{source}'. Returning empty list.")
            return []
    except Exception as e:
        print(f"Error extracting from {source}: {e}")
        # In a real pipeline, we might want to log this and continue
        return []

@transform_env.task
async def transform_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a single record.
    """
    print(f"Transforming record {record['id']} from {record['source']}...")
    
    # Simulate transformation logic
    record["data"] = record["data"].upper()
    record["processed_by"] = "flyte-etl-pipeline"
    record["status"] = "transformed"
    
    return record

@transform_env.task
async def load_data(records: List[Dict[str, Any]], output_path: str):
    """
    Loads the transformed data into a JSON file (simulating a warehouse).
    """
    print(f"Loading {len(records)} records into {output_path}...")
    
    with open(output_path, "w") as f:
        json.dump(records, f, indent=4)
    
    print("ETL pipeline completed successfully.")

async def run_pipeline():
    """
    Orchestrates the ETL pipeline.
    """
    sources = ["database", "api", "unknown_source", "failed_source"]
    output_path = "/home/user/flyte_project/etl_output.json"

    print("Starting ETL Pipeline...")

    # 1. Extraction Phase (Parallel)
    # Use flyte.map to run extraction tasks in parallel across sources
    # return_exceptions=True ensures that one failure doesn't stop the whole map
    extraction_results = []
    async for result in flyte.map.aio(extract_data, sources, return_exceptions=True):
        if asyncio.iscoroutine(result):
            result = await result
            
        if isinstance(result, Exception):
            print(f"Extraction task failed with error: {result}")
        else:
            extraction_results.extend(result)

    if not extraction_results:
        print("No data extracted. Exiting.")
        return

    # 2. Transformation Phase (Parallel)
    # Transform each record in parallel
    transformed_records = []
    async for result in flyte.map.aio(transform_record, extraction_results, return_exceptions=True):
        if asyncio.iscoroutine(result):
            result = await result

        if isinstance(result, Exception):
            print(f"Transformation task failed with error: {result}")
        else:
            transformed_records.append(result)

    # 3. Loading Phase
    # Load all transformed records into the destination
    await load_data(transformed_records, output_path)

if __name__ == "__main__":
    # Run the pipeline
    asyncio.run(run_pipeline())
