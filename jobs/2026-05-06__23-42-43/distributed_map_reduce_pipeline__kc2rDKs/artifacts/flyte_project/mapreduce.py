"""
Flyte 2.0 Distributed Map-Reduce Word Frequency Counter
========================================================

Implements a map-reduce pipeline using Flyte 2.0 primitives:
  - flyte.TaskEnvironment  : declares resources for all tasks in this environment
  - @env.task              : decorates each map/reduce step as a Flyte task
  - asyncio.gather         : runs shard-level word-count tasks concurrently
  - reduce step            : merges per-shard counts into a final frequency table
  - JSON output            : writes results to /home/user/flyte_project/wordcount.json

Pipeline
--------
                         ┌─────────────┐
        input_text ──────► split_shards │  (pure Python helper, not a task)
                         └──────┬──────┘
                                │  List[str]  (N shards)
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
             count_shard  count_shard  count_shard   (map – asyncio.gather)
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                        reduce_counts                (reduce)
                                │
                                ▼
                      wordcount.json  (sorted by frequency desc)
"""

from __future__ import annotations

import asyncio
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

import flyte

# ---------------------------------------------------------------------------
# Sample corpus used when the script is run directly
# ---------------------------------------------------------------------------
SAMPLE_TEXT = """
To be or not to be that is the question
Whether tis nobler in the mind to suffer
The slings and arrows of outrageous fortune
Or to take arms against a sea of troubles
And by opposing end them to die to sleep
No more and by a sleep to say we end
The heartache and the thousand natural shocks
That flesh is heir to tis a consummation
Devoutly to be wished to die to sleep
To sleep perchance to dream ay there is the rub
For in that sleep of death what dreams may come
When we have shuffled off this mortal coil
Must give us pause there is the respect
That makes calamity of so long life
""" * 10  # repeat to create a non-trivial corpus

# ---------------------------------------------------------------------------
# Task Environment
# ---------------------------------------------------------------------------
env = flyte.TaskEnvironment(
    name="word-counter-env",
    resources=flyte.Resources(cpu=2, memory="512Mi"),
    description="Environment for distributed map-reduce word frequency counting",
)

# ---------------------------------------------------------------------------
# Helper: split text into N roughly equal shards
# ---------------------------------------------------------------------------

def split_into_shards(text: str, n_shards: int) -> List[str]:
    """Tokenise *text* and partition tokens into *n_shards* equal buckets."""
    tokens = re.findall(r"[a-z]+", text.lower())
    if not tokens:
        return [""] * n_shards
    size = math.ceil(len(tokens) / n_shards)
    shards: List[str] = []
    for i in range(0, len(tokens), size):
        shards.append(" ".join(tokens[i : i + size]))
    # Pad to exactly n_shards if rounding left fewer
    while len(shards) < n_shards:
        shards.append("")
    return shards


# ---------------------------------------------------------------------------
# Map task: count word frequencies in a single text shard
# ---------------------------------------------------------------------------

@env.task
async def count_shard(shard: str) -> Dict[str, int]:
    """Count word frequencies in a single text shard (map step)."""
    if not shard:
        return {}
    counts: Dict[str, int] = {}
    for word in shard.split():
        counts[word] = counts.get(word, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Reduce task: merge a list of per-shard frequency dicts into one
# ---------------------------------------------------------------------------

@env.task
async def reduce_counts(shard_counts: List[Dict[str, int]]) -> Dict[str, int]:
    """Merge per-shard word-count dicts into a single frequency table (reduce step)."""
    total: Counter = Counter()
    for counts in shard_counts:
        total.update(counts)
    # Return sorted by frequency descending, then alphabetically for ties
    return dict(sorted(total.items(), key=lambda kv: (-kv[1], kv[0])))


# ---------------------------------------------------------------------------
# Orchestrator task: splits → parallel map → reduce → write JSON
# ---------------------------------------------------------------------------

@env.task
async def word_count_pipeline(
    text: str,
    n_shards: int = 8,
    output_path: str = "/home/user/flyte_project/wordcount.json",
) -> str:
    """
    Full map-reduce word-count pipeline.

    1. Split *text* into *n_shards* token buckets.
    2. Run ``count_shard`` on every shard concurrently with ``asyncio.gather``.
    3. Pass the list of shard-level dicts to ``reduce_counts``.
    4. Serialise the final frequency table to *output_path* as JSON.

    Returns the output file path.
    """
    # ── Phase 1: split ──────────────────────────────────────────────────────
    shards: List[str] = split_into_shards(text, n_shards)
    flyte.logger.info("Split corpus into %d shards (%d tokens total)",
                      len(shards), sum(len(s.split()) for s in shards))

    # ── Phase 2: map – run count_shard on every shard concurrently ──────────
    # asyncio.gather schedules all coroutines on the event loop simultaneously
    # so each shard's counting overlaps with all others.
    shard_counts: List[Dict[str, int]] = list(
        await asyncio.gather(*[count_shard(shard) for shard in shards])
    )
    flyte.logger.info("Map phase complete: collected %d shard-count dicts", len(shard_counts))

    # ── Phase 3: reduce ──────────────────────────────────────────────────────
    word_frequencies: Dict[str, int] = await reduce_counts(shard_counts)
    flyte.logger.info("Reduce phase complete: %d unique words", len(word_frequencies))

    # ── Phase 4: write JSON ──────────────────────────────────────────────────
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(word_frequencies, fh, indent=2, ensure_ascii=False)
    flyte.logger.info("Results written to %s", out)

    return str(out)


# ---------------------------------------------------------------------------
# Local entry-point
# ---------------------------------------------------------------------------

async def _main() -> None:
    output = await word_count_pipeline(
        text=SAMPLE_TEXT,
        n_shards=8,
        output_path="/home/user/flyte_project/wordcount.json",
    )
    # Pretty-print a quick summary
    result_path = Path(output)
    with result_path.open() as fh:
        freq: Dict[str, int] = json.load(fh)
    top_n = 15
    print(f"\n{'='*50}")
    print(f"  Word-count complete — {len(freq)} unique words")
    print(f"  Results: {result_path}")
    print(f"{'='*50}")
    print(f"  Top {top_n} words:")
    for rank, (word, count) in enumerate(list(freq.items())[:top_n], start=1):
        bar = "█" * min(count // 5 + 1, 40)
        print(f"  {rank:>2}. {word:<18} {count:>5}  {bar}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(_main())
