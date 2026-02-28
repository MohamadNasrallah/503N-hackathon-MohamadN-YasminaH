"""
Combo Optimization – Association Rule Mining on delivery basket data.
Uses the Apriori algorithm (mlxtend) to find items frequently bought together.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional


def build_baskets(delivery_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert line-item delivery data into a customer × item basket matrix.
    Returns a binary (0/1) DataFrame where rows = orders and cols = items.
    """
    # Filter out free/zero items and modifiers (price == 0)
    paid = delivery_df[delivery_df["price"] > 0].copy()
    # Clean item names
    paid["item"] = paid["item"].str.strip().str.upper()
    # Drop delivery charges and very generic items
    exclude = ["DELIVERY CHARGE", "SERVICE CHARGE"]
    paid = paid[~paid["item"].isin(exclude)]

    # Each (branch, customer) order = one basket
    baskets = (
        paid.groupby(["branch", "customer", "item"])["qty"]
        .sum()
        .unstack(fill_value=0)
        .clip(upper=1)  # binarise
        .reset_index(drop=True)
    )
    return baskets


def run_apriori(
    baskets: pd.DataFrame,
    min_support: float = 0.02,
    min_confidence: float = 0.3,
    min_lift: float = 1.2,
) -> pd.DataFrame:
    """
    Run association rule mining and return a DataFrame of rules.
    Falls back to a manual frequency calculation if mlxtend is unavailable.
    """
    try:
        from mlxtend.frequent_patterns import apriori, association_rules
        frequent_items = apriori(
            baskets.astype(bool),
            min_support=min_support,
            use_colnames=True,
        )
        if frequent_items.empty:
            return _fallback_top_pairs(baskets)
        rules = association_rules(
            frequent_items,
            metric="lift",
            min_threshold=min_lift,
        )
        rules = rules[rules["confidence"] >= min_confidence].copy()
        rules.sort_values("lift", ascending=False, inplace=True)
        rules.reset_index(drop=True, inplace=True)
        # Convert frozensets to readable strings
        rules["antecedents"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(x)))
        rules["consequents"] = rules["consequents"].apply(lambda x: ", ".join(sorted(x)))
        return rules[[
            "antecedents","consequents",
            "support","confidence","lift","leverage","conviction"
        ]]
    except ImportError:
        return _fallback_top_pairs(baskets)


def _fallback_top_pairs(baskets: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Manual co-occurrence counting when mlxtend is not installed.
    Returns top N item pairs by co-occurrence frequency.
    """
    items = baskets.columns.tolist()
    records = []
    mat = baskets.values
    n = len(mat)
    for i, item_a in enumerate(items):
        for j, item_b in enumerate(items):
            if j <= i:
                continue
            both = int(((mat[:, i] > 0) & (mat[:, j] > 0)).sum())
            support = both / n if n > 0 else 0
            if both > 0:
                conf_ab = both / max(int((mat[:, i] > 0).sum()), 1)
                conf_ba = both / max(int((mat[:, j] > 0).sum()), 1)
                records.append(dict(
                    antecedents=item_a,
                    consequents=item_b,
                    support=support,
                    confidence=max(conf_ab, conf_ba),
                    lift=conf_ab / max(int((mat[:, j] > 0).sum()) / n, 1e-9),
                ))
    df = pd.DataFrame(records).sort_values("support", ascending=False)
    return df.head(top_n).reset_index(drop=True)


def top_combos(
    delivery_df: pd.DataFrame,
    top_n: int = 10,
    min_support: float = 0.02,
) -> pd.DataFrame:
    """
    High-level function: return top N combo recommendations.
    """
    baskets = build_baskets(delivery_df)
    if baskets.empty or baskets.shape[0] < 5:
        return pd.DataFrame(columns=["antecedents","consequents","support","confidence","lift"])
    rules = run_apriori(baskets, min_support=min_support)
    return rules.head(top_n)


def get_combo_summary(delivery_df: pd.DataFrame) -> dict:
    """Return a JSON-serializable summary of top combo recommendations."""
    df = top_combos(delivery_df)
    if df.empty:
        # Fallback: most frequently ordered single items
        paid = delivery_df[delivery_df["price"] > 0].copy()
        paid["item"] = paid["item"].str.strip().str.upper()
        top_items = (
            paid.groupby("item")["qty"].sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        return {
            "method": "top_single_items",
            "top_items": top_items.to_dict(orient="records"),
            "recommendations": [
                f"Promote {row['item']} as a featured item (sold {row['qty']:.0f} units)"
                for _, row in top_items.head(5).iterrows()
            ]
        }
    combos = []
    for _, row in df.iterrows():
        combos.append({
            "items": f"{row['antecedents']} + {row['consequents']}",
            "support": round(float(row["support"]), 4),
            "confidence": round(float(row["confidence"]), 4),
            "lift": round(float(row["lift"]), 4),
        })
    recommendations = [
        f"Bundle '{c['items']}' — {c['confidence']*100:.0f}% of customers who buy one also buy the other (lift {c['lift']:.2f}x)"
        for c in combos[:5]
    ]
    return {"method": "apriori", "top_combos": combos, "recommendations": recommendations}
