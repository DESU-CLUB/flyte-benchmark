from flytekit import workflow
from tasks.tasks import ingest_data, validate_data, train_model, select_best_model

@workflow
def ml_pipeline() -> dict:
    """Main Flyte workflow for the ML platform."""
    df = ingest_data()
    validated_df = validate_data(df=df)
    
    # Parallel training of multiple models
    lr_result = train_model(df=validated_df, model_type="logistic_regression")
    rf_result = train_model(df=validated_df, model_type="random_forest")
    
    # Select the best performing model
    best_model = select_best_model(results=[lr_result, rf_result])
    return best_model

if __name__ == "__main__":
    print("Running ML pipeline locally...")
    result = ml_pipeline()
    print(f"Workflow completed. Best model: {result}")
