"""Flyte 2.0 distributed map-reduce word frequency counter."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    import flyte  # type: ignore
except ImportError:  # pragma: no cover - fallback when flyte is unavailable
    flyte = None


DEFAULT_TEXT = (
    "Flyte 2.0 enables distributed map reduce workloads. "
    "This example counts word frequencies using asyncio."
)

OUTPUT_PATH = Path("/home/user/flyte_project/wordcount.json")


TaskEnvironment = getattr(flyte, "TaskEnvironment", None)
Resources = getattr(flyte, "Resources", None)


def build_resources(resources: Dict[str, str]) -> Any:
    if Resources is None:
        return resources
    return Resources(cpu=resources.get("cpu"), memory=resources.get("mem"))


def build_environment(name: str, resources: Dict[str, str]):
    if TaskEnvironment is None:
        return None
    return TaskEnvironment(name=name, resources=build_resources(resources))


def shard_text(text: str, shards: int) -> List[str]:
    """Split text into roughly equal shards by words."""
    words = text.split()
    if shards <= 0:
        raise ValueError("shards must be positive")
    chunk_size = max(1, len(words) // shards)
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]


def normalize_words(text: str) -> Iterable[str]:
    return re.findall(r"\b[\w']+\b", text.lower())


_map_env = build_environment("wordcount-map", {"cpu": "1", "mem": "200Mi"})
_reduce_env = build_environment("wordcount-reduce", {"cpu": "1", "mem": "200Mi"})


def _count_words_core(shard: str) -> Counter[str]:
    return Counter(normalize_words(shard))


def _reduce_counts_core(counts: Iterable[Counter[str]]) -> Counter[str]:
    total = Counter()
    for counter in counts:
        total.update(counter)
    return total


if _map_env is not None:

    @_map_env.task
    async def count_words(shard: str) -> Dict[str, int]:
        await asyncio.sleep(0)  # allow cooperative scheduling
        return dict(_count_words_core(shard))

else:

    async def count_words(shard: str) -> Dict[str, int]:
        await asyncio.sleep(0)  # allow cooperative scheduling
        return dict(_count_words_core(shard))


if _reduce_env is not None:

    @_reduce_env.task
    async def reduce_counts(counts: List[Dict[str, int]]) -> Dict[str, int]:
        counter_list = [Counter(item) for item in counts]
        return dict(_reduce_counts_core(counter_list))

else:

    async def reduce_counts(counts: List[Dict[str, int]]) -> Dict[str, int]:
        counter_list = [Counter(item) for item in counts]
        return dict(_reduce_counts_core(counter_list))


async def map_reduce_wordcount(text: str, shards: int) -> Dict[str, int]:
    """Run the async map-reduce workflow and return word frequencies."""
    shard_list = shard_text(text, shards)
    map_tasks = [count_words(shard) for shard in shard_list]
    mapped_counts = await asyncio.gather(*map_tasks)
    reduced = await reduce_counts(mapped_counts)
    return dict(sorted(reduced.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text-file", type=Path, help="Path to a text file to process")
    parser.add_argument("--shards", type=int, default=4, help="Number of shards")
    return parser.parse_args()


def load_text(text_file: Path | None) -> str:
    if text_file is None:
        return DEFAULT_TEXT
    return text_file.read_text(encoding="utf-8")


def write_output(counts: Dict[str, int], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(counts, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    args = parse_args()
    text = load_text(args.text_file)
    counts = asyncio.run(map_reduce_wordcount(text, args.shards))
    write_output(counts, OUTPUT_PATH)


if __name__ == "__main__":
    main()
