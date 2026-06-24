# DECISIONS.md — Architectural & Product Decision Log

Every meaningful technical or product choice is recorded here so future
sessions can understand *why* things are the way they are without having to
re-derive it from code or git history.

> **Phase-number caveat**: entries dated before 2026-06-16 use the OLD phase
> numbering (old Phase 3 = Screener, old Phase 4 = UI). The 2026-06-16
> renumbering entry explains the mapping.

---

| Date       | Decision |
|------------|----------|
| 2026-04-10 | Python chosen over Kotlin — LangGraph ecosystem is Python-native |
| 2026-04-10 | FMP for US deep fundamentals, Screener.in for Indian data |
| 2026-04-10 | NotebookLM used manually for con-call/annual report deep dives |
| 2026-04-10 | Three-file structure: CLAUDE.md + SPEC.md + PLAN.md |
| 2026-04-10 | Build starts with US stocks (Phase 1) before Indian market |
| 2026-05-16 | Phase 1 scoped to 3 agents only (quality/value/bear) — 80% value, less risk |
| 2026-05-16 | Google Sheets dropped from near-term — portfolio lives in Groww + INDMoney |
| 2026-05-16 | Portfolio store: local portfolio.json updated monthly via CSV export |
| 2026-05-16 | Screener moved to Phase 3 (before UI) — monthly cadence means finding candidates |
| 2026-05-16 | Streamlit UI moved to Phase 4 — CLI sufficient for monthly analysis cadence |
| 2026-05-16 | Daily digest cut from roadmap — noise at monthly analysis frequency |
| 2026-05-16 | Phase 6 scope intentionally left open — decide after Phase 5 retrospective |
| 2026-05-17 | No real-time price API — EOD prices via yfinance are sufficient for long-term analysis |
| 2026-05-17 | Indian basic fundamentals via yfinance (.NS) — covers income stmt, balance sheet, CF |
| 2026-05-17 | Indian promoter/pledge data via Screener.in scraping — only source under budget |
| 2026-05-17 | Trendlyne GuruQ added (₹2,190/yr) for Phase 3 bulk screener data — not Phase 1-2 |
| 2026-05-17 | FMP API (~$15/mo) retained for US deep fundamentals — best coverage at the price |
| 2026-05-17 | EODHD rejected — fundamentals plan ~₹5,000/mo, Indian promoter data coverage unclear |
| 2026-05-17 | Orchestrator must route 4 query types: analyze / screen / review / allocate |
| 2026-05-17 | Portfolio review: mixed output — brief pulse + flag issues only, runs on schedule |
| 2026-05-17 | Allocation query output: ranked candidates + suggested ₹ sizing per position |
| 2026-05-18 | quality_agent scores 6 checks (ROE, ROCE, FCF, OCF quality, D/E, interest coverage) weighted to 10 |
| 2026-05-18 | value_agent: DCF growth rates kept as module constants — Phase 4 (Screener, renumbered 2026-06-16) will derive from historical FCF CAGR |
| 2026-05-18 | Graham formula intentionally kept for value signals; irrelevant for asset-light/buyback-heavy stocks |
| 2026-05-18 | bear_case_agent automates 3 of 7 auto-reject flags (CFQ, receivables, debt growth); remaining 4 need manual/news data not available in Phase 1 |
| 2026-05-24 | Architecture: 5-layer hybrid — Python for data/math, Claude (tool use) for reasoning. Persona-based agents with tight prompts. See ARCHITECTURE.md. |
| 2026-05-24 | LangGraph deferred to Phase 6 — plain Anthropic SDK sufficient for Phase 1-5 parallel agent execution |
| 2026-05-24 | Screener mode (Phase 4) uses two-speed system: Python pre-filter on 500 stocks, LLM only on shortlist of 20-30 — keeps cost under ₹20/run |
| 2026-05-24 | Phase 1 refactor: current rule-based agents to be replaced with LLM agents (Python computes metrics, Claude reasons via persona prompts) |
| 2026-05-28 | LLM refactor complete: tools/key_figures.py (Layer 2), tools/metrics.py + tool_schemas.py + llm_agent.py (Layer 3/loop), agents refactored to Claude tool use with Munger/Graham/Burry personas, prompt caching on system prompt block |
| 2026-06-08 | Phase 2 Steps 4–11 complete: India key figures extractor, 3 new metrics (eps_cagr, promoter_analysis, fii_trend), 3 new tool schemas, growth_agent (Lynch/Fisher persona), quality_agent India extension, orchestrator market-aware routing (4 agents, new weights), India tax banner. 211 tests passing. |
| 2026-06-16 | Phases renumbered after a 3-way (user / PM / Tech Lead) discussion: old Phase 3 (Screener) → Phase 4, old Phase 4 (Streamlit UI + Momentum) split into new Phase 3 (UI only) + Phase 5 (Momentum only), old Phase 5 (Portfolio) → Phase 6, old Phase 6 → Phase 7. Decision log entries dated before 2026-06-16 that mention "Phase 3/4/5" use the OLD numbering — read them in that context. |
| 2026-06-16 | Web UI pulled forward to Phase 3, ahead of the screener — terminal output was judged both a content/trust problem (generic prose, unverifiable numbers) and a scan-cost problem (ASCII wall of text). Fixing the report used on every analysis outranks finding new candidates right now. |
| 2026-06-16 | Tech stack for the web UI: plain HTML/CSS template + FastAPI + Jinja2, NOT Streamlit and NOT a JS framework. Rationale: charts/interactivity (Streamlit's main edge) were explicitly deprioritized, leaving fine-grained layout/CSS control as the actual requirement; FastAPI picked over Flask for type-hint-native style and future JSON endpoint headroom. |
| 2026-06-16 | Charts/data visualization explicitly deprioritized (lowest priority) for the web UI phase — if revisited, reuse data already fetched by fetch_price_history()/fetch_technical_indicators() and value_agent's DCF scenarios before adding any new paid data source. |
| 2026-06-16 | Content upgrade (raw key-figures table + DCF bear/base/bull breakdown) folded into the Phase 3 web UI work — same render pass fixes both the content/trust and scan-cost complaints. |
| 2026-06-16 | dashboard/ (empty placeholder) renamed to web/ — name and tech (Streamlit) had both gone stale relative to the actual plan. |
| 2026-06-16 | Multi-user sharing scope noted: goal is to eventually share with parents, friends, and recruiters. Rollout: (1) personal use first, (2) public demo + own hosted instance later (Phase 7 candidate), (3) per-user accounts only if genuinely needed at that point. |
| 2026-06-16 | Recruiter demo strategy (deferred to Phase 7): pre-compute and cache 3–5 tickers (mix BUY/WATCH/AVOID, US + India). Serve from JSON cache — zero live API calls on demo path. |
| 2026-06-16 | Password gate for future public instance: single shared INSTANCE_PASSWORD via HTTP Basic Auth or session cookie — sufficient for a personal demo, must be replaced with per-user auth before real portfolio data enters. |
| 2026-06-24 | Key figures table shows multi-year sparkrow (latest · prior · prior) for income/CF metrics instead of single latest value + arrow — trend is the signal, showing 3 values is more actionable than an arrow alone. D/E ratio, interest coverage, and current P/E (US) / forward P/E (India) added as computed rows; all derivable from existing raw dict, no new data source needed. |
| 2026-06-16 | Claude-generated mockups vs Emergent (emergent.sh) for full frontend: deferred. Plan is to use Claude wireframes to spec it, then decide build-vs-Emergent at that phase. |
| 2026-06-21 | Public deployment/sharing deferred to Phase 7 candidates. Primary goal is personal investment decision-support — trust and usability for the owner's own money comes first. Deployment is worth doing only after Phase 6, when the tool knows the portfolio and is genuinely mature. |
