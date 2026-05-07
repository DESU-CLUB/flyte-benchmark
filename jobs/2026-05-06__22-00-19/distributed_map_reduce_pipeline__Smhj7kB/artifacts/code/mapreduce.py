import asyncio
import json
import os
import flyte
from collections import Counter

# 1. Define TaskEnvironment with appropriate resources
# This sets the default configuration for all tasks in this environment.
env = flyte.TaskEnvironment(
    name="wordcount-distributed",
    resources=flyte.Resources(cpu="1", memory="512Mi"),
)

# 2. Map Task: Count words in a single shard
# The @env.task decorator registers this function as a Flyte task.
@env.task
async def map_shard(text: str) -> dict[str, int]:
    """
    Counts word frequencies in a given shard of text.
    """
    # Normalize text and split into words
    words = text.lower().split()
    # Remove common punctuation
    words = [w.strip('.,!?;:"()') for w in words if w.strip('.,!?;:"()')]
    return dict(Counter(words))

# 3. Reduce Task: Aggregate multiple word count dictionaries
@env.task
async def reduce_counts(counts_list: list[dict[str, int]]) -> dict[str, int]:
    """
    Aggregates a list of word count dictionaries into a single dictionary.
    """
    total_counts = Counter()
    for counts in counts_list:
        total_counts.update(counts)
    return dict(total_counts)

# Orchestrator logic
async def run_map_reduce(input_text: str):
    """
    Orchestrates the distributed map-reduce process using asyncio.gather.
    """
    # Split text into shards (e.g., by lines)
    shards = [line.strip() for line in input_text.strip().split('\n') if line.strip()]
    
    if not shards:
        return {}

    # Map phase: Process shards in parallel with asyncio.gather
    # Each call to map_shard returns a coroutine that Flyte executes.
    print(f"Map phase: processing {len(shards)} shards in parallel...")
    map_results = await asyncio.gather(*(map_shard(shard) for shard in shards))
    
    # Reduce phase: Aggregate all results into the final word frequency map
    print("Reduce phase: aggregating results...")
    final_result = await reduce_counts(list(map_results))
    
    return final_result

async def main():
    # Sample input text for the word counter
    input_text = """
    Flyte is a cloud-native workflow orchestrator.
    Flyte is built on Kubernetes to handle distributed computing.
    This task implements a distributed word counter using Flyte 2.0.
    Distributed systems can be complex, but Flyte makes them easier.
    Map-reduce is a classic pattern for distributed processing.
    We use asyncio.gather for parallel execution of map tasks.
    The results are then reduced into a single word frequency count.
    Flyte 2.0 provides a modern SDK for compound AI and distributed workflows.
    """
    
    # Initialize Flyte context for local execution
    flyte.init()
    
    # Run the map-reduce process
    results = await run_map_reduce(input_text)
    
    # Define output path
    output_path = "/home/user/flyte_project/wordcount.json"
    
    # Ensure the directory exists (though it should already exist based on the prompt)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write results to wordcount.json
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"Success! Results written to {output_path}")
    print("Word counts sample:", dict(list(results.items())[:5]))

if __name__ == "__main__":
    # Execute the main orchestrator
    asyncio.run(main())
