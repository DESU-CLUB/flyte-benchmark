import asyncio
import json
from tasks import run_pipeline

if __name__ == "__main__":
    result = asyncio.run(run_pipeline(["source_a", "source_b", "source_c"]))
    with open("/home/user/flyte_project/aggregate_report.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Pipeline complete:", result)
