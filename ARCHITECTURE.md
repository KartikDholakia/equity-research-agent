# ARCHITECTURE.md — System Design Reference

## Core Philosophy

- **Python does math. Claude does judgment.**
- **Tools are dumb. Agents are smart.**
- Agents never hardcode thresholds — they reason contextually using computed metrics.
- Every agent returns the same schema: `{ signal, score, summary, flags }`.
- Numeric scores (0–10) are kept for comparability across stocks and over time.

---

## Phase 1 Architecture — US Stocks, CLI, 3 Agents

### Layer Diagram

```
┌──────────────────────────────────────────────────────┐
│  LAYER 1 — DATA FETCHING (Python)                    │
│                                                      │
│  data/fmp.py             data/yfinance_client.py     │
│  fetch_income_statement  fetch_current_price         │
│  fetch_balance_sheet     fetch_price_history         │
│  fetch_cash_flow                                     │
│  fetch_key_metrics                                   │
│                                                      │
│  Returns: raw financial statements as list[dict]     │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  LAYER 2 — KEY FIGURES EXTRACTION (Python)           │
│                                                      │
│  extract_key_figures(statements) → clean dict        │
│                                                      │
│  ~15-20 numbers only:                                │
│  revenue (5yr), net_income (5yr), ocf (5yr),         │
│  fcf (5yr), total_debt, equity, current_price,       │
│  shares_outstanding, graham_number, earnings_yield   │
│                                                      │
│  Rule: no raw statement dumps into the LLM context   │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  LAYER 3 — TOOL POOL (Python functions)              │
│                                                      │
│  All agents share the same pool.                     │
│  Persona prompt governs which tools Claude calls.    │
│                                                      │
│  compute_roe_trend(income, equity)                   │
│  compute_fcf_quality(ocf, net_income)                │
│  compute_debt_analysis(debt, equity, interest, ebit) │
│  compute_dcf(fcf_per_share, current_price)           │
│  compute_graham(graham_number, current_price)        │
│  compute_pe_history(earnings_yields)                 │
│  compute_peg(pe, eps_growth)                         │
│  compute_revenue_cagr(revenues)                      │
│                                                      │
│  Rule: tools return numbers + raw data. No verdicts. │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  LAYER 4 — AGENT LAYER (Claude + Tool Use)           │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │ quality_agent                                │    │
│  │ Persona: Charlie Munger / Vijay Malik        │    │
│  │ Focus: moat, ROE consistency, FCF quality,   │    │
│  │        management, capital allocation        │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │ value_agent                                  │    │
│  │ Persona: Ben Graham / Mohnish Pabrai         │    │
│  │ Focus: DCF, margin of safety, Graham number, │    │
│  │        P/E vs history, never overpay         │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │ bear_case_agent                              │    │
│  │ Persona: Michael Burry                       │    │
│  │ Focus: red flags, accounting anomalies,      │    │
│  │        debt traps, FCF vs profit divergence  │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  Agent loop (each agent):                            │
│  1. Receives key figures + company context           │
│  2. Decides which tools to call (Claude chooses)     │
│  3. Calls tools, receives computed results           │
│  4. Reasons over results through persona lens        │
│  5. Returns: { signal, score, summary, flags }       │
│                                                      │
│  All three run in parallel.                          │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│  LAYER 5 — ORCHESTRATOR (Python)                     │
│                                                      │
│  - Fetches data (Layer 1)                            │
│  - Extracts key figures (Layer 2)                    │
│  - Runs 3 agents in parallel (Layer 4)               │
│  - Synthesizes: weighted conviction score            │
│  - Formats and prints verdict card (CLI)             │
└──────────────────────────────────────────────────────┘
```

### Agent Output Schema (all phases)
```python
{
    "agent":   str,       # "quality_agent" | "value_agent" | "bear_case_agent"
    "ticker":  str,       # "AAPL"
    "signal":  str,       # "bullish" | "neutral" | "bearish"
    "score":   float,     # 0.0–10.0
    "summary": str,       # 2–3 sentence plain English reasoning
    "flags":   list[str], # red flags found; empty list if none
    "timestamp": str      # ISO format
}
```

### Prompt Caching
System prompts (persona definition + tool definitions) are identical across
all analyses of the same agent. Cache them via Anthropic's prompt caching to
reduce token cost by ~80% on repeated runs.

---

## Full Project Architecture — All Phases

### What changes per phase

#### Phase 2 — Indian Market + Growth Agent
- **Layer 1**: Add `data/screener.py` (promoter holding, FII/DII from Screener.in)
- **Layer 2**: Add India key figures extractor (includes promoter %, pledging %, FII trend)
- **Layer 3**: Add `compute_promoter_analysis()`, `compute_eps_cagr()`, `compute_tam_growth()`
- **Layer 4**: Add `growth_agent` — Peter Lynch / Phil Fisher persona
  - Focus: revenue CAGR, EPS CAGR, TAM, forward estimates
- **Layer 5**: Orchestrator now runs 4 agents

#### Phase 3 — Research/Chat Web UI + Content Upgrade
- **New**: Presentation layer — plain HTML/CSS template, served by FastAPI +
  Jinja2, wraps the same orchestrator. No Streamlit, no JS framework — see
  PLAN.md's 2026-06-16 Decisions Log entries for the rationale (charts
  deprioritized, so Streamlit's main edge doesn't apply; plain HTML gives
  the layout/CSS control the scan-cost complaint actually needs).
  `main.py` (CLI) and `web/app.py` (FastAPI) are independent entrypoints —
  both call `agents/orchestrator.py` directly, neither wraps the other.
- **No new Layer 1-4 work**: the verdict dict already has everything needed;
  this phase only adds a renderer. Content upgrade (raw key figures table +
  DCF bear/base/bull breakdown) is surfaced from data already computed in
  Layer 2/3 — no new data sources.
- Resequenced ahead of the original Phase 3 (Screener) — see PLAN.md.

#### Phase 4 — Screener
- **Layer 1**: Add `data/universe.py` — universe cache (Trendlyne / NSE bulk), weekly refresh
- **Layer 5**: Orchestrator gets a second mode — **screener mode**:

```
SCREENER MODE (two-speed system):

500 stocks
  ↓ Python pre-filter using tool pool (no LLM)
  → shortlist 20-30 candidates
  ↓ LLM agents on shortlist only
  → surface top 5 with one-line thesis + score

Rationale: running full LLM on 500 stocks = ~₹500/run.
Pre-filter in Python keeps screener cost under ₹20/run.
```

#### Phase 5 — Momentum Agent
- **Layer 4**: Add `momentum_agent` — Stan Druckenmiller persona
  - Focus: RSI, MACD, 200-DMA, volume trends — entry timing
- **Layer 5**: Orchestrator now runs 5 agents
- Renders on the web UI built in Phase 3 — no presentation-layer change here.

#### Phase 6 — Portfolio + Allocation (LangGraph enters)
- **Layer 1**: Add `data/portfolio.py` — reads `portfolio.json`
- **Layer 4**: Add `risk_manager` and `portfolio_manager` agents
  - Agents now receive a second input: **portfolio context**
    ```python
    portfolio_context = {
        "holdings": [...],
        "sector_exposure": { "Tech": 0.40, "Finance": 0.20 },
        "cash_available": 50000,
        "overweight_positions": ["AAPL"]
    }
    ```
- **Layer 5**: Orchestrator migrates to **LangGraph** for multi-step workflows:
  - *Portfolio review*: fetch prices → bear_case on each holding → flag issues
  - *Allocation query*: screener → analyze candidates → portfolio fit → risk sizing → ranked output
  - Plain `concurrent.futures` is insufficient for stateful multi-step orchestration

#### Phase 7 — Macro + Sentiment (scope TBD after Phase 6)
- **Layer 1**: Add news RSS feeds, RBI/NSE macro data sources
- **Layer 4**: Add `macro_agent`, `sentiment_agent` (if manual NotebookLM workflow is too slow)

---

## Full Architecture Diagram (all phases)

```
┌──────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                      │
│  CLI (Phase 1–2, ongoing)     Web — FastAPI+Jinja2 (Phase 3+) │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  ORCHESTRATOR                                            │
│                                                          │
│  Phase 1–2:  parallel agents → synthesize                │
│  Phase 4:    + screener mode (two-speed)                 │
│  Phase 6+:   LangGraph — stateful multi-step workflows   │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  AGENT LAYER — Claude + Tool Use                         │
│                                                          │
│  Phase 1:  quality · value · bear                        │
│  Phase 2:  + growth (Lynch / Fisher)                     │
│  Phase 5:  + momentum (Druckenmiller)                    │
│  Phase 6:  + risk_manager · portfolio_manager            │
│  Phase 7:  + macro · sentiment (if needed)               │
│                                                          │
│  Phase 6+: agents also receive portfolio_context         │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  TOOL POOL — Python functions                            │
│  Grows every phase. No structural change.                │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  KEY FIGURES EXTRACTION                                  │
│  Phase 1:  US extractor                                  │
│  Phase 2:  + India extractor (promoter, FII/DII)         │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  DATA LAYER — Python                                     │
│                                                          │
│  Phase 1:  FMP · yfinance                                │
│  Phase 2:  + Screener.in scraper                         │
│  Phase 4:  + Universe cache (Trendlyne / NSE bulk)       │
│  Phase 6:  + portfolio.json reader                       │
│  Phase 7:  + News RSS · RBI/NSE macro feeds              │
└──────────────────────────────────────────────────────────┘
```

---

## Key Invariants (never break these)

1. **Python does math. Claude does judgment.** Tools return numbers. Agents return verdicts.
2. **Never dump raw statements into the LLM.** Always go through the key figures extractor.
3. **Structured output is non-negotiable.** Every agent returns parseable JSON. No free-text verdicts.
4. **Scores are kept.** 0–10 per agent enables comparability across stocks and over time.
5. **All tool pools are shared.** Persona prompts govern tool selection, not hard restrictions.
6. **LangGraph only from Phase 6.** Don't introduce it earlier — plain SDK is simpler and sufficient.
