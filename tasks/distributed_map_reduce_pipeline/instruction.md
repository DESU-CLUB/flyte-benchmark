# Flyte 2.0 Distributed Map-Reduce Word Counter

Implement a distributed word frequency counter using a Flyte 2.0 map-reduce pattern at `/home/user/flyte_project/mapreduce.py`.

## Requirements
- Use `flyte.TaskEnvironment` with appropriate resources
- Implement map-reduce pattern: split text into shards, count words per shard in parallel with `asyncio.gather`, then reduce
- Count word frequencies in the input text
- Write results to `/home/user/flyte_project/wordcount.json`

## Constraints
- Project path: /home/user/flyte_project
- Log file: /home/user/flyte_project/wordcount.json
