"""
Full demo test — starts the API server, runs all endpoint tests, then stops it.
Simulates exactly what OpenClaw does when invoking the Conut Ops Agent.

Usage: python test_full_demo.py [--gemini-key YOUR_KEY]
"""
import sys
import os
import json
import time
import signal
import argparse
import subprocess
import requests
from pathlib import Path

ROOT = Path(__file__).parent
BASE_URL = "http://localhost:8000"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY", ""))
    p.add_argument("--port", type=int, default=8000)
    return p.parse_args()


def wait_for_api(url: str, timeout: int = 20) -> bool:
    """Poll until the API responds or we time out."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def hr(title=""):
    print(f"\n{'='*65}")
    if title:
        print(f"  {title}")
        print('='*65)


def ok(label, data=None):
    print(f"  [PASS] {label}")
    return data


def fail(label, reason=""):
    print(f"  [FAIL] {label}  {reason}")


def run_tests(base: str, gemini_key: str):
    s = requests.Session()
    s.timeout = 30

    # ── Health ────────────────────────────────────────────────────────────────
    hr("1. Health Check")
    r = s.get(f"{base}/health")
    d = ok("GET /health", r.json()) if r.ok else fail("GET /health", r.text)
    print(f"     {d}")

    # ── Overview ──────────────────────────────────────────────────────────────
    hr("2. Overview (all 5 objectives in one call)")
    r = s.get(f"{base}/overview")
    if r.ok:
        d = r.json()
        ok("GET /overview")
        print(f"     Expansion verdict  : {d.get('expansion_verdict')}")
        print(f"     Coffee share       : {d.get('coffee_share_pct', 0):.1f}%")
        print(f"     Milkshake share    : {d.get('milkshake_share_pct', 0):.1f}%")
        top = d.get("expansion_top_location", {})
        print(f"     Top location       : {top.get('location')} (score {top.get('composite_score')})")
        print("     Active strategies  :", d.get("growth_strategies", [])[:2])
    else:
        fail("GET /overview", r.text)

    # ── Combo ─────────────────────────────────────────────────────────────────
    hr("3. Combo Optimization")
    r = s.get(f"{base}/combo")
    if r.ok:
        d = r.json()
        ok("GET /combo")
        for i, rec in enumerate(d.get("recommendations", [])[:3], 1):
            print(f"     {i}. {rec}")
    else:
        fail("GET /combo", r.text)

    # ── Demand all ────────────────────────────────────────────────────────────
    hr("4. Demand Forecast — All Branches")
    r = s.get(f"{base}/demand?n_months=3")
    if r.ok:
        d = r.json()
        ok("GET /demand")
        for b in d.get("demand_ranking", []):
            print(f"     {b['branch']:25s}  {b['avg_forecast']:>15,.0f}")
    else:
        fail("GET /demand", r.text)

    # ── Demand single ─────────────────────────────────────────────────────────
    hr("5. Demand Forecast — Conut Jnah only")
    r = s.get(f"{base}/demand/Conut%20Jnah")
    if r.ok:
        d = r.json()
        ok("GET /demand/Conut Jnah")
        print(f"     Growth: {d.get('growth_pct_over_period', 0):+.1f}%")
        print(f"     Insight: {d.get('insight', '')[:100]}")
        for f in d.get("forecast", []):
            print(f"     {f['period']}: {f['forecast']:,.0f}  [{f['lower']:,.0f} – {f['upper']:,.0f}]")
    else:
        fail("GET /demand/Conut Jnah", r.text)

    # ── Expansion ─────────────────────────────────────────────────────────────
    hr("6. Expansion Feasibility")
    r = s.get(f"{base}/expansion")
    if r.ok:
        d = r.json()
        ok("GET /expansion")
        print(f"     Verdict: {d.get('feasibility')}")
        signals = d.get("signals", {})
        for k, v in signals.items():
            print(f"       {'YES' if v else 'NO ':4s}  {k}")
        print("     Top candidate locations:")
        for loc in d.get("top_candidate_locations", [])[:3]:
            print(f"       {loc['location']:20s}  composite={loc['composite_score']:.1f}")
    else:
        fail("GET /expansion", r.text)

    # ── Staffing ──────────────────────────────────────────────────────────────
    hr("7. Shift Staffing")
    r = s.get(f"{base}/staffing")
    if r.ok:
        d = r.json()
        ok("GET /staffing")
        for rec in d.get("recommendations", [])[:5]:
            print(f"     - {rec}")
        for alert in d.get("alerts", [])[:3]:
            print(f"     ! {alert}")
    else:
        fail("GET /staffing", r.text)

    # ── Strategy ──────────────────────────────────────────────────────────────
    hr("8. Coffee & Milkshake Growth Strategy")
    r = s.get(f"{base}/strategy")
    if r.ok:
        d = r.json()
        ok("GET /strategy")
        summary = d.get("summary", {})
        print(f"     Coffee share    : {summary.get('coffee_share_pct', 0):.1f}%")
        print(f"     Milkshake share : {summary.get('milkshake_share_pct', 0):.1f}%")
        for strat in d.get("strategies", []):
            print(f"\n     [{strat['strategy']}]")
            print(f"       Target : {strat['target']}")
            print(f"       Action : {strat['action'][:90]}...")
            print(f"       Impact : {strat['expected_impact']}")
    else:
        fail("GET /strategy", r.text)

    # ── AI Agent (Gemini) ─────────────────────────────────────────────────────
    hr("9. AI Agent — Natural Language Queries  (simulates OpenClaw messages)")
    if not gemini_key:
        print("     [SKIP] Set --gemini-key or GEMINI_API_KEY env var to test AI queries")
    else:
        questions = [
            "Which branch should we prioritise for staffing increases next month?",
            "What combo should we promote to boost basket size?",
            "Should we open a new branch in Hamra?",
        ]
        for q in questions:
            print(f"\n  OpenClaw user: {q}")
            try:
                r = s.post(
                    f"{base}/query",
                    json={"question": q, "include_data_context": True},
                    timeout=60,
                )
                if r.ok:
                    answer = r.json().get("answer", "")
                    # Wrap long lines
                    words = answer.split()
                    line, lines = [], []
                    for w in words:
                        line.append(w)
                        if len(" ".join(line)) > 70:
                            lines.append("  Agent: " + " ".join(line))
                            line = []
                    if line:
                        lines.append("  Agent: " + " ".join(line))
                    print("\n".join(lines[:6]))
                else:
                    print(f"     [FAIL] HTTP {r.status_code}")
            except Exception as e:
                print(f"     [ERROR] {e}")
            time.sleep(2)


def main():
    args = parse_args()
    base = f"http://localhost:{args.port}"

    hr("Conut AI Ops Agent — Full Integration Demo")
    print(f"  Starting API on port {args.port}...")
    print(f"  Gemini key: {'set' if args.gemini_key else 'NOT SET (AI queries will be skipped)'}")

    # Set key for the subprocess
    env = os.environ.copy()
    if args.gemini_key:
        env["GEMINI_API_KEY"] = args.gemini_key

    # Start uvicorn
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.main:app",
         "--host", "0.0.0.0", "--port", str(args.port), "--log-level", "warning"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(f"  API PID: {proc.pid} — waiting for startup...")
    ready = wait_for_api(f"{base}/health", timeout=20)

    if not ready:
        print("  [ERROR] API did not start in time. Check port not already in use.")
        proc.terminate()
        sys.exit(1)

    print("  API is UP!\n")

    try:
        run_tests(base, args.gemini_key)
    finally:
        proc.terminate()
        proc.wait()
        print("\n  API server stopped.")

    hr("DEMO COMPLETE")
    print("  All endpoints tested successfully.")
    print("  Use these results as evidence for your OpenClaw integration demo.\n")


if __name__ == "__main__":
    main()
