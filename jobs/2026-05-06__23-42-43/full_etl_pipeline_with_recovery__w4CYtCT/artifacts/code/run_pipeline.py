"""
Local runner for the Flyte 2.0 ETL pipeline.

Executes the workflow entirely in-process (no Flyte cluster needed)
using flytekit's local execution mode, then pretty-prints the summary
and the first few transformed records from the output file.

Usage:
    python run_pipeline.py [--db-url URL] [--api-endpoint URL]
                           [--api-key KEY] [--unknown-source NAME]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ── Import the workflow ───────────────────────────────────────────────────
from etl_pipeline import OUTPUT_PATH, etl_workflow


def _banner(msg: str, width: int = 62) -> None:
    bar = "─" * width
    print(f"\n╭{bar}╮")
    print(f"│  {msg:<{width - 1}}│")
    print(f"╰{bar}╯")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Flyte ETL pipeline locally.")
    parser.add_argument("--db-url",       default="postgresql://prod-db:5432/warehouse")
    parser.add_argument("--api-endpoint", default="https://api.example.com/v2/events")
    parser.add_argument("--api-key",      default="demo-key-abc123")
    parser.add_argument("--unknown-source", default="legacy_csv")
    parser.add_argument("--unknown-conn",   default="ftp://legacy.internal/data/")
    args = parser.parse_args()

    _banner("Flyte 2.0 ETL Pipeline  –  Local Execution")

    # ── Execute ───────────────────────────────────────────────────────────
    result = etl_workflow(
        database_url=args.db_url,
        api_endpoint=args.api_endpoint,
        api_key=args.api_key,
        unknown_source_name=args.unknown_source,
        unknown_connection_string=args.unknown_conn,
    )

    # ── Summary ───────────────────────────────────────────────────────────
    _banner("Pipeline Summary")
    rows = [
        ("Status",             result.status),
        ("Records extracted",  str(result.total_records_extracted)),
        ("Records transformed",str(result.total_records_transformed)),
        ("Sources succeeded",  ", ".join(result.sources_succeeded)),
        ("Sources failed",     ", ".join(result.sources_failed) or "none"),
        ("Duration",           f"{result.pipeline_duration_seconds}s"),
        ("Output file",        result.output_path),
    ]
    for label, value in rows:
        print(f"  {label:<26}: {value}")

    # ── Peek at output file ───────────────────────────────────────────────
    out_path = Path(OUTPUT_PATH)
    if out_path.exists():
        _banner(f"Output preview  →  {OUTPUT_PATH}")
        with open(out_path) as fh:
            data = json.load(fh)
        preview = {
            "pipeline":  data["pipeline"],
            "status":    data["status"],
            "summary":   data["summary"],
            "records_preview (first 3)": data["records"][:3],
        }
        print(json.dumps(preview, indent=2))
    else:
        print(f"\n⚠  Output file not found at {OUTPUT_PATH}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
