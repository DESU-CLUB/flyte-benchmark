import asyncio
import csv
import json
import flyte

env = flyte.TaskEnvironment("file-env")


@env.task
async def read_csv(path: str) -> list:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


@env.task
async def filter_high_scores(records: list, threshold: int) -> list:
    return [r for r in records if int(r["score"]) > threshold]


@env.task
async def write_results(records: list, output_path: str) -> str:
    with open(output_path, "w") as f:
        json.dump(records, f)
    return output_path


@env.task
async def csv_filter_pipeline(input_path: str, output_path: str, threshold: int) -> str:
    records = await read_csv(input_path)
    filtered = await filter_high_scores(records, threshold)
    result_path = await write_results(filtered, output_path)
    return result_path


if __name__ == "__main__":
    asyncio.run(csv_filter_pipeline(
        "/home/user/flyte_project/input.csv",
        "/home/user/flyte_project/filtered.json",
        80
    ))