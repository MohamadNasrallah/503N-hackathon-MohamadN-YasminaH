"""
Conut AI Operations Dashboard — Business Intelligence Reports.
Run with: streamlit run app/dashboard.py
"""
import os
import sys
import json
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Conut AI Ops — Chief of Operations",
    page_icon="🍩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens ──────────────────────────────────────────────────────────────
C_GOLD    = "#C8913A"   # primary brand accent — coffee gold
C_BROWN   = "#181B20"   # sidebar background — espresso dark
C_CREAM   = "#F7F3EE"   # page background — warm cream
C_WHITE   = "#FFFFFF"
C_BORDER  = "#E8E0D8"   # subtle warm border
C_TEXT    = "#181B20"   # primary text
C_MUTED   = "#6C7583"   # secondary / caption text
C_GREEN   = "#27AE60"
C_AMBER   = "#E67E22"
C_RED     = "#C0392B"

# Chart color palette — applied to every plotly figure
CHART_COLORS = [C_GOLD, "#2D5A8E", C_GREEN, C_AMBER, "#8E44AD", C_RED, "#16A085"]
CHART_TEMPLATE = "plotly_white"

# ── Full design system CSS ────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Google Font ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Page background ─────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {{
    background-color: {C_CREAM};
    font-family: 'Inter', sans-serif;
    color: {C_TEXT};
}}

/* ── Sidebar — espresso dark ──────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {C_BROWN} !important;
}}
[data-testid="stSidebar"] * {{
    color: #D6C9B8 !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    color: #D6C9B8 !important;
    font-size: 0.85rem;
    padding: 0.15rem 0;
}}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{
    color: #D6C9B8 !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: #333840 !important;
}}
[data-testid="stSidebarNav"] {{
    background-color: {C_BROWN};
}}

/* ── Main area ────────────────────────────────────────────────────── */
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}}

/* ── Page title ───────────────────────────────────────────────────── */
h1 {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: {C_TEXT} !important;
    letter-spacing: -0.03em;
    margin-bottom: 0 !important;
}}
h2 {{
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: {C_TEXT} !important;
    margin-top: 1.5rem !important;
}}
h3 {{
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: {C_TEXT} !important;
}}

/* ── Section rule ─────────────────────────────────────────────────── */
.section-rule {{
    border: none;
    border-top: 1px solid {C_BORDER};
    margin: 1.2rem 0;
}}

/* ── Report label ─────────────────────────────────────────────────── */
.report-header {{
    font-size: 0.7rem;
    color: {C_GOLD};
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 0.1rem;
}}

/* ── KPI card grid ────────────────────────────────────────────────── */
.kpi-row {{
    display: flex;
    gap: 1rem;
    margin: 0.8rem 0 1.2rem;
    flex-wrap: wrap;
}}
.kpi-card {{
    background: {C_WHITE};
    border-radius: 10px;
    padding: 1rem 1.25rem;
    flex: 1;
    min-width: 140px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-top: 3px solid {C_GOLD};
}}
.kpi-label {{
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {C_MUTED};
    margin-bottom: 0.35rem;
}}
.kpi-value {{
    font-size: 1.8rem;
    font-weight: 800;
    color: {C_TEXT};
    line-height: 1;
    letter-spacing: -0.03em;
}}
.kpi-sub {{
    font-size: 0.72rem;
    color: {C_MUTED};
    margin-top: 0.25rem;
}}
.kpi-delta-pos {{ color: {C_GREEN}; font-size: 0.75rem; font-weight: 600; margin-top: 0.2rem; }}
.kpi-delta-neg {{ color: {C_RED};   font-size: 0.75rem; font-weight: 600; margin-top: 0.2rem; }}
.kpi-delta-neu {{ color: {C_MUTED}; font-size: 0.75rem; font-weight: 600; margin-top: 0.2rem; }}

/* ── Verdict / finding cards ──────────────────────────────────────── */
.verdict-green {{
    background: #F0FAF4;
    border-left: 4px solid {C_GREEN};
    padding: 0.9rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 0.8rem 0;
    font-size: 0.88rem;
    line-height: 1.65;
    box-shadow: 0 1px 6px rgba(39,174,96,0.08);
}}
.verdict-red {{
    background: #FDF0EF;
    border-left: 4px solid {C_RED};
    padding: 0.9rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 0.8rem 0;
    font-size: 0.88rem;
    line-height: 1.65;
    box-shadow: 0 1px 6px rgba(192,57,43,0.08);
}}
.verdict-amber {{
    background: #FEF9EE;
    border-left: 4px solid {C_AMBER};
    padding: 0.9rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 0.8rem 0;
    font-size: 0.88rem;
    line-height: 1.65;
    box-shadow: 0 1px 6px rgba(230,126,34,0.08);
}}
.verdict-blue {{
    background: #EEF4FC;
    border-left: 4px solid #2D5A8E;
    padding: 0.9rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 0.8rem 0;
    font-size: 0.88rem;
    line-height: 1.65;
    box-shadow: 0 1px 6px rgba(45,90,142,0.08);
}}

/* ── Analysis / insight card ──────────────────────────────────────── */
.analysis-box {{
    background: {C_WHITE};
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 0.8rem 0;
    font-size: 0.86rem;
    line-height: 1.75;
    color: {C_TEXT};
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border: 1px solid {C_BORDER};
}}

/* ── Section card wrapper ─────────────────────────────────────────── */
.section-card {{
    background: {C_WHITE};
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}}

/* ── Tabs styling ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    background: {C_WHITE};
    border-radius: 8px 8px 0 0;
    border: 1px solid {C_BORDER};
    border-bottom: none;
    padding: 0.4rem 1rem;
    font-size: 0.82rem;
    font-weight: 600;
}}
.stTabs [aria-selected="true"] {{
    background: {C_GOLD} !important;
    color: white !important;
    border-color: {C_GOLD} !important;
}}

/* ── Dataframe ────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}}

/* ── Slider ───────────────────────────────────────────────────────── */
.stSlider [data-testid="stThumbValue"] {{
    color: {C_GOLD};
}}

/* ── Buttons ──────────────────────────────────────────────────────── */
.stButton > button {{
    background-color: {C_GOLD} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.15s;
}}
.stButton > button:hover {{
    opacity: 0.88;
}}

/* ── Metric native override ───────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {C_WHITE};
    border-radius: 10px;
    padding: 0.8rem 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border-top: 3px solid {C_GOLD};
}}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch(endpoint: str) -> dict:
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def post_query(question: str) -> str:
    try:
        r = requests.post(
            f"{API_URL}/query",
            json={"question": question, "include_data_context": True},
            timeout=90,
        )
        r.raise_for_status()
        return r.json().get("answer", "No answer returned.")
    except Exception as e:
        return f"Error: {e}"


def api_error(data: dict) -> bool:
    if "error" in data:
        st.error(
            f"**API not reachable.** Start the backend first:\n\n"
            f"```\nuvicorn src.api.main:app --port 8000 --reload\n```\n\n"
            f"Details: `{data['error']}`"
        )
        return True
    return False


def divider():
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)


def report_label(text: str):
    st.markdown(f'<p class="report-header">{text}</p>', unsafe_allow_html=True)


def verdict_box(text: str, kind: str = "green"):
    st.markdown(f'<div class="verdict-{kind}">{text}</div>', unsafe_allow_html=True)


def analysis_box(text: str):
    st.markdown(f'<div class="analysis-box">{text}</div>', unsafe_allow_html=True)


def kpi_row(cards: list[dict]):
    """
    Render a row of KPI cards.
    Each card dict: {label, value, sub="", delta="", delta_dir="pos"|"neg"|"neu"}
    """
    html = '<div class="kpi-row">'
    for c in cards:
        delta_html = ""
        if c.get("delta"):
            cls = f"kpi-delta-{c.get('delta_dir', 'neu')}"
            arrow = "&#8593;" if c.get("delta_dir") == "pos" else ("&#8595;" if c.get("delta_dir") == "neg" else "")
            delta_html = f'<div class="{cls}">{arrow} {c["delta"]}</div>'
        sub_html = f'<div class="kpi-sub">{c["sub"]}</div>' if c.get("sub") else ""
        # Keep HTML on one line — multi-line indented HTML breaks CommonMark parsing
        # (whitespace-only lines from empty sub/delta end the HTML block prematurely)
        html += (
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{c["label"]}</div>'
            f'<div class="kpi-value">{c["value"]}</div>'
            f'{sub_html}{delta_html}'
            f'</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _style_fig(fig, title: str = "", height: int = 380) -> object:
    """Apply consistent brand styling to any Plotly figure."""
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
        title=dict(text=title, font=dict(size=13, color=C_TEXT, family="Inter"), x=0),
        font=dict(family="Inter", color=C_TEXT, size=11),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40 if title else 20, b=10),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=C_BORDER,
            borderwidth=1,
            font=dict(size=10),
        ),
        xaxis=dict(gridcolor="#EDE8E2", linecolor=C_BORDER, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#EDE8E2", linecolor=C_BORDER, tickfont=dict(size=10)),
    )
    return fig


def _build_coo_narrative(ov: dict, demand: dict, expansion: dict, staffing: dict, strategy: dict) -> str:
    """
    Generate a fully local Chief of Operations executive briefing narrative.
    No API key needed — pure Python f-string synthesis from model outputs.
    """
    lines = []

    # ── 1. Network Health ─────────────────────────────────────────────────────
    ranking = ov.get("demand_ranking", [])
    top_branch = ranking[0]["branch"] if ranking else "N/A"
    top_val = ranking[0]["avg_forecast"] if ranking else 0
    bottom_branch = ranking[-1]["branch"] if len(ranking) > 1 else "N/A"
    bottom_val = ranking[-1]["avg_forecast"] if len(ranking) > 1 else 0
    spread = ((top_val - bottom_val) / max(bottom_val, 1) * 100) if bottom_val else 0

    exp_verdict = ov.get("expansion_verdict", "N/A")
    coffee_pct = ov.get("coffee_share_pct", 0)
    shake_pct = ov.get("milkshake_share_pct", 0)
    bev_pct = coffee_pct + shake_pct

    exp_stats = expansion.get("network_stats", {})
    total_rev = exp_stats.get("total_revenue", 0)
    total_cust = exp_stats.get("total_customers", 0)
    avg_growth = exp_stats.get("avg_monthly_growth_pct", 0)

    growth_label = (
        "strong" if avg_growth > 3 else
        "moderate" if avg_growth > 1 else
        "slow" if avg_growth > 0 else "negative"
    )

    lines.append("## Executive Briefing — Conut Operations\n")
    lines.append("### 1. Network Health Overview\n")
    lines.append(
        f"The Conut network of 4 branches is generating **{avg_growth:.1f}% average monthly revenue growth** "
        f"({growth_label}), with a total customer base of **{total_cust:,}** and aggregate revenue of "
        f"**{total_rev:,.0f}**. "
        f"Demand is led by **{top_branch}** ({top_val:,.0f} units/month projected) and trails at "
        f"**{bottom_branch}** ({bottom_val:,.0f} units/month) — a **{spread:.0f}% gap** across the network "
        f"that signals uneven market penetration.\n"
    )

    # ── 2. Most Urgent Operational Issue ─────────────────────────────────────
    lines.append("### 2. Most Urgent Operational Issue\n")
    alerts = ov.get("staffing_alerts", [])
    shift_summary = staffing.get("shift_summary", [])
    if alerts:
        lines.append(
            f"**Staffing is the highest-urgency issue.** {len(alerts)} shift(s) have recorded "
            f"dangerously low headcounts — as few as 1 staff member on some days. "
            f"This creates a single-point-of-failure risk in service delivery, increases staff burnout, "
            f"and exposes the business to service failure during peak hours. "
            f"Immediate roster corrections are required before the next operating week.\n"
        )
        for a in alerts[:3]:
            lines.append(f"> ⚠️ {a}\n")
    else:
        # Find next most urgent issue
        forecasts = demand.get("forecasts", {})
        declining = [
            (b, d.get("growth_pct_over_period", 0))
            for b, d in forecasts.items()
            if d.get("growth_pct_over_period", 0) < -5
        ]
        if declining:
            worst = min(declining, key=lambda x: x[1])
            lines.append(
                f"**Demand decline at {worst[0]} is the most urgent concern.** "
                f"This branch shows a {worst[1]:+.1f}% trend over the data period. "
                f"Without intervention, this trajectory will widen the network demand gap. "
                f"A root-cause review of pricing, product mix, and local competition is recommended.\n"
            )
        else:
            lines.append(
                "**No critical operational alerts at this time.** "
                "All staffing levels are above minimum thresholds and demand trends are stable or positive. "
                "The priority should shift to revenue mix optimisation.\n"
            )

    # ── 3. Top Revenue Growth Opportunity ────────────────────────────────────
    lines.append("### 3. Top Revenue Growth Opportunity\n")
    under_coffee = strategy.get("underperforming_coffee_branches", [])
    combo_recs = ov.get("combo_highlights", [])
    strats = strategy.get("strategies", [])
    gap_to_benchmark = max(35 - bev_pct, 0)

    lines.append(
        f"**Beverage revenue uplift is the single largest near-term growth lever.** "
        f"Coffee and milkshakes currently represent **{bev_pct:.1f}%** of network revenue "
        f"(coffee: {coffee_pct:.1f}%, milkshake: {shake_pct:.1f}%). "
        f"The industry benchmark for specialty café-bakery concepts is 35%+. "
        f"Closing this **{gap_to_benchmark:.1f} percentage-point gap** would meaningfully shift the "
        f"revenue mix toward higher-margin products without requiring new branches or capital investment.\n"
    )
    if under_coffee:
        lines.append(
            f"Branches **{', '.join(under_coffee)}** are below the 20% coffee revenue share threshold "
            f"and represent the highest-opportunity targets for a focused 'Coffee Drive' campaign.\n"
        )
    if combo_recs:
        lines.append(
            f"Additionally, association rule mining has identified product combos with strong buying affinity. "
            f"Activating the top bundle at a 5% discount is a zero-cost promotional lever: "
            f"*{combo_recs[0]}*\n"
        )

    # ── 4. Expansion Readiness ────────────────────────────────────────────────
    lines.append("### 4. Expansion Readiness\n")
    signals = expansion.get("signals", {})
    top_locs = expansion.get("top_candidate_locations", [])
    n_signals = sum(signals.values())

    if exp_verdict == "RECOMMENDED":
        top_loc_name = top_locs[0]["location"] if top_locs else "N/A"
        top_score = top_locs[0].get("composite_score", "N/A") if top_locs else "N/A"
        lines.append(
            f"**The network is ready for a 5th branch ({n_signals}/3 expansion signals met).** "
            f"Growth momentum, customer density, and branch saturation signals collectively indicate "
            f"that the network can support additional coverage. "
            f"The top-ranked candidate location is **{top_loc_name}** (composite score: {top_score}). "
            f"The recommended next step is a formal site survey and lease feasibility study.\n"
        )
    else:
        lines.append(
            f"**Expansion is premature at this stage ({n_signals}/3 signals met).** "
            f"Average monthly growth of {avg_growth:.1f}% and a customer base of {total_cust:,} "
            f"do not yet justify the fixed cost commitment of a new branch. "
            f"The priority is to strengthen existing branch performance — "
            f"particularly demand growth and beverage mix — before committing to expansion capital.\n"
        )

    # ── 5. Highest-Priority Recommendation ───────────────────────────────────
    lines.append("### 5. Chief of Operations Recommendation\n")

    if alerts:
        rec = (
            f"**Fix staffing immediately.** Understaffed shifts pose an immediate service and compliance risk. "
            f"Re-roster all flagged shifts to a minimum of 2 staff before the next operating day. "
            f"Use the recommended headcounts from the staffing model as your new roster baseline."
        )
    elif bev_pct < 25:
        rec = (
            f"**Launch a network-wide beverage growth initiative this week.** "
            f"At {bev_pct:.1f}% beverage share, there is significant margin being left on the table. "
            f"Activate the Coffee + Chimney Cake combo bundle, run the off-peak happy hour Mon–Thu 14:00–17:00, "
            f"and brief branch managers on the underperforming branches. "
            f"This can be done with zero capital and should show results within 30 days."
        )
    elif exp_verdict == "RECOMMENDED":
        top_loc_name = top_locs[0]["location"] if top_locs else "the top-ranked location"
        rec = (
            f"**Commission a site survey for {top_loc_name}.** "
            f"The network is financially and operationally ready for expansion. "
            f"Delaying the process means losing first-mover advantage in a competitive market. "
            f"Initiate lease negotiations in parallel with the beverage growth campaign."
        )
    else:
        rec = (
            f"**Consolidate before expanding.** "
            f"The network's growth rate of {avg_growth:.1f}%/month is not yet strong enough to absorb "
            f"the cost of a new branch. Focus resources on growing beverage share, "
            f"closing the demand gap between branches, and improving staffing efficiency. "
            f"Reassess expansion readiness in Q3."
        )

    lines.append(rec + "\n")
    lines.append("\n---\n*Generated locally from live operational data — no external AI required.*")

    return "\n".join(lines)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="padding:0.5rem 0 0.2rem;font-size:1.3rem;font-weight:800;'
        f'color:{C_GOLD};letter-spacing:-0.02em;">🍩 Conut AI</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="font-size:0.7rem;color:#8A9BAB;letter-spacing:0.08em;'
        f'text-transform:uppercase;margin-bottom:1rem;">Chief of Operations</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr style="border-color:#2C333B;margin:0.5rem 0 1rem;">', unsafe_allow_html=True)
    page = st.radio(
        "",
        [
            "🏢 Chief of Operations Briefing",
            "🛒 Objective 1 — Combo Optimization",
            "📈 Objective 2 — Demand Forecast",
            "🗺️ Objective 3 — Expansion Feasibility",
            "👥 Objective 4 — Shift Staffing",
            "☕ Objective 5 — Beverage Growth",
            "🎯 Projected Gains & Model Notes",
            "🤖 Ask the Agent",
        ],
        label_visibility="collapsed",
    )
    st.markdown('<hr style="border-color:#2C333B;margin:1rem 0 0.5rem;">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.68rem;color:#5A6470;line-height:1.8;">'
        f'API <span style="color:#8A9BAB;">{API_URL}</span><br>'
        f'4 branches · Conut · Tyre · Jnah · MSC</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# OBJECTIVE 1 — COMBO OPTIMIZATION
# ══════════════════════════════════════════════════════════════════════════════
if page == "🛒 Objective 1 — Combo Optimization":
    st.title("Objective 1: Product Combo Optimization")
    report_label("Business Intelligence Report · Market Basket Analysis · Delivery Channel")
    st.caption(
        "Using **Apriori association rule mining** on delivery basket data to identify "
        "which products customers buy together — and translate that into bundling and upsell strategy."
    )
    divider()

    data = fetch("/combo")
    if api_error(data):
        st.stop()

    method = data.get("method", "")
    combos = data.get("top_combos", [])
    top_items = data.get("top_items", [])
    recommendations = data.get("recommendations", [])

    # ── Executive Finding ─────────────────────────────────────────────────────
    st.subheader("Executive Finding")

    if method == "apriori" and combos:
        best = combos[0]
        lift = best.get("lift", 0)
        conf = best.get("confidence", 0)
        support = best.get("support", 0)
        items = best.get("items", "")

        strength = "very strong" if lift > 3 else ("strong" if lift > 2 else ("moderate" if lift > 1.5 else "present"))
        verdict_box(
            f"<strong>Association rules found via Apriori.</strong> The strongest combo is "
            f"<strong>{items}</strong> with a lift of <strong>{lift:.2f}x</strong> — "
            f"a {strength} buying affinity. {conf*100:.0f}% of customers who order one "
            f"item in this pair also order the other.",
            kind="green"
        )
    elif top_items:
        verdict_box(
            "<strong>Association rules could not be extracted</strong> — basket density is below the minimum "
            "support threshold. Falling back to top individually ordered items as a proxy for bundle candidates.",
            kind="amber"
        )
    else:
        verdict_box("No combo data could be computed from the delivery records.", kind="red")

    divider()

    # ── Analysis Narrative ────────────────────────────────────────────────────
    st.subheader("Analysis")

    if method == "apriori" and combos:
        df = pd.DataFrame(combos)

        # Interpretation guide
        analysis_box(
            "<strong>How to read these results:</strong><br>"
            "• <strong>Support</strong> = % of all orders that contain this pair. Higher = more common.<br>"
            "• <strong>Confidence</strong> = Given item A was bought, % chance item B was also bought.<br>"
            "• <strong>Lift</strong> = How much more likely this pair is bought together vs. randomly. "
            "Lift > 1.0 means positive affinity; lift > 2.0 is a strong, actionable combo."
        )

        high_lift = df[df["lift"] >= 2.0]
        kpi_row([
            {"label": "Combos Identified", "value": str(len(df)), "sub": "association rules"},
            {"label": "High-Lift (≥2.0×)", "value": str(len(high_lift)), "sub": "prime bundle candidates",
             "delta": f"{len(high_lift)/max(len(df),1)*100:.0f}% of total", "delta_dir": "pos" if high_lift.shape[0] > 0 else "neu"},
            {"label": "Strongest Lift", "value": f"{df['lift'].max():.2f}×", "sub": "top combo affinity"},
            {"label": "Avg Confidence", "value": f"{df['confidence'].mean()*100:.0f}%", "sub": "cross-purchase rate"},
        ])

        st.markdown("#### Top Combo Pairs by Association Strength")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df.head(10)["items"],
            y=df.head(10)["lift"],
            marker_color=[
                C_GREEN if v >= 2 else C_AMBER if v >= 1.5 else C_GOLD
                for v in df.head(10)["lift"]
            ],
            name="Lift",
        ))
        _style_fig(fig, "Association Lift by Combo — Gold ≥ 2.0× (Bundle Priority)")
        fig.update_layout(xaxis_tickangle=-30, xaxis_title="Product Pair", yaxis_title="Lift")
        fig.add_hline(y=2.0, line_dash="dash", line_color=C_GREEN,
                      annotation_text="Bundle threshold (2.0×)")
        fig.add_hline(y=1.0, line_dash="dot", line_color=C_MUTED,
                      annotation_text="No affinity (1.0×)")
        st.plotly_chart(fig, use_container_width=True)

        # Confidence vs Lift scatter
        st.markdown("#### Confidence vs. Lift — Combo Prioritisation Matrix")
        fig2 = px.scatter(
            df, x="confidence", y="lift",
            size="support", color="lift",
            hover_data=["items", "support", "confidence", "lift"],
            color_continuous_scale=[[0, C_AMBER], [0.5, C_GOLD], [1, C_GREEN]],
            labels={"confidence": "Confidence (conversion rate)", "lift": "Lift (affinity strength)"},
        )
        _style_fig(fig2, "Upper-right = High-confidence, high-lift: prime bundle candidates")
        fig2.add_vline(x=0.4, line_dash="dash", line_color=C_MUTED)
        fig2.add_hline(y=2.0, line_dash="dash", line_color=C_MUTED)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Full Combo Rules Table")
        display_df = df.copy()
        display_df["lift"] = display_df["lift"].apply(lambda x: f"{x:.2f}x")
        display_df["confidence"] = display_df["confidence"].apply(lambda x: f"{x*100:.1f}%")
        display_df["support"] = display_df["support"].apply(lambda x: f"{x*100:.2f}%")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    elif top_items:
        df_items = pd.DataFrame(top_items)
        st.markdown("#### Most Ordered Individual Items (Proxy for Bundle Seed)")
        fig = px.bar(df_items, x="item", y="qty", color="qty",
                     color_continuous_scale="Blues",
                     title="Top Items by Delivery Volume — Use as Anchor Products for Bundles",
                     labels={"qty": "Units Sold", "item": "Product"})
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_items, use_container_width=True, hide_index=True)

    divider()

    # ── Business Recommendations ──────────────────────────────────────────────
    st.subheader("Business Recommendations")

    if method == "apriori" and combos:
        df = pd.DataFrame(combos)
        top3 = df.head(3)

        for i, (_, row) in enumerate(top3.iterrows(), 1):
            lift_val = row["lift"]
            conf_val = row["confidence"]
            supp_val = row["support"]
            items_val = row["items"]
            priority = "HIGH" if lift_val >= 2 else "MEDIUM"
            kind = "green" if lift_val >= 2 else "amber"
            verdict_box(
                f"<strong>Recommendation {i} [{priority} PRIORITY] — Bundle: {items_val}</strong><br>"
                f"<strong>Data:</strong> {conf_val*100:.0f}% cross-purchase rate · {lift_val:.2f}x affinity · "
                f"appears in {supp_val*100:.1f}% of all delivery orders.<br>"
                f"<strong>Action:</strong> Create a discounted bundle at 5–8% below à-la-carte pricing. "
                f"Feature at POS checkout and on the delivery app item page. "
                f"At {conf_val*100:.0f}% natural conversion, even a partial push will meaningfully lift basket size.",
                kind=kind
            )
    else:
        for rec in recommendations:
            verdict_box(f"{rec}", kind="amber")

    analysis_box(
        "<strong>Bundle pricing rationale:</strong> A 5% discount on a combo is typically recovered "
        "within 2–3 units through the increased basket value. The goal is not margin per item but "
        "total transaction value per customer — especially critical for delivery where "
        "platform fees erode per-item margins."
    )


# ══════════════════════════════════════════════════════════════════════════════
# OBJECTIVE 2 — DEMAND FORECAST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Objective 2 — Demand Forecast":
    st.title("Objective 2: Demand Forecasting by Branch")
    report_label("Business Intelligence Report · Time-Series Analysis · Monthly Sales Projection")
    st.caption(
        "Linear regression trend model (with Prophet where available) applied to monthly sales history. "
        "Forecasts are used to drive inventory planning, staffing allocation, and promotional timing."
    )
    divider()

    n_months = st.slider("Forecast horizon (months ahead)", 1, 6, 3)
    data = fetch(f"/demand?n_months={n_months}")
    if api_error(data):
        st.stop()

    forecasts = data.get("forecasts", {})
    ranking = data.get("demand_ranking", [])

    # ── Executive Finding ─────────────────────────────────────────────────────
    st.subheader("Executive Finding")

    if ranking:
        rank_df = pd.DataFrame(ranking)
        top_branch = rank_df.iloc[0]["branch"]
        top_val = rank_df.iloc[0]["avg_forecast"]
        bottom_branch = rank_df.iloc[-1]["branch"]
        bottom_val = rank_df.iloc[-1]["avg_forecast"]
        spread_pct = ((top_val - bottom_val) / max(bottom_val, 1)) * 100

        # Find growing vs declining branches
        growing = [b for b, d in forecasts.items() if d.get("growth_pct_over_period", 0) > 5]
        declining = [b for b, d in forecasts.items() if d.get("growth_pct_over_period", 0) < -5]

        trend_summary = ""
        if growing:
            trend_summary += f"Growing: {', '.join(growing)}. "
        if declining:
            trend_summary += f"Declining: {', '.join(declining)}. "
        if not growing and not declining:
            trend_summary = "All branches showing stable demand trends. "

        verdict_box(
            f"<strong>{top_branch}</strong> is the highest-demand branch with an average projected "
            f"{n_months}-month demand of <strong>{top_val:,.0f} units/month</strong>. "
            f"{bottom_branch} sits at the bottom at {bottom_val:,.0f} — a <strong>{spread_pct:.0f}% gap</strong> "
            f"across the network. {trend_summary}"
            f"Resource allocation should reflect this asymmetry.",
            kind="green"
        )

    divider()

    # ── Cross-Branch Demand Comparison ────────────────────────────────────────
    st.subheader("Cross-Branch Demand Analysis")

    if ranking:
        fig = go.Figure()
        for i, row in rank_df.iterrows():
            fig.add_trace(go.Bar(
                name=row["branch"],
                x=[row["branch"]],
                y=[row["avg_forecast"]],
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                text=f"{row['avg_forecast']:,.0f}",
                textposition="outside",
            ))
        _style_fig(fig, f"Projected Average Monthly Demand — Next {n_months} Months", height=360)
        fig.update_layout(yaxis_title="Avg Forecast (units/month)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    analysis_box(
        "Demand ranking determines where inventory buffers, staffing uplifts, and promotional spend "
        "should be concentrated. A branch with high demand and high growth warrants proactive resourcing, "
        "while a declining branch signals a need for investigation into causes before additional investment."
    )

    divider()

    # ── Per-Branch Deep Dive ──────────────────────────────────────────────────
    st.subheader("Branch-Level Deep Dive")

    branches = list(forecasts.keys())
    if branches:
        tabs = st.tabs([f"{'📈' if forecasts[b].get('growth_pct_over_period',0)>5 else '📉' if forecasts[b].get('growth_pct_over_period',0)<-5 else '➡️'} {b}" for b in branches])

        for tab, branch in zip(tabs, branches):
            with tab:
                bdata = forecasts[branch]
                if "error" in bdata:
                    st.error(bdata["error"])
                    continue

                growth = bdata.get("growth_pct_over_period", 0)
                hist_mean = bdata.get("historical_mean", 0)
                method_used = bdata.get("method", "linear_regression")
                flist = bdata.get("forecast", [])
                avg_fc = sum(f["forecast"] for f in flist) / len(flist) if flist else 0

                # Trend classification
                if growth > 10:
                    trend_label, trend_color = "Strong Growth", "green"
                elif growth > 3:
                    trend_label, trend_color = "Moderate Growth", "green"
                elif growth > -3:
                    trend_label, trend_color = "Stable", "amber"
                elif growth > -10:
                    trend_label, trend_color = "Moderate Decline", "red"
                else:
                    trend_label, trend_color = "Sharp Decline", "red"

                verdict_box(
                    f"<strong>{branch} — {trend_label}</strong><br>"
                    f"Historical mean: <strong>{hist_mean:,.0f} units/month</strong> | "
                    f"Trend: <strong>{growth:+.1f}% over the data period</strong> | "
                    f"Projected avg next {n_months} months: <strong>{avg_fc:,.0f} units/month</strong> | "
                    f"Model: {method_used.replace('_', ' ').title()}",
                    kind=trend_color
                )

                if flist:
                    fdf = pd.DataFrame(flist)

                    # Forecast chart with confidence band
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=fdf["period"], y=fdf["upper"],
                        fill=None, mode="lines",
                        line=dict(color=C_GOLD, width=0),
                        name="Upper bound", showlegend=False,
                    ))
                    fig.add_trace(go.Scatter(
                        x=fdf["period"], y=fdf["lower"],
                        fill="tonexty", mode="lines",
                        line=dict(color=C_GOLD, width=0),
                        name="Confidence band",
                        fillcolor=f"rgba(200,145,58,0.12)",
                    ))
                    fig.add_trace(go.Scatter(
                        x=fdf["period"], y=fdf["forecast"],
                        mode="lines+markers",
                        line=dict(color=C_GOLD, width=2.5),
                        marker=dict(size=9, color=C_GOLD,
                                    line=dict(color=C_WHITE, width=2)),
                        name="Point forecast",
                    ))
                    fig.add_hline(
                        y=hist_mean, line_dash="dot", line_color=C_MUTED,
                        annotation_text=f"Hist. mean: {hist_mean:,.0f}",
                        annotation_position="bottom right",
                    )
                    _style_fig(fig, f"{branch} — {n_months}-Month Demand Forecast", height=360)
                    fig.update_layout(yaxis_title="Demand (units)")
                    st.plotly_chart(fig, use_container_width=True)

                    # Month-by-month forecast table
                    st.markdown("**Month-by-Month Projection**")
                    table_df = fdf.copy()
                    table_df["vs_historical"] = ((table_df["forecast"] - hist_mean) / max(hist_mean, 1) * 100).round(1)
                    table_df["vs_historical"] = table_df["vs_historical"].apply(lambda x: f"{x:+.1f}%")
                    table_df["forecast"] = table_df["forecast"].apply(lambda x: f"{x:,.0f}")
                    table_df["lower"] = table_df["lower"].apply(lambda x: f"{x:,.0f}")
                    table_df["upper"] = table_df["upper"].apply(lambda x: f"{x:,.0f}")
                    table_df.columns = ["Period", "Forecast", "Lower Bound", "Upper Bound", "vs Historical Avg"]
                    st.dataframe(table_df, use_container_width=True, hide_index=True)

                # Business implication
                if growth > 5:
                    analysis_box(
                        f"<strong>Operational implication for {branch}:</strong> A growing trend means "
                        f"demand is likely to exceed the historical average. Pre-position inventory buffers "
                        f"(~10–15% above forecast) and consider adding one staffing cover during peak shifts. "
                        f"Monitor stockout frequency as a leading indicator."
                    )
                elif growth < -5:
                    analysis_box(
                        f"<strong>Operational implication for {branch}:</strong> A declining trend warrants "
                        f"investigation. Is this a competitive pressure, product-mix issue, or local market shift? "
                        f"Run a customer exit survey and compare product mix with growing branches. "
                        f"Avoid over-stocking until the trend reversal is confirmed."
                    )
                else:
                    analysis_box(
                        f"<strong>Operational implication for {branch}:</strong> Stable demand. "
                        f"Use the historical mean as your inventory baseline with a standard ±10% buffer. "
                        f"Focus on efficiency improvements rather than volume growth."
                    )


# ══════════════════════════════════════════════════════════════════════════════
# OBJECTIVE 3 — EXPANSION FEASIBILITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Objective 3 — Expansion Feasibility":
    st.title("Objective 3: Expansion Feasibility Analysis")
    report_label("Business Intelligence Report · Network Growth Signals · Location Scoring")
    st.caption(
        "Multi-signal feasibility model evaluating network growth momentum, branch saturation, "
        "and customer density — followed by composite scoring of 10 candidate locations."
    )
    divider()

    data = fetch("/expansion")
    if api_error(data):
        st.stop()

    verdict = data.get("feasibility", "N/A")
    signals = data.get("signals", {})
    stats = data.get("network_stats", {})
    branch_metrics = data.get("branch_metrics", [])
    top_locs = data.get("top_candidate_locations", [])
    all_locs = data.get("all_candidates_ranked", [])
    recommendations = data.get("recommendations", [])

    growing = signals.get("growing_network", False)
    saturated = signals.get("saturated_branch_present", False)
    dense = signals.get("high_customer_density", False)
    signals_fired = sum([growing, saturated, dense])

    total_rev = stats.get("total_revenue", 0)
    total_cust = stats.get("total_customers", 0)
    avg_growth = stats.get("avg_monthly_growth_pct", 0)

    # ── Executive Finding ─────────────────────────────────────────────────────
    st.subheader("Executive Finding")

    if verdict == "RECOMMENDED":
        verdict_box(
            f"<strong>EXPANSION RECOMMENDED — {signals_fired}/3 signals met.</strong><br>"
            f"The Conut network is generating <strong>{avg_growth:.1f}% avg monthly growth</strong>, "
            f"serving <strong>{total_cust:,} customers</strong> across 4 branches with "
            f"total revenue of <strong>{total_rev:,.0f}</strong>. "
            f"Network indicators support opening a 5th branch.",
            kind="green"
        )
    else:
        verdict_box(
            f"<strong>EXPANSION NOT RECOMMENDED — only {signals_fired}/3 signals met.</strong><br>"
            f"Current network avg monthly growth is <strong>{avg_growth:.1f}%</strong> with "
            f"<strong>{total_cust:,} total customers</strong>. "
            f"Expansion would dilute resources before the network is mature enough to support it.",
            kind="red"
        )

    divider()

    # ── Signal Breakdown ──────────────────────────────────────────────────────
    st.subheader("Feasibility Signal Analysis")
    analysis_box(
        "Three business signals are evaluated. Each represents a different dimension of expansion readiness. "
        "A minimum of 2 out of 3 signals must be met for expansion to be recommended."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        icon = "✅" if growing else "❌"
        color = "green" if growing else "red"
        verdict_box(
            f"<strong>{icon} Network Growth Signal</strong><br>"
            f"Threshold: >1% avg monthly growth<br>"
            f"Actual: <strong>{avg_growth:.2f}%/month</strong><br>"
            f"{'PASSED — network is actively expanding.' if growing else 'FAILED — growth too slow to justify new fixed costs.'}",
            kind=color
        )
    with c2:
        bm_df = pd.DataFrame(branch_metrics) if branch_metrics else pd.DataFrame()
        max_share = bm_df["revenue_share_pct"].max() if not bm_df.empty and "revenue_share_pct" in bm_df.columns else 0
        saturated_branch = bm_df.loc[bm_df["revenue_share_pct"].idxmax(), "branch"] if not bm_df.empty and "revenue_share_pct" in bm_df.columns else "N/A"
        icon = "✅" if saturated else "❌"
        color = "green" if saturated else "amber"
        verdict_box(
            f"<strong>{icon} Saturation Signal</strong><br>"
            f"Threshold: Any branch >40% network revenue<br>"
            f"Actual: <strong>{saturated_branch} at {max_share:.1f}%</strong><br>"
            f"{'PASSED — one branch dominates; demand should be redistributed.' if saturated else 'NOT MET — revenue balanced; no saturation pressure.'}",
            kind=color
        )
    with c3:
        icon = "✅" if dense else "❌"
        color = "green" if dense else "amber"
        verdict_box(
            f"<strong>{icon} Customer Density Signal</strong><br>"
            f"Threshold: >500 customers network-wide<br>"
            f"Actual: <strong>{total_cust:,} customers</strong><br>"
            f"{'PASSED — customer base large enough to justify new coverage.' if dense else 'NOT MET — customer base still too thin; build loyalty first.'}",
            kind=color
        )

    divider()

    # ── Branch Performance Context ────────────────────────────────────────────
    st.subheader("Current Branch Performance")

    if branch_metrics:
        bm_df = pd.DataFrame(branch_metrics)
        numeric_cols = ["total_revenue", "revenue_share_pct", "monthly_growth_pct",
                        "num_customers", "avg_spend", "pct_delivery", "pct_table", "pct_take_away"]
        numeric_cols = [c for c in numeric_cols if c in bm_df.columns]

        col_l, col_r = st.columns(2)
        with col_l:
            if "total_revenue" in bm_df.columns and "branch" in bm_df.columns:
                fig = px.pie(
                    bm_df, values="total_revenue", names="branch",
                    color_discrete_sequence=CHART_COLORS,
                    hole=0.42,
                )
                _style_fig(fig, "Revenue Share by Branch", height=320)
                fig.update_traces(textinfo="label+percent", textfont_size=11)
                st.plotly_chart(fig, use_container_width=True)
        with col_r:
            if "monthly_growth_pct" in bm_df.columns and "branch" in bm_df.columns:
                bar_colors = [C_GREEN if v > 0 else C_RED for v in bm_df["monthly_growth_pct"]]
                fig2 = go.Figure(go.Bar(
                    x=bm_df["branch"], y=bm_df["monthly_growth_pct"],
                    marker_color=bar_colors,
                    text=bm_df["monthly_growth_pct"].apply(lambda x: f"{x:+.2f}%"),
                    textposition="outside",
                ))
                fig2.add_hline(y=0, line_color=C_TEXT, line_width=1)
                _style_fig(fig2, "Monthly Growth Rate by Branch (%)", height=320)
                fig2.update_layout(yaxis_title="% Growth/Month")
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Branch KPI Summary**")
        display = bm_df[["branch"] + [c for c in numeric_cols if c in bm_df.columns]].copy()
        for col in ["total_revenue", "avg_spend"]:
            if col in display.columns:
                display[col] = display[col].apply(lambda x: f"{x:,.0f}")
        for col in ["revenue_share_pct", "monthly_growth_pct", "pct_delivery", "pct_table", "pct_take_away"]:
            if col in display.columns:
                display[col] = display[col].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display, use_container_width=True, hide_index=True)

    divider()

    # ── Location Scoring ──────────────────────────────────────────────────────
    st.subheader("Candidate Location Scoring")
    analysis_box(
        "10 Beirut-area locations are scored on demand potential, growth factor, and competition risk. "
        "Composite score = (demand × growth factor) − (competition risk × 0.3). "
        "Higher composite = more attractive location. Note: scoring uses calibrated heuristics "
        "in the absence of geodemographic data."
    )

    if all_locs:
        loc_df = pd.DataFrame(all_locs)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Demand Score",
            x=loc_df["location"],
            y=loc_df["demand_score"],
            marker_color=f"rgba(200,145,58,0.75)",
        ))
        fig.add_trace(go.Bar(
            name="Competition Risk",
            x=loc_df["location"],
            y=loc_df["competition_risk"],
            marker_color=f"rgba(192,57,43,0.6)",
        ))
        fig.add_trace(go.Scatter(
            name="Composite Score",
            x=loc_df["location"],
            y=loc_df["composite_score"],
            mode="lines+markers",
            line=dict(color=C_GREEN, width=2.5),
            marker=dict(size=8, color=C_GREEN,
                        line=dict(color=C_WHITE, width=2)),
            yaxis="y2",
        ))
        _style_fig(fig, "Location Scoring — Demand vs. Competition Risk vs. Composite", height=420)
        fig.update_layout(
            barmode="group",
            yaxis=dict(title="Score", gridcolor="#EDE8E2"),
            yaxis2=dict(title="Composite Score", overlaying="y", side="right",
                        gridcolor="rgba(0,0,0,0)"),
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**All Locations Ranked**")
        display_loc = loc_df.copy()
        display_loc.index = range(1, len(display_loc) + 1)
        st.dataframe(display_loc, use_container_width=True)

    # Top 3 location verdicts
    st.markdown("#### Top 3 Location Recommendations")
    for i, loc in enumerate(top_locs[:3], 1):
        priority = ["HIGH", "MEDIUM", "MEDIUM"][i - 1]
        kind = ["green", "amber", "amber"][i - 1]
        verdict_box(
            f"<strong>#{i} {loc['location']} [{priority} PRIORITY]</strong><br>"
            f"Demand score: {loc['demand_score']} · Competition risk: {loc['competition_risk']} · "
            f"Composite: <strong>{loc['composite_score']}</strong><br>"
            f"{'Primary recommendation — highest composite score, proceed to site survey.' if i == 1 else 'Strong alternative — suitable if primary site is unavailable.'}",
            kind=kind
        )


# ══════════════════════════════════════════════════════════════════════════════
# OBJECTIVE 4 — SHIFT STAFFING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Objective 4 — Shift Staffing":
    st.title("Objective 4: Shift Staffing Optimization")
    report_label("Business Intelligence Report · Time & Attendance Analysis · Workforce Planning")
    st.caption(
        "Staffing recommendations derived from punch-in/out logs. Headcounts are aggregated by "
        "branch × shift × day, with a 15% safety buffer applied above the observed mean. "
        "Understaffing (< 2 staff/shift) is flagged as an operational risk."
    )
    divider()

    data = fetch("/staffing")
    if api_error(data):
        st.stop()

    alerts = data.get("alerts", [])
    recommendations = data.get("recommendations", [])
    shift_summary = data.get("shift_summary", [])
    hours_data = data.get("hours_per_employee", [])

    # ── Executive Finding ─────────────────────────────────────────────────────
    st.subheader("Executive Finding")

    if alerts:
        verdict_box(
            f"<strong>STAFFING RISK DETECTED — {len(alerts)} shift(s) below minimum safe headcount.</strong><br>"
            "One or more branch-shift combinations have recorded as few as 1 staff member on some days. "
            "This creates operational vulnerability: single-point-of-failure risk, service quality degradation, "
            "and potential regulatory non-compliance.",
            kind="red"
        )
    else:
        verdict_box(
            "<strong>STAFFING LEVELS ADEQUATE — No critical gaps detected.</strong><br>"
            "All observed shifts maintained a minimum of 2 staff. "
            "Recommendations below reflect data-driven optimisation opportunities.",
            kind="green"
        )

    if alerts:
        st.markdown("#### Critical Alerts")
        for alert in alerts:
            st.error(f"⚠️ {alert}")

    divider()

    # ── Shift Staffing Analysis ────────────────────────────────────────────────
    st.subheader("Shift-Level Staffing Analysis")

    analysis_box(
        "<strong>Methodology:</strong> Each day's attendance log is aggregated to count distinct employees "
        "per (branch, shift, date). The mean headcount across all observed days gives the baseline. "
        "Recommended staff = ⌈mean × 1.15⌉ — adding a 15% safety buffer — capped at the observed maximum "
        "to avoid over-staffing. Shifts with min < 2 are flagged."
    )

    if shift_summary:
        shift_df = pd.DataFrame(shift_summary)

        total_rec = shift_df["recommended_staff"].sum()
        understaffed_count = len(shift_df[shift_df["min_staff"] < 2])
        kpi_row([
            {"label": "Branch-Shift Combinations", "value": str(len(shift_df)),
             "sub": "tracked shift slots"},
            {"label": "Total Recommended Staff", "value": str(int(total_rec)),
             "sub": "daily across all shifts"},
            {"label": "At-Risk Shifts", "value": str(understaffed_count),
             "sub": "min < 2 staff observed",
             "delta": "Action needed" if understaffed_count > 0 else "All clear",
             "delta_dir": "neg" if understaffed_count > 0 else "pos"},
        ])

        # Main staffing chart
        st.markdown("#### Recommended vs. Historical Staffing by Branch & Shift")
        fig = go.Figure()
        for i, branch in enumerate(shift_df["branch"].unique()):
            bdf = shift_df[shift_df["branch"] == branch]
            xlabels = [f"{row['branch']}<br>{row['shift']}" for _, row in bdf.iterrows()]
            fig.add_trace(go.Bar(
                name=f"{branch} — Recommended",
                x=xlabels, y=bdf["recommended_staff"],
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                offsetgroup=branch,
            ))
            fig.add_trace(go.Bar(
                name=f"{branch} — Hist. Mean",
                x=xlabels, y=bdf["mean_staff"],
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                opacity=0.4,
                offsetgroup=branch + "_mean",
            ))
        _style_fig(fig, "Recommended Staff (15% buffer) vs Historical Mean", height=420)
        fig.update_layout(barmode="group", yaxis_title="Staff Count", xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

        # Min/Max range chart
        st.markdown("#### Staff Count Range by Shift (Min → Mean → Max)")
        fig2 = go.Figure()
        labels = [f"{r['branch']} · {r['shift']}" for _, r in shift_df.iterrows()]
        fig2.add_trace(go.Scatter(
            x=labels, y=shift_df["min_staff"],
            mode="markers", name="Min observed",
            marker=dict(color=C_RED, size=11, symbol="triangle-down"),
        ))
        fig2.add_trace(go.Scatter(
            x=labels, y=shift_df["mean_staff"],
            mode="markers", name="Mean",
            marker=dict(color=C_AMBER, size=11),
        ))
        fig2.add_trace(go.Scatter(
            x=labels, y=shift_df["max_staff"],
            mode="markers", name="Max observed",
            marker=dict(color=C_GREEN, size=11, symbol="triangle-up"),
        ))
        fig2.add_trace(go.Scatter(
            x=labels, y=shift_df["recommended_staff"],
            mode="lines+markers", name="Recommended",
            line=dict(color=C_GOLD, width=2.5, dash="dash"),
            marker=dict(size=8, color=C_GOLD, line=dict(color=C_WHITE, width=2)),
        ))
        fig2.add_hline(y=2, line_dash="dot", line_color=C_RED,
                       annotation_text="Minimum safe (2 staff)", annotation_position="top right")
        _style_fig(fig2, "Staffing Variability Range — Identifying Risk Floors", height=400)
        fig2.update_layout(yaxis_title="Staff Count", xaxis_tickangle=-20)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Full Shift Staffing Table**")
        disp = shift_df.copy()
        disp["mean_staff"] = disp["mean_staff"].round(1)
        disp.columns = [c.replace("_", " ").title() for c in disp.columns]
        st.dataframe(disp, use_container_width=True, hide_index=True)

    divider()

    # ── Employee Hours Analysis ───────────────────────────────────────────────
    st.subheader("Employee Hours Analysis")

    if hours_data:
        hours_df = pd.DataFrame(hours_data)

        analysis_box(
            "Average hours worked per shift record, broken down by branch. "
            "A large gap between average and maximum hours may indicate reliance on overtime — "
            "a cost risk and a burnout risk. A gap between average and minimum may indicate "
            "high turnover or erratic scheduling."
        )

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="Avg Hours", x=hours_df["branch"], y=hours_df["avg_hours"],
            marker_color=C_GOLD,
        ))
        fig3.add_trace(go.Scatter(
            name="Max Hours", x=hours_df["branch"], y=hours_df["max_hours"],
            mode="markers", marker=dict(color=C_RED, size=12, symbol="triangle-up"),
        ))
        fig3.add_trace(go.Scatter(
            name="Min Hours", x=hours_df["branch"], y=hours_df["min_hours"],
            mode="markers", marker=dict(color=C_GREEN, size=12, symbol="triangle-down"),
        ))
        fig3.add_hline(y=8, line_dash="dot", line_color=C_MUTED,
                       annotation_text="Standard shift (8h)")
        _style_fig(fig3, "Work Hours per Employee by Branch — Average, Min, Max", height=380)
        fig3.update_layout(yaxis_title="Hours per Shift Record")
        st.plotly_chart(fig3, use_container_width=True)

        st.dataframe(hours_df.round(1), use_container_width=True, hide_index=True)

    divider()

    # ── Staffing Recommendations ──────────────────────────────────────────────
    st.subheader("Staffing Recommendations")

    if recommendations:
        for rec in recommendations:
            parts = rec.split(":")
            branch_shift = parts[0].strip() if parts else rec
            detail = ":".join(parts[1:]).strip() if len(parts) > 1 else ""
            verdict_box(
                f"<strong>{branch_shift}</strong><br>{detail}",
                kind="amber"
            )

    analysis_box(
        "<strong>Implementation note:</strong> Recommended headcounts should be treated as the "
        "target rostered staff for a given shift, not the actual clock-in count. Build rosters "
        "with 1 on-call backup per branch per day to absorb sick leave and no-shows — "
        "this is especially critical for shifts that have historically fallen below 2 staff."
    )


# ══════════════════════════════════════════════════════════════════════════════
# OBJECTIVE 5 — BEVERAGE GROWTH STRATEGY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "☕ Objective 5 — Beverage Growth":
    st.title("Objective 5: Coffee & Milkshake Revenue Growth")
    report_label("Business Intelligence Report · Segment Analysis · Revenue Growth Strategy")
    st.caption(
        "Sales data segmented into coffee, milkshake, chimney cake, and other categories. "
        "Underperforming branches are identified, top products ranked, and a prioritised "
        "growth strategy playbook is generated."
    )
    divider()

    data = fetch("/strategy")
    if api_error(data):
        st.stop()

    summary = data.get("summary", {})
    under_coffee = data.get("underperforming_coffee_branches", [])
    over_coffee = data.get("outperforming_coffee_branches", [])
    under_shake = data.get("underperforming_shake_branches", [])
    top_coffee = data.get("top_coffee_items", [])
    top_shakes = data.get("top_milkshake_items", [])
    branch_compare = data.get("branch_comparison", [])
    seg_share = data.get("segment_share", [])
    strategies = data.get("strategies", [])

    coffee_pct = summary.get("coffee_share_pct", 0)
    shake_pct = summary.get("milkshake_share_pct", 0)
    bev_pct = coffee_pct + shake_pct
    coffee_rev = summary.get("coffee_total_revenue", 0)
    shake_rev = summary.get("milkshake_total_revenue", 0)

    # ── Executive Finding ─────────────────────────────────────────────────────
    st.subheader("Executive Finding")

    # Benchmark context: specialty coffee chains target 40%+ bev revenue
    bev_benchmark = 35
    gap_pct = max(bev_benchmark - bev_pct, 0)

    if bev_pct >= bev_benchmark:
        kind = "green"
        bev_status = f"Beverage revenue at {bev_pct:.1f}% meets the {bev_benchmark}% benchmark."
    elif bev_pct >= bev_benchmark * 0.7:
        kind = "amber"
        bev_status = (f"Beverage revenue at {bev_pct:.1f}% is below the {bev_benchmark}% industry benchmark. "
                      f"A {gap_pct:.1f}pp improvement would reach best-in-class.")
    else:
        kind = "red"
        bev_status = (f"Beverage revenue at {bev_pct:.1f}% is significantly below the {bev_benchmark}% benchmark. "
                      f"This represents a major untapped revenue opportunity.")

    verdict_box(
        f"<strong>Total beverage revenue share: {bev_pct:.1f}% (Coffee: {coffee_pct:.1f}% + Milkshake: {shake_pct:.1f}%)</strong><br>"
        f"{bev_status}<br>"
        f"Underperforming branches for coffee: {', '.join(under_coffee) if under_coffee else 'None'}. "
        f"{'Immediate branch-level action required.' if under_coffee else ''}",
        kind=kind
    )

    divider()

    # ── Revenue Segmentation ──────────────────────────────────────────────────
    st.subheader("Revenue Segmentation Analysis")

    if seg_share:
        seg_df = pd.DataFrame(seg_share)

        col_l, col_r = st.columns(2)
        with col_l:
            total_by_seg = seg_df.groupby("segment")["segment_revenue"].sum().reset_index()
            seg_colors = {"coffee": C_GOLD, "milkshake": "#D4718A",
                          "chimney_cake": C_AMBER, "other": C_MUTED}
            fig = px.pie(
                total_by_seg, names="segment", values="segment_revenue",
                color="segment",
                color_discrete_map=seg_colors,
                hole=0.45,
            )
            _style_fig(fig, "Network-Wide Revenue by Segment", height=320)
            fig.update_traces(textinfo="label+percent", textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            if not seg_df.empty and "branch" in seg_df.columns:
                pivot = seg_df.pivot_table(
                    index="branch", columns="segment", values="share_pct", aggfunc="sum"
                ).fillna(0)
                fig2 = go.Figure()
                seg_colors_map = {"coffee": C_GOLD, "milkshake": "#D4718A",
                                  "chimney_cake": C_AMBER, "other": C_MUTED}
                for seg in pivot.columns:
                    fig2.add_trace(go.Bar(
                        name=seg.title(), x=pivot.index, y=pivot[seg],
                        marker_color=seg_colors_map.get(seg, "#999"),
                    ))
                _style_fig(fig2, "Revenue Share by Segment per Branch (%)", height=320)
                fig2.update_layout(barmode="stack", yaxis_title="% of Branch Revenue")
                fig2.add_hline(y=20, line_dash="dash", line_color=C_GOLD,
                               annotation_text="Coffee target (20%)")
                fig2.add_hline(y=bev_benchmark, line_dash="dot", line_color="#8E44AD",
                               annotation_text=f"Bev benchmark ({bev_benchmark}%)")
                st.plotly_chart(fig2, use_container_width=True)

    # Branch Performance Gap
    if under_coffee or under_shake:
        st.markdown("#### Branch Performance Gap")
        if under_coffee:
            verdict_box(
                f"<strong>Coffee underperformance (&lt;20% share):</strong> {', '.join(under_coffee)}<br>"
                "These branches have the most room to grow coffee revenue and should be prioritised "
                "for barista training, menu prominence, and promotional campaigns.",
                kind="amber"
            )
        if under_shake:
            verdict_box(
                f"<strong>Milkshake underperformance (&lt;10% share):</strong> {', '.join(under_shake)}<br>"
                "Milkshake volume is thin at these locations. Seasonal or limited-edition SKUs "
                "can stimulate trial without committing to permanent menu expansion.",
                kind="amber"
            )

    divider()

    # ── Top Products Analysis ─────────────────────────────────────────────────
    st.subheader("Top Products by Segment")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Top Coffee Products by Revenue**")
        if top_coffee:
            coffee_df = pd.DataFrame(top_coffee)
            fig3 = px.bar(
                coffee_df, x="item", y="total_revenue",
                color="total_qty",
                color_continuous_scale=[[0, "#F5E6C8"], [1, C_GOLD]],
                labels={"total_revenue": "Revenue", "item": "Product", "total_qty": "Units Sold"},
            )
            _style_fig(fig3, "Coffee — Revenue by Product", height=340)
            fig3.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig3, use_container_width=True)
            coffee_df["total_revenue"] = coffee_df["total_revenue"].apply(lambda x: f"{x:,.0f}")
            st.dataframe(coffee_df, use_container_width=True, hide_index=True)
        else:
            st.info("No coffee items found in sales data.")

    with col_b:
        st.markdown("**Top Milkshake Products by Revenue**")
        if top_shakes:
            shake_df = pd.DataFrame(top_shakes)
            fig4 = px.bar(
                shake_df, x="item", y="total_revenue",
                color="total_qty",
                color_continuous_scale=[[0, "#F5D0DC"], [1, "#D4718A"]],
                labels={"total_revenue": "Revenue", "item": "Product", "total_qty": "Units Sold"},
            )
            _style_fig(fig4, "Milkshake — Revenue by Product", height=340)
            fig4.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig4, use_container_width=True)
            shake_df["total_revenue"] = shake_df["total_revenue"].apply(lambda x: f"{x:,.0f}")
            st.dataframe(shake_df, use_container_width=True, hide_index=True)
        else:
            st.info("No milkshake items found in sales data.")

    divider()

    # ── Strategy Playbook ─────────────────────────────────────────────────────
    st.subheader("Growth Strategy Playbook")
    analysis_box(
        "The following strategies are ranked by ease of implementation and expected impact. "
        "Strategies 1–2 can be activated immediately. Strategy 3 requires branch-level coordination. "
        "Strategies 4–5 require product/marketing planning (2–4 week lead time)."
    )

    priority_labels = ["IMMEDIATE", "IMMEDIATE", "THIS MONTH", "THIS QUARTER", "THIS QUARTER"]
    priority_kinds = ["green", "green", "amber", "amber", "amber"]

    for i, strategy in enumerate(strategies):
        priority = priority_labels[i] if i < len(priority_labels) else "PLANNED"
        kind = priority_kinds[i] if i < len(priority_kinds) else "amber"
        target = strategy.get("target", "")
        action = strategy.get("action", "")
        impact = strategy.get("expected_impact", "")
        name = strategy.get("strategy", "")

        with st.expander(f"Strategy {i+1} [{priority}] — {name}  |  Target: {target}"):
            verdict_box(
                f"<strong>Action:</strong> {action}<br><br>"
                f"<strong>Expected Impact:</strong> {impact}",
                kind=kind
            )

    analysis_box(
        f"<strong>Revenue opportunity sizing:</strong> If the network brings beverage share from "
        f"{bev_pct:.1f}% to {bev_benchmark}%, and current total revenue is proportional — "
        f"that represents a {gap_pct:.1f} percentage-point shift in mix. "
        f"On a high-volume base, even a 5pp improvement in beverage share compounds significantly "
        f"given higher margins on beverages vs. baked goods."
    )


# ══════════════════════════════════════════════════════════════════════════════
# CHIEF OF OPERATIONS BRIEFING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏢 Chief of Operations Briefing":
    st.title("Chief of Operations — Executive Briefing")
    report_label("Conut Bakery Chain · 4 Branches · AI-Powered Operations Intelligence")
    st.caption(
        "A synthesised view across all 5 business objectives. "
        "This page is your single source of truth for operational decision-making."
    )
    divider()

    ov = fetch("/overview")
    if api_error(ov):
        st.stop()

    expansion_verdict = ov.get("expansion_verdict", "N/A")
    coffee_pct = ov.get("coffee_share_pct", 0)
    shake_pct = ov.get("milkshake_share_pct", 0)
    top_loc = ov.get("expansion_top_location", {})
    demand_ranking = ov.get("demand_ranking", [])
    combo_highlights = ov.get("combo_highlights", [])
    staffing_alerts = ov.get("staffing_alerts", [])
    growth_strategies = ov.get("growth_strategies", [])

    bev_pct = coffee_pct + shake_pct

    # ── Network Health Scorecard ───────────────────────────────────────────────
    st.subheader("Network Health Scorecard")

    top_branch = demand_ranking[0]["branch"] if demand_ranking else "N/A"
    top_demand = demand_ranking[0]["avg_forecast"] if demand_ranking else 0

    kpi_row([
        {"label": "Expansion Verdict", "value": expansion_verdict,
         "delta": "Go" if expansion_verdict == "RECOMMENDED" else "Hold",
         "delta_dir": "pos" if expansion_verdict == "RECOMMENDED" else "neg"},
        {"label": "Top Demand Branch", "value": top_branch,
         "sub": f"{top_demand:,.0f} units/month projected"},
        {"label": "Beverage Revenue Share", "value": f"{bev_pct:.1f}%",
         "sub": f"Coffee {coffee_pct:.1f}% · Shake {shake_pct:.1f}%",
         "delta": f"+{35-bev_pct:.1f}pp to benchmark" if bev_pct < 35 else "At benchmark",
         "delta_dir": "neg" if bev_pct < 35 else "pos"},
        {"label": "Top Expansion Location", "value": top_loc.get("location", "N/A"),
         "sub": f"Composite score: {top_loc.get('composite_score', 'N/A')}"},
        {"label": "Staffing Alerts", "value": str(len(staffing_alerts)),
         "delta": "Action needed" if staffing_alerts else "All clear",
         "delta_dir": "neg" if staffing_alerts else "pos"},
    ])

    divider()

    # ── Demand Overview ────────────────────────────────────────────────────────
    if demand_ranking:
        st.subheader("Demand Ranking — Next Quarter Outlook")
        rank_df = pd.DataFrame(demand_ranking)
        fig = go.Figure()
        for i, row in rank_df.iterrows():
            fig.add_trace(go.Bar(
                name=row["branch"], x=[row["branch"]], y=[row["avg_forecast"]],
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                text=f"{row['avg_forecast']:,.0f}", textposition="outside",
                showlegend=False,
            ))
        _style_fig(fig, "Projected Monthly Demand by Branch", height=340)
        fig.update_layout(yaxis_title="Avg Units/Month")
        st.plotly_chart(fig, use_container_width=True)

    divider()

    # ── Priority Action Board ──────────────────────────────────────────────────
    st.subheader("Priority Action Board")
    analysis_box(
        "The following actions represent the highest-leverage operational decisions "
        "the Chief of Operations should take this period, derived from all 5 model analyses."
    )

    action_num = 1

    if staffing_alerts:
        for alert in staffing_alerts[:2]:
            verdict_box(
                f"<strong>Action {action_num} [URGENT — STAFFING]</strong><br>{alert}<br>"
                "Resolve roster immediately. Single-staff shifts create operational and service risk.",
                kind="red"
            )
            action_num += 1

    if combo_highlights:
        verdict_box(
            f"<strong>Action {action_num} [THIS WEEK — REVENUE]</strong><br>"
            f"{combo_highlights[0]}<br>"
            "Activate this bundle in the delivery app and POS upsell flow.",
            kind="amber"
        )
        action_num += 1

    if expansion_verdict == "RECOMMENDED" and top_loc:
        verdict_box(
            f"<strong>Action {action_num} [THIS MONTH — STRATEGIC]</strong><br>"
            f"Expansion is recommended. Commission a site survey for "
            f"<strong>{top_loc.get('location', 'top location')}</strong> "
            f"(composite score: {top_loc.get('composite_score', 'N/A')}).",
            kind="green"
        )
        action_num += 1

    if bev_pct < 35:
        verdict_box(
            f"<strong>Action {action_num} [THIS MONTH — REVENUE MIX]</strong><br>"
            f"Beverage share is {bev_pct:.1f}% — below the 35% benchmark. "
            f"Launch the Coffee + Chimney Cake combo bundle and activate the off-peak happy hour promo.",
            kind="amber"
        )
        action_num += 1

    if growth_strategies:
        for strat in growth_strategies[:2]:
            verdict_box(
                f"<strong>Action {action_num} [THIS QUARTER — GROWTH]</strong><br>{strat}",
                kind="amber"
            )
            action_num += 1

    divider()

    # ── Local COO Narrative Briefing ──────────────────────────────────────────
    st.subheader("Chief of Operations Narrative")
    analysis_box(
        "The following briefing is generated locally from live model data — "
        "no API key required. It synthesises all 5 operational objectives into "
        "the structured narrative you would present in a board or C-suite meeting."
    )

    # Fetch additional detail for richer narrative
    demand_data = fetch("/demand?n_months=3")
    expansion_data = fetch("/expansion")
    staffing_data = fetch("/staffing")
    strategy_data = fetch("/strategy")

    narrative = _build_coo_narrative(ov, demand_data, expansion_data, staffing_data, strategy_data)
    st.markdown(narrative)

    divider()

    # ── Combo & Staffing Details ───────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Top Combo Highlights")
        for rec in combo_highlights:
            st.success(rec)

    with col_r:
        st.markdown("#### Staffing Alerts")
        if staffing_alerts:
            for a in staffing_alerts:
                st.error(f"⚠️ {a}")
        else:
            st.success("No staffing alerts — all shifts adequately covered.")


# ══════════════════════════════════════════════════════════════════════════════
# PROJECTED GAINS & MODEL NOTES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Projected Gains & Model Notes":
    st.title("Projected Gains & Model Transparency")
    report_label("Executive Summary · Top 5 Actions · Quantified Impact · Analytical Transparency")
    st.caption(
        "A consolidated view of the **five highest-priority actions** Conut can execute today, "
        "the expected business impact of each, and the **model limitations** that bound the "
        "precision of these estimates."
    )
    divider()

    # ── SECTION 1: PRINCIPAL GAINS ────────────────────────────────────────────
    st.subheader("If Conut executes the top actions, the principal gains are:")

    kpi_row([
        {"label": "Delivery Basket Size", "value": "+15%",       "sub": "Bundle activation · lift 3.23×",         "delta": "Immediate",     "delta_dir": "pos"},
        {"label": "Compliance Risk",      "value": "Eliminated", "sub": "7 shifts re-rostered",                   "delta": "This week",     "delta_dir": "pos"},
        {"label": "Beverage Rev Share",   "value": "+3–5 pp",    "sub": "Coffee Drive · branches <20% share",     "delta": "2-wk campaign", "delta_dir": "pos"},
        {"label": "New Revenue Stream",   "value": "5th Branch", "sub": "Verdun — site survey → opening",         "delta": "Medium-term",   "delta_dir": "pos"},
        {"label": "Milkshake Volume",     "value": "+10–20%",    "sub": "SKU rollout at low-share branches",      "delta": "4–6 weeks",     "delta_dir": "pos"},
    ])

    divider()

    st.markdown("#### Action Detail")

    ACTIONS = [
        {
            "rank": 1, "icon": "🛒", "kind": "green",
            "action": "Bundle Activation",
            "trigger": "Lift 3.23× · 5% discount on Chimney Cake + Coffee",
            "mechanism": (
                "Apriori analysis confirms the pair is purchased together 3.23× more than chance. "
                "A modest 5% discount removes the last friction and pushes the bundle into every POS "
                "prompt and delivery menu header."
            ),
            "gain": "+15% avg delivery basket size",
            "timeline": "Immediate — POS & menu update",
        },
        {
            "rank": 2, "icon": "👥", "kind": "green",
            "action": "Staffing Correction",
            "trigger": "Re-roster 7 under-covered shifts",
            "mechanism": (
                "December attendance logs show 7 shifts that fell below the 2-person minimum. "
                "Re-rostering closes the coverage gap before it triggers a service failure or a "
                "labour-law violation."
            ),
            "gain": "Service &amp; compliance risk eliminated",
            "timeline": "This week — roster update",
        },
        {
            "rank": 3, "icon": "☕", "kind": "green",
            "action": "Coffee Drive",
            "trigger": "Barista training + menu re-ordering at branches below 20% coffee share",
            "mechanism": (
                "Branches where coffee accounts for less than 20% of revenue are treated as a cohort. "
                "A focused 2-week Coffee Drive — updated menu prominence and staff training — "
                "shifts the channel mix within weeks."
            ),
            "gain": "+3–5 pp beverage revenue share",
            "timeline": "2-week campaign — next operating period",
        },
        {
            "rank": 4, "icon": "🗺️", "kind": "blue",
            "action": "5th Branch — Verdun",
            "trigger": "Site survey → fit-out → soft opening",
            "mechanism": (
                "Network growth signals confirm expansion readiness (month-on-month revenue growth, "
                "no saturation at existing branches). Verdun adds a high-footfall urban node "
                "with no current Conut presence."
            ),
            "gain": "New revenue stream from Day 1",
            "timeline": "Medium-term — site survey first",
        },
        {
            "rank": 5, "icon": "🥤", "kind": "green",
            "action": "Milkshake SKU Rollout",
            "trigger": "Pistachio, rose water &amp; seasonal rotations at low-share branches",
            "mechanism": (
                "Milkshake volume sits at 10–15% of beverage revenue, well below potential. "
                "New named SKUs drive trial, word-of-mouth, and repeat purchase in markets where "
                "the category is underdeveloped."
            ),
            "gain": "+10–20% milkshake volume at target branches",
            "timeline": "4–6 weeks — menu &amp; supply update",
        },
    ]

    for a in ACTIONS:
        gain_color = C_GREEN if a["kind"] == "green" else "#2D5A8E"
        verdict_box(
            f"<strong>{a['icon']} Action {a['rank']}: {a['action']}</strong>"
            f"<span style='color:{C_MUTED};font-size:0.8em;'> &nbsp;·&nbsp; {a['timeline']}</span><br>"
            f"<em style='font-size:0.85em;color:{C_MUTED};'>{a['trigger']}</em><br><br>"
            f"{a['mechanism']}<br><br>"
            f"<strong style='color:{gain_color};'>Expected gain: {a['gain']}</strong>",
            kind=a["kind"],
        )

    divider()

    # Impact summary chart
    st.markdown("#### Quantified Impact at a Glance")

    impact_data = {
        "Action": [
            "Bundle Activation\n(Basket Size +15%)",
            "Coffee Drive\n(Rev Share +3–5 pp)",
            "Milkshake SKU\n(Volume +10–20%)",
            "Staffing Fix\n(Risk eliminated)",
            "5th Branch\n(New revenue stream)",
        ],
        "Impact": [15, 4, 15, 12, 20],
        "Color": [C_GREEN, C_GOLD, "#8E44AD", C_AMBER, "#2D5A8E"],
        "Label": ["+15%", "+4 pp", "+15%", "Risk = 0", "New stream"],
    }
    impact_df = pd.DataFrame(impact_data)

    fig_impact = go.Figure(go.Bar(
        x=impact_df["Impact"],
        y=impact_df["Action"],
        orientation="h",
        marker_color=impact_df["Color"].tolist(),
        text=impact_df["Label"],
        textposition="outside",
        cliponaxis=False,
    ))
    _style_fig(fig_impact, "Expected Business Impact by Action (illustrative scale)", height=340)
    fig_impact.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(size=11)),
        margin=dict(l=10, r=120, t=40, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_impact, use_container_width=True)

    divider()

    # ── SECTION 2: MODEL LIMITATIONS ──────────────────────────────────────────
    st.subheader("Model Limitations to Disclose")
    st.caption(
        "These notes accompany any presentation of Conut agent outputs to stakeholders. "
        "They define the confidence boundaries of each model and clarify what additional data "
        "or tooling would improve precision."
    )

    LIMITATIONS = [
        {
            "model": "Demand Forecast",
            "icon": "📈",
            "limitation": "Linear regression on a 5-month window — no seasonality without Prophet.",
            "detail": (
                "The model captures trend direction reliably but cannot decompose intra-year seasonality "
                "(Ramadan lift, summer dip, year-end spike). Installing <strong>Prophet</strong> with a "
                "full 12-month series would add seasonal decomposition and probabilistic confidence intervals. "
                "Treat current forecasts as <em>directional guidance</em>, not precise volume commitments."
            ),
            "fix": "Feed 12+ months of POS data and enable the Prophet seasonal model.",
        },
        {
            "model": "Expansion Scoring",
            "icon": "🗺️",
            "limitation": "Calibrated heuristics — not geodemographic data.",
            "detail": (
                "Feasibility is evaluated on three binary network signals (growth rate, saturation, customer density). "
                "The model does <strong>not</strong> ingest foot-traffic counts, competitor proximity, rent indices, "
                "or census data. Site recommendations should be validated with a physical survey and a geodemographic "
                "layer (e.g., Google Places API, OpenStreetMap POI density) before signing a lease."
            ),
            "fix": "Integrate Google Places API or OpenStreetMap POI density for geodemographic scoring.",
        },
        {
            "model": "Staffing Estimator",
            "icon": "👥",
            "limitation": "Assumes stationarity of shift patterns — re-calibrate after roster changes.",
            "detail": (
                "Recommended headcounts are computed from December 2025 punch records plus a 15% safety buffer. "
                "If the roster structure changes materially (new shift windows, rebranded branches, seasonal hires), "
                "the baseline must be <strong>recomputed from fresh attendance data</strong>. "
                "The model does not self-update; recalibration is a manual step after any structural change."
            ),
            "fix": "Re-run the staffing model after each roster restructure with updated attendance logs.",
        },
        {
            "model": "Combo Optimizer (Apriori)",
            "icon": "🛒",
            "limitation": "Requires minimum basket density — sparse data may fall below support threshold.",
            "detail": (
                "The algorithm needs a support threshold (currently 1%) to surface reliable rules. "
                "If a branch has fewer than ~200 delivery orders in the analysis window, many item pairs "
                "fall below threshold and the model falls back to single-item frequency ranking rather than "
                "true co-purchase association rules. Volume growth at smaller branches will improve this over time."
            ),
            "fix": "Lower support threshold or aggregate data across branches to increase density.",
        },
        {
            "model": "Local Fallback Agent",
            "icon": "🤖",
            "limitation": "Keyword-based classification — complex multi-turn reasoning requires Gemini.",
            "detail": (
                "When Gemini is unavailable, the local agent routes questions by keyword matching. "
                "It handles single-intent, well-formed queries reliably but will misroute or give incomplete "
                "answers for compound questions (e.g., <em>\"Which branch needs more staff and which combo should we push?\"</em>) "
                "or ambiguous phrasing. Full multi-turn reasoning and contextual grounding require the "
                "<strong>Gemini path with a valid API key</strong>."
            ),
            "fix": "Set GEMINI_API_KEY in .env to unlock full conversational reasoning.",
        },
    ]

    for lim in LIMITATIONS:
        verdict_box(
            f"<strong>{lim['icon']} {lim['model']}</strong>"
            f" &nbsp;—&nbsp; <em>{lim['limitation']}</em><br><br>"
            f"{lim['detail']}<br><br>"
            f"<span style='font-size:0.82em;color:{C_MUTED};'>"
            f"<strong>How to improve:</strong> {lim['fix']}</span>",
            kind="amber",
        )


# ══════════════════════════════════════════════════════════════════════════════
# AI AGENT QUERY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Ask the Agent":
    st.title("Ask the AI Operations Agent")
    report_label("Business Intelligence · Natural-Language Q&A · Local Agent")

    # Detect which agent mode the backend is running
    health_data = fetch("/health")
    if api_error(health_data):
        st.stop()

    agent_mode = health_data.get("agent_mode", "local")
    if agent_mode == "gemini":
        st.caption(
            "Powered by **Google Gemini 2.5 Flash** — grounded on live operational data from all 5 models."
        )
    else:
        st.caption(
            "Running in **local agent mode** — answers are generated directly from operational model outputs. "
            "No external API calls. Add `GEMINI_API_KEY` to `.env` to upgrade to Gemini."
        )
    divider()

    examples = [
        "Which branch should we prioritise for staffing increases next month?",
        "What combo should we promote to boost average basket size?",
        "Is now a good time to open a new branch?",
        "How can we increase coffee sales?",
        "Which branch has the highest demand forecast for next quarter?",
        "What are the top 3 actions I should take as COO this week?",
        "Where is the biggest revenue gap across our branches?",
    ]

    selected = st.selectbox("Example questions — pick one or write your own below:", [""] + examples)
    question = st.text_area(
        "Your question:",
        value=selected,
        height=100,
        placeholder="e.g. Which branch needs more staff on weekend evenings?",
    )

    if st.button("Ask Agent", type="primary") and question.strip():
        with st.spinner("Analysing data and generating response..."):
            answer = post_query(question.strip())
        divider()
        st.markdown("### Agent Response")
        st.markdown(answer)

    divider()
    st.caption(
        "Local agent: zero API cost, works offline. "
        "Set GEMINI_API_KEY in .env for conversational Gemini responses."
    )
