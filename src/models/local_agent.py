"""
Local rule-based operations agent.
Classifies natural-language questions and answers them from live model outputs.
No external API calls — safe to deploy anywhere.
"""
from __future__ import annotations
import math
from typing import Any


# ── Question classifier ───────────────────────────────────────────────────────

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "staffing": [
        "staff", "shift", "employee", "roster", "headcount", "worker",
        "schedule", "attendance", "crew", "understaffed", "overstaffed",
        "how many people", "how many staff",
    ],
    "combo": [
        "combo", "bundle", "pair", "together", "upsell", "basket",
        "buy", "association", "lift", "cross-sell", "frequently",
        "product pair", "promotion", "offer",
    ],
    "demand": [
        "demand", "forecast", "sales forecast", "predict", "projection",
        "next month", "next quarter", "volume", "units", "how much will",
        "how many units", "trending", "sales trend",
    ],
    "expansion": [
        "expand", "expansion", "new branch", "open", "location",
        "fifth branch", "5th branch", "where should", "site",
        "feasibility", "new store", "grow the network",
    ],
    "beverage": [
        "coffee", "milkshake", "shake", "beverage", "drink",
        "revenue share", "increase sales", "grow sales", "bev",
        "chimney cake", "pastry", "food mix", "product mix",
    ],
}


def _classify(question: str) -> str:
    q = question.lower()
    scores: dict[str, int] = {topic: 0 for topic in _TOPIC_KEYWORDS}
    for topic, kws in _TOPIC_KEYWORDS.items():
        for kw in kws:
            if kw in q:
                scores[topic] += 1
    best = max(scores, key=lambda t: scores[t])
    return best if scores[best] > 0 else "overview"


# ── Individual answer generators ──────────────────────────────────────────────

def _fmt(n: float, decimals: int = 0) -> str:
    """Format a number with commas."""
    if decimals == 0:
        return f"{int(round(n)):,}"
    return f"{n:,.{decimals}f}"


def _answer_staffing(staffing: dict, question: str) -> str:
    alerts = staffing.get("alerts", [])
    shift_summary = staffing.get("shift_summary", [])
    recommendations = staffing.get("recommendations", [])

    lines = ["## Staffing Analysis\n"]

    if alerts:
        lines.append(f"**{len(alert_list := alerts)} shift(s) are below minimum safe headcount (< 2 staff):**\n")
        for a in alerts:
            lines.append(f"- {a}")
        lines.append("")
    else:
        lines.append("**All shifts are adequately staffed** — no critical gaps detected.\n")

    if shift_summary:
        total_rec = sum(r.get("recommended_staff", 0) for r in shift_summary)
        at_risk = [r for r in shift_summary if r.get("min_staff", 2) < 2]
        lines.append(f"**Network summary:**")
        lines.append(f"- {len(shift_summary)} branch-shift slots tracked")
        lines.append(f"- {int(total_rec)} total recommended staff daily (across all shifts)")
        lines.append(f"- {len(at_risk)} shift(s) have recorded min < 2 staff\n")

        # highest-need shifts
        sorted_shifts = sorted(shift_summary, key=lambda r: r.get("recommended_staff", 0), reverse=True)
        lines.append("**Top shifts by recommended headcount:**")
        for r in sorted_shifts[:4]:
            lines.append(
                f"- **{r.get('branch')} — {r.get('shift')}**: "
                f"recommended {int(r.get('recommended_staff', 0))} staff "
                f"(historical mean {r.get('mean_staff', 0):.1f}, "
                f"min observed {int(r.get('min_staff', 0))})"
            )
        lines.append("")

    if recommendations:
        lines.append("**Recommended actions:**")
        for rec in recommendations[:5]:
            lines.append(f"- {rec}")

    return "\n".join(lines)


def _answer_combo(combo: dict, question: str) -> str:
    method = combo.get("method", "")
    combos = combo.get("top_combos", [])
    top_items = combo.get("top_items", [])
    recs = combo.get("recommendations", [])

    lines = ["## Product Combo Analysis\n"]

    if method == "apriori" and combos:
        best = combos[0]
        lines.append(
            f"**Strongest combo:** {best.get('items')} — "
            f"lift {best.get('lift', 0):.2f}x, "
            f"{best.get('confidence', 0)*100:.0f}% cross-purchase rate, "
            f"appears in {best.get('support', 0)*100:.1f}% of all orders.\n"
        )

        high_lift = [c for c in combos if c.get("lift", 0) >= 2.0]
        lines.append(f"**{len(high_lift)} combo(s)** have lift ≥ 2.0x — strong bundle candidates:\n")
        for c in high_lift[:5]:
            lines.append(
                f"- **{c['items']}** — lift {c['lift']:.2f}x, "
                f"{c['confidence']*100:.0f}% confidence"
            )
        lines.append("")
        lines.append("**Recommended bundle strategy:**")
        lines.append(
            f"- Offer the top combo **{best.get('items')}** at 5–8% below à-la-carte pricing."
        )
        lines.append("- Feature it on the delivery app and at POS checkout.")
        lines.append(
            f"- At {best.get('confidence', 0)*100:.0f}% natural co-purchase rate, "
            "even light promotion will lift average basket size."
        )
    elif top_items:
        lines.append(
            "Basket density was below the Apriori minimum support threshold. "
            "Top individual items by volume (use as bundle seeds):\n"
        )
        for item in top_items[:5]:
            lines.append(f"- **{item.get('item')}**: {_fmt(item.get('qty', 0))} units sold")
        lines.append("")
        if recs:
            lines.append("**Recommendations:**")
            for r in recs:
                lines.append(f"- {r}")
    else:
        lines.append("No combo data available — ensure delivery basket data is loaded.")

    return "\n".join(lines)


def _answer_demand(demand: dict, question: str) -> str:
    ranking = demand.get("demand_ranking", [])
    forecasts = demand.get("forecasts", {})

    lines = ["## Demand Forecast Analysis\n"]

    if ranking:
        top = ranking[0]
        bottom = ranking[-1]
        spread = ((top["avg_forecast"] - bottom["avg_forecast"]) / max(bottom["avg_forecast"], 1)) * 100

        lines.append("**Projected monthly demand — next 3 months:**\n")
        for i, r in enumerate(ranking, 1):
            lines.append(
                f"{i}. **{r['branch']}**: {_fmt(r['avg_forecast'])} units/month avg"
            )
        lines.append(
            f"\n**{top['branch']}** leads demand by a {spread:.0f}% margin over **{bottom['branch']}**.\n"
        )

    if forecasts:
        growing = [(b, d.get("growth_pct_over_period", 0)) for b, d in forecasts.items()
                   if d.get("growth_pct_over_period", 0) > 5]
        declining = [(b, d.get("growth_pct_over_period", 0)) for b, d in forecasts.items()
                     if d.get("growth_pct_over_period", 0) < -5]

        if growing:
            lines.append("**Growing branches** (trend > +5%):")
            for b, g in growing:
                lines.append(f"- {b}: {g:+.1f}% trend — pre-position inventory above forecast")
        if declining:
            lines.append("\n**Declining branches** (trend < -5%):")
            for b, g in declining:
                lines.append(f"- {b}: {g:+.1f}% trend — investigate before committing stock")
        if not growing and not declining:
            lines.append("**All branches show stable demand trends** — use historical means as baseline.")

    return "\n".join(lines)


def _answer_expansion(expansion: dict, question: str) -> str:
    verdict = expansion.get("feasibility", "N/A")
    signals = expansion.get("signals", {})
    stats = expansion.get("network_stats", {})
    top_locs = expansion.get("top_candidate_locations", [])

    growing = signals.get("growing_network", False)
    saturated = signals.get("saturated_branch_present", False)
    dense = signals.get("high_customer_density", False)
    n_signals = sum([growing, saturated, dense])

    avg_growth = stats.get("avg_monthly_growth_pct", 0)
    total_cust = stats.get("total_customers", 0)

    lines = ["## Expansion Feasibility\n"]
    verdict_line = "RECOMMENDED" if verdict == "RECOMMENDED" else "NOT RECOMMENDED"
    lines.append(f"**Verdict: {verdict_line}** ({n_signals}/3 signals met)\n")

    lines.append("**Signal breakdown:**")
    lines.append(f"- Network growth (>1%/month): {'PASSED' if growing else 'FAILED'} — {avg_growth:.2f}%/month actual")
    lines.append(f"- Branch saturation (>40% revenue share): {'PASSED' if saturated else 'NOT MET'}")
    lines.append(f"- Customer density (>500 network-wide): {'PASSED' if dense else 'NOT MET'} — {_fmt(total_cust)} customers")
    lines.append("")

    if top_locs:
        lines.append("**Top candidate locations:**")
        for i, loc in enumerate(top_locs[:3], 1):
            lines.append(
                f"{i}. **{loc.get('location')}** — composite score {loc.get('composite_score')}, "
                f"demand {loc.get('demand_score')}, competition risk {loc.get('competition_risk')}"
            )
        lines.append("")

    if verdict == "RECOMMENDED":
        lines.append(
            f"**Recommendation:** Commission a site survey for **{top_locs[0]['location']}**. "
            "Network momentum supports a 5th branch."
        )
    else:
        lines.append(
            f"**Recommendation:** Hold on expansion. "
            f"Strengthen existing branch performance (avg growth {avg_growth:.1f}%/month) "
            "before committing to new fixed costs."
        )

    return "\n".join(lines)


def _answer_strategy(strategy: dict, question: str) -> str:
    summary = strategy.get("summary", {})
    under_coffee = strategy.get("underperforming_coffee_branches", [])
    under_shake = strategy.get("underperforming_shake_branches", [])
    top_coffee = strategy.get("top_coffee_items", [])
    top_shakes = strategy.get("top_milkshake_items", [])
    strategies = strategy.get("strategies", [])

    coffee_pct = summary.get("coffee_share_pct", 0)
    shake_pct = summary.get("milkshake_share_pct", 0)
    bev_pct = coffee_pct + shake_pct
    gap = max(35 - bev_pct, 0)

    lines = ["## Beverage Growth Strategy\n"]
    lines.append(
        f"**Current beverage revenue share: {bev_pct:.1f}%** "
        f"(coffee {coffee_pct:.1f}% + milkshake {shake_pct:.1f}%)\n"
        f"Industry benchmark: 35%. Gap to close: **{gap:.1f} percentage points**.\n"
    )

    if under_coffee:
        lines.append(f"**Underperforming on coffee (<20% share):** {', '.join(under_coffee)}")
        lines.append("→ Priority targets for barista training and menu prominence.\n")
    if under_shake:
        lines.append(f"**Underperforming on milkshakes (<10% share):** {', '.join(under_shake)}")
        lines.append("→ Consider seasonal/limited SKUs to stimulate trial.\n")

    if top_coffee:
        lines.append("**Top coffee products by revenue:**")
        for item in top_coffee[:3]:
            lines.append(f"- {item.get('item')}: {_fmt(item.get('total_qty', 0))} units")
        lines.append("")

    if strategies:
        lines.append("**Prioritised growth actions:**")
        priority_labels = ["IMMEDIATE", "IMMEDIATE", "THIS MONTH", "THIS QUARTER", "THIS QUARTER"]
        for i, s in enumerate(strategies[:5]):
            label = priority_labels[i] if i < len(priority_labels) else "PLANNED"
            lines.append(
                f"{i+1}. **[{label}] {s.get('strategy')}** — {s.get('action')} "
                f"*(expected: {s.get('expected_impact')})*"
            )

    return "\n".join(lines)


def _answer_overview(
    combo: dict, demand: dict, expansion: dict, staffing: dict, strategy: dict, question: str
) -> str:
    lines = ["## Operations Overview\n"]

    # Top priority
    alerts = staffing.get("alerts", [])
    if alerts:
        lines.append(f"**URGENT — Staffing:** {len(alerts)} shift(s) below minimum safe headcount.")
        for a in alerts[:2]:
            lines.append(f"- {a}")
        lines.append("")

    # Demand
    ranking = demand.get("demand_ranking", [])
    if ranking:
        top = ranking[0]
        bottom = ranking[-1]
        lines.append(
            f"**Demand:** {top['branch']} leads at {_fmt(top['avg_forecast'])} units/month; "
            f"{bottom['branch']} trails at {_fmt(bottom['avg_forecast'])} units/month."
        )

    # Expansion
    verdict = expansion.get("feasibility", "N/A")
    top_locs = expansion.get("top_candidate_locations", [])
    top_loc_name = top_locs[0].get("location", "N/A") if top_locs else "N/A"
    lines.append(f"**Expansion:** {verdict}. Top candidate location: {top_loc_name}.")

    # Beverage
    summary = strategy.get("summary", {})
    bev_pct = summary.get("coffee_share_pct", 0) + summary.get("milkshake_share_pct", 0)
    gap = max(35 - bev_pct, 0)
    lines.append(f"**Beverages:** {bev_pct:.1f}% revenue share — {gap:.1f}pp below the 35% benchmark.")

    # Top combo
    combos = combo.get("top_combos", [])
    if combos:
        best = combos[0]
        lines.append(
            f"**Top combo to promote:** {best.get('items')} "
            f"(lift {best.get('lift', 0):.2f}x, {best.get('confidence', 0)*100:.0f}% confidence)."
        )

    lines.append("")
    lines.append("Ask a more specific question about staffing, demand, combos, expansion, or beverage growth for deeper detail.")
    return "\n".join(lines)


# ── Public entry point ────────────────────────────────────────────────────────

def answer_question(question: str, data: dict) -> str:
    """
    Classify the question and return a markdown-formatted answer
    drawn entirely from local model outputs. No external API calls.
    """
    from src.models.combo_optimizer import get_combo_summary
    from src.models.demand_forecaster import forecast_all_branches
    from src.models.expansion_analyzer import expansion_feasibility
    from src.models.staffing_estimator import get_staffing_recommendations
    from src.models.sales_strategist import generate_growth_strategy

    topic = _classify(question)

    try:
        if topic == "staffing":
            staffing = get_staffing_recommendations(data["attendance"])
            return _answer_staffing(staffing, question)

        elif topic == "combo":
            combo = get_combo_summary(data["delivery_items"])
            return _answer_combo(combo, question)

        elif topic == "demand":
            demand = forecast_all_branches(data["monthly_sales"])
            return _answer_demand(demand, question)

        elif topic == "expansion":
            expansion = expansion_feasibility(
                data["monthly_sales"], data["branch_revenue"], data["menu_avg_sales"]
            )
            return _answer_expansion(expansion, question)

        elif topic == "beverage":
            strategy = generate_growth_strategy(data["sales_by_item"], data["division_summary"])
            return _answer_strategy(strategy, question)

        else:  # overview / fallback
            combo = get_combo_summary(data["delivery_items"])
            demand = forecast_all_branches(data["monthly_sales"])
            expansion = expansion_feasibility(
                data["monthly_sales"], data["branch_revenue"], data["menu_avg_sales"]
            )
            staffing = get_staffing_recommendations(data["attendance"])
            strategy = generate_growth_strategy(data["sales_by_item"], data["division_summary"])
            return _answer_overview(combo, demand, expansion, staffing, strategy, question)

    except Exception as e:
        return f"**Error generating answer:** {e}\n\nPlease ensure the API backend is running with all data files present."
