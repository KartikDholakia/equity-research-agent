# Phase 2 Plan — Indian Market + Growth Agent

## Context
Phase 1 shipped a working US-only verdict engine: quality + value + bear-case agents backed by Claude tool use, FMP data, and yfinance prices. Phase 2 extends the same architecture to Indian stocks (NSE/BSE via `.NS`/`.BO` tickers) and adds a fourth agent focused on growth trajectory.

**Exit criterion**: `python main.py --ticker ZOMATO.NS` produces a verdict card that feels accurate. Same for INFY.NS and HDFCBANK.NS.

**User decisions captured**:
- Screener.in failure → degrade gracefully: add a prominent "PROMOTER DATA UNAVAILABLE" flag and continue the analysis
- Growth agent data → historical CAGR always + yfinance forward estimates when available, omit with note when missing

---

## Architecture Changes (what changes per layer)

| Layer | Phase 1 | Phase 2 additions |
|-------|---------|-------------------|
| **1 — Data** | FMP (US), yfinance (prices) | + `data/screener.py` (promoter/FII), + `fetch_fundamentals_india()` in yfinance_client |
| **2 — Key Figures** | `extract_key_figures()` (FMP format) | + `extract_india_key_figures()` (yfinance DataFrame format) |
| **3 — Tool Pool** | 14 tools | + `compute_eps_cagr`, `compute_promoter_analysis`, `compute_fii_trend` |
| **4 — Agents** | quality, value, bear | + `growth_agent`; quality_agent prompt extended for India checks |
| **5 — Orchestrator** | 3 agents, FMP-only fetch | 4 agents, market-aware fetch, updated weights |
| **Formatters** | USD everywhere | Currency derived from ticker suffix; India tax banner |

---

## Implementation Tasks (in order)

### Step 1 — Currency fix · `agents/value_agent.py` ✅
- System prompt updated: Claude now uses ₹ for `.NS`/`.BO` tickers, $ for US

### Step 2 — India fundamentals fetch · `data/yfinance_client.py` ✅
Add `fetch_fundamentals_yfinance(ticker: str) -> dict[str, Any]`:
```
Returns:
  income_stmt:   pd.DataFrame  (yfinance ticker.financials — rows=metrics, cols=fiscal years, newest first)
  balance_sheet: pd.DataFrame  (ticker.balance_sheet)
  cashflow:      pd.DataFrame  (ticker.cashflow)
  info:          dict          (ticker.info — forwardPE, forwardEps, pegRatio, etc.)
```
- Raise ValueError with clear message if all DataFrames are empty
- `info` should never raise — return empty dict on failure

### Step 3 — Screener.in scraper · `data/screener.py` (new file) ✅
Two public functions:

**`fetch_promoter_holding(ticker: str) -> dict[str, Any]`**
- URL: `https://www.screener.in/company/{SLUG}/consolidated/`
- Slug: strip `.NS`/`.BO` suffix, uppercase (ZOMATO.NS → ZOMATO)
- Parse shareholding HTML table (BeautifulSoup) — extract latest promoter % and pledged %
- On scrape failure (any exception): return `{"promoter_pct": None, "pledging_pct": None, "error": str(e)}`
- Rate limit: 2-second delay before each request (`time.sleep(2)`)

**`fetch_fii_dii_trends(ticker: str) -> dict[str, Any]`**
- Same URL as above, parse "Foreign Institutions" and "Domestic Institutions" rows
- Extract last 3 quarters of FII % holding to determine trend direction
- Trend: "rising" if latest > 3 quarters ago, "falling" if lower, "stable" otherwise
- On failure: return `{"fii_pct": None, "dii_pct": None, "fii_trend": None, "error": str(e)}`

### Step 4 — India key figures extractor · `tools/key_figures.py`
Add `extract_india_key_figures(ticker, income_stmt, balance_sheet, cashflow, promoter_data, price_data) -> dict`:
- Read DataFrames using `.loc[metric_name]` with fallbacks for alternative row names
- yfinance row name mapping:
  - Revenue: `"Total Revenue"` · Net income: `"Net Income"` · Operating income: `"Operating Income"`
  - OCF: `"Operating Cash Flow"` · FCF: `"Free Cash Flow"`
  - Total debt: `"Total Debt"` or `"Long Term Debt"`
  - Equity: `"Common Stock Equity"` or `"Stockholders Equity"`
- Columns = fiscal years → convert to `list[float]`, newest first
- Derive `fcf_yield` as 3-year average `FCF / market_cap`
- Add India-specific fields: `promoter_pct`, `pledging_pct`, `fii_trend`, `forward_pe`, `forward_eps`, `promoter_data_available`

### Step 5 — New metric functions · `tools/metrics.py`
Three new functions:

**`compute_eps_cagr(eps_history: list[float]) -> dict[str, Any]`**
- Same CAGR formula as `compute_revenue_cagr` but for EPS
- Add consistency check: count positive growth years vs negative; flag lumpy growth

**`compute_promoter_analysis(promoter_pct: float | None, pledging_pct: float | None) -> dict[str, Any]`**
- If either is None: return `{"available": False, "flag": "PROMOTER DATA UNAVAILABLE — verify pledging % manually before investing"}`
- Auto-reject flag: if `pledging_pct >= 30`: `"AUTO-REJECT: Promoter pledging {pct}% exceeds 30% threshold"`

**`compute_fii_trend(fii_trend: str | None, fii_pct: float | None) -> dict[str, Any]`**
- Return: `{"trend": str, "signal": "bullish"|"neutral"|"bearish", "note": str}`

### Step 6 — New tool schemas · `tools/tool_schemas.py`
Add Anthropic tool definition dicts for `compute_eps_cagr`, `compute_promoter_analysis`, `compute_fii_trend`.

### Step 7 — Growth agent · `agents/growth_agent.py` (new file)
- Persona: **Peter Lynch / Phil Fisher**
- Tools: `compute_revenue_cagr`, `compute_eps_cagr`, `compute_peg`, `compute_pe_history`
- System prompt instructs Claude to: compute revenue + EPS CAGR, check growth consistency, evaluate PEG, assess forward PE vs trailing PE when available
- Structure: identical to existing agent files (~50 lines), uses `tools/llm_agent.py` shared loop

### Step 8 — Quality agent India extension · `agents/quality_agent.py`
- Add `compute_promoter_analysis` and `compute_fii_trend` to the tool pool
- Extend system prompt: "For Indian stocks, always check promoter holding and pledging data"

### Step 9 — Orchestrator updates · `agents/orchestrator.py`
- `_fetch_data()`: market-aware branching — India path calls yfinance + Screener.in, US path unchanged
- `_run_agents()`: add growth_agent to parallel pool (4 agents total)
- Conviction weights: Quality 35% · Value 25% · Growth 20% · Bear 20%
- Add `india_tax_note` to verdict dict for Indian tickers

### Step 10 — India tax banner · `tools/formatters.py`
- Render `💡 INDIA TAX NOTE` section at bottom of verdict card when `india_tax_note` is present

### Step 11 — Tests
- `tests/unit/test_india_key_figures.py` — `extract_india_key_figures()` with mock DataFrames
- `tests/unit/test_growth_metrics.py` — `compute_eps_cagr`, `compute_promoter_analysis`, `compute_fii_trend`
- All 154 existing tests must continue to pass

### Step 12 — End-to-end verification
- `python main.py --ticker AAPL` — regression check, output must be unchanged
- `python main.py --ticker ZOMATO.NS` — ₹ symbols, 4 agent signals, India tax note
- `python main.py --ticker INFY.NS`
- `python main.py --ticker HDFCBANK.NS`

---

## Key Invariants (do not break)

- Python does math. Claude does judgment. Tools return numbers, agents return verdicts.
- Never dump raw DataFrames/dicts into LLM context — always go through `extract_india_key_figures()` first.
- Screener failure → graceful degradation flag, not a crash.
- All agents return the same schema: `{agent, ticker, signal, score, summary, details, flags, timestamp}`.
- Prompt caching on system prompt block must be preserved in growth_agent.

---

## Files Modified / Created

| File | Change type | Status |
|------|-------------|--------|
| `agents/value_agent.py` | Modify — currency symbol fix | ✅ Done |
| `data/yfinance_client.py` | Modify — add `fetch_fundamentals_yfinance()` | ✅ (tested) |
| `data/screener.py` | New — Screener.in scraper | ✅ (tested) |
| `tools/key_figures.py` | Modify — add `extract_india_key_figures()` | ✅ (tested) |
| `tools/metrics.py` | Modify — add 3 new metric functions | ✅ (tested) |
| `tools/tool_schemas.py` | Modify — add 3 new tool schemas | ✅ |
| `agents/growth_agent.py` | New — Peter Lynch / Phil Fisher growth agent | ✅ |
| `agents/quality_agent.py` | Modify — extend for India checks | ✅ |
| `agents/orchestrator.py` | Modify — market-aware fetch, 4 agents, new weights | ✅ |
| `tools/formatters.py` | Modify — India tax banner | ✅ |
