import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from database import get_engine


def run_anomaly_agent(contamination: float = 0.05) -> dict:
    """
    Detects anomalous orders using IsolationForest.
    contamination = expected % of outliers (5% by default).
    """
    engine = get_engine()

    try:
        df = pd.read_sql("SELECT * FROM sales", con=engine)
    except Exception as e:
        return {"error": f"Could not read sales table: {str(e)}"}

    # Find key numeric columns
    sales_col = next((c for c in df.columns if c == "sales"), None)
    profit_col = next((c for c in df.columns if c == "profit"), None)
    quantity_col = next((c for c in df.columns if c == "quantity"), None)

    feature_cols = [c for c in [sales_col, profit_col, quantity_col] if c]

    if not feature_cols:
        return {"error": "No numeric feature columns found"}

    features = df[feature_cols].fillna(0)

    # Train IsolationForest
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
    )
    df["anomaly_score"] = model.fit_predict(features)
    df["anomaly"] = df["anomaly_score"] == -1

    anomalies = df[df["anomaly"] == True].copy()

    # Build readable output
    result_cols = []
    for candidate in ["order_id", "order_date", "customer_name", "product_name",
                       "region", "sales", "profit", "quantity"]:
        if candidate in df.columns:
            result_cols.append(candidate)

    anomaly_records = anomalies[result_cols].head(20).copy()

    # Convert dates to string for JSON serialization
    for col in anomaly_records.columns:
        if "date" in col:
            anomaly_records.loc[:, col] = anomaly_records[col].astype(str)

    return {
        "total_anomalies": int(df["anomaly"].sum()),
        "total_records": len(df),
        "anomaly_rate_percent": round(df["anomaly"].mean() * 100, 2),
        "anomalies": anomaly_records.to_dict(orient="records"),
        "summary": {
            "avg_anomaly_sales": round(float(anomalies[sales_col].mean()), 2) if sales_col else None,
            "avg_normal_sales": round(float(df[~df["anomaly"]][sales_col].mean()), 2) if sales_col else None,
            "feature_columns_used": feature_cols,
        },
    }