import json
import os
from typing import Dict, List

from flytekit import Cache, Resources, TaskEnvironment, map_task, task, workflow

OUTPUT_PATH = "/home/user/flyte_project/etl_output.json"

EXTRACT_ENV = TaskEnvironment(resources=Resources(cpu="500m", mem="512Mi"))
TRANSFORM_ENV = TaskEnvironment(resources=Resources(cpu="1", mem="1Gi"))

EXTRACT_CACHE = Cache(version="1", serialize=True)


@task(task_environment=EXTRACT_ENV, cache=EXTRACT_CACHE)
def extract_source(source: str) -> List[Dict[str, str]]:
    """Extract data from supported sources and handle failures gracefully."""
    try:
        if source == "database":
            return [
                {"id": "db-1", "name": "alpha", "source": source},
                {"id": "db-2", "name": "beta", "source": source},
            ]
        if source == "api":
            return [
                {"id": "api-1", "name": "gamma", "source": source},
                {"id": "api-2", "name": "delta", "source": source},
            ]
        return []
    except Exception as exc:
        return [{"id": "", "name": f"error:{exc}", "source": source}]


@task(task_environment=TRANSFORM_ENV)
def transform_record(record: Dict[str, str]) -> Dict[str, str]:
    """Normalize record fields for downstream loading."""
    return {
        "record_id": record.get("id", ""),
        "name": record.get("name", "").upper(),
        "source": record.get("source", "unknown"),
    }


@task
def flatten_records(nested: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    return [record for batch in nested for record in batch]


@task
def load_records(records: List[Dict[str, str]], output_path: str = OUTPUT_PATH) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump({"records": records}, handle, indent=2)
    return output_path


@workflow
def etl_pipeline(sources: List[str] = ["database", "api", "unknown"]) -> str:
    extracted = map_task(extract_source)(source=sources)
    flattened = flatten_records(nested=extracted)
    transformed = map_task(transform_record)(record=flattened)
    return load_records(records=transformed)


if __name__ == "__main__":
    etl_pipeline()
