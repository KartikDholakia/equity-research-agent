# CLAUDE.md — Instructions for Claude Code

## What This Project Is
A personal AI-powered equity research platform for a retail investor in
Bangalore. It analyzes Indian and US stocks, tracks a portfolio, and
surfaces investment decisions. The human always makes the final call —
this is a decision-support tool, not a trading bot.

## Before Every Session
1. Read PLAN.md to find the current phase and the next unchecked task
2. Only work on what PLAN.md marks as next — do not jump ahead
3. If a task touches an agent, a tool, or the data layer, skim the
   relevant section of ARCHITECTURE.md first — it has the layer this
   change belongs in and the invariants not to break
4. If anything is ambiguous, ask clarifying questions before writing code

## After Every Task
- Mark the completed task as [x] in PLAN.md
- Add a one-line note under PLAN.md's "Decisions Log" if any meaningful
  technical choice was made
- Confirm the code runs without errors before moving on
- If the task added/moved/removed a file, folder, agent, persona, or
  skill — or changed either schema below — update the relevant section
  of this file in the same task. Don't defer it to a cleanup pass.

## Keeping This File Current
This file goes stale the moment the repo changes underneath it — that's
exactly what happened before this section was added (the repo layout,
DEV_AGENT.md's location, and a stale checklist item had all drifted from
reality). Treat it as code, not as a one-time write-up:

- A "Current Repo Layout" entry, doc-map row, or schema that no longer
  matches the code is a bug — fix it the moment you notice it, even if
  you're mid-way through an unrelated task.
- When a phase's checklist in PLAN.md is fully checked off, do one quick
  pass over this file before starting the next phase: does the layout
  still match `git status`/the actual tree? Does every doc-map row still
  point to a file that exists at that path?
- Prefer linking to SPEC.md / ARCHITECTURE.md / PLAN.md over inlining
  detail here — a fact that lives in one place can't drift out of sync
  with itself.

---

## Where to Find Things

This repo has several context files. Each one owns a different question —
read the one that answers what you're trying to do instead of guessing.

| File | Answers | Read it when |
|------|---------|--------------|
| `SPEC.md` | What are we building, and why does this rule/metric exist? | You need the product reasoning behind a feature or investment rule |
| `PLAN.md` | What phase are we in? What's the next task? | Start of every session |
| `DECISIONS.md` | Why was each architectural or product choice made? | Before revisiting a past decision or making a new one that overlaps |
| `ARCHITECTURE.md` | How is the system layered? What changes in which phase? What must never break? | Before touching any agent, tool, or data source |
| `PHASE2_PLAN.md` | How was the Phase 2 (India + growth agent) build sequenced? | Historical reference only — it documents how one phase was planned, not a template that repeats every phase |
| `TEST_PLAN.md` | What test framework, directory layout, and coverage do we use? | Writing or locating tests |
| `README.md` | How do I set up the venv and run the CLI/dashboard? | First-time setup, or you forgot a CLI flag |
| `.claude/PM_AGENT.md` | Product-manager persona for scope/priority critique | User says "enter PM mode" |
| `.claude/DEV_AGENT.md` | Tech-lead persona for architecture/code-quality critique | User says "enter dev mode" |
| `.claude/skills/smart-commit` | Skill that commits pending changes as granular, user-approved commits | User asks to commit, or work is ready to land |
| `FUTURE.md` | Unscoped ideas not assigned to any phase (frontend revamp, threshold annotations, public deployment) | An idea comes up that's worth keeping but not acting on yet |

---

## Current Repo Layout

This is what actually exists today — not an aspirational target. See
ARCHITECTURE.md's "Full Project Architecture" section for how this grows
phase by phase.

```
equity-research-agent/
├── agents/
│   ├── base.py              # AgentStrategy — shared LLM tool-use loop binding
│   ├── orchestrator.py      # Routes queries, runs agents in parallel, synthesizes verdict
│   ├── quality_agent.py     # Munger/Malik persona — ROE, ROCE, FCF, moat, promoter holding
│   ├── value_agent.py       # Graham/Pabrai persona — DCF, Graham number, PEG
│   ├── growth_agent.py      # Lynch/Fisher persona — revenue/EPS CAGR, PEG, forward PE
│   └── bear_case_agent.py   # Burry persona — red flags, auto-rejects
├── data/
│   ├── fmp.py                # Financial Modeling Prep API (US fundamentals)
│   ├── yfinance_client.py    # Prices + India fundamentals (.NS/.BO)
│   └── screener.py           # Screener.in scraper — promoter holding, FII/DII trend
├── tools/
│   ├── key_figures.py        # Layer 2 — raw statements → ~15-20 clean numbers
│   ├── metrics.py            # Layer 3 — compute_* functions (pure math, no verdicts)
│   ├── tool_schemas.py        # Anthropic tool definitions for the metric functions
│   ├── llm_agent.py           # Layer 4 — shared agent tool-use loop (run_agent)
│   └── formatters.py          # format_verdict_card() + India tax banner
├── web/
│   ├── __init__.py
│   ├── app.py                   # FastAPI — GET / and POST /research; mounts /static
│   ├── static/
│   │   └── style.css            # All CSS (dark minimal theme); served at /static/style.css
│   └── templates/
│       ├── base.html            # Shared shell — links style.css, nav block
│       ├── index.html           # Ticker-input form (extends base)
│       └── verdict.html         # Full verdict page (extends base; expects: verdict, key_figures, dcf, currency, is_india)
├── digest/                   # Empty — daily digest was cut from roadmap (see PLAN.md Decisions Log)
├── tests/
│   ├── conftest.py           # Shared fixtures
│   ├── fixtures/             # JSON snapshots of real API responses
│   ├── unit/                 # Pure Python, no network — Layer 2/3 tests
│   └── integration/          # Mocked APIs — Layer 1/4 tests
├── resources/raw/            # Personal reference material (not part of the build)
├── DECISIONS.md              # All architectural/product decisions with rationale
├── main.py                   # CLI entry point
├── .env / .env.example       # API keys — .env is gitignored, never commit it
└── requirements.txt
```

Not yet built (planned, see PLAN.md for phase): `web/app.py` (FastAPI),
`risk_manager.py`, `portfolio_manager.py`,
`momentum_agent.py`, `macro_agent.py`, `sentiment_agent.py`,
`data/portfolio.py`.

---

## How to Run

```bash
python main.py --ticker AAPL
python main.py --ticker ZOMATO.NS
pytest
```

Web UI (Phase 3, once built): `uvicorn web.app:app --reload` — separate entrypoint
from `main.py`, both call `agents/orchestrator.py` directly, neither wraps the other.

Full setup (uv, venv, `.env`) is in README.md — don't duplicate it here.

---

## Coding Conventions

- Python 3.11+
- Type hints on every function signature
- Docstring on every class and public function
- Keep each file under 200 lines — split into smaller modules if larger
- Never hardcode API keys — always load from `.env` via python-dotenv
- All agents must return a consistent structured dict (see Agent Output
  Schema below) — plain dicts, not dataclasses, to match what the
  Anthropic tool-use loop and JSON serialization expect
- Prefer explicit over clever — this codebase should be easy to read
  and modify
- Tools return numbers and raw data; agents return verdicts. Never let a
  tool function decide bullish/bearish/neutral (see ARCHITECTURE.md
  Key Invariant #1)

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

# Google Sheets (portfolio) — Phase 6 only, leave blank for now
GOOGLE_SHEETS_CREDS_PATH=credentials.json
PORTFOLIO_SHEET_ID=

# Email digest — Phase 6 only, leave blank for now
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
- Never commit `.env`, `portfolio.json`, or `journal.json` (already
  gitignored — don't add code that writes secrets elsewhere)
