"""
data_ingestion.py
-----------------
Flyte 2.0 task: Ingest raw data and return a structured dataset.

Simulates reading a CSV from a data source and converting it into
a clean pandas DataFrame for downstream processing.
"""

import typing
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from flytekit import task, current_context
from flytekit.types.structured import StructuredDataset


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass
class IngestionConfig:
    """Configuration for the data ingestion step."""
    n_samples: int = 2000
    n_features: int = 20
    n_informative: int = 10
    n_classes: int = 2
    random_state: int = 42
    test_size: float = 0.20
    noise_fraction: float = 0.05   # fraction of rows with injected noise
    dataset_name: str = "synthetic_classification"


@dataclass
class RawDataset:
    """Raw output bundle from ingestion."""
    feature_columns: typing.List[str] = field(default_factory=list)
    target_column: str = "target"
    n_samples: int = 0
    n_features: int = 0
    class_distribution: typing.Dict[str, int] = field(default_factory=dict)
    dataset_name: str = ""
    ingestion_metadata: typing.Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@task(cache=True, cache_version="v1.0")
def ingest_data(config: IngestionConfig) -> typing.Tuple[pd.DataFrame, RawDataset]:
    """
    Generate / ingest a classification dataset.

    Returns
    -------
    df       : pandas DataFrame (features + target)
    metadata : RawDataset describing what was ingested
    """
    from sklearn.datasets import make_classification

    rng = np.random.default_rng(config.random_state)

    # ---- generate base dataset ----------------------------------------
    X, y = make_classification(
        n_samples=config.n_samples,
        n_features=config.n_features,
        n_informative=config.n_informative,
        n_redundant=max(0, config.n_features - config.n_informative - 2),
        n_classes=config.n_classes,
        random_state=config.random_state,
        flip_y=0.03,
    )

    feature_names = [f"feature_{i:02d}" for i in range(config.n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y.astype(int)

    # ---- inject synthetic noise (missing + outliers) -------------------
    n_noisy = int(config.noise_fraction * len(df))
    noisy_idx = rng.choice(len(df), size=n_noisy, replace=False)
    noisy_cols = rng.choice(feature_names, size=max(1, config.n_features // 5), replace=False)

    # Random NaNs
    nan_idx = noisy_idx[: n_noisy // 2]
    df.loc[nan_idx, noisy_cols[0]] = np.nan

    # Outliers (10× std)
    out_idx = noisy_idx[n_noisy // 2 :]
    df.loc[out_idx, noisy_cols[-1]] = df[noisy_cols[-1]].std() * 10.0

    # ---- build metadata -----------------------------------------------
    class_dist = {str(c): int((y == c).sum()) for c in np.unique(y)}
    meta = RawDataset(
        feature_columns=feature_names,
        target_column="target",
        n_samples=len(df),
        n_features=config.n_features,
        class_distribution=class_dist,
        dataset_name=config.dataset_name,
        ingestion_metadata={
            "random_state": str(config.random_state),
            "noise_fraction": str(config.noise_fraction),
            "nan_rows_injected": str(len(nan_idx)),
            "outlier_rows_injected": str(len(out_idx)),
            "source": "sklearn.make_classification (synthetic)",
        },
    )

    print(f"[ingest_data] Ingested {len(df)} rows × {config.n_features} features")
    print(f"[ingest_data] Class distribution: {class_dist}")
    print(f"[ingest_data] NaN rows: {df.isna().any(axis=1).sum()}")

    return df, meta
