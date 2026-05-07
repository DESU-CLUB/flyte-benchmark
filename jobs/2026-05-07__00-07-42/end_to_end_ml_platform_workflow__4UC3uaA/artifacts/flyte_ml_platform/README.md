# Flyte 2.0 ML Platform

A complete end-to-end machine learning platform built with Flyte 2.0 that orchestrates data ingestion, validation, parallel model training, evaluation, and automatic model selection.

## 🚀 Features

- **Data Ingestion**: Automated synthetic dataset generation with configurable parameters
- **Data Validation**: Comprehensive data quality checks and validation
- **Parallel Model Training**: Train multiple models simultaneously for efficiency
- **Model Evaluation**: Comprehensive evaluation metrics (accuracy, precision, recall, F1-score)
- **Model Selection**: Automatic selection of the best model based on configurable metrics
- **Logging**: Detailed logging of all pipeline stages to JSON
- **Reproducibility**: Configurable random seeds for reproducible results

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ML Platform Workflow                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    1. Data Ingestion                         │
│  - Generate synthetic dataset                                │
│  - Split into train/test sets                                │
│  - Save to CSV files                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. Data Validation                        │
│  - Check sample size requirements                            │
│  - Validate missing values ratio                            │
│  - Verify target column presence                             │
│  - Calculate statistics                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              3. Parallel Model Training                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Random       │  │ Gradient     │  │ Logistic     │      │
│  │ Forest       │  │ Boosting     │  │ Regression   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. Model Evaluation                       │
│  - Evaluate all models on test data                          │
│  - Calculate accuracy, precision, recall, F1-score           │
│  - Record performance metrics                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    5. Model Selection                        │
│  - Compare all models based on selected metric               │
│  - Select best performing model                              │
│  - Return model with metrics                                 │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or navigate to the project directory:
```bash
cd /home/user/flyte_project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install in development mode:
```bash
pip install -e .
```

## 📖 Usage

### Local Execution

Run the workflow locally for testing:

```bash
python workflow.py
```

This will execute the complete pipeline with default parameters and output results to the console and `platform_output.json`.

### Custom Parameters

You can customize the workflow by modifying the parameters in `workflow.py`:

```python
best_model = ml_platform_workflow(
    n_samples=2000,           # Number of samples
    n_features=25,            # Total number of features
    n_informative=20,         # Number of informative features
    random_state=42,          # Random seed
    selection_metric="accuracy"  # Metric for model selection
)
```

### Available Selection Metrics

- `accuracy`: Overall accuracy of predictions
- `precision`: Weighted precision score
- `recall`: Weighted recall score
- `f1_score`: Weighted F1-score (default)

## 📊 Output

The workflow generates several outputs:

### 1. Platform Output Log (`platform_output.json`)

Detailed JSON log containing:
- Data ingestion statistics
- Validation results
- Model training metrics
- Model evaluation results
- Model selection information

Example output:
```json
[
  {
    "stage": "data_ingestion",
    "status": "completed",
    "n_samples": 1000,
    "train_size": 800,
    "test_size": 200,
    "timestamp": "2024-01-01T12:00:00"
  },
  {
    "stage": "model_selection",
    "status": "completed",
    "best_model": "random_forest",
    "selection_metric": "f1_score",
    "best_value": 0.9234,
    "timestamp": "2024-01-01T12:05:00"
  }
]
```

### 2. Trained Models

Each trained model is saved as a pickle file:
- `random_forest_model.pkl`
- `gradient_boosting_model.pkl`
- `logistic_regression_model.pkl`

### 3. Data Files

- `train_data.csv`: Training dataset
- `test_data.csv`: Test dataset

## 🔧 Configuration

Edit `config.yaml` to customize platform behavior:

```yaml
# Data ingestion settings
data_ingestion:
  n_samples: 1000
  n_features: 20
  n_informative: 15

# Model training settings
model_training:
  models:
    - name: random_forest
      type: random_forest
      params:
        n_estimators: 100

# Model selection settings
model_selection:
  default_metric: f1_score
```

## 🧪 Testing

The workflow includes a local test mode. Simply run:

```bash
python workflow.py
```

This will execute all tasks sequentially and display results in the console.

## 📁 Project Structure

```
flyte_project/
├── workflow.py              # Main Flyte workflow definition
├── requirements.txt         # Python dependencies
├── setup.py                # Package setup configuration
├── config.yaml             # Platform configuration
├── README.md               # This file
├── train_data.csv          # Generated training data
├── test_data.csv           # Generated test data
├── *model.pkl              # Trained models
└── platform_output.json    # Execution logs
```

## 🎯 Supported Models

The platform currently supports three model types:

1. **Random Forest**: Ensemble of decision trees
   - Good for complex patterns
   - Handles non-linear relationships

2. **Gradient Boosting**: Sequential ensemble method
   - High predictive power
   - Good for structured data

3. **Logistic Regression**: Linear classification model
   - Fast training
   - Good baseline model
   - Interpretable coefficients

## 🔍 Data Validation

The platform performs the following validation checks:

- Minimum sample size requirements
- Missing value ratio limits
- Target column presence
- Data type consistency
- Feature distribution analysis

## 📈 Evaluation Metrics

All models are evaluated using:

- **Accuracy**: Overall correctness of predictions
- **Precision**: Weighted average precision
- **Recall**: Weighted average recall
- **F1-Score**: Harmonic mean of precision and recall

## 🚀 Flyte Deployment

To deploy this workflow to a Flyte cluster:

1. Register the workflow:
```bash
flytectl register workflow \
  --project flyte-ml-platform \
  --domain development \
  --archive workflow.py
```

2. Execute the workflow:
```bash
flytectl launch workflow \
  --project flyte-ml-platform \
  --domain development \
  --name ml_platform_workflow \
  --inputs n_samples=1000,n_features=20
```

## 🤝 Contributing

To extend the platform:

1. Add new models in `train_model_task`
2. Add new validation checks in `data_validation_task`
3. Add new evaluation metrics in `evaluate_models_task`
4. Customize selection criteria in `select_best_model_task`

## 📝 License

This project is provided as-is for educational and development purposes.

## 🆘 Troubleshooting

### Common Issues

1. **Import Error**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Permission Error**: Check write permissions in project directory

3. **Memory Error**: Reduce `n_samples` parameter for smaller datasets

## 📞 Support

For issues or questions:
- Check the logs in `platform_output.json`
- Review the console output for error messages
- Verify all dependencies are correctly installed

---

Built with ❤️ using Flyte 2.0