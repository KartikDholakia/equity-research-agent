# TEST_PLAN.md — Testing Framework & Roadmap

## Framework Stack

| Library | Purpose | Notes |
|---|---|---|
| `pytest` | Test runner | Already in requirements.txt |
| `pytest-mock` | `mocker` fixture for patching | Already in requirements.txt |
| `responses` | Mock HTTP calls (`requests` library) | **Add to requirements.txt** |
| `pytest-asyncio` | Async test support | Add in Phase 5 when LangGraph arrives |

---

## Directory Architecture

```
tests/
├── __init__.py                  (exists)
├── conftest.py                  ← shared pytest fixtures and sample data
├── fixtures/                    ← JSON snapshots of real API responses
│   ├── fmp_income.json          ← 5-year AAPL-like income statement
│   ├── fmp_balance.json         ← 5-year balance sheet
│   ├── fmp_cashflow.json        ← 5-year cash flow statement
│   └── fmp_key_metrics.json     ← 5-year key metrics (fcfYield, PEG, graham)
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
- `tests/integration/test_orchestrator.py` — Phase 5 (LangGraph workflows)
- `tests/e2e/` — Phase 4 (Streamlit UI)

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

A `pytest.ini` (or `pyproject.toml [tool.pytest]`) section will be added during
Milestone 1 boilerplate to configure test paths and markers.

---

## Milestones

### Milestone 1 — Framework Boilerplate ✅
Goal: `pytest` runs cleanly, discovers tests, markers work.

- [x] Add `responses>=0.25.0` to `requirements.txt`
- [x] Create `pytest.ini` with testpaths, markers (`unit`, `integration`), and
      `filterwarnings` to silence third-party deprecation noise
- [x] Create `tests/unit/__init__.py`
- [x] Create `tests/integration/__init__.py`
- [x] Create `tests/conftest.py` with shared fixtures:
      - `sample_income_statements` — 5-row list[dict] matching FMP income-statement shape
      - `sample_balance_sheets` — 5-row list[dict]
      - `sample_cash_flows` — 5-row list[dict]
      - `sample_key_metrics` — 5-row list[dict] (with fcfYield, pegRatio, grahamNumber)
      - `sample_price_data` — dict with `price` key
      - `sample_key_figures` — output of `extract_key_figures` called on the above
- [x] Create `tests/fixtures/fmp_income.json` with realistic 5-year AAPL data
- [x] Create `tests/fixtures/fmp_balance.json`
- [x] Create `tests/fixtures/fmp_cashflow.json`
- [x] Create `tests/fixtures/fmp_key_metrics.json`
- [x] Create `tests/fixtures/fmp_earnings.json` (added for Milestone 4 test_fmp.py)
- [x] Verify `pytest --collect-only` runs with 0 tests collected and 0 errors

---

### Milestone 2 — Unit Tests: Layer 3 (Metrics)
File: `tests/unit/test_metrics.py`
Goal: Every `compute_*` function in `tools/metrics.py` is covered.

- [ ] **compute_roe_trend**
  - ROE values computed correctly across 5 years
  - `consistent_above_15` is True when ≥ 60% of years exceed 15%
  - `consistent_above_15` is False when < 60% exceed 15%
  - Empty list input → returns safe defaults (no crash)
  - Zero equity in a year → that year is skipped, no ZeroDivisionError

- [ ] **compute_roce_trend**
  - ROCE values computed correctly (operating income / capital employed)
  - Zero capital employed year is skipped gracefully

- [ ] **compute_fcf_consistency**
  - Counts positive FCF years correctly
  - All-negative FCF → positive_years = 0
  - Empty input → returns zeroes

- [ ] **compute_ocf_quality**
  - Counts consecutive years where OCF < net income
  - Breaks on first year where OCF ≥ net income (not total count)

- [ ] **compute_debt_ratio**
  - D/E ratios computed correctly; `latest` matches index 0
  - Zero equity year is skipped

- [ ] **compute_interest_coverage**
  - Coverage values computed; `no_debt` flag is False when expense > 0
  - Zero interest expense year is skipped
  - Empty interest_expenses → `no_debt` is True

- [ ] **compute_dcf**
  - All three scenarios (bear 5%, base 10%, bull 15%) produce distinct values
  - Base scenario margin_of_safety is negative when stock is overvalued
  - `fcf_yield = None` → returns all None fields (no crash)
  - `fcf_yield <= 0` → returns all None fields
  - `current_price = 0` → returns all None fields

- [ ] **compute_graham**
  - Undervalued case (graham > price) → positive margin_of_safety_pct
  - Overvalued case (price > graham) → negative margin_of_safety_pct
  - `None` graham_number → returns None fields

- [ ] **compute_peg**
  - PEG < 1.0 → interpretation = "undervalued_growth"
  - PEG 1.0–1.49 → "fair"
  - PEG 1.5–1.99 → "slightly_expensive"
  - PEG ≥ 2.0 → "expensive"
  - `None` input → interpretation = "unavailable"

- [ ] **compute_pe_history**
  - Current P/E and 5yr average computed from earnings yields
  - `pct_vs_avg` is positive when current P/E > average (expensive vs own history)
  - Fewer than 2 data points → returns None fields (no crash)

- [ ] **compute_revenue_cagr**
  - 5-year CAGR computed correctly
  - Only 1 year of data → `cagr_pct = None`
  - Oldest revenue = 0 → `cagr_pct = None` (no ZeroDivisionError)

- [ ] **compute_cash_flow_quality**
  - 0 consecutive gaps → `auto_reject = False`
  - 1 consecutive gap → `auto_reject = False`
  - 2 consecutive gaps → `auto_reject = True` (threshold hit)
  - 3 consecutive gaps → `auto_reject = True`
  - Gap broken mid-sequence → only leading run counts, no false positive

- [ ] **compute_receivables_growth**
  - No flagged years when receivables grow slower than revenue
  - `bad_years` increments correctly when receivables grow > 1.5× revenue
  - Fewer than 3 data points → `bad_years = 0`, no crash

- [ ] **compute_debt_growth**
  - 0, 1, 2 consecutive years → `auto_reject = False`
  - 3 consecutive years → `auto_reject = True` (threshold hit)
  - Fewer than 4 data points → returns safe defaults, no crash
  - `year_flags` list length matches available year-pairs

---

### Milestone 3 — Unit Tests: Layer 2 (Key Figures)
File: `tests/unit/test_key_figures.py`

- [ ] Full valid statements → all 15+ keys present with correct Python types
      (`revenues` is `list[float]`, `current_price` is `float | None`, etc.)
- [ ] `interestExpense` missing from income statement rows → `interest_expenses`
      is an empty list, no KeyError
- [ ] `totalStockholdersEquity` absent but `totalEquity` present → equity fallback works
- [ ] Empty income statements list → `revenues`, `net_incomes`, etc. are all `[]`
- [ ] `freeCashFlowYield` present for 5 years → `fcf_yield` is 3-year average of newest 3
- [ ] `freeCashFlowYield` present for only 1 year → `fcf_yield` averages what's available
- [ ] All `freeCashFlowYield` values are negative → `fcf_yield` is `None`
- [ ] No `key_metrics` rows → `peg_ratio`, `graham_number`, `fcf_yield` all `None`

---

### Milestone 4 — Integration Tests: Layer 1 (FMP Client)
File: `tests/integration/test_fmp.py`
Uses `responses` library to intercept HTTP calls.

- [ ] `fetch_income_statement("AAPL")` with mocked 200 response → returns `list[dict]`
      with expected keys (`revenue`, `netIncome`, `operatingIncome`)
- [ ] `fetch_balance_sheet("AAPL")` → returns list with `totalDebt`, `totalAssets`, etc.
- [ ] `fetch_cash_flow("AAPL")` → returns list with `operatingCashFlow`, `freeCashFlow`
- [ ] `fetch_key_metrics("AAPL")` → returns list with `pegRatio`, `grahamNumber`,
      `freeCashFlowYield`
- [ ] `fetch_earnings_history("AAPL")` → returns list with `eps`, `date`
- [ ] FMP error payload `{"Error Message": "Invalid API KEY"}` → raises `ValueError`
- [ ] HTTP 404 response → raises `requests.HTTPError`
- [ ] `FMP_API_KEY` not set in environment → raises `EnvironmentError` before any HTTP call

---

### Milestone 5 — Integration Tests: Layer 4 (Agents)
File: `tests/integration/test_agents.py`
Uses `pytest-mock` to patch `anthropic.Anthropic().messages.create`.

- [ ] **Schema compliance — all three agents**
  For each of `quality_agent`, `value_agent`, `bear_case_agent`:
  - Mock Anthropic SDK to return a `submit_analysis` tool call with valid payload
  - Verify output dict has all 7 required keys:
    `agent`, `ticker`, `signal`, `score`, `summary`, `flags`, `timestamp`
  - `signal` is one of `"bullish"`, `"neutral"`, `"bearish"`
  - `score` is a `float` between `0.0` and `10.0`
  - `flags` is a `list`
  - `timestamp` is a non-empty string (ISO format)
  - `agent` matches the expected agent name string

- [ ] **Fallback path** (applies to all agents via `llm_agent.run_agent`)
  - Mock SDK to return `stop_reason = "end_turn"` without a `submit_analysis` call
  - Verify output still matches schema (no KeyError / crash)
  - Verify `flags` list contains `"Agent loop ended without submit_analysis"`
  - Verify `score` defaults to `5.0` and `signal` defaults to `"neutral"`

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

### Unit Tests
- `compute_quality_score(metrics)` — Python pre-filter scoring used in screener

### Integration Tests
- `tests/integration/test_universe.py`
  - Universe cache is populated from bulk download
  - Stale cache (> 7 days old) is refreshed; fresh cache is reused
  - Pre-filter correctly drops stocks below quality gates

---

## Phase 4 Tests (add when Phase 4 work begins)

### Integration Tests
- `tests/integration/test_agents.py` additions:
  - `momentum_agent.analyze()` schema compliance

### E2E Tests (new directory)
- `tests/e2e/test_dashboard.py` — Streamlit app smoke test
  - Page loads without error
  - Ticker input → verdict card rendered (mocked orchestrator)

---

## Phase 5 Tests (add when Phase 5 work begins)

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
