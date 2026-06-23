# PLAN.md — Build Tracker

## Current Phase
**Phase 3 — Research/Chat Web UI + Content Upgrade**

## Next Task To Work On
Phase 3 → Step 1: Pick a free, simple HTML/CSS template for the verdict card

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

## Phase 3: Research Web UI + Content Upgrade
Goal: Replace the terminal verdict card with a browser page — same
orchestrator, richer content. Resequenced ahead of the screener (originally
Phase 4) per the 2026-06-16 PM/Tech Lead discussion (see Decisions Log):
terminal output was flagged as both a content/trust problem (prose feels
generic, can't verify the numbers behind a verdict) and a scan-cost problem
(ASCII wall of text is tedious to read) — fixing the report you already use
for every analysis matters more right now than finding new candidates to
analyze with it.
Exit criterion: you'd rather open this in a browser than read the CLI card.

- [ ] Pick a free, simple HTML/CSS template (card-based layout) suited to a
      financial verdict card — no specific template in hand, source one
- [ ] Build web/app.py (FastAPI) — GET / renders an empty ticker-input form,
      POST /research calls agents/orchestrator.py and renders the result.
      main.py (CLI) stays untouched as a separate, independent entrypoint —
      both call agents/orchestrator.py directly, neither wraps the other.
- [ ] Build web/templates/verdict.html (Jinja2) — maps the verdict dict
      (CLAUDE.md Final Verdict Schema) onto the chosen template's markup.
      Color-code BUY/WATCH/AVOID, clear typographic hierarchy for fair
      value vs. current price and conviction score.
- [ ] Content upgrade (folded into this phase, not deferred): surface the
      ~15-20 raw key figures (tools/key_figures.py) and the 3-scenario DCF
      breakdown (already computed in value_agent.py) on the page — not just
      agent prose. Goal: let the user verify the numbers behind the verdict
      instead of just trusting a sentence.
- [ ] No charts/data visualization in this phase — explicitly deprioritized
      in the 2026-06-16 discussion. If revisited later: a price chart with
      200-DMA overlay can use data already pulled by fetch_price_history()/
      fetch_technical_indicators() (no new API or cost), and/or a DCF
      bear/base/bull bar chart from value_agent's existing scenarios. Do not
      add a new data source for charts without a separate scoping pass.
- [ ] Test: run a real analysis (one US ticker, one India ticker) end-to-end
      through the web form and confirm the rendered page matches the
      verdict dict's actual values.
- [ ] Streaming via SSE — stream each agent's output to the browser as it
      completes instead of waiting for all four agents. Use FastAPI's
      StreamingResponse with Server-Sent Events. Verdict page shows agent
      cards appearing one by one in real time. Teaching goal: streaming LLM
      responses + SSE in FastAPI.

---

## Phase 4: Chat Session — Cross-Question the Analysis
Goal: After the verdict card renders, the user can ask follow-up questions
about the analysis. The system answers from the already-computed data —
agent outputs, key figures, DCF scenarios — not from memory.
Exit criterion: ask 3 follow-up questions on a real analysis and get
grounded, non-hallucinated answers that reference actual numbers from the report.
Teaching goal: multi-turn conversation state, context grounding, prompt caching.

- [ ] Build session state: in-memory dict keyed by session ID, stores
      messages list + full verdict dict per session. Session ID generated
      on POST /research and embedded in the verdict page.
- [ ] Build POST /chat endpoint in web/app.py — receives session_id +
      user message, looks up session state, calls Claude, appends to
      messages list, returns Claude's reply.
      System context = full verdict dict + all agent outputs (prompt-cached —
      same block for all turns in a session, ideal cache breakpoint).
      Messages = rolling conversation history.
      Analysis-only scope: if user asks something outside the report, Claude
      says so rather than fetching new data. Fresh data fetch on demand is a
      future enhancement.
- [ ] Build chat UI on verdict.html — text input + message history panel
      below the verdict card. Use fetch() to POST to /chat and append
      replies without a page reload. No external chat library needed.
- [ ] Decide model for chat turns at phase start (lighter/faster vs. same
      as agents — defer until then).
- [ ] Test: run an analysis, ask 3-4 follow-up questions, verify answers
      cite actual numbers from the report (conviction score, fair value,
      specific flags) rather than generic LLM responses.

---

## Phase 5: Screener — Monthly Candidate Finder (CLI + Web)
Goal: `python main.py --screen india` returns 5 ranked candidates to analyze,
and the same results render as a web page so you can click straight through
to a verdict card.
Exit criterion: screener surfaces stocks you'd actually want to look at, and
the web table makes it easy to act on them.
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
- [ ] Add POST /screen route to web/app.py and web/templates/screener.html
      — ranked table of 5 candidates (ticker, score, verdict, one-line thesis);
      each row links to the verdict card form pre-filled with that ticker.
      No new infrastructure needed — reuses Phase 3's FastAPI app and Jinja2.
- [ ] Test: output 5 reasonable candidates, not junk; confirm web table renders
      and links through to verdict card correctly

---

## Phase 6: Concall Agent — Earnings Call RAG
Goal: Add a concall_agent that reads and reasons over the last 4 quarters of
earnings call transcripts. Surfaces management tone, guidance quality, and
promises vs. delivery — signals the financial numbers alone can't provide.
Exit criterion: concall_agent produces a meaningful signal on INFY.NS and AAPL;
orchestrator incorporates it gracefully when transcripts are available.
Teaching goal: RAG, chunking strategy, ChromaDB, retrieval quality vs. hallucination.

- [ ] Research and confirm transcript sources:
      India — NSE concall transcripts, MoneyControl earnings page
      US — Motley Fool earnings transcripts, SEC 8-K filings
      Pick the most reliably parseable source for each market.
- [ ] Build data/transcripts.py
      - fetch_concall_transcripts(ticker, num_quarters=4) → list of raw transcript texts
      - Lazy-load: check local ChromaDB first; fetch + embed only if missing
        or stale (older than the most recent quarter boundary)
- [ ] Set up ChromaDB (persisted to disk)
      - Chunk transcripts (paragraph-level, ~300-500 tokens per chunk)
      - Embed chunks and store with ticker + quarter metadata
      - Cache invalidation: re-embed when a new quarter's transcript is available
- [ ] Build agents/concall_agent.py (buy-side analyst persona)
      - Reads between the lines of management commentary
      - Tracks promises vs. delivery across quarters
      - Flags tone changes, hedging language, guidance misses
      - Tool: query_transcript(question) → retrieves top-k relevant chunks via ChromaDB
      - Output: standard agent signal dict
- [ ] Add tool schema for query_transcript to tools/tool_schemas.py
- [ ] Wire into orchestrator: 5th agent when transcripts are available;
      skip gracefully with a note in the verdict if no transcripts found.
- [ ] Test on INFY.NS (good concall availability) and AAPL; verify retrieved
      chunks are relevant and the agent's signal is grounded in actual transcript text.

---

## Phase 7: Momentum Agent
Goal: Add an entry-timing signal to the web UI built in Phase 3.
Exit criterion: momentum_agent output renders correctly on the verdict page.

- [ ] Build agents/momentum_agent.py
      - RSI, MACD, 200-DMA, volume trends
      - Useful for entry timing on stocks already being watched
- [ ] Wire momentum_agent into orchestrator (now 6 agents)
- [ ] Test end-to-end on the web UI: ticker in → momentum signal renders correctly

---

## Phase 8: Portfolio + Watchlist + Review + Allocation
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
- [ ] Add Portfolio screen to the web UI
      - Holdings table with EOD prices (via yfinance)
      - P&L per position
      - Allocation breakdown: sector, geography, market cap
      - Warning if any position is overweight (>10%)
- [ ] Add Watchlist screen to the web UI
      - Current price vs target entry (progress bar)
      - Alert when stock enters buy zone

---

## Phase 9: Full Dashboard + Remaining Features (revisit scope here)
Goal: Assess what Phase 8 revealed is actually needed. Build accordingly.
Do not plan the detail of this phase until Phase 8 is complete.

Candidates to build (confirm at Phase 8 retrospective):
- [ ] Dashboard / Home screen — portfolio pulse + alerts
- [ ] agents/macro_agent.py — RBI/Fed cycle, FII flows, sector rotation
- [ ] agents/sentiment_agent.py — news tone, con-call signals (if NotebookLM
      manual workflow is proving too slow)
- [ ] Investment Journal — thesis logging + quarterly review
- [ ] Chat with optional fresh data fetch — triggered by user cross-question
      when existing analysis doesn't have the answer (extends Phase 4 chat)
- [ ] Google Sheets migration — only if portfolio.json update friction is real
- [ ] Daily digest email — only if analysis cadence has increased from monthly
- [ ] Screener architecture review before adding daily/on-demand runs
- [ ] Public deployment + sharing: deploy to Render/Fly.io, add a shared
      password gate (INSTANCE_PASSWORD env var), pre-cache 3–5 analyses for
      a zero-live-API demo path. Scope this properly once Phase 8 is done and
      the tool is genuinely useful to share. Per-user accounts are a separate
      decision at that point.

---

## Decisions Log

All architectural and product decisions are in **[DECISIONS.md](DECISIONS.md)**.
Add new entries there, not here.
