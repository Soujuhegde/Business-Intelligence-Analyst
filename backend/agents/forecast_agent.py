import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from database import get_engine


def run_forecast_agent(days: int = 30) -> dict:
    """
    Reads sales data from DB, trains a regression model on daily sales,
    and forecasts the next N days.
    """
    engine = get_engine()

    try:
        df = pd.read_sql("SELECT * FROM sales", con=engine)
    except Exception as e:
        return {"error": f"Could not read sales table: {str(e)}"}

    # Find date and sales columns
    date_col = next((c for c in df.columns if "order_date" in c or "date" in c), None)
    sales_col = next((c for c in df.columns if "sales" in c), None)

    if not date_col or not sales_col:
        return {"error": "Could not find date or sales columns in data"}

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, sales_col])

    # Aggregate daily sales
    daily = (
        df.groupby(df[date_col].dt.date)[sales_col]
        .sum()
        .reset_index()
        .rename(columns={date_col: "date", sales_col: "sales"})
    )
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    # Feature: days since start
    daily["day_num"] = (daily["date"] - daily["date"].min()).dt.days

    X = daily[["day_num"]].values
    y = daily["sales"].values

    model = LinearRegression()
    model.fit(X, y)

    # Forecast future days
    last_day = daily["day_num"].max()
    future_days = np.arange(last_day + 1, last_day + days + 1).reshape(-1, 1)
    future_sales = model.predict(future_days)
    future_sales = np.maximum(future_sales, 0)  # no negative forecasts

    last_date = daily["date"].max()
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1), periods=days, freq="D"
    )

    # Historical data for chart
    historical = daily[["date", "sales"]].copy()
    historical["date"] = historical["date"].astype(str)

    # Forecast data for chart
    forecast = pd.DataFrame(
        {"date": future_dates.astype(str), "sales": future_sales.round(2)}
    )

    # Summary stats
    avg_daily = float(daily["sales"].mean())
    forecast_avg = float(future_sales.mean())
    growth_pct = ((forecast_avg - avg_daily) / avg_daily * 100) if avg_daily else 0

    return {
        "historical": historical.to_dict(orient="records"),
        "forecast": forecast.to_dict(orient="records"),
        "summary": {
            "historical_avg_daily_sales": round(avg_daily, 2),
            "forecast_avg_daily_sales": round(forecast_avg, 2),
            "growth_percent": round(growth_pct, 2),
            "forecast_days": days,
            "total_forecast_revenue": round(float(future_sales.sum()), 2),
        },
    }