import json
import os
import concurrent.futures

class flyte:
    class Cache:
        def __init__(self, version="1.0"):
            self.version = version
            self.cache = {}
            
        def __call__(self, func):
            def wrapper(*args, **kwargs):
                key = str(args) + str(kwargs)
                if key not in self.cache:
                    self.cache[key] = func(*args, **kwargs)
                return self.cache[key]
            return wrapper

class TaskEnvironment:
    def __init__(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

extract_env = TaskEnvironment(cpu=2, memory="4Gi")
transform_env = TaskEnvironment(cpu=4, memory="8Gi")

@extract_env
@flyte.Cache(version="1.0")
def extract(source):
    if source == "database":
        return {"source": source, "data": [1, 2, 3]}
    elif source == "api":
        return {"source": source, "data": [4, 5, 6]}
    else:
        # Handle unknown sources gracefully
        print(f"Unknown source: {source}")
        return {"source": source, "data": []}

@transform_env
def transform(record):
    try:
        if record is None:
            return None
        return {"source": record["source"], "transformed_data": [x * 2 for x in record.get("data", [])]}
    except Exception as e:
        print(f"Transform failed for {record}: {e}")
        return None

def load(records):
    valid_records = [r for r in records if r is not None]
    with open("/home/user/flyte_project/etl_output.json", "w") as f:
        json.dump(valid_records, f, indent=2)

def main():
    sources = ["database", "api", "unknown_source_123"]
    
    # Extract
    extracted = []
    for source in sources:
        try:
            res = extract(source)
            extracted.append(res)
        except Exception as e:
            print(f"Extraction failed for {source}: {e}")
            
    # Transform in parallel
    transformed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(transform, record): record for record in extracted}
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                transformed.append(result)
            except Exception as e:
                print(f"Transform future failed: {e}")
                
    # Load
    load(transformed)

if __name__ == "__main__":
    main()
