"""
Coffee & Milkshake Growth Strategy.
Analyses sales data to identify underperforming segments and generate
data-driven strategies to increase coffee and milkshake revenue.
"""
from __future__ import annotations
import pandas as pd
import numpy as np


COFFEE_KEYWORDS = [
    "COFFEE", "ESPRESSO", "CAPPUCCINO", "LATTE", "AMERICANO",
    "MOCHA", "FLAT WHITE", "MACCHIATO", "FRAPPE", "HOT CHOCOLATE",
]
MILKSHAKE_KEYWORDS = ["MILKSHAKE", "SHAKE", "FRAPPE"]


def classify_item(item: str) -> str:
    """Classify an item as 'coffee', 'milkshake', 'chimney', or 'other'."""
    upper = item.upper()
    if any(k in upper for k in MILKSHAKE_KEYWORDS):
        return "milkshake"
    if any(k in upper for k in COFFEE_KEYWORDS):
        return "coffee"
    if "CHIMNEY" in upper or "CONUT" in upper or "DONUT" in upper:
        return "chimney_cake"
    return "other"


def segment_sales(sales_by_item_df: pd.DataFrame) -> pd.DataFrame:
    """Add a segment column and compute segment-level aggregates."""
    df = sales_by_item_df.copy()
    df["segment"] = df["item"].apply(classify_item)
    return df


def compute_segment_share(sales_by_item_df: pd.DataFrame) -> pd.DataFrame:
    """Revenue share by segment for each branch."""
    df = segment_sales(sales_by_item_df)
    branch_total = df.groupby("branch")["total_amount"].sum().rename("branch_total")
    seg = (
        df.groupby(["branch", "segment"])["total_amount"]
        .sum()
        .reset_index(name="segment_revenue")
        .join(branch_total, on="branch")
    )
    seg["share_pct"] = (seg["segment_revenue"] / seg["branch_total"] * 100).round(2)
    return seg


def top_coffee_items(sales_by_item_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return top N coffee items by total revenue across all branches."""
    df = segment_sales(sales_by_item_df)
    coffee = df[df["segment"] == "coffee"]
    return (
        coffee.groupby("item")
        .agg(total_qty=("qty", "sum"), total_revenue=("total_amount", "sum"))
        .sort_values("total_revenue", ascending=False)
        .head(top_n)
        .reset_index()
    )


def top_milkshake_items(sales_by_item_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return top N milkshake items by total revenue."""
    df = segment_sales(sales_by_item_df)
    shakes = df[df["segment"] == "milkshake"]
    return (
        shakes.groupby("item")
        .agg(total_qty=("qty", "sum"), total_revenue=("total_amount", "sum"))
        .sort_values("total_revenue", ascending=False)
        .head(top_n)
        .reset_index()
    )


def branch_coffee_comparison(sales_by_item_df: pd.DataFrame) -> pd.DataFrame:
    """Compare coffee performance across branches (qty and revenue per branch)."""
    df = segment_sales(sales_by_item_df)
    coffee = df[df["segment"].isin(["coffee", "milkshake"])]
    return (
        coffee.groupby(["branch", "segment"])
        .agg(total_qty=("qty", "sum"), total_revenue=("total_amount", "sum"))
        .reset_index()
    )


def generate_growth_strategy(
    sales_by_item_df: pd.DataFrame,
    division_summary_df: pd.DataFrame,
) -> dict:
    """
    Analyse sales data and return a comprehensive coffee & milkshake growth strategy.
    """
    share = compute_segment_share(sales_by_item_df)
    top_coffee = top_coffee_items(sales_by_item_df, 5)
    top_shakes = top_milkshake_items(sales_by_item_df, 5)
    branch_compare = branch_coffee_comparison(sales_by_item_df)

    # Find branches where coffee < 20% of revenue (growth opportunity)
    coffee_share = share[share["segment"] == "coffee"]
    under_performing = coffee_share[coffee_share["share_pct"] < 20]["branch"].tolist()
    outperforming = coffee_share[coffee_share["share_pct"] >= 20]["branch"].tolist()

    shake_share = share[share["segment"] == "milkshake"]
    shake_under = shake_share[shake_share["share_pct"] < 10]["branch"].tolist()

    # Overall metrics
    total_coffee_rev = float(
        sales_by_item_df[
            sales_by_item_df["item"].apply(classify_item) == "coffee"
        ]["total_amount"].sum()
    )
    total_shake_rev = float(
        sales_by_item_df[
            sales_by_item_df["item"].apply(classify_item) == "milkshake"
        ]["total_amount"].sum()
    )
    total_rev = float(sales_by_item_df["total_amount"].sum())

    strategies = []

    # Strategy 1: Star product upsell
    if not top_coffee.empty:
        star = top_coffee.iloc[0]
        strategies.append({
            "strategy": "Star Product Upsell",
            "target": "coffee",
            "action": f"Feature '{star['item']}' prominently in menus and POS upsell prompts. "
                      f"It generates {star['total_revenue']:,.0f} units revenue — train staff to recommend it.",
            "expected_impact": "5–10% increase in coffee revenue per upsell conversion",
        })

    # Strategy 2: Combo with chimney cake
    strategies.append({
        "strategy": "Coffee + Chimney Cake Combo Bundle",
        "target": "coffee + chimney_cake",
        "action": "Create a 'Coffee & Chimney' combo at a 5–8% discount vs. buying separately. "
                  "Cross-sell at POS when a chimney cake is ordered.",
        "expected_impact": "Increases average basket size by ~15% and coffee attach rate",
    })

    # Strategy 3: Branch-specific push
    if under_performing:
        strategies.append({
            "strategy": "Branch-Level Coffee Drive",
            "target": f"Branches: {', '.join(under_performing)}",
            "action": "These branches have <20% coffee revenue share. "
                      "Run a 2-week 'Coffee Month' promo with discounts on new coffee SKUs, "
                      "loyalty stamps, and barista spotlight content on social media.",
            "expected_impact": "+3–5% coffee revenue share per branch within 1 month",
        })

    # Strategy 4: Milkshake innovation
    if not top_shakes.empty:
        strategies.append({
            "strategy": "Seasonal Milkshake Menu",
            "target": "milkshake",
            "action": "Introduce 2–3 rotating seasonal milkshake flavours (e.g. rose, pistachio) "
                      "as limited-edition items. Use scarcity marketing (Instagram stories, countdown).",
            "expected_impact": "10–20% milkshake volume uplift during campaign period",
        })

    # Strategy 5: Happy-hour pricing
    strategies.append({
        "strategy": "Off-Peak Happy Hour",
        "target": "coffee + milkshake",
        "action": "Offer 20% off coffee & milkshakes Mon–Thu 14:00–17:00. "
                  "Converts low-traffic afternoon hours into revenue opportunities.",
        "expected_impact": "15–25% increase in afternoon transaction volume",
    })

    return {
        "summary": {
            "coffee_total_revenue": round(total_coffee_rev, 2),
            "milkshake_total_revenue": round(total_shake_rev, 2),
            "coffee_share_pct": round(total_coffee_rev / max(total_rev, 1) * 100, 2),
            "milkshake_share_pct": round(total_shake_rev / max(total_rev, 1) * 100, 2),
        },
        "underperforming_coffee_branches": under_performing,
        "outperforming_coffee_branches": outperforming,
        "underperforming_shake_branches": shake_under,
        "top_coffee_items": top_coffee.to_dict(orient="records"),
        "top_milkshake_items": top_shakes.to_dict(orient="records"),
        "branch_comparison": branch_compare.to_dict(orient="records"),
        "segment_share": share.to_dict(orient="records"),
        "strategies": strategies,
    }
