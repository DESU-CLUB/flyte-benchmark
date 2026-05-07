from environments import cpu_env, gpu_env, eval_env

@cpu_env.task
async def preprocess(raw_data: list) -> dict:
    cleaned = [float(x) for x in raw_data if x is not None]
    return {"data": cleaned, "n_samples": len(cleaned), "preprocessing_env": "cpu"}

@gpu_env.task
async def train(preprocessed: dict) -> dict:
    return {
        "model_weights": [0.1 * i for i in range(5)],
        "n_samples_trained": preprocessed["n_samples"],
        "training_env": "gpu",
        "loss": max(0.01, 1.0 / preprocessed["n_samples"])
    }

@eval_env.task
async def evaluate(model: dict, test_data: list) -> dict:
    return {
        "accuracy": min(0.99, model["n_samples_trained"] * 0.05),
        "loss": model["loss"],
        "test_samples": len(test_data),
        "eval_env": "cpu"
    }

@cpu_env.task
async def full_pipeline(train_data: list, test_data: list) -> dict:
    preprocessed = await preprocess(train_data)
    model = await train(preprocessed)
    eval_result = await evaluate(model, test_data)
    return {"preprocessing": preprocessed, "model": model, "evaluation": eval_result}
