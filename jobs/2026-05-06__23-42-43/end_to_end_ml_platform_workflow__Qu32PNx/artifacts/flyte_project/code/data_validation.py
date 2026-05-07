"""
data_validation.py
------------------
Flyte 2.0 task: Validate and clean an ingested DataFrame.

Checks performed
~~~~~~~~~~~~~~~~
1. Schema / column presence
2. Missing-value rate per column
3. Outlier detection via IQR
4. Class balance (warn if imbalanced)
5. Feature correlation (warn if extremely correlated pairs exist)

If hard failures exceed the threshold the task raises, halting the pipeline.
"""

import typing
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from flytekit import task

from data_ingestion import RawDataset


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------

@dataclass
class ValidationConfig:
    max_missing_rate: float = 0.15       # column dropped above this
    iqr_multiplier: float = 3.0          # outlier fence
    min_class_ratio: float = 0.20        # warn below this
    max_correlation: float = 0.95        # warn above this
    imputation_strategy: str = "median"  # median | mean | drop


@dataclass
class ValidationReport:
    passed: bool = True
    n_rows_before: int = 0
    n_rows_after: int = 0
    n_cols_before: int = 0
    n_cols_after: int = 0
    dropped_columns: typing.List[str] = field(default_factory=list)
    outlier_rows_clipped: int = 0
    missing_imputed: int = 0
    warnings: typing.List[str] = field(default_factory=list)
    errors: typing.List[str] = field(default_factory=list)
    feature_stats: typing.Dict[str, typing.Dict[str, float]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@task(cache=True, cache_version="v1.0")
def validate_data(
    df: pd.DataFrame,
    raw_meta: RawDataset,
    config: ValidationConfig,
) -> typing.Tuple[pd.DataFrame, ValidationReport]:
    """
    Validate and clean the raw DataFrame.

    Returns a cleaned DataFrame and a validation report.
    Raises RuntimeError if hard validation errors are found.
    """
    report = ValidationReport(
        n_rows_before=len(df),
        n_cols_before=len(df.columns),
    )

    feature_cols = [c for c in df.columns if c != raw_meta.target_column]

    # ---- 1. Schema check -----------------------------------------------
    missing_cols = [c for c in raw_meta.feature_columns if c not in df.columns]
    if missing_cols:
        report.errors.append(f"Missing expected columns: {missing_cols}")
        report.passed = False

    # ---- 2. Drop high-missing-rate columns -----------------------------
    missing_rates = df[feature_cols].isna().mean()
    cols_to_drop = missing_rates[missing_rates > config.max_missing_rate].index.tolist()
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        report.dropped_columns.extend(cols_to_drop)
        report.warnings.append(
            f"Dropped {len(cols_to_drop)} column(s) with missing rate > "
            f"{config.max_missing_rate}: {cols_to_drop}"
        )
        feature_cols = [c for c in feature_cols if c not in cols_to_drop]

    # ---- 3. Impute remaining missing values ----------------------------
    if config.imputation_strategy == "drop":
        before = len(df)
        df = df.dropna()
        report.missing_imputed = before - len(df)
    else:
        for col in feature_cols:
            n_nan = df[col].isna().sum()
            if n_nan > 0:
                fill_val = (
                    df[col].median()
                    if config.imputation_strategy == "median"
                    else df[col].mean()
                )
                df[col] = df[col].fillna(fill_val)
                report.missing_imputed += int(n_nan)

    # ---- 4. Clip outliers via IQR fence --------------------------------
    clipped_mask = pd.Series(False, index=df.index)
    for col in feature_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lo = q1 - config.iqr_multiplier * iqr
        hi = q3 + config.iqr_multiplier * iqr
        outliers = (df[col] < lo) | (df[col] > hi)
        if outliers.any():
            df[col] = df[col].clip(lower=lo, upper=hi)
            clipped_mask |= outliers
    report.outlier_rows_clipped = int(clipped_mask.sum())

    # ---- 5. Class balance check ----------------------------------------
    y = df[raw_meta.target_column]
    class_ratios = y.value_counts(normalize=True)
    min_ratio = float(class_ratios.min())
    if min_ratio < config.min_class_ratio:
        report.warnings.append(
            f"Potential class imbalance: smallest class ratio = {min_ratio:.3f}"
        )

    # ---- 6. High correlation pairs (warn only) -------------------------
    corr_matrix = df[feature_cols].corr().abs()
    upper_tri = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )
    high_corr = [
        (c1, c2, float(upper_tri.loc[c1, c2]))
        for c1 in upper_tri.index
        for c2 in upper_tri.columns
        if upper_tri.loc[c1, c2] > config.max_correlation
    ]
    if high_corr:
        report.warnings.append(
            f"{len(high_corr)} highly correlated feature pair(s) found (>{config.max_correlation})"
        )

    # ---- 7. Feature statistics summary ---------------------------------
    desc = df[feature_cols].describe().to_dict()
    report.feature_stats = {
        col: {k: float(v) for k, v in stats.items()}
        for col, stats in desc.items()
    }

    # ---- Final state ---------------------------------------------------
    report.n_rows_after = len(df)
    report.n_cols_after = len(df.columns)

    if report.errors:
        raise RuntimeError(
            f"[validate_data] Hard validation failures: {report.errors}"
        )

    print(f"[validate_data] Validation PASSED={report.passed}")
    print(f"[validate_data] Rows: {report.n_rows_before} → {report.n_rows_after}")
    print(f"[validate_data] Cols dropped: {report.dropped_columns}")
    print(f"[validate_data] Missing imputed: {report.missing_imputed}")
    print(f"[validate_data] Outlier rows clipped: {report.outlier_rows_clipped}")
    for w in report.warnings:
        print(f"[validate_data] WARN: {w}")

    return df, report
