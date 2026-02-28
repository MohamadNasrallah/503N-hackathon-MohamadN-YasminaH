"""
Quick-start script — validates the pipeline end-to-end without starting a server.
Run: python run.py
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from src.data.ingestion import load_all
from src.models.combo_optimizer import get_combo_summary
from src.models.demand_forecaster import forecast_all_branches
from src.models.expansion_analyzer import expansion_feasibility
from src.models.staffing_estimator import get_staffing_recommendations
from src.models.sales_strategist import generate_growth_strategy


def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def main():
    banner("Loading data...")
    data = load_all()
    for name, df in data.items():
        print(f"  {name:25s} {df.shape}")

    banner("1. Combo Optimization")
    combo = get_combo_summary(data["delivery_items"])
    for r in combo.get("recommendations", [])[:3]:
        print(f"  • {r}")

    banner("2. Demand Forecasting")
    demand = forecast_all_branches(data["monthly_sales"], n_months=3)
    for r in demand.get("demand_ranking", []):
        print(f"  {r['branch']:25s} -> avg forecast {r['avg_forecast']:>15,.0f}")

    banner("3. Expansion Feasibility")
    expansion = expansion_feasibility(
        data["monthly_sales"], data["branch_revenue"], data["menu_avg_sales"]
    )
    print(f"  Verdict: {expansion['feasibility']}")
    for loc in expansion.get("top_candidate_locations", [])[:3]:
        print(f"  • {loc['location']:20s} score={loc['composite_score']:.1f}")

    banner("4. Shift Staffing")
    staffing = get_staffing_recommendations(data["attendance"])
    for r in staffing.get("recommendations", [])[:4]:
        print(f"  • {r}")

    banner("5. Coffee & Milkshake Strategy")
    strategy = generate_growth_strategy(data["sales_by_item"], data["division_summary"])
    print(f"  Coffee share: {strategy['summary']['coffee_share_pct']:.1f}%")
    print(f"  Milkshake share: {strategy['summary']['milkshake_share_pct']:.1f}%")
    for s in strategy.get("strategies", [])[:3]:
        print(f"  [{s['strategy']}] -> {s['expected_impact']}")

    banner("All checks passed!")
    print("\nNext steps:")
    print("  1. Start API:       double-click start_api.bat")
    print("                  or: python -m uvicorn src.api.main:app --port 8000 --reload")
    print("  2. Start dashboard: double-click start_dashboard.bat")
    print("                  or: python -m streamlit run app/dashboard.py")
    print("  3. AI queries:      set GEMINI_API_KEY=your_key  then  python test_full_demo.py --gemini-key YOUR_KEY")


if __name__ == "__main__":
    main()
