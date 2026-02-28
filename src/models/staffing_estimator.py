"""
Shift Staffing Estimation.
Analyses time & attendance logs to derive per-shift employee requirements
and correlates with sales demand to produce data-driven staffing recommendations.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional


SHIFT_BINS = {
    "Morning (06–14)": (6, 14),
    "Afternoon (14–22)": (14, 22),
    "Night (22–06)": (22, 30),   # hour > 24 = next day
}


def parse_punch_hour(time_str: Optional[str]) -> Optional[int]:
    """Extract hour (0-23) from 'HH.MM.SS' or 'HH:MM:SS' format."""
    if not time_str or pd.isna(time_str):
        return None
    s = str(time_str).replace(".", ":").strip()
    try:
        return int(s.split(":")[0])
    except (ValueError, IndexError):
        return None


def assign_shift(hour: Optional[int]) -> str:
    if hour is None:
        return "Unknown"
    for shift, (start, end) in SHIFT_BINS.items():
        if start <= hour < (end if end <= 24 else 24) or (end > 24 and hour < end - 24):
            return shift
    return "Night (22–06)"


def compute_shift_staffing(attendance_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate attendance by branch × shift × day to get headcount per shift.
    Returns a summary DataFrame with mean/max/recommended staff.
    """
    df = attendance_df.copy()
    df = df[df["work_hours"] > 0.5]  # remove ghost/test punches

    df["punch_hour"] = df["punch_in"].apply(parse_punch_hour)
    df["shift"] = df["punch_hour"].apply(assign_shift)
    df["date_str"] = df["date"].dt.date.astype(str)
    df["day_of_week"] = df["date"].dt.day_name()

    # Count distinct employees per branch × shift × date
    daily_counts = (
        df.groupby(["branch", "shift", "date_str", "day_of_week"])["employee_id"]
        .nunique()
        .reset_index(name="staff_count")
    )

    summary = (
        daily_counts.groupby(["branch", "shift"])
        .agg(
            mean_staff=("staff_count", "mean"),
            max_staff=("staff_count", "max"),
            min_staff=("staff_count", "min"),
            days_observed=("staff_count", "count"),
        )
        .reset_index()
    )
    # Recommended = ceil(mean * 1.15) safety buffer, capped at max
    summary["recommended_staff"] = np.ceil(summary["mean_staff"] * 1.15).clip(
        upper=summary["max_staff"]
    ).astype(int)

    return summary


def staffing_by_day(attendance_df: pd.DataFrame) -> pd.DataFrame:
    """Day-of-week staffing patterns."""
    df = attendance_df.copy()
    df = df[df["work_hours"] > 0.5]
    df["day_of_week"] = df["date"].dt.day_name()
    df["punch_hour"] = df["punch_in"].apply(parse_punch_hour)
    df["shift"] = df["punch_hour"].apply(assign_shift)

    return (
        df.groupby(["branch", "day_of_week", "shift"])["employee_id"]
        .nunique()
        .reset_index(name="avg_staff")
    )


def compute_avg_hours_per_employee(attendance_df: pd.DataFrame) -> pd.DataFrame:
    """Return avg, min, max hours worked per branch."""
    df = attendance_df[attendance_df["work_hours"] > 0.5].copy()
    return (
        df.groupby("branch")["work_hours"]
        .agg(["mean", "median", "min", "max", "count"])
        .rename(columns={"mean":"avg_hours","median":"median_hours",
                         "min":"min_hours","max":"max_hours","count":"shift_records"})
        .reset_index()
    )


def get_staffing_recommendations(attendance_df: pd.DataFrame) -> dict:
    """Main entry-point: full staffing recommendation report."""
    if attendance_df.empty:
        return {"error": "No attendance data available"}

    shift_summary = compute_shift_staffing(attendance_df)
    hours_summary = compute_avg_hours_per_employee(attendance_df)

    recommendations = []
    for _, row in shift_summary.iterrows():
        recommendations.append(
            f"{row['branch']} – {row['shift']}: "
            f"recommend {row['recommended_staff']} staff "
            f"(observed range {int(row['min_staff'])}–{int(row['max_staff'])}, "
            f"avg {row['mean_staff']:.1f})"
        )

    # Identify understaffed shifts (min < 2 staff)
    understaffed = shift_summary[shift_summary["min_staff"] < 2]
    alerts = [
        f"ALERT: {row['branch']} – {row['shift']} had as few as {int(row['min_staff'])} staff on some days."
        for _, row in understaffed.iterrows()
    ]

    return {
        "shift_summary": shift_summary.to_dict(orient="records"),
        "hours_per_employee": hours_summary.to_dict(orient="records"),
        "recommendations": recommendations,
        "alerts": alerts,
    }
