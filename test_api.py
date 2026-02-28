"""
API integration test — simulates OpenClaw calling the Conut Ops Agent.
Run AFTER starting the API: uvicorn src.api.main:app --port 8000 --reload

Usage: python test_api.py [--api-url http://localhost:8000]
"""
import sys
import json
import time
import argparse
import requests

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--api-url", default="http://localhost:8000")
    return p.parse_args()


def hr(title=""):
    print(f"\n{'='*60}")
    if title:
        print(f"  {title}")
        print('='*60)


def check(label, r):
    if r.status_code == 200:
        print(f"  [OK] {label}")
        return r.json()
    else:
        print(f"  [FAIL] {label} — HTTP {r.status_code}: {r.text[:200]}")
        return {}


def main():
    args = parse_args()
    BASE = args.api_url.rstrip("/")
    s = requests.Session()
    s.timeout = 30

    hr("Conut AI Ops Agent — OpenClaw Integration Test")
    print(f"  Target: {BASE}\n")

    # ── 1. Health ─────────────────────────────────────────────────────────────
    hr("1. Health Check")
    r = s.get(f"{BASE}/health")
    data = check("GET /health", r)
    print(f"     Status: {data.get('status')} | Service: {data.get('service')}")

    # ── 2. Combo ──────────────────────────────────────────────────────────────
    hr("2. Combo Optimization  (GET /combo)")
    r = s.get(f"{BASE}/combo")
    data = check("GET /combo", r)
    recs = data.get("recommendations", [])
    for i, rec in enumerate(recs[:3], 1):
        print(f"     {i}. {rec}")

    # ── 3. Demand — all branches ──────────────────────────────────────────────
    hr("3. Demand Forecast — All Branches  (GET /demand)")
    r = s.get(f"{BASE}/demand?n_months=3")
    data = check("GET /demand", r)
    for b in data.get("demand_ranking", []):
        print(f"     {b['branch']:25s}  avg_forecast = {b['avg_forecast']:>15,.0f}")

    # ── 4. Demand — single branch ─────────────────────────────────────────────
    hr("4. Demand Forecast — Conut Jnah  (GET /demand/{branch})")
    r = s.get(f"{BASE}/demand/Conut%20Jnah?n_months=3")
    data = check("GET /demand/Conut Jnah", r)
    print(f"     Growth: {data.get('growth_pct_over_period', 0):+.1f}%")
    print(f"     Insight: {data.get('insight', '')}")
    for f in data.get("forecast", [])[:3]:
        print(f"     {f['period']}: {f['forecast']:,.0f}  [{f['lower']:,.0f} - {f['upper']:,.0f}]")

    # ── 5. Expansion ──────────────────────────────────────────────────────────
    hr("5. Expansion Feasibility  (GET /expansion)")
    r = s.get(f"{BASE}/expansion")
    data = check("GET /expansion", r)
    print(f"     Verdict: {data.get('feasibility')}")
    stats = data.get("network_stats", {})
    print(f"     Avg monthly growth: {stats.get('avg_monthly_growth_pct', 0):.2f}%")
    print("     Top candidate locations:")
    for loc in data.get("top_candidate_locations", [])[:3]:
        print(f"       - {loc['location']:20s}  composite={loc['composite_score']:.1f}")

    # ── 6. Staffing ───────────────────────────────────────────────────────────
    hr("6. Shift Staffing  (GET /staffing)")
    r = s.get(f"{BASE}/staffing")
    data = check("GET /staffing", r)
    for rec in data.get("recommendations", [])[:4]:
        print(f"     - {rec}")
    alerts = data.get("alerts", [])
    if alerts:
        print("     ALERTS:")
        for a in alerts[:3]:
            print(f"       ! {a}")

    # ── 7. Strategy ───────────────────────────────────────────────────────────
    hr("7. Coffee & Milkshake Strategy  (GET /strategy)")
    r = s.get(f"{BASE}/strategy")
    data = check("GET /strategy", r)
    summary = data.get("summary", {})
    print(f"     Coffee share:    {summary.get('coffee_share_pct', 0):.1f}%")
    print(f"     Milkshake share: {summary.get('milkshake_share_pct', 0):.1f}%")
    for strat in data.get("strategies", [])[:3]:
        print(f"     [{strat['strategy']}]")
        print(f"       Action: {strat['action'][:80]}...")
        print(f"       Impact: {strat['expected_impact']}")

    # ── 8. Overview ───────────────────────────────────────────────────────────
    hr("8. Full Overview  (GET /overview)")
    r = s.get(f"{BASE}/overview")
    data = check("GET /overview", r)
    print(f"     Expansion verdict: {data.get('expansion_verdict')}")
    top_loc = data.get("expansion_top_location", {})
    print(f"     Top location: {top_loc.get('location')} (score {top_loc.get('composite_score')})")
    print(f"     Coffee share: {data.get('coffee_share_pct', 0):.1f}%")
    print("     Active strategies:", data.get("growth_strategies", [])[:2])

    # ── 9. AI Agent Query (requires GEMINI_API_KEY) ───────────────────────────
    hr("9. AI Agent Query  (POST /query) — requires GEMINI_API_KEY")
    questions = [
        "Which branch should we prioritise for staffing increases next month?",
        "What is the best combo to promote this week?",
        "Should we open a new branch in Hamra?",
    ]
    for q in questions:
        print(f"\n  Q: {q}")
        try:
            r = s.post(f"{BASE}/query", json={"question": q}, timeout=60)
            if r.status_code == 503:
                print("     [SKIP] GEMINI_API_KEY not set — set env var to enable AI responses")
                break
            elif r.status_code == 200:
                answer = r.json().get("answer", "")
                # Print first 300 chars
                short = answer[:300].replace("\n", " ")
                print(f"  A: {short}{'...' if len(answer) > 300 else ''}")
            else:
                print(f"     [FAIL] HTTP {r.status_code}")
        except requests.exceptions.Timeout:
            print("     [TIMEOUT] Gemini took too long")
        time.sleep(1)

    hr("ALL TESTS COMPLETE")
    print("  Screenshot or record this output for your demo evidence.\n")


if __name__ == "__main__":
    main()
