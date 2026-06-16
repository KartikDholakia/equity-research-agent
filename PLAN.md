# PLAN.md — Build Tracker

## Current Phase
**Phase 1 — First Agent: US Stocks via FMP (CLI)**

## Next Task To Work On
Phase 1 → Step 1: Project scaffolding

---

## Phase 0: Foundation ✅
- [x] Create CLAUDE.md
- [x] Create SPEC.md
- [x] Create PLAN.md

---

## Phase 1: Verdict Engine — US Stocks (CLI)
Goal: Run `python main.py --ticker AAPL` and get a trustworthy verdict card.
Exit criterion: verdict card on AAPL/NVDA/MSFT feels like something you'd
actually act on.

- [x] Create project folder structure (agents/, data/, tools/, tests/)
- [x] Create requirements.txt with initial dependencies
- [x] Create .env.example with all required keys
- [x] Create main.py with CLI argument parsing (--ticker, --market)
- [x] Build data/fmp.py
      - fetch_income_statement(ticker)
      - fetch_balance_sheet(ticker)
      - fetch_cash_flow(ticker)
      - fetch_key_metrics(ticker)
      - fetch_earnings_history(ticker)
- [x] Build data/yfinance_client.py
      - fetch_current_price(ticker)
      - fetch_price_history(ticker, period)
      - fetch_technical_indicators(ticker)
- [x] Build agents/quality_agent.py
      - Inputs: income statement, balance sheet, cash flow
      - Checks: ROE, ROCE, FCF consistency, debt levels, interest coverage
      - Output: agent signal dict (see CLAUDE.md schema)
- [x] Build agents/value_agent.py
      - Inputs: key metrics, price, earnings history
      - Checks: DCF (3 scenarios), Graham formula, PEG, P/E vs 5yr avg
      - Output: agent signal dict
- [x] Build agents/bear_case_agent.py
      - Inputs: all financial statements
      - Checks: all auto-reject red flags from SPEC.md
      - Output: agent signal dict with flags list populated if issues found
- [x] Build tools/formatters.py
      - format_verdict_card(verdict_dict) → pretty printed string
- [x] Build agents/orchestrator.py (Phase 1 — 3 agents only)
      - Runs quality + value + bear case agents in parallel
      - Synthesizes into verdict dict
      - Calls formatter and prints to CLI
      - Design for 4 query types from the start: analyze / screen /
        review / allocate — only "analyze" ships in Phase 1, but routing
        logic must accommodate the rest without a rewrite
- [x] Test on AAPL, NVDA, MSFT — verify output looks correct
- [x] Fix bugs found in architecture review (do before LLM refactor)
      - Add fetch_earnings_history(ticker, years=5) to data/fmp.py.
        Use the FMP stable endpoint "earnings" with params symbol=ticker, limit=years.
        Return list[dict] like the other fetch_* functions in that file.
        This function was listed as a Phase 1 deliverable but was never added.
        It is needed by the growth_agent in Phase 2 for EPS CAGR calculation.
        Signature: fetch_earnings_history(ticker: str, years: int = 5) -> list[dict[str, Any]]
      - Fix run_analysis in agents/orchestrator.py (lines 19-26).
        The except block currently calls print(...) and then raise, so the user
        sees a clean error message immediately followed by a raw Python traceback.
        Remove the re-raise. Print the error message and call sys.exit(1) instead,
        so the CLI exits with a non-zero code without dumping a traceback.
        Import sys at the top of the file if not already present.
- [x] Refactor agents to LLM-backed (Claude tool use)
      - Replace rule-based scoring in quality_agent, value_agent, bear_case_agent
      - Add key figures extractor (Layer 2) — ~15-20 clean numbers from raw statements
      - Move metric functions to tool pool — tools return numbers, Claude reasons
      - Add persona system prompts (tight) — Munger, Graham, Burry
      - Wire tool use loop in each agent via Anthropic SDK
      - Redesign _bull_reasons in agents/orchestrator.py (lines 139-159).
        The current implementation digs into agent details dicts using hardcoded keys
        like quality.get("details", {}).get("roe", {}).get("avg_pct"). Those keys
        belong to the rule-based agents and will not exist after the LLM refactor.
        Replace the function so it builds the bull reasons list by extracting
        meaningful sentences from each agent's summary string field instead.
        The summary field is guaranteed by the agent output schema and will survive
        the refactor unchanged.
      - Add prompt caching to each LLM agent (quality, value, bear case) via the
        Anthropic SDK cache_control parameter. The system prompt (persona definition
        + tool definitions) is identical on every call for a given agent, making it
        the ideal cache breakpoint. Mark the system prompt content block with
        cache_control={"type": "ephemeral"}. This cuts token cost by ~80% on
        repeated runs of the same agent. See Anthropic prompt caching docs for
        the exact API shape.
      - See ARCHITECTURE.md for full design
- [x] Fix DCF input: replaced single-year freeCashFlowYield with 3-year average
      in tools/key_figures.py. Prevents heavily-investing companies (AMZN, NVDA)
      from producing absurdly low fair values due to one bad FCF year.
- [x] Write tests — 154 tests across 4 files, all passing. See TEST_PLAN.md for coverage detail.

---

## Phase 2: Indian Market + Growth Agent
Goal: Same CLI works for Indian stocks. `python main.py --ticker ZOMATO.NS`
Exit criterion: verdict card on ZOMATO.NS / HDFCBANK.NS feels accurate.

- [x] Fix currency symbol hardcode in agents/value_agent.py.
      System prompt updated: Claude uses ₹ for .NS/.BO tickers, $ for US.
- [x] Extend data/yfinance_client.py for NSE/BSE tickers (.NS / .BO suffix)
      - fetch_fundamentals_yfinance(ticker) — income stmt, balance sheet, CF, info
      - Raises ValueError if all DataFrames empty; info returns {} on failure
      - Tested: 7 unit tests, all passing
- [x] Build data/screener.py (Screener.in scraper — India-specific data only)
      - fetch_promoter_holding(ticker) — promoter % and pledging %
      - fetch_fii_dii_trends(ticker) — FII/DII %, trend direction (rising/falling/stable)
      - 2-second rate-limit delay per request; graceful degradation on all failures
      - Tested: 18 unit tests (slug, trend, holding, FII), all passing
- [x] Add India key figures extractor to tools/key_figures.py
      - extract_india_key_figures() — yfinance DataFrame format with India-specific fields
- [x] Add 3 new metric functions to tools/metrics.py
      - compute_eps_cagr, compute_promoter_analysis, compute_fii_trend
- [x] Add 3 new tool schemas to tools/tool_schemas.py
- [x] Build agents/growth_agent.py (Peter Lynch / Phil Fisher persona)
      - Revenue CAGR, EPS CAGR, PEG, forward PE
      - Output: agent signal dict
- [x] Add India-specific checks to quality_agent.py
      - compute_promoter_analysis and compute_fii_trend in tool pool
      - Extended system prompt for India checks
- [x] Wire growth_agent into orchestrator (now 4 agents); market-aware fetch;
      updated conviction weights; India tax note in verdict dict
- [x] Add India tax banner to tools/formatters.py
- [x] Write tests — 32 new tests across 2 files (test_india_key_figures, test_growth_metrics), all 211 passing
- [x] Test on ZOMATO.NS, INFY.NS, HDFCBANK.NS; regression check on AAPL

---

## Phase 3: Screener — Monthly Candidate Finder (CLI)
Goal: `python main.py --screen india` returns 5 ranked candidates to analyze.
Exit criterion: screener surfaces stocks you'd actually want to look at.
Architecture note: pre-filter universe weekly and cache results — do NOT
run full 500-stock scan on every invocation (API cost + rate limits).

- [ ] Build data/universe.py
      - get_nifty500_tickers() — cached weekly via Trendlyne GuruQ downloader
      - get_sp500_tickers() — cached weekly via yfinance/FMP
      - Pre-filter on basic quality gates before deeper analysis
- [ ] Build agents/screener_agent.py
      - Apply quality filters from SPEC.md on pre-filtered universe
      - Apply valuation filters
      - Return top 5 ranked candidates with one-line thesis each
- [ ] Build caching layer for universe data (local JSON, weekly refresh)
- [ ] Add --screen flag to main.py CLI
- [ ] Test: output 5 reasonable candidates, not junk

---

## Phase 4: Research / Chat UI (Streamlit — single screen)
Goal: Browser UI where you type a ticker and get a verdict card rendered.
No portfolio, no watchlist, no home screen — just the core research job.
Exit criterion: you use this instead of the CLI for stock analysis.

- [ ] Set up dashboard/app.py with single Research/Chat screen
      - Text input → calls orchestrator → renders formatted verdict card
      - No sidebar navigation yet
- [ ] Build agents/momentum_agent.py
      - RSI, MACD, 200-DMA, volume trends
      - Useful for entry timing on stocks already being watched
- [ ] Wire momentum_agent into orchestrator (now 5 agents)
- [ ] Test end-to-end: type "AAPL" → verdict card renders correctly

---

## Phase 5: Portfolio + Watchlist + Review + Allocation
Goal: App knows your holdings, can review the portfolio periodically,
and answer "where should I invest ₹X?"
Portfolio source: local portfolio.json (exported from Groww / INDMoney).

- [ ] Build data/portfolio.py
      - read_holdings() — reads from portfolio.json
      - read_watchlist() — reads from portfolio.json
      - import_from_csv(path) — import Groww/INDMoney CSV export
- [ ] Build agents/risk_manager.py
      - Position sizing, concentration check, drawdown estimate
- [ ] Build agents/portfolio_manager.py
      - Does this stock fit current holdings? Sector/geo overlap?
      - Tax flag: approximate LTCG/STCG impact before suggesting sell
- [ ] Wire risk_manager + portfolio_manager into orchestrator
- [ ] Build portfolio review workflow (orchestrator "review" query type)
      - Fetch current prices for all holdings via yfinance
      - Run bear_case_agent on each holding to check auto-reject flags
      - Output: brief pulse (total value, P&L) + flagged positions only
      - Flag triggers: auto-reject hit, position >10%, thesis age >6 months
      - Runs on schedule (APScheduler) or via CLI --review flag
- [ ] Build allocation query workflow (orchestrator "allocate" query type)
      - Input: cash amount available (e.g. --allocate 50000)
      - Run screener → analyze top 5-10 candidates → portfolio fit check
      - risk_manager sizes each position
      - Output: ranked candidates with suggested ₹ allocation + rationale
- [ ] Add Portfolio screen to Streamlit dashboard
      - Holdings table with EOD prices (via yfinance)
      - P&L per position
      - Allocation breakdown: sector, geography, market cap
      - Warning if any position is overweight (>10%)
- [ ] Add Watchlist screen to Streamlit dashboard
      - Current price vs target entry (progress bar)
      - Alert when stock enters buy zone

---

## Phase 6: Full Dashboard + Remaining Features (revisit scope here)
Goal: Assess what Phase 5 revealed is actually needed. Build accordingly.
Do not plan the detail of this phase until Phase 5 is complete.

Candidates to build (confirm at Phase 5 retrospective):
- [ ] Dashboard / Home screen — portfolio pulse + alerts
- [ ] agents/macro_agent.py — RBI/Fed cycle, FII flows, sector rotation
- [ ] agents/sentiment_agent.py — news tone, con-call signals (if NotebookLM
      manual workflow is proving too slow)
- [ ] Investment Journal — thesis logging + quarterly review
- [ ] Google Sheets migration — only if portfolio.json update friction is real
- [ ] Daily digest email — only if analysis cadence has increased from monthly
- [ ] Screener architecture review before adding daily/on-demand runs

---

## Decisions Log

| Date       | Decision                                                                         |
|------------|----------------------------------------------------------------------------------|
| 2026-04-10 | Python chosen over Kotlin — LangGraph ecosystem is Python-native                 |
| 2026-04-10 | FMP for US deep fundamentals, Screener.in for Indian data                        |
| 2026-04-10 | NotebookLM used manually for con-call/annual report deep dives                   |
| 2026-04-10 | Three-file structure: CLAUDE.md + SPEC.md + PLAN.md                              |
| 2026-04-10 | Build starts with US stocks (Phase 1) before Indian market                       |
| 2026-05-16 | Phase 1 scoped to 3 agents only (quality/value/bear) — 80% value, less risk      |
| 2026-05-16 | Google Sheets dropped from near-term — portfolio lives in Groww + INDMoney       |
| 2026-05-16 | Portfolio store: local portfolio.json updated monthly via CSV export              |
| 2026-05-16 | Screener moved to Phase 3 (before UI) — monthly cadence means finding candidates |
| 2026-05-16 | Streamlit UI moved to Phase 4 — CLI sufficient for monthly analysis cadence      |
| 2026-05-16 | Daily digest cut from roadmap — noise at monthly analysis frequency               |
| 2026-05-16 | Phase 6 scope intentionally left open — decide after Phase 5 retrospective       |
| 2026-05-17 | No real-time price API — EOD prices via yfinance are sufficient for long-term analysis |
| 2026-05-17 | Indian basic fundamentals via yfinance (.NS) — covers income stmt, balance sheet, CF |
| 2026-05-17 | Indian promoter/pledge data via Screener.in scraping — only source under budget   |
| 2026-05-17 | Trendlyne GuruQ added (₹2,190/yr) for Phase 3 bulk screener data — not Phase 1-2  |
| 2026-05-17 | FMP API (~$15/mo) retained for US deep fundamentals — best coverage at the price   |
| 2026-05-17 | EODHD rejected — fundamentals plan ~₹5,000/mo, Indian promoter data coverage unclear |
| 2026-05-17 | Orchestrator must route 4 query types: analyze / screen / review / allocate        |
| 2026-05-17 | Portfolio review: mixed output — brief pulse + flag issues only, runs on schedule   |
| 2026-05-17 | Allocation query output: ranked candidates + suggested ₹ sizing per position        |
| 2026-05-18 | quality_agent scores 6 checks (ROE, ROCE, FCF, OCF quality, D/E, interest coverage) weighted to 10 |
| 2026-05-18 | value_agent: DCF growth rates kept as module constants — Phase 3 will derive from historical FCF CAGR |
| 2026-05-18 | Graham formula intentionally kept for value signals; irrelevant for asset-light/buyback-heavy stocks |
| 2026-05-18 | bear_case_agent automates 3 of 7 auto-reject flags (CFQ, receivables, debt growth); remaining 4 need manual/news data not available in Phase 1 |
| 2026-05-24 | Architecture: 5-layer hybrid — Python for data/math, Claude (tool use) for reasoning. Persona-based agents with tight prompts. See ARCHITECTURE.md. |
| 2026-05-24 | LangGraph deferred to Phase 5 — plain Anthropic SDK sufficient for Phase 1-4 parallel agent execution |
| 2026-05-24 | Screener mode (Phase 3) uses two-speed system: Python pre-filter on 500 stocks, LLM only on shortlist of 20-30 — keeps cost under ₹20/run |
| 2026-05-24 | Phase 1 refactor: current rule-based agents to be replaced with LLM agents (Python computes metrics, Claude reasons via persona prompts) |
| 2026-05-28 | LLM refactor complete: tools/key_figures.py (Layer 2), tools/metrics.py + tool_schemas.py + llm_agent.py (Layer 3/loop), agents refactored to Claude tool use with Munger/Graham/Burry personas, prompt caching on system prompt block |
| 2026-06-08 | Phase 2 Steps 4–11 complete: India key figures extractor, 3 new metrics (eps_cagr, promoter_analysis, fii_trend), 3 new tool schemas, growth_agent (Lynch/Fisher persona), quality_agent India extension, orchestrator market-aware routing (4 agents, new weights), India tax banner. 211 tests passing. |