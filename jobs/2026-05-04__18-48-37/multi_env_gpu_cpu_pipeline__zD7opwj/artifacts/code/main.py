import asyncio
import json
from pipeline import full_pipeline

async def main():
    train_data = [1.0, None, 2.0, 3.0, None, 4.0, 5.0]
    test_data = [0.5, 1.5, 2.5]
    result = await full_pipeline(train_data, test_data)
    with open("/home/user/flyte_project/training_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
