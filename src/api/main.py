"""
Conut AI Chief of Operations Agent — FastAPI Backend.

Exposes:
  GET  /health
  POST /query          → Natural-language query via Gemini agent
  GET  /combo          → Combo optimization
  GET  /demand         → Demand forecasting (all branches)
  GET  /demand/{branch} → Demand forecasting (single branch)
  GET  /expansion      → Expansion feasibility
  GET  /staffing       → Shift staffing estimates
  GET  /strategy       → Coffee & milkshake growth strategy
  GET  /overview       → Full dashboard summary
"""

import os
import sys
import json
import traceback
from pathlib import Path
from functools import lru_cache
from typing import Optional, Any

# Load .env file if present (never required — all analytical models run without it)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed; rely on environment variables set externally

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def _numpy_safe(obj: Any) -> Any:
    """Recursively convert numpy scalars/arrays to native Python types."""
    if isinstance(obj, dict):
        return {k: _numpy_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_numpy_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.data.ingestion import load_all
from src.models.combo_optimizer import get_combo_summary
from src.models.demand_forecaster import forecast_branch, forecast_all_branches
from src.models.expansion_analyzer import expansion_feasibility
from src.models.staffing_estimator import get_staffing_recommendations
from src.models.sales_strategist import generate_growth_strategy
from src.models.local_agent import answer_question as local_answer

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Conut AI Operations Agent",
    description="AI-Driven Chief of Operations Agent for Conut Bakery",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cached data loading ───────────────────────────────────────────────────────
_DATA: Optional[dict] = None

def get_data() -> dict:
    global _DATA
    if _DATA is None:
        _DATA = load_all()
    return _DATA


# ── Gemini agent setup ────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None
    _GENAI_AVAILABLE = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_AGENT = None

def get_agent():
    global _AGENT
    if not _GENAI_AVAILABLE:
        return None
    if _AGENT is None and GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        _AGENT = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=_SYSTEM_PROMPT,
        )
    return _AGENT


_SYSTEM_PROMPT = """
You are the AI Chief of Operations for Conut — a Lebanese sweets and beverages chain
with four branches: Conut, Conut-Tyre, Conut Jnah, and Main Street Coffee.

You have access to real operational data and can answer questions about:
1. COMBO OPTIMIZATION — Which products are frequently bought together?
2. DEMAND FORECASTING — What are expected sales for each branch next month?
3. EXPANSION FEASIBILITY — Should Conut open a new branch? Where?
4. SHIFT STAFFING — How many employees are needed per shift per branch?
5. COFFEE & MILKSHAKE GROWTH — How can Conut increase beverage sales?

When given a business question:
- Be concise, actionable, and data-driven.
- Always give specific numbers when available.
- Format your response with bullet points or short paragraphs.
- If the question doesn't match any of the 5 objectives, answer generally from an operations perspective.

You will be provided with a JSON context block containing the latest data analysis results.
Use that data to ground your answers in evidence.
""".strip()


# ── Request/Response models ───────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    include_data_context: bool = True


class QueryResponse(BaseModel):
    question: str
    answer: str
    data_context_used: bool


# ── Helper: build agent context ───────────────────────────────────────────────
def build_context_snippet(data: dict) -> str:
    """Build a compact JSON context block from the latest analyses."""
    try:
        combo = get_combo_summary(data["delivery_items"])
        demand = forecast_all_branches(data["monthly_sales"])
        expansion = expansion_feasibility(
            data["monthly_sales"], data["branch_revenue"], data["menu_avg_sales"]
        )
        staffing = get_staffing_recommendations(data["attendance"])
        strategy = generate_growth_strategy(data["sales_by_item"], data["division_summary"])

        context = {
            "combo_top3": combo.get("top_combos", combo.get("top_items", []))[:3],
            "demand_ranking": demand.get("demand_ranking", []),
            "expansion_feasibility": expansion.get("feasibility"),
            "expansion_top_location": expansion.get("top_candidate_locations", [{}])[0],
            "staffing_alerts": staffing.get("alerts", []),
            "coffee_share_pct": strategy["summary"]["coffee_share_pct"],
            "milkshake_share_pct": strategy["summary"]["milkshake_share_pct"],
            "top_strategy": strategy["strategies"][0] if strategy["strategies"] else {},
        }
        return json.dumps(context, indent=2)
    except Exception:
        return "{}"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    agent = get_agent()
    return {
        "status": "ok",
        "service": "Conut AI Operations Agent",
        "agent_mode": "gemini" if agent is not None else "local",
    }


@app.post("/query", response_model=QueryResponse)
async def query_agent(req: QueryRequest):
    """Natural-language query — uses Gemini if configured, local rule-based agent otherwise."""
    data = get_data()
    agent = get_agent()

    if agent is not None:
        # ── Gemini path ────────────────────────────────────────────────────────
        context_block = build_context_snippet(data) if req.include_data_context else "{}"
        prompt = f"""
CURRENT DATA CONTEXT:
```json
{context_block}
```

BUSINESS QUESTION:
{req.question}
""".strip()
        try:
            response = agent.generate_content(prompt)
            answer = response.text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")
    else:
        # ── Local rule-based agent (no API key required) ───────────────────────
        answer = local_answer(req.question, data)

    return QueryResponse(
        question=req.question,
        answer=answer,
        data_context_used=req.include_data_context,
    )


@app.get("/combo")
def get_combos(top_n: int = Query(default=10, ge=1, le=50)):
    """Return top product combination recommendations."""
    data = get_data()
    try:
        result = get_combo_summary(data["delivery_items"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demand")
def get_demand_all(n_months: int = Query(default=3, ge=1, le=12)):
    """Return demand forecast for all branches."""
    data = get_data()
    try:
        return forecast_all_branches(data["monthly_sales"], n_months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demand/{branch}")
def get_demand_branch(branch: str, n_months: int = Query(default=3, ge=1, le=12)):
    """Return demand forecast for a specific branch."""
    data = get_data()
    try:
        return forecast_branch(data["monthly_sales"], branch, n_months)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/expansion")
def get_expansion():
    """Return expansion feasibility analysis."""
    data = get_data()
    try:
        result = expansion_feasibility(
            data["monthly_sales"],
            data["branch_revenue"],
            data["menu_avg_sales"],
        )
        return JSONResponse(content=_numpy_safe(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/staffing")
def get_staffing():
    """Return shift staffing recommendations."""
    data = get_data()
    try:
        return get_staffing_recommendations(data["attendance"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/strategy")
def get_strategy():
    """Return coffee & milkshake growth strategy."""
    data = get_data()
    try:
        return generate_growth_strategy(data["sales_by_item"], data["division_summary"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/overview")
def get_overview():
    """Return a full dashboard summary combining all 5 objectives."""
    data = get_data()
    try:
        combo = get_combo_summary(data["delivery_items"])
        demand = forecast_all_branches(data["monthly_sales"])
        expansion = expansion_feasibility(
            data["monthly_sales"], data["branch_revenue"], data["menu_avg_sales"]
        )
        staffing = get_staffing_recommendations(data["attendance"])
        strategy = generate_growth_strategy(data["sales_by_item"], data["division_summary"])

        result = {
            "combo_highlights": combo.get("recommendations", [])[:3],
            "demand_ranking": demand.get("demand_ranking", []),
            "expansion_verdict": expansion.get("feasibility"),
            "expansion_top_location": expansion.get("top_candidate_locations", [{}])[0],
            "staffing_alerts": staffing.get("alerts", []),
            "growth_strategies": [s["strategy"] for s in strategy.get("strategies", [])],
            "coffee_share_pct": strategy["summary"]["coffee_share_pct"],
            "milkshake_share_pct": strategy["summary"]["milkshake_share_pct"],
        }
        return JSONResponse(content=_numpy_safe(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
