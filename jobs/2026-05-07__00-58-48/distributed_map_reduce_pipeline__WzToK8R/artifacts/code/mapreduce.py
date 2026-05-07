import asyncio
import json
import re
from collections import Counter
from typing import List, Dict
import sys
import flyte

env = flyte.TaskEnvironment(
    name="wordcount_env",
    resources=flyte.Resources(cpu="1", memory="1Gi")
)

@env.task
async def map_words(text_shard: str) -> Dict[str, int]:
    words = re.findall(r'\b\w+\b', text_shard.lower())
    return dict(Counter(words))

@env.task
async def reduce_counts(counts_list: List[Dict[str, int]]) -> Dict[str, int]:
    total_counts = Counter()
    for counts in counts_list:
        total_counts.update(counts)
    return dict(total_counts)

async def process_text(text: str) -> Dict[str, int]:
    # Split text into shards
    lines = text.split('\n')
    # Let's create 4 shards for demonstration
    num_shards = 4
    chunk_size = max(1, len(lines) // num_shards)
    shards = ['\n'.join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]
    
    # Map in parallel
    mapped_results = await asyncio.gather(*(map_words(shard) for shard in shards))
    
    # Reduce
    final_counts = await reduce_counts(mapped_results)
    
    # Write results
    with open('/home/user/flyte_project/wordcount.json', 'w') as f:
        json.dump(final_counts, f, indent=2)
        
    return final_counts

async def main():
    text = "Hello world! This is a test. Hello Flyte 2.0 distributed map-reduce test."
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            text = f.read()
    
    await process_text(text)

if __name__ == "__main__":
    asyncio.run(main())
