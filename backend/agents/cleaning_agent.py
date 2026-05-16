import pandas as pd
import numpy as np


def run_cleaning_agent(filepath: str) -> dict:
    """
    Cleans the uploaded CSV and returns a quality report + cleaned DataFrame.
    """
    df = pd.read_csv(filepath, encoding="latin-1")

    report = {
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "issues_found": [],
        "fixes_applied": [],
    }

    # ── 1. Normalize column names ──────────────────────────────────────────
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace("/", "_")
    )

    # ── 2. Parse date columns ──────────────────────────────────────────────
    date_cols = [c for c in df.columns if "date" in c]
    for col in date_cols:
        before = df[col].isna().sum()
        df[col] = pd.to_datetime(df[col], errors="coerce")
        after = df[col].isna().sum()
        if after > before:
            report["issues_found"].append(f"{col}: {after - before} unparseable dates")
        report["fixes_applied"].append(f"Parsed '{col}' as datetime")

    # ── 3. Missing values ──────────────────────────────────────────────────
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]

    for col, count in null_cols.items():
        report["issues_found"].append(f"'{col}' has {count} missing values")
        if df[col].dtype in [np.float64, np.int64]:
            df[col] = df[col].fillna(df[col].median())
            report["fixes_applied"].append(f"Filled '{col}' nulls with median")
        else:
            df[col] = df[col].fillna("Unknown")
            report["fixes_applied"].append(f"Filled '{col}' nulls with 'Unknown'")

    # ── 4. Duplicate rows ──────────────────────────────────────────────────
    dupes = df.duplicated().sum()
    if dupes > 0:
        report["issues_found"].append(f"{dupes} duplicate rows found")
        df = df.drop_duplicates()
        report["fixes_applied"].append(f"Removed {dupes} duplicate rows")

    # ── 5. Negative values in numeric columns ─────────────────────────────
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0 and col not in ["profit", "discount"]:
            report["issues_found"].append(
                f"'{col}' has {neg_count} negative values (kept — may be returns)"
            )

    # ── 6. Data quality score ──────────────────────────────────────────────
    total_issues = len(report["issues_found"])
    quality_score = max(0, 100 - (total_issues * 5))

    report["cleaned_rows"] = len(df)
    report["cleaned_columns"] = len(df.columns)
    report["data_quality_score"] = quality_score
    report["columns"] = list(df.columns)

    return {"dataframe": df, "report": report}