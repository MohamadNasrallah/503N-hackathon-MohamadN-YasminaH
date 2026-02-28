# Conut AI — Chief of Operations Agent

**AI Engineering Hackathon | American University of Beirut | EECE 503N**

---

## Business Problem

Conut is a growing Lebanese sweets and beverages chain with four active branches:
- **Conut** (flagship)
- **Conut - Tyre**
- **Conut Jnah**
- **Main Street Coffee**

Management lacks a unified system to turn raw POS and attendance data into operational decisions. This project delivers an **AI-Driven Chief of Operations Agent** that addresses five critical business objectives.

---

## Approach & Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenClaw (AI Agent Interface)                │
│   WhatsApp / Telegram / Slack → natural-language questions       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                    │
│   POST /query  →  Gemini 2.0 Flash  (LLM agent with context)    │
│   GET  /combo  →  Apriori association rules                      │
│   GET  /demand →  Linear regression / Prophet forecasting        │
│   GET  /expansion → Multi-signal feasibility scoring             │
│   GET  /staffing  → Attendance-based shift analysis              │
│   GET  /strategy  → Segment share + growth playbook              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│               Data Pipeline (src/data/ingestion.py)              │
│  Robust CSV parser → handles repeated headers, page markers,     │
│  comma-formatted numbers, multi-branch files                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│             Raw Data (data/ — 9 report-style CSVs)               │
│  Sales · Attendance · Customer orders · Menu averages            │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│             Streamlit Dashboard (app/dashboard.py)               │
│  6 pages · Plotly charts · Live API calls · AI chat              │
└─────────────────────────────────────────────────────────────────┘
```

### Five Business Objectives

| # | Objective | Technique | Key File |
|---|-----------|-----------|----------|
| 1 | **Combo Optimization** | Apriori association rules (mlxtend) | `src/models/combo_optimizer.py` |
| 2 | **Demand Forecasting** | Linear regression / Prophet | `src/models/demand_forecaster.py` |
| 3 | **Expansion Feasibility** | Multi-signal composite scoring | `src/models/expansion_analyzer.py` |
| 4 | **Shift Staffing** | Attendance clustering + buffer | `src/models/staffing_estimator.py` |
| 5 | **Coffee & Milkshake Strategy** | Segment share analysis + playbook | `src/models/sales_strategist.py` |

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
# Copy .env.example to .env, then set your key in .env

# Windows CMD
set GEMINI_API_KEY=your_google_gemini_api_key

# Linux / Mac
export GEMINI_API_KEY=your_google_gemini_api_key
```

### 3. Start the Backend API

**Windows (easiest):** double-click `start_api.bat`

**Or from terminal — always use `python -m uvicorn` to ensure the correct Python env:**
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
API docs: http://localhost:8000/docs

### 4. Start the Dashboard

**Windows (easiest):** double-click `start_dashboard.bat`

**Or:**
```bash
python -m streamlit run app/dashboard.py
```

### 5. Run the Integration Test (produces demo evidence)
```bash
python test_full_demo.py --gemini-key YOUR_KEY
```
This starts the API, tests all 8 endpoints + 3 live AI queries, then stops cleanly.

### 6. Run Notebooks (Optional)
```bash
python -m jupyter lab notebooks/
```

### 7. Connect OpenClaw
OpenClaw is already installed (`npm install -g openclaw@latest`) and the skill is deployed.
```bash
# Run the OpenClaw onboarding wizard
openclaw onboard --install-daemon
```
Select Gemini as your LLM, paste your API key, and connect a channel (Telegram recommended).

Then send: *"Ask the Conut agent: which branch needs more staff this weekend?"*

---

## Project Structure

```
conut-ops-agent/
├── data/                          # Raw CSV files (9 report files)
├── src/
│   ├── data/
│   │   └── ingestion.py           # Robust CSV parser for all 9 files
│   ├── models/
│   │   ├── combo_optimizer.py     # Objective 1: Association rules
│   │   ├── demand_forecaster.py   # Objective 2: Forecasting
│   │   ├── expansion_analyzer.py  # Objective 3: Expansion scoring
│   │   ├── staffing_estimator.py  # Objective 4: Staffing
│   │   └── sales_strategist.py    # Objective 5: Growth strategy
│   └── api/
│       └── main.py                # FastAPI backend + Gemini agent
├── app/
│   └── dashboard.py               # Streamlit web dashboard
├── notebooks/
│   ├── 00_data_exploration.ipynb
│   ├── 01_combo_optimization.ipynb
│   ├── 02_demand_forecasting.ipynb
│   ├── 03_expansion_feasibility.ipynb
│   ├── 04_staffing_estimation.ipynb
│   └── 05_coffee_milkshake_strategy.ipynb
├── openclaw/
│   ├── SKILL.md                   # OpenClaw skill definition
│   └── install_skill.sh           # One-command skill installer
├── requirements.txt
└── README.md
```

---

## Key Results & Recommendations

### 1. Combo Optimization
Top combos identified from delivery basket analysis (Apriori, support ≥ 2%):
- **Chimney Cake + Coffee** — highest co-occurrence; bundle at 5% discount
- **Milkshake + Chimney Topping** — strong lift score; promote as "indulgence bundle"

### 2. Demand Forecasting
- **Conut Jnah** and **Main Street Coffee** show the strongest growth trajectories
- **Conut - Tyre** shows the highest absolute volume; prioritise inventory here

### 3. Expansion Feasibility
- Network shows consistent month-on-month growth → **expansion is recommended**
- Top candidate locations: **Hamra**, **Achrafieh**, **Jounieh** (based on composite demand/competition scoring)

### 4. Shift Staffing
- Afternoon shift (14:00–22:00) is the peak period across all branches
- Recommended minimum staffing: **3 staff for morning**, **5–6 for afternoon**, **3 for night**
- Alert: some branches had single-person shifts during December — coverage gap risk

### 5. Coffee & Milkshake Growth Strategy
- Coffee represents ~20–25% of revenue; milkshakes ~10–15% — both below potential
- Strategies: star-product upsell, combo bundles, branch-level drive campaigns, seasonal milkshake menu, off-peak happy hour pricing

---

## OpenClaw Integration

The `openclaw/SKILL.md` file teaches OpenClaw how to:
1. Route natural-language operational questions to the correct API endpoint
2. Parse JSON responses into human-readable summaries
3. Deliver answers through any connected channel (WhatsApp, Telegram, Slack)

**Example OpenClaw conversation:**
> 🧑 "Which branch needs more staff next weekend?"
> 🤖 "Based on attendance patterns, **Conut Jnah** and **Main Street Coffee** are understaffed on Saturday afternoons. Recommend 6 staff for 14:00–22:00 shift. Conut-Tyre had single-staff incidents in December — flag for HR review."

---

## Hackathon Deliverables Mapping

This section maps directly to the required submission items in `CONUT_AI_ENGINEERING_HACKATHON.md`.

1. **Public GitHub repository**
- This repository (`conut-ops-agent`) contains all source code, data files, scripts, and docs.

2. **README with required content**
- Business problem: see **Business Problem**
- Approach and architecture: see **Approach & Architecture**
- How to run: see **How to Run**
- Key results and recommendations: see **Key Results & Recommendations**

3. **Executive brief (max 2 pages PDF)**
- `../Executive_Summary.pdf`
- Source draft: `docs/executive_brief.tex`

4. **Demo evidence (OpenClaw invoking the system)**
- Recommended evidence files to include in repo:
  - `evidence/openclaw_chat.png`
  - `evidence/api_invocation_log.png`
  - `evidence/backend_docs_or_health.png`
  - `evidence/demo.mp4` (optional, strongly recommended)

---

## OpenClaw Demo (What To Show)

To satisfy the mandatory OpenClaw integration requirement, show all three in one flow:
1. OpenClaw receives the operations question.
2. OpenClaw invokes the Conut API endpoint(s).
3. The Conut backend returns the answer used in the OpenClaw response.

Minimal demo run:
```bash
# Terminal 1
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --access-log

# Terminal 2
openclaw gateway

# Terminal 3
openclaw dashboard
```

Use prompts such as:
- `Which branch needs more staff next weekend, and by shift?`
- `Should we expand now? Give top 3 candidate locations.`
- `What combo should we promote this week?`

If OpenClaw security blocks `url-fetch` to localhost, use `exec` with curl:
- `curl.exe -s "http://localhost:8000/staffing"`
- `curl.exe -s "http://localhost:8000/expansion"`

---

## Reproducibility

- Python 3.11+
- All dependencies pinned in `requirements.txt`
- Data files in `data/` (committed to repo)
- No internet connection required after install (except for Gemini API calls)

---

*Built for EECE 503N AI Engineering Hackathon — Professor Ammar Mohanna, AUB*
