"""
Flyte 2.0 Distributed Map-Reduce Word Counter

This module implements a distributed word frequency counter using the map-reduce pattern.
It splits text into shards, processes each shard in parallel using asyncio.gather,
and reduces the results to produce word frequency counts.
"""

import asyncio
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

from flytekit import task, workflow, Resources


# Define resources for tasks
task_resources = Resources(
    cpu=("500m", "2000m"),  # Request 500m CPU, limit to 2000m CPU
    mem=("512Mi", "2Gi")     # Request 512Mi memory, limit to 2Gi memory
)


# Sample input text for demonstration
SAMPLE_TEXT = """
Flyte is a cloud-native workflow processing platform that enables you to build, 
test, and deploy data processing pipelines and machine learning workflows. 
Flyte provides a unified interface for building scalable and reproducible data 
and ML pipelines. With Flyte, you can easily orchestrate complex workflows 
and manage compute resources efficiently.

The key features of Flyte include:
- Type-safe workflows with strong typing
- Automatic caching and checkpointing
- Scalable execution across multiple compute environments
- Built-in support for popular ML frameworks
- Extensible plugin architecture

Flyte simplifies the development of production-grade data pipelines 
by providing a declarative way to define workflows. The platform handles 
resource management, retry logic, and failure recovery automatically.

Map-reduce is a programming model for processing large data sets with a 
parallel, distributed algorithm on a cluster. A map-reduce program consists 
of a map procedure that performs filtering and sorting, and a reduce procedure 
that performs a summary operation.

In this implementation, we use Flyte to orchestrate a distributed word 
counting operation using the map-reduce pattern. The text is split into 
shards, each shard is processed independently to count word frequencies, 
and then the results are aggregated to produce the final word counts.
"""


@dataclass
class TextShard:
    """Represents a shard of text to be processed."""
    shard_id: int
    content: str


@dataclass
class WordCountResult:
    """Represents word count results from a single shard."""
    shard_id: int
    word_counts: Dict[str, int]


def normalize_word(word: str) -> str:
    """
    Normalize a word by converting to lowercase and removing non-alphanumeric characters.
    
    Args:
        word: The word to normalize
        
    Returns:
        The normalized word
    """
    # Convert to lowercase and remove non-alphanumeric characters
    word = word.lower()
    word = re.sub(r'[^a-z0-9]', '', word)
    return word


def split_text_into_shards(text: str, num_shards: int) -> List[TextShard]:
    """
    Split text into multiple shards for parallel processing.
    
    Args:
        text: The input text to split
        num_shards: Number of shards to create
        
    Returns:
        List of TextShard objects
    """
    # Split text into words
    words = text.split()
    total_words = len(words)
    
    # Calculate words per shard
    words_per_shard = total_words // num_shards
    shards = []
    
    for i in range(num_shards):
        start_idx = i * words_per_shard
        # Last shard gets remaining words
        end_idx = start_idx + words_per_shard if i < num_shards - 1 else total_words
        
        shard_words = words[start_idx:end_idx]
        shard_content = ' '.join(shard_words)
        
        shards.append(TextShard(
            shard_id=i,
            content=shard_content
        ))
    
    return shards


async def process_shard(shard: TextShard) -> WordCountResult:
    """
    Process a single text shard to count word frequencies (map phase).
    
    This function runs asynchronously to allow parallel processing of multiple shards.
    
    Args:
        shard: The text shard to process
        
    Returns:
        WordCountResult with word frequencies for this shard
    """
    # Simulate async processing (in real scenarios, this might involve I/O)
    await asyncio.sleep(0.01)
    
    # Split shard content into words
    words = shard.content.split()
    
    # Normalize and count words
    word_counter = Counter()
    for word in words:
        normalized = normalize_word(word)
        if normalized:  # Skip empty strings
            word_counter[normalized] += 1
    
    return WordCountResult(
        shard_id=shard.shard_id,
        word_counts=dict(word_counter)
    )


def reduce_results(results: List[WordCountResult]) -> Dict[str, int]:
    """
    Reduce phase: aggregate word counts from all shards.
    
    Args:
        results: List of WordCountResult objects from all shards
        
    Returns:
        Combined word frequency dictionary
    """
    combined_counter = Counter()
    
    for result in results:
        combined_counter.update(result.word_counts)
    
    # Sort by frequency (descending) and then by word (ascending)
    sorted_counts = dict(sorted(
        combined_counter.items(),
        key=lambda x: (-x[1], x[0])
    ))
    
    return sorted_counts


@task(
    resources=task_resources,
    cache=True,
    cache_version="1.0"
)
def map_task(text: str, num_shards: int = 4) -> List[WordCountResult]:
    """
    Map task: Split text into shards and process each shard in parallel.
    
    Args:
        text: Input text to process
        num_shards: Number of shards for parallel processing
        
    Returns:
        List of WordCountResult objects from each shard
    """
    # Split text into shards
    shards = split_text_into_shards(text, num_shards)
    
    # Process all shards in parallel using asyncio.gather
    import asyncio
    
    async def process_all_shards():
        return await asyncio.gather(
            *[process_shard(shard) for shard in shards]
        )
    
    # Check if there's already a running event loop
    try:
        loop = asyncio.get_running_loop()
        # If we're in a running loop, create a task and await it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, process_all_shards())
            results = future.result()
    except RuntimeError:
        # No running loop, use asyncio.run
        results = asyncio.run(process_all_shards())
    
    return results


@task(
    resources=task_resources,
    cache=True,
    cache_version="1.0"
)
def reduce_task(results: List[WordCountResult]) -> Dict[str, int]:
    """
    Reduce task: Aggregate word counts from all shards.
    
    Args:
        results: List of WordCountResult objects from map phase
        
    Returns:
        Combined word frequency dictionary
    """
    return reduce_results(results)


@task(
    resources=task_resources,
    cache=True,
    cache_version="1.0"
)
def write_results_task(word_counts: Dict[str, int], output_path: str) -> str:
    """
    Write word count results to a JSON file.
    
    Args:
        word_counts: Combined word frequency dictionary
        output_path: Path to output JSON file
        
    Returns:
        Path to the written file
    """
    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare output data with metadata
    output_data = {
        "total_unique_words": len(word_counts),
        "total_word_count": sum(word_counts.values()),
        "word_frequencies": word_counts
    }
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return str(output_file)


@workflow
def wordcount_workflow(
    text: str = SAMPLE_TEXT,
    num_shards: int = 4,
    output_path: str = "/home/user/flyte_project/wordcount.json"
) -> str:
    """
    Main workflow for distributed word counting using map-reduce pattern.
    
    This workflow:
    1. Splits input text into shards
    2. Processes each shard in parallel (map phase)
    3. Aggregates results from all shards (reduce phase)
    4. Writes final results to output file
    
    Args:
        text: Input text to process
        num_shards: Number of shards for parallel processing
        output_path: Path to output JSON file
        
    Returns:
        Path to the output file
    """
    # Map phase: Process shards in parallel
    map_results = map_task(text=text, num_shards=num_shards)
    
    # Reduce phase: Aggregate results
    word_counts = reduce_task(results=map_results)
    
    # Write results to file
    output_file = write_results_task(
        word_counts=word_counts,
        output_path=output_path
    )
    
    return output_file


async def main():
    """
    Main function to execute the word counting workflow.
    """
    print("Starting Flyte 2.0 Distributed Map-Reduce Word Counter")
    print("=" * 60)
    
    # Execute the workflow
    output_file = wordcount_workflow(
        text=SAMPLE_TEXT,
        num_shards=4,
        output_path="/home/user/flyte_project/wordcount.json"
    )
    
    print(f"\nWord count completed successfully!")
    print(f"Results written to: {output_file}")
    
    # Display some statistics
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    print(f"\nStatistics:")
    print(f"  Total unique words: {data['total_unique_words']}")
    print(f"  Total word count: {data['total_word_count']}")
    
    print(f"\nTop 10 most frequent words:")
    for i, (word, count) in enumerate(list(data['word_frequencies'].items())[:10], 1):
        print(f"  {i:2d}. {word:20s} : {count:3d}")
    
    return output_file


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())