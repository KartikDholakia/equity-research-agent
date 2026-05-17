# SPEC.md — Product & Architecture Specification

## Vision
A personal AI-powered equity research platform that acts like a smart
analyst: monitors markets, analyzes stocks deeply, tracks a portfolio,
and helps make better investment decisions. Not a trading bot — a
decision-support system where the human always decides.

## Owner Profile
- 24-year-old software engineer, Bangalore
- Monthly income: ~₹2L, invests 50%+ monthly
- Risk tolerance: High (7.5/10), investment horizon: 5+ years
- Markets: Indian equities (NSE/BSE) + US stocks
- Existing platforms: Groww, Angel One, FI Money, Screener.in
- Tax regime: New regime — aware of LTCG/STCG/slab implications
- Goals: Wealth building, financial independence by 40, home in 6-10 yrs

---

## Core Use Cases

1. **Morning Brief** — Open the app, see portfolio pulse + 1-2 alerts
   + any screener hits from overnight
2. **Stock Analysis** — Ask "Analyze Zomato" → get full verdict card
3. **Screener** — Ask "Find 5 undervalued Indian mid-caps" → ranked list
4. **Watchlist** — Track stocks with target entry prices + thesis
5. **Portfolio Check** — "Should I add to NVIDIA?" → context-aware answer
6. **Portfolio Review** — Weekly/monthly: brief portfolio pulse (total value,
   P&L per position) + flag only positions that need attention (thesis broken,
   auto-reject triggered, position overweight). Silent on holdings that are fine.
7. **Allocation Query** — "I have ₹X, where should I invest?" → system runs
   screener, analyzes top candidates, checks portfolio fit, and returns ranked
   candidates with suggested ₹ allocation and sizing rationale per position.
8. **Investment Journal** — Log thesis on buy, review quarterly

---

## Application Screens

Screens are introduced in phases. Research/Chat is the core product —
all other screens are supporting infrastructure built once the verdict
card is trusted.

### Phase 4 — Research / Chat
- Chat interface for natural language queries
- Returns structured verdict cards for stock analysis
- Supports: analyze stock, run screener, portfolio questions

### Phase 5 — Portfolio
- All holdings with live prices (read from local portfolio.json)
- P&L and XIRR per position
- Allocation breakdown: sector, geography, market cap
- Warning if any position is overweight (>10% of portfolio)

### Phase 5 — Portfolio Review (periodic)
Output format:
```
PORTFOLIO PULSE — [Date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Value:    ₹X  (↑₹Y this week, +Z% overall)

Holdings:
  ZOMATO.NS    ✅  ₹220 → ₹285  (+29%)   Thesis intact
  HDFCBANK.NS  🟡  ₹1,640 → ₹1,590 (-3%) Soft quarter — monitoring
  AAPL         ❌  ₹175 → ₹162  (-7%)    FLAG: FCF diverging 2 quarters

⚠️ NEEDS ATTENTION:
  AAPL — auto-reject flag triggered (cash flow vs profit gap)
  ZOMATO.NS — 14% of portfolio, approaching 10% limit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
Flag triggers: auto-reject condition met, position >10%, thesis age >6 months.
Runs on schedule (weekly or monthly) or on demand.

### Phase 5 — Allocation Query
Triggered by: "I have ₹X, where should I invest?"
Output format:
```
WHERE TO INVEST ₹50,000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TITAN.NS    BUY  8.1/10  → ₹22,000 (44%)
   Fills consumer discretionary gap. ROE>25% consistent.

2. HDFCBANK.NS BUY  7.8/10  → ₹18,000 (36%)
   Undervalued vs 5yr P/B. Banking underweight in portfolio.

3. INFY.NS     WATCH 6.5/10 → ₹10,000 (20%)
   Existing holding — averaging down, thesis intact.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
Workflow: screener → analyze top candidates → portfolio fit check →
risk sizing → output ranked list with ₹ allocation per position.

### Phase 5 — Watchlist
- Stocks being tracked but not yet bought
- Current price vs target entry price (progress bar)
- One-line thesis per stock
- Alert when stock enters buy zone

### Phase 6 — Dashboard (Home)
- Portfolio P&L snapshot (today + overall)
- Top movers in holdings
- Active alerts (entry price hits, thesis review due)

### Phase 6 — Investment Journal
- Every buy has a logged thesis + exit criteria
- Quarterly: system checks if thesis is still intact
- Timeline of decisions with agent verdicts at time of purchase
- Note: manual NotebookLM workflow covers this adequately until Phase 6

---

## Architecture

### System Layers

```
LAYER 3 — DECISION LAYER
  Verdict Engine + Portfolio Context + Risk Check

LAYER 2 — ANALYSIS LAYER
  Specialized AI Agents (run in parallel)

LAYER 1 — DATA LAYER
  Screener.in | FMP | yfinance | Trendlyne | News RSS
```

### Tech Stack

| Component              | Technology                           |
|------------------------|--------------------------------------|
| Agent framework        | LangGraph                            |
| LLM                    | Claude API (claude-sonnet-4-6)       |
| US fundamentals        | Financial Modeling Prep (FMP) API    |
| Indian basic fundamentals | yfinance (.NS / .BO)              |
| Indian promoter/pledge | Screener.in (scraping)               |
| Indian bulk screener   | Trendlyne GuruQ (data downloader)    |
| Prices — EOD (both)    | yfinance (no real-time needed)       |
| Technicals             | yfinance                             |
| News/sentiment         | Google News RSS + FMP news           |
| Portfolio store        | local portfolio.json                 |
| Dashboard              | Streamlit                            |
| Scheduling             | APScheduler                          |
| Language               | Python 3.11+                         |

### Data Source Mapping

| Need                          | Source                  | Cost          |
|-------------------------------|-------------------------|---------------|
| Indian basic fundamentals     | yfinance (.NS/.BO)      | Free          |
| Indian promoter/pledge data   | Screener.in (scraping)  | Free          |
| Indian bulk screener data     | Trendlyne GuruQ         | ₹183/mo       |
| Indian/US prices (EOD only)   | yfinance                | Free          |
| US fundamentals               | FMP API                 | ~$15/mo       |
| Technical indicators          | yfinance                | Free          |
| News & sentiment              | Google News RSS         | Free          |
| Macro (RBI, FII flows)        | RBI website + NSE       | Free          |
| Document analysis             | NotebookLM (manual)     | Free          |
| Portfolio storage             | local portfolio.json    | Free          |
| **Estimated total**           |                         | **~₹1,750/mo**|

Note: No real-time price feed needed. EOD prices are sufficient for
long-term fundamental analysis at monthly cadence. Trendlyne GuruQ
(₹2,190/year) is used primarily in Phase 3 for bulk screener data
across 500 stocks — not needed for single-stock analysis in Phase 1-2.

---

## Agent System

### Analysis Agents

Agents are introduced in phases. The first three form the core analytical
triangle and answer the fundamental buy/avoid question. Later agents add
nuance once the core is trusted.

| Agent              | Inspired By                  | Focus                                      | Phase |
|--------------------|------------------------------|--------------------------------------------|-------|
| quality_agent      | Charlie Munger / Vijay Malik | ROE, ROCE, FCF, moat, promoter holding     | 1     |
| value_agent        | Ben Graham / Mohnish Pabrai  | DCF, Graham formula, PEG, margin of safety | 1     |
| bear_case_agent    | Michael Burry                | Red flags, accounting issues, auto-rejects | 1     |
| growth_agent       | Peter Lynch / Phil Fisher    | Revenue CAGR, EPS CAGR, TAM, estimates    | 2     |
| momentum_agent     | Stan Druckenmiller           | RSI, MACD, 200-DMA, volume trends         | 4     |
| macro_agent        | —                            | RBI/Fed cycle, FII flows, sector rotation  | 5     |
| sentiment_agent    | —                            | News tone, con-call language, mgmt signals | 5 (if needed) |

### Coordination Agents

| Agent              | Role                                                    | Phase |
|--------------------|---------------------------------------------------------|-------|
| orchestrator       | Routes query → runs agents → synthesizes verdict        | 1     |
| risk_manager       | Position sizing, concentration check, drawdown estimate | 4     |
| portfolio_manager  | Does this fit what the investor already holds?          | 4     |

---

## Investment Framework (Rules Baked Into Agents)

### Business Quality (Must-Pass Filter)
- Can the business model be explained in 2 sentences? If not, skip.
- Does it have a durable moat? (brand, switching cost, network effect,
  cost advantage, IP)
- Is the industry growing over a 10-year horizon?
- Promoter holding > 50%? Any pledged shares? (India red flag)

### Financial Health
- Revenue CAGR > 15% over 5 years
- EPS CAGR > 15% over 5 years — must be consistent, not lumpy
- ROE > 15% consistently (not a single-year spike)
- Operating cash flow ≥ net profit (if not, investigate why)
- FCF positive in at least 3 of last 5 years
- Debt/Equity < 1.5 for non-financial companies
- Interest coverage ratio > 3x
- No frequent equity dilution

### Valuation Signals
- Compare P/E vs own 5-year average AND sector peers (never in isolation)
- PEG ratio < 1.5 preferred
- EV/EBITDA vs peer median
- DCF in three scenarios: bear / base / bull
- Note: valuation is the one filter that can be relaxed if all quality
  and growth metrics are exceptional — but lower entry price = higher
  future returns all else equal

### Auto-Reject Red Flags (hard stops)
- Promoter pledging > 30% of holdings
- Cash flow diverging from reported profit for 2+ consecutive years
- Auditor resignation or unexplained auditor change
- Receivables growing significantly faster than revenue
- Unusual or large related-party transactions
- Active regulatory investigation (SEBI, SEC, etc.)
- Debt growing faster than revenue for 3+ years

### Management Quality Check
- Track earnings call promises vs actual delivery over 8 quarters
- Red flag if guidance misses > 2 consecutive quarters without explanation
- Check tone shift in con-calls (defensive → confident or vice versa)
- Review capex commitments and whether they materialised

---

## Verdict Output Format

Every analysis produces this structured card:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOCK: [Name] ([TICKER])
DATE: [Date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERDICT:      BUY | WATCH | AVOID
CONVICTION:   X.X / 10
FAIR VALUE:   ₹/$ XXX  (current: XXX → XX% upside/downside)
ACTION:       [Specific suggested action]

AGENT SIGNALS:
  Quality Agent     ✅ / 🟡 / ❌   [one-line summary]
  Value Agent       ✅ / 🟡 / ❌   [one-line summary]
  Growth Agent      ✅ / 🟡 / ❌   [one-line summary]
  Bear Case Agent   ✅ / 🟡 / ❌   [one-line summary]
  Momentum Agent    ✅ / 🟡 / ❌   [one-line summary]
  Sentiment Agent   ✅ / 🟡 / ❌   [one-line summary]
  Macro Agent       ✅ / 🟡 / ❌   [one-line summary]

TOP 3 BULL REASONS:
  1. [Reason]
  2. [Reason]
  3. [Reason]

TOP 3 RISKS:
  1. [Risk]
  2. [Risk]
  3. [Risk]

WHAT WOULD CHANGE MY MIND:
  → Strong Buy if: [specific trigger]
  → Exit/Avoid if: [specific trigger]

PORTFOLIO FIT:
  [Note on how this fits with existing holdings, sector exposure,
   suggested max allocation %]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Portfolio Data Schema

### Source of Truth
Holdings live in Groww (Indian equities) and INDMoney (consolidated view).
Both platforms support CSV export. The app reads from a local
`portfolio.json` file that is updated monthly by exporting from
Groww/INDMoney and running an import script.

Google Sheets integration is deferred to Phase 6. It will only be built
if the manual JSON update workflow proves too friction-heavy at that point.

### portfolio.json Schema

```json
{
  "holdings": [
    {
      "ticker": "ZOMATO.NS",
      "name": "Zomato Ltd",
      "market": "India",
      "qty": 100,
      "avg_buy_price": 220.50,
      "buy_date": "2024-06-15",
      "sector": "Consumer",
      "thesis": "One-line reason for holding"
    }
  ],
  "watchlist": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc",
      "target_entry": 175.00,
      "fair_value": 210.00,
      "thesis": "Why you're watching it",
      "added_date": "2025-01-10",
      "status": "Watching"
    }
  ],
  "last_updated": "2026-05-16"
}
```

### Investment Journal
Stored as `journal.json`. Each entry is created at time of buy and
reviewed quarterly. Manual NotebookLM workflow covers this until Phase 6.

```json
{
  "entries": [
    {
      "date": "2024-06-15",
      "ticker": "ZOMATO.NS",
      "thesis": ["Reason 1", "Reason 2", "Reason 3"],
      "exit_criteria": "What would make you sell",
      "agent_verdict": "BUY",
      "conviction_score": 7.5,
      "last_reviewed": "2025-03-15",
      "thesis_status": "Intact"
    }
  ]
}
```

---

## NotebookLM Integration (Manual Workflow)

NotebookLM is used separately for deep qualitative research — it is NOT
automated. Use it when doing a serious deep-dive on a new stock.

Workflow:
1. Create one notebook per company in NotebookLM
2. Upload: last 3 annual reports + last 8 quarters of con-call transcripts
   + any analyst reports you find
3. First prompt: "What is the bear case? What are the red flags?"
4. Then: "How has management guidance matched actual results over 8 quarters?"
5. Then: "What are the top 3 growth drivers and risks to each?"
6. Paste qualitative findings into Investment Journal before buying

Key rule: Do NOT ask NotebookLM to compute ratios or percentages —
it miscomputes. Ask factual questions only. Let the Python agents handle
all the math.

---

## Tax Awareness (Baked Into Portfolio Manager Agent)

- Indian equity LTCG: 12.5% if held > 1 year (above ₹1.25L exemption)
- Indian equity STCG: 20% if held < 1 year
- US stock gains: taxed at slab rate (30%) in India regardless of holding
- US and Indian losses cannot be offset against each other
- Before suggesting a sell, the portfolio_manager agent must flag the
  approximate tax impact