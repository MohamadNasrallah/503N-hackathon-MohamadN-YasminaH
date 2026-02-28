---
name: conut-ops-agent
description: "Route Conut operations questions to the local Conut FastAPI backend and return actionable summaries for staffing, demand, combos, expansion, strategy, and overview."
metadata: { "openclaw": { "emoji": "🍩", "requires": { "bins": ["curl"] } } }
---

# Conut AI Operations Agent Skill

## Overview
This skill connects OpenClaw to the **Conut AI Chief of Operations Agent** — a FastAPI-backed analytics system that answers operational questions for a Lebanese sweets and beverages chain.

## Prerequisites
- The Conut API must be running locally: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
- Or deployed to a remote URL (set `CONUT_API_URL` below)

## Configuration
```
CONUT_API_URL=http://localhost:8000
```

## What this skill can do
Ask the agent anything about Conut's operations. It will:
1. Call the appropriate API endpoint
2. Format a natural-language answer
3. Return actionable insights

## Available Endpoints

| Action | Endpoint | Description |
|--------|----------|-------------|
| Natural language query | `POST /query` | Ask any business question |
| Combo recommendations | `GET /combo` | Best product bundles |
| Demand forecast | `GET /demand` | All-branch demand forecast |
| Branch forecast | `GET /demand/{branch}` | Single branch demand forecast |
| Expansion analysis | `GET /expansion` | New branch feasibility |
| Staffing plan | `GET /staffing` | Shift staffing recommendations |
| Growth strategy | `GET /strategy` | Coffee & milkshake strategy |
| Full overview | `GET /overview` | Combined dashboard summary |

## Example Invocations

### Via OpenClaw (natural language)
> "Ask the Conut agent: which branch needs the most staff next weekend?"

> "Ask the Conut ops agent for the top product combo to promote this week"

> "Get the expansion feasibility report from Conut AI"

> "What does the Conut agent say about coffee sales strategy?"

### Direct API calls (when OpenClaw executes shell/HTTP)
```bash
# Natural language query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which branch should we open next?", "include_data_context": true}'

# Combo optimization
curl http://localhost:8000/combo

# Demand forecast (next 3 months)
curl "http://localhost:8000/demand?n_months=3"

# Single branch forecast
curl "http://localhost:8000/demand/Conut%20Jnah?n_months=3"

# Expansion feasibility
curl http://localhost:8000/expansion

# Staffing recommendations
curl http://localhost:8000/staffing

# Coffee & milkshake strategy
curl http://localhost:8000/strategy

# Full overview
curl http://localhost:8000/overview
```

## Skill Instructions (for OpenClaw agent system prompt)

When the user asks about Conut operations, staffing, demand, combos, expansion, or sales strategy:

1. Identify the relevant endpoint from the table above.
2. Make an HTTP GET (or POST for `/query`) request to `$CONUT_API_URL/<endpoint>`.
3. Parse the JSON response.
4. Summarise the key insights in 2-4 bullet points.
5. Always end with a concrete recommended action.

For general or ambiguous questions, use the `/query` endpoint with the user's question verbatim — it will route to the Gemini-powered agent with live data context.

## Error Handling
- If the API is unreachable: "The Conut Operations Agent is offline. Start it with `uvicorn src.api.main:app --port 8000` from the project directory."
- If an endpoint returns 500: Retry with `/overview` as a fallback.

## Branch Names (exact spelling for URL encoding)
- `Conut`
- `Conut - Tyre` → URL: `Conut%20-%20Tyre`
- `Conut Jnah` → URL: `Conut%20Jnah`
- `Main Street Coffee` → URL: `Main%20Street%20Coffee`
