# TEST_PLAN.md — Testing Framework & Roadmap

## Framework Stack

| Library | Purpose | Notes |
|---|---|---|
| `pytest` | Test runner | In requirements.txt |
| `pytest-mock` | `mocker` fixture for patching | In requirements.txt |
| `responses` | Mock HTTP calls (`requests` library) | In requirements.txt |
| `pytest-asyncio` | Async test support | Add in Phase 5 when LangGraph arrives |

---

## Directory Architecture

```
tests/
├── __init__.py
├── conftest.py                  ← shared pytest fixtures and sample data
├── fixtures/                    ← JSON snapshots of real API responses
│   ├── fmp_income.json          ← 5-year AAPL-like income statement
│   ├── fmp_balance.json         ← 5-year balance sheet
│   ├── fmp_cashflow.json        ← 5-year cash flow statement
│   ├── fmp_key_metrics.json     ← 5-year key metrics (fcfYield, PEG, graham)
│   └── fmp_earnings.json        ← 5-year earnings history
├── unit/                        ← pure Python, zero network calls, fast
│   ├── __init__.py
│   ├── test_metrics.py          ← Layer 3: all compute_* functions
│   └── test_key_figures.py      ← Layer 2: extract_key_figures
└── integration/                 ← mocked APIs, tests full data flow per layer
    ├── __init__.py
    ├── test_fmp.py              ← Layer 1: FMP client with mocked HTTP
    └── test_agents.py           ← Layer 4: agents with mocked Anthropic SDK
```

Future directories added per phase:
- `tests/integration/test_screener.py` — Phase 2 (Screener.in scraper)
- `tests/integration/test_yfinance.py` — Phase 2 (Indian market yfinance)
- `tests/integration/test_orchestrator.py` — Phase 6 (LangGraph workflows)
- `tests/e2e/` — Phase 3 (Web UI — FastAPI + Jinja2)

---

## Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (fast, no mocking needed)
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Run a single file
pytest tests/unit/test_metrics.py -v
```

---

## Phase 1 Coverage

**154 tests, all passing.** Covers Layers 1–4 of the Phase 1 architecture.

### Unit — Layer 3: `tools/metrics.py` (76 tests)
`tests/unit/test_metrics.py`

| Function | Cases covered |
|---|---|
| `compute_roe_trend` | Correct values; `consistent_above_15` true/false at 60% threshold; empty input; zero equity skipped |
| `compute_roce_trend` | Correct values; zero capital employed year skipped; empty input |
| `compute_fcf_consistency` | Positive year count; all-negative; empty input; values preserved |
| `compute_ocf_quality` | No gaps; 1 gap then break; all gaps; gap broken mid-sequence; empty input |
| `compute_debt_ratio` | Correct values; latest = index 0; zero equity skipped; empty input |
| `compute_interest_coverage` | Correct values; empty expenses → no_debt; zero expense year skipped; empty OI after zip |
| `compute_dcf` | bull > base > bear; all positive; MoS sign (over/undervalued); None/zero/negative yield → all None; zero/None price → all None |
| `compute_graham` | Undervalued (positive MoS); overvalued (negative MoS); None inputs |
| `compute_peg` | All 4 interpretation buckets; None/zero/negative → unavailable; rounding |
| `compute_pe_history` | P/E from yields; pct_vs_avg sign; < 2 data points → None fields |
| `compute_revenue_cagr` | Correct CAGR; multi-year; single year → None; zero oldest → None |
| `compute_cash_flow_quality` | 0/1 gaps → no auto-reject; 2/3 gaps → auto-reject; gap broken mid-sequence |
| `compute_receivables_growth` | < 3 data points → empty; clean growth → no flags; fast recv growth → flagged; declining revenue → not flagged |
| `compute_debt_growth` | < 4 data points → safe defaults; 0/2 consecutive → no auto-reject; 3 consecutive → auto-reject; reset after break |

### Unit — Layer 2: `tools/key_figures.py` (33 tests)
`tests/unit/test_key_figures.py`

- All 17 output keys present with correct Python types on full fixture data
- `interestExpense` field absent → `interest_expenses = []`, no KeyError
- `totalStockholdersEquity` absent, `totalEquity` present → equity fallback works
- Both equity fields absent → row excluded from `equities` list
- `netReceivables` absent → falls back to `accountsReceivable`; both absent → 0.0
- `net_receivables` always emits one entry per row (unlike `_pull` which skips missing fields)
- Empty income / balance / cash flow lists → all corresponding output lists are `[]`
- `freeCashFlowYield` for 5 years → 3-year average of newest 3 only
- Single-year FCF yield → averages that one value
- All-negative FCF yields → `fcf_yield = None`
- Mixed yields averaging to ≤ 0 → `fcf_yield = None`
- `freeCashFlowYield` field absent → treated as missing
- Empty `key_metrics` → `peg_ratio`, `graham_number`, `fcf_yield` all None
- `price = 0` or missing → `current_price = None`
- Negative `interestExpense` stored as absolute value

### Integration — Layer 1: `data/fmp.py` (14 tests)
`tests/integration/test_fmp.py` — HTTP intercepted via `responses` library

- All 5 fetch functions return `list[dict]` with correct shape
- Each endpoint hits the correct URL
- FMP error payload `{"Error Message": "..."}` with HTTP 200 → raises `ValueError`
- HTTP 404 → raises `requests.HTTPError`
- `FMP_API_KEY` not set → raises `EnvironmentError` before any HTTP call

### Integration — Layer 4: agents (31 tests)
`tests/integration/test_agents.py` — Anthropic SDK mocked via `pytest-mock`

- All 8 required keys present in output: `agent`, `ticker`, `signal`, `score`, `summary`, `details`, `flags`, `timestamp`
- `signal` is one of `bullish / neutral / bearish`
- `score` is a `float` in `[0.0, 10.0]`
- `flags` is a `list`; populated flags are passed through correctly
- `agent` field matches the module name; `ticker` matches the input
- `timestamp` is a non-empty string
- All schema assertions run against all 3 agents via `@pytest.mark.parametrize`
- Fallback path (`end_turn` without `submit_analysis`): schema still valid, `signal = "neutral"`, `score = 5.0`, diagnostic flag present

---

## Phase 2 Tests (add when Phase 2 work begins)

### Unit Tests
File additions to `tests/unit/test_metrics.py`:
- `compute_eps_cagr(eps_list)` — EPS CAGR over available years
- `compute_promoter_analysis(holding_pct, pledge_pct)` — promoter quality flags
- `compute_tam_growth(revenues, sector_growth)` — relative TAM sizing

### Integration Tests
- `tests/integration/test_screener.py` — Screener.in scraper with mocked HTTP
  - `fetch_promoter_holding` → returns dict with `promoter_pct`, `pledged_pct`
  - `fetch_fii_dii_trends` → returns list of quarterly holding changes
  - Rate limiting: consecutive calls have delay between them
- `tests/integration/test_yfinance.py` — yfinance India client
  - `fetch_fundamentals_india("ZOMATO.NS")` with mocked yfinance response
- `tests/integration/test_agents.py` additions:
  - `growth_agent.analyze()` schema compliance (same pattern as Phase 1 agents)

---

## Phase 3 Tests (add when Phase 3 work begins)

### E2E Tests (new directory)
- `tests/e2e/test_web.py` — FastAPI + Jinja2 app smoke test
  - GET / loads the ticker-input form without error
  - POST /research → verdict card rendered (mocked orchestrator), including
    the key-figures table and DCF scenario breakdown
  - Both a US ticker and an .NS ticker render without error

---

## Phase 4 Tests (add when Phase 4 work begins)

### Unit Tests
- `compute_quality_score(metrics)` — Python pre-filter scoring used in screener

### Integration Tests
- `tests/integration/test_universe.py`
  - Universe cache is populated from bulk download
  - Stale cache (> 7 days old) is refreshed; fresh cache is reused
  - Pre-filter correctly drops stocks below quality gates

---

## Phase 5 Tests (add when Phase 5 work begins)

### Integration Tests
- `tests/integration/test_agents.py` additions:
  - `momentum_agent.analyze()` schema compliance
- `tests/e2e/test_web.py` additions:
  - Momentum agent signal renders correctly on the verdict page

---

## Phase 6 Tests (add when Phase 6 work begins)

### New dependencies
- Add `pytest-asyncio` when LangGraph async workflows are introduced

### Integration Tests
- `tests/integration/test_portfolio.py`
  - `read_holdings()` from a fixture `portfolio.json` → returns list[dict]
  - `import_from_csv(path)` → correctly parses Groww/INDMoney CSV format
- `tests/integration/test_orchestrator.py` — LangGraph workflow tests
  - Portfolio review workflow: bear_case flags trigger correctly
  - Allocation workflow: screener → candidates → risk sizing → ranked output
  - Agents `risk_manager` and `portfolio_manager` schema compliance

---

## Decisions Log

| Date | Decision |
|---|---|
| 2026-06-07 | `responses` chosen over `httpx`/`respx` because FMP client uses `requests` |
| 2026-06-07 | `pytest-asyncio` deferred to Phase 5 — all current code is synchronous |
| 2026-06-07 | Fixture JSON files checked into repo — realistic data, no secrets, enables offline CI |
| 2026-06-07 | `e2e/` directory deferred to Phase 4 — no UI exists yet |
