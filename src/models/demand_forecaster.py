"""
Demand Forecasting by Branch.
Uses monthly sales data + linear regression / exponential smoothing.
Falls back gracefully when prophet is unavailable.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional


def _prepare_series(monthly_df: pd.DataFrame, branch: str) -> pd.DataFrame:
    """Return a sorted time-series DataFrame for a single branch."""
    df = monthly_df[monthly_df["branch"] == branch].copy()
    df = df.sort_values(["year", "month_num"])
    df["period"] = df["year"] * 100 + df["month_num"]  # YYYYMM integer
    # Create a sequential index (t = 1,2,3,…)
    df = df.reset_index(drop=True)
    df["t"] = range(1, len(df) + 1)
    return df


def _linear_forecast(series: pd.DataFrame, n_periods: int = 3) -> pd.DataFrame:
    """Simple OLS trend + seasonal adjustment."""
    from sklearn.linear_model import LinearRegression

    X = series[["t"]].values
    y = series["total_sales"].values

    model = LinearRegression()
    model.fit(X, y)

    t_future = np.arange(len(series) + 1, len(series) + n_periods + 1).reshape(-1, 1)
    forecast = model.predict(t_future)

    # Assign month/year labels
    last_period = series["period"].iloc[-1]
    last_year = last_period // 100
    last_month = last_period % 100
    future_rows = []
    for i, f in enumerate(forecast):
        m = (last_month + i) % 12 + 1
        y_ = last_year + (last_month + i) // 12
        future_rows.append({"year": y_, "month_num": m, "forecast": max(f, 0)})

    return pd.DataFrame(future_rows)


def forecast_branch(
    monthly_df: pd.DataFrame,
    branch: str,
    n_months: int = 3,
) -> dict:
    """
    Return demand forecast for the next n_months for a given branch.
    Tries Prophet first, falls back to linear regression.
    """
    series = _prepare_series(monthly_df, branch)
    if series.empty:
        return {"branch": branch, "error": "No data for this branch"}

    month_names = {
        1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
        7:"July",8:"August",9:"September",10:"October",11:"November",12:"December",
    }

    # Historical stats
    mean_sales = series["total_sales"].mean()
    std_sales = series["total_sales"].std()
    growth_pct = (
        (series["total_sales"].iloc[-1] - series["total_sales"].iloc[0])
        / series["total_sales"].iloc[0] * 100
        if len(series) > 1 and series["total_sales"].iloc[0] > 0 else 0
    )

    # Attempt Prophet
    try:
        from prophet import Prophet  # type: ignore
        pdf = series.copy()
        pdf["ds"] = pd.to_datetime(
            pdf["year"].astype(str) + "-" + pdf["month_num"].astype(str).str.zfill(2) + "-01"
        )
        pdf = pdf.rename(columns={"total_sales": "y"})[["ds", "y"]]
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(pdf)
        future = m.make_future_dataframe(periods=n_months, freq="MS")
        forecast_df = m.predict(future).tail(n_months)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        forecast_list = [
            {
                "period": f"{row['ds'].strftime('%B %Y')}",
                "forecast": round(max(row["yhat"], 0), 2),
                "lower": round(max(row["yhat_lower"], 0), 2),
                "upper": round(max(row["yhat_upper"], 0), 2),
            }
            for _, row in forecast_df.iterrows()
        ]
        method = "prophet"
    except (ImportError, Exception):
        fdf = _linear_forecast(series, n_months)
        forecast_list = [
            {
                "period": f"{month_names.get(int(row['month_num']), int(row['month_num']))} {int(row['year'])}",
                "forecast": round(float(row["forecast"]), 2),
                "lower": round(float(row["forecast"]) * 0.9, 2),
                "upper": round(float(row["forecast"]) * 1.1, 2),
            }
            for _, row in fdf.iterrows()
        ]
        method = "linear_regression"

    return {
        "branch": branch,
        "method": method,
        "historical_mean": round(mean_sales, 2),
        "growth_pct_over_period": round(growth_pct, 2),
        "forecast": forecast_list,
        "insight": _generate_demand_insight(branch, growth_pct, forecast_list),
    }


def _generate_demand_insight(branch: str, growth_pct: float, forecast: list) -> str:
    trend = "growing" if growth_pct > 5 else ("declining" if growth_pct < -5 else "stable")
    avg_forecast = np.mean([f["forecast"] for f in forecast]) if forecast else 0
    return (
        f"{branch} shows a {trend} trend ({growth_pct:+.1f}% over the data period). "
        f"Next {len(forecast)} months avg projected demand: {avg_forecast:,.0f} units."
    )


def forecast_all_branches(monthly_df: pd.DataFrame, n_months: int = 3) -> dict:
    """Forecast demand for all branches and return a combined summary."""
    branches = monthly_df["branch"].unique().tolist()
    results = {}
    for branch in branches:
        results[branch] = forecast_branch(monthly_df, branch, n_months)

    # Rank branches by projected demand
    ranking = sorted(
        [(b, np.mean([f["forecast"] for f in r.get("forecast", [{}])]))
         for b, r in results.items() if "forecast" in r],
        key=lambda x: x[1], reverse=True,
    )
    return {
        "forecasts": results,
        "demand_ranking": [{"branch": b, "avg_forecast": round(v, 2)} for b, v in ranking],
    }
