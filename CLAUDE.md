# CLAUDE.md — Instructions for Claude Code

## What This Project Is
A personal AI-powered equity research platform for a retail investor
in Bangalore. It analyzes Indian and US stocks, tracks a portfolio,
and surfaces investment decisions. Full product spec is in SPEC.md.
Current build status and next tasks are in PLAN.md.

## Before Every Session
1. Read SPEC.md to understand the product we are building
2. Read PLAN.md to find the current phase and the next unchecked task
3. Only work on what PLAN.md marks as next — do not jump ahead
4. If anything is ambiguous, ask one clarifying question before writing code

## After Every Task
- Mark the completed task as [x] in PLAN.md
- Add a one-line note under "Decisions Log" if any meaningful technical
  choice was made
- Confirm the code runs without errors before moving on

---

## Project Structure (target layout — build toward this)

```
equity-research-agent/
├── agents/
│   ├── orchestrator.py       # Routes queries, synthesizes final verdict
│   ├── quality_agent.py      # ROE, ROCE, FCF, moat, promoter holding
│   ├── value_agent.py        # DCF, Graham formula, PEG, margin of safety
│   ├── growth_agent.py       # Revenue/EPS CAGR, TAM, forward estimates
│   ├── bear_case_agent.py    # Red flags, accounting issues, short thesis
│   ├── momentum_agent.py     # RSI, MACD, 200-DMA, volume
│   ├── sentiment_agent.py    # News tone, con-call language
│   ├── macro_agent.py        # RBI/Fed cycle, FII flows, sector signals
│   ├── risk_manager.py       # Position sizing, concentration, drawdown
│   └── portfolio_manager.py  # Fit check within existing holdings
├── data/
│   ├── fmp.py                # Financial Modeling Prep API (US stocks)
│   ├── screener.py           # Screener.in scraper (Indian stocks)
│   ├── yfinance_client.py    # Prices + basic fundamentals (both markets)
│   ├── google_sheets.py      # Portfolio read/write via gspread
│   └── news.py               # Google News RSS + FMP news feed
├── tools/
│   ├── prompts.py            # All LLM prompt templates
│   ├── formatters.py         # Verdict card formatter
│   └── utils.py              # Shared helpers
├── dashboard/
│   └── app.py                # Streamlit web dashboard
├── digest/
│   └── daily_brief.py        # Morning email digest
├── tests/
│   ├── test_fmp.py
│   ├── test_screener.py
│   └── test_agents.py
├── .env                      # API keys — NEVER commit this
├── .env.example              # Template — commit this
├── requirements.txt
├── main.py                   # CLI entry point
├── CLAUDE.md                 # This file
├── SPEC.md                   # Product + architecture spec
└── PLAN.md                   # Build tracker
```

---

## How to Run

```bash
# Setup
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Fill in your API keys

# Analyze a stock (CLI)
python main.py --ticker AAPL
python main.py --ticker ZOMATO.NS

# Run dashboard
streamlit run dashboard/app.py

# Run screener
python main.py --screen india --filter undervalued
```

---

## Coding Conventions

- Python 3.11+
- Type hints on every function signature
- Docstring on every class and public function
- Keep each file under 200 lines — split into smaller modules if larger
- Never hardcode API keys — always load from .env via python-dotenv
- All agents must return a consistent structured dict (see Agent Output
  Schema below)
- Prefer explicit over clever — this codebase should be easy to read
  and modify

## Agent Output Schema
Every agent must return a dict with this structure:
```python
{
    "agent": str,           # agent name e.g. "quality_agent"
    "ticker": str,          # e.g. "AAPL" or "ZOMATO.NS"
    "signal": str,          # "bullish" | "bearish" | "neutral"
    "score": float,         # 0.0 to 10.0
    "summary": str,         # 2-3 sentence plain English summary
    "details": dict,        # agent-specific metrics and findings
    "flags": list[str],     # any red flags found (empty list if none)
    "timestamp": str        # ISO format
}
```

## Final Verdict Schema
The orchestrator synthesizes all agent outputs into:
```python
{
    "ticker": str,
    "verdict": str,           # "BUY" | "WATCH" | "AVOID"
    "conviction": float,      # 1.0 to 10.0
    "fair_value": float,      # estimated intrinsic value
    "current_price": float,
    "upside_pct": float,
    "bull_reasons": list[str],   # top 3
    "risks": list[str],          # top 3
    "what_changes_mind": dict,   # {"bull": str, "bear": str}
    "portfolio_fit": str,        # note on fit with existing holdings
    "agent_signals": list[dict], # all agent outputs
    "generated_at": str
}
```

---

## Environment Variables Required

```
# .env.example

# Anthropic
ANTHROPIC_API_KEY=

# Financial Modeling Prep (US stocks)
FMP_API_KEY=

# Alpha Vantage (technicals fallback)
ALPHA_VANTAGE_API_KEY=

# Google Sheets (portfolio)
GOOGLE_SHEETS_CREDS_PATH=credentials.json
PORTFOLIO_SHEET_ID=

# Email digest (optional, Phase 5)
SMTP_EMAIL=
SMTP_PASSWORD=
DIGEST_RECIPIENT_EMAIL=
```

---

## Important Constraints

- This is a personal decision-support tool, not an autonomous trading bot
- Never write code that places actual buy/sell orders
- The human always makes the final investment decision
- When scraping Screener.in, be respectful — add delays between requests
  and do not hammer the server
- All financial data is for personal use only