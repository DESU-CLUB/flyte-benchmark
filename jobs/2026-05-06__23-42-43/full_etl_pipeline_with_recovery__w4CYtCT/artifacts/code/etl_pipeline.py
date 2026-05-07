"""
Flyte 2.0 Production-Ready ETL Pipeline with Recovery
======================================================

Architecture
------------
 ┌─────────────────────────────────────────────────────────┐
 │                     etl_workflow                        │
 │                                                         │
 │  extract_env (1 CPU / 512Mi)                            │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
 │  │ extract_db   │  │ extract_api  │  │ extract_src  │  │
 │  │  (cached)    │  │  (cached)    │  │  (graceful)  │  │
 │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
 │         └─────────────────┴──────────────────┘          │
 │                           │ merge                        │
 │  transform_env (2 CPU / 1Gi)                            │
 │              ┌────────────▼────────────┐                │
 │              │  map_task(transform)    │  (parallel)    │
 │              └────────────┬────────────┘                │
 │                           │                             │
 │              ┌────────────▼────────────┐                │
 │              │    load_to_warehouse    │                 │
 │              └─────────────────────────┘                │
 └─────────────────────────────────────────────────────────┘

* Two TaskEnvironments:
    - extract_env : requests=Resources(cpu="1", mem="512Mi")
    - transform_env: requests=Resources(cpu="2", mem="1Gi")
* flyte.Cache(version="v1", serialize=True) on every extraction task
* Unknown sources are handled by returning an empty result set (no crash)
* Final result written to /home/user/flyte_project/etl_output.json
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import flytekit
from flytekit import Cache, Resources, map_task, task, workflow
from flytekit.core.environment import Environment

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class RawRecord:
    """A single record as it arrives from any source."""
    id: str
    source: str
    payload: str
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TransformedRecord:
    """A record after transformation (normalised, enriched)."""
    id: str
    source: str
    value: float
    tags: List[str]
    processed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ExtractionResult:
    """
    Wrapper returned by every extraction task.
    `success=False` signals a source failure; the pipeline continues.
    """
    source: str
    records: List[RawRecord]
    success: bool
    error_message: str = ""
    record_count: int = 0

    def __post_init__(self) -> None:
        self.record_count = len(self.records)


@dataclass
class LoadResult:
    """Summary written to the output file."""
    status: str
    total_records_extracted: int
    total_records_transformed: int
    sources_attempted: List[str]
    sources_succeeded: List[str]
    sources_failed: List[str]
    output_path: str
    pipeline_duration_seconds: float
    completed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# TaskEnvironments  (Flyte 2.0 – flytekit.core.environment.Environment)
# ---------------------------------------------------------------------------
# Each Environment bundles resource specs so they can be reused across tasks.

extract_env = Environment(
    requests=Resources(cpu="1", mem="512Mi"),
    limits=Resources(cpu="2", mem="1Gi"),
)

transform_env = Environment(
    requests=Resources(cpu="2", mem="1Gi"),
    limits=Resources(cpu="4", mem="2Gi"),
)

# ---------------------------------------------------------------------------
# Extraction tasks  (cached, extraction_env resources)
# ---------------------------------------------------------------------------

EXTRACT_CACHE = Cache(version="v1", serialize=True)


@extract_env(cache=EXTRACT_CACHE, retries=2)
def extract_from_database(database_url: str) -> ExtractionResult:
    """
    Simulates pulling rows from a relational database.
    Cached so repeated calls with the same URL never hit the DB again.
    """
    print(f"[extract_from_database] Connecting to: {database_url}")
    try:
        # ── Simulated DB pull ─────────────────────────────────────────────
        random.seed(42)
        records = [
            RawRecord(
                id=f"db-{i:04d}",
                source="database",
                payload=json.dumps({"col_a": random.randint(1, 100),
                                    "col_b": f"row_{i}"}),
            )
            for i in range(10)
        ]
        print(f"[extract_from_database] Extracted {len(records)} records.")
        return ExtractionResult(source="database", records=records, success=True)
    except Exception as exc:  # pragma: no cover
        return ExtractionResult(
            source="database",
            records=[],
            success=False,
            error_message=str(exc),
        )


@extract_env(cache=EXTRACT_CACHE, retries=2)
def extract_from_api(api_endpoint: str, api_key: str) -> ExtractionResult:
    """
    Simulates paginated REST API extraction.
    Cached per (endpoint, api_key) pair.
    """
    print(f"[extract_from_api] Calling endpoint: {api_endpoint}")
    try:
        # ── Simulated HTTP pages ──────────────────────────────────────────
        random.seed(7)
        records = [
            RawRecord(
                id=f"api-{i:04d}",
                source="api",
                payload=json.dumps({"event": f"click_{i}",
                                    "score": round(random.uniform(0, 1), 4)}),
            )
            for i in range(8)
        ]
        print(f"[extract_from_api] Extracted {len(records)} records.")
        return ExtractionResult(source="api", records=records, success=True)
    except Exception as exc:  # pragma: no cover
        return ExtractionResult(
            source="api",
            records=[],
            success=False,
            error_message=str(exc),
        )


@extract_env(cache=EXTRACT_CACHE, retries=1)
def extract_from_unknown_source(source_name: str, connection_string: str) -> ExtractionResult:
    """
    Graceful handler for any source type that is not yet implemented.
    Returns an empty, but successful, result set – the pipeline is never aborted.
    """
    print(
        f"[extract_from_unknown_source] Source '{source_name}' is not recognised. "
        "Returning empty result set to allow downstream tasks to continue."
    )
    return ExtractionResult(
        source=source_name,
        records=[],
        success=True,          # <── graceful: does NOT fail the pipeline
        error_message=(
            f"Source '{source_name}' is unsupported. "
            "Gracefully returning empty record set."
        ),
    )


# ---------------------------------------------------------------------------
# Merge helper
# ---------------------------------------------------------------------------

@task
def merge_extraction_results(
    db_result: ExtractionResult,
    api_result: ExtractionResult,
    unknown_result: ExtractionResult,
) -> List[RawRecord]:
    """Combines records from all sources; logs warnings for failures."""
    combined: List[RawRecord] = []
    for result in (db_result, api_result, unknown_result):
        if not result.success:
            print(
                f"[merge] WARNING – source '{result.source}' failed: "
                f"{result.error_message}. Skipping."
            )
        else:
            combined.extend(result.records)
            print(f"[merge] Added {result.record_count} records from '{result.source}'.")

    print(f"[merge] Total merged records: {len(combined)}")
    return combined


# ---------------------------------------------------------------------------
# Transform task  (transform_env resources, used with map_task)
# ---------------------------------------------------------------------------

@transform_env
def transform_record(record: RawRecord) -> TransformedRecord:
    """
    Normalises and enriches a single record.
    This is the unit that map_task fans out in parallel over every record.
    """
    payload = json.loads(record.payload)

    # Derive a numeric `value` regardless of source schema
    if "col_a" in payload:
        value = float(payload["col_a"])
    elif "score" in payload:
        value = float(payload["score"]) * 100
    else:
        value = 0.0

    tags = [record.source, "etl-v1"]
    if value > 50:
        tags.append("high-value")

    return TransformedRecord(
        id=record.id,
        source=record.source,
        value=round(value, 4),
        tags=tags,
    )


# ---------------------------------------------------------------------------
# Pipeline clock task — captures wall-clock start inside a proper Flyte task
# so the timestamp is always evaluated at runtime, not at import time.
# ---------------------------------------------------------------------------

@task
def record_pipeline_start() -> str:
    """Returns the current UTC timestamp as an ISO-8601 string."""
    ts = datetime.utcnow().isoformat()
    print(f"[record_pipeline_start] Pipeline started at {ts}")
    return ts


# ---------------------------------------------------------------------------
# Load task
# ---------------------------------------------------------------------------

OUTPUT_PATH = "/home/user/flyte_project/etl_output.json"


@task
def load_to_warehouse(
    transformed_records: List[TransformedRecord],
    db_result: ExtractionResult,
    api_result: ExtractionResult,
    unknown_result: ExtractionResult,
    pipeline_start_iso: str,
) -> LoadResult:
    """
    Writes the final output JSON and produces a summary LoadResult.
    In production this would INSERT into a data warehouse (BigQuery, Redshift, …).
    """
    start_ts = datetime.fromisoformat(pipeline_start_iso)
    duration = (datetime.utcnow() - start_ts).total_seconds()

    sources_succeeded = [
        r.source for r in (db_result, api_result, unknown_result) if r.success
    ]
    sources_failed = [
        r.source for r in (db_result, api_result, unknown_result) if not r.success
    ]

    output = {
        "pipeline": "flyte-etl-v1",
        "status": "SUCCESS" if transformed_records else "EMPTY",
        "summary": {
            "total_records_extracted": (
                db_result.record_count
                + api_result.record_count
                + unknown_result.record_count
            ),
            "total_records_transformed": len(transformed_records),
            "sources_attempted": ["database", "api", "unknown_source"],
            "sources_succeeded": sources_succeeded,
            "sources_failed": sources_failed,
            "pipeline_duration_seconds": round(duration, 3),
            "completed_at": datetime.utcnow().isoformat(),
            "output_path": OUTPUT_PATH,
        },
        "records": [
            {
                "id": r.id,
                "source": r.source,
                "value": r.value,
                "tags": r.tags,
                "processed_at": r.processed_at,
            }
            for r in transformed_records
        ],
    }

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"[load] Wrote {len(transformed_records)} records → {OUTPUT_PATH}")

    return LoadResult(
        status=output["status"],
        total_records_extracted=output["summary"]["total_records_extracted"],
        total_records_transformed=output["summary"]["total_records_transformed"],
        sources_attempted=output["summary"]["sources_attempted"],
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
        output_path=OUTPUT_PATH,
        pipeline_duration_seconds=round(duration, 3),
    )


# ---------------------------------------------------------------------------
# Top-level workflow
# ---------------------------------------------------------------------------

@workflow
def etl_workflow(
    database_url: str = "postgresql://prod-db:5432/warehouse",
    api_endpoint: str = "https://api.example.com/v2/events",
    api_key: str = "demo-key-abc123",
    unknown_source_name: str = "legacy_csv",
    unknown_connection_string: str = "ftp://legacy.internal/data/",
) -> LoadResult:
    """
    Full ETL workflow:

    1. **Extract** – three sources in parallel (database, API, unknown).
       Each extraction task is independently cached with ``Cache(version='v1')``.
       The unknown-source handler returns an empty record set gracefully.

    2. **Merge** – combine all records into one list, log any source warnings.

    3. **Transform** – fan-out via ``map_task`` so every record is processed
       concurrently on transform_env nodes (2 CPU / 1Gi).

    4. **Load** – write the JSON result to ``/home/user/flyte_project/etl_output.json``.
    """
    pipeline_start = record_pipeline_start()

    # ── EXTRACT (parallel fan-out) ─────────────────────────────────────────
    db_result = extract_from_database(database_url=database_url)
    api_result = extract_from_api(api_endpoint=api_endpoint, api_key=api_key)
    unknown_result = extract_from_unknown_source(
        source_name=unknown_source_name,
        connection_string=unknown_connection_string,
    )

    # ── MERGE ──────────────────────────────────────────────────────────────
    all_records = merge_extraction_results(
        db_result=db_result,
        api_result=api_result,
        unknown_result=unknown_result,
    )

    # ── TRANSFORM (parallel map) ───────────────────────────────────────────
    transformed = map_task(transform_record)(record=all_records)

    # ── LOAD ───────────────────────────────────────────────────────────────
    result = load_to_warehouse(
        transformed_records=transformed,
        db_result=db_result,
        api_result=api_result,
        unknown_result=unknown_result,
        pipeline_start_iso=pipeline_start,
    )

    return result


# ---------------------------------------------------------------------------
# Entry point for direct execution (``python etl_pipeline.py``)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = etl_workflow()
    print("\n" + "=" * 60)
    print("ETL Pipeline completed successfully!")
    print(f"  Status                : {result.status}")
    print(f"  Records extracted     : {result.total_records_extracted}")
    print(f"  Records transformed   : {result.total_records_transformed}")
    print(f"  Sources succeeded     : {result.sources_succeeded}")
    print(f"  Sources failed        : {result.sources_failed}")
    print(f"  Duration              : {result.pipeline_duration_seconds}s")
    print(f"  Output written to     : {result.output_path}")
    print("=" * 60)
