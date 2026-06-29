"""Unit tests for tools/key_figures.py — Layer 2 key figures extractor.

All tests are pure Python: no network calls, no API keys, no LLM.
The `sample_key_figures` fixture (via conftest.py) uses the full fixture
JSON files; inline fixtures are kept minimal for edge-case clarity.
"""
import pytest

from tools.key_figures import extract_key_figures

pytestmark = pytest.mark.unit

# ── Helpers ───────────────────────────────────────────────────────────────────

_PRICE = {"price": 100.0}


def _income(revenue=1000.0, net_income=100.0, operating_income=150.0, interest_expense: float | None = -10.0):
    row = {"revenue": revenue, "netIncome": net_income, "operatingIncome": operating_income}
    if interest_expense is not None:
        row["interestExpense"] = interest_expense
    return row


def _balance(total_assets=500.0, total_debt=200.0, equity=300.0,
             current_liabilities=100.0, net_receivables=50.0):
    return {
        "totalAssets": total_assets,
        "totalDebt": total_debt,
        "totalStockholdersEquity": equity,
        "totalEquity": equity,
        "totalCurrentLiabilities": current_liabilities,
        "netReceivables": net_receivables,
    }


def _cashflow(ocf=120.0, fcf=100.0, net_income=100.0):
    return {"operatingCashFlow": ocf, "freeCashFlow": fcf, "netIncome": net_income}


def _metrics(fcf_yield=0.05, peg=2.0, graham=30.0, earnings_yield=0.04):
    return {
        "freeCashFlowYield": fcf_yield,
        "pegRatio": peg,
        "grahamNumber": graham,
        "earningsYield": earnings_yield,
    }


def _extract(income=None, balance=None, cashflow=None, metrics=None, price=None):
    """Convenience wrapper with sensible single-row defaults."""
    return extract_key_figures(
        ticker="TEST",
        income_statements=income if income is not None else [_income()],
        balance_sheets=balance if balance is not None else [_balance()],
        cash_flows=cashflow if cashflow is not None else [_cashflow()],
        key_metrics=metrics if metrics is not None else [_metrics()],
        price_data=price if price is not None else _PRICE,
    )


# ── Output schema ─────────────────────────────────────────────────────────────


class TestOutputSchema:
    EXPECTED_KEYS = {
        "ticker", "company_name", "current_price", "revenues", "net_incomes",
        "operating_incomes", "interest_expenses", "equities", "total_assets",
        "current_liabilities", "total_debts", "net_receivables", "ocfs", "fcfs",
        "peg_ratio", "graham_number", "fcf_yield", "earnings_yields",
    }

    def test_all_18_keys_present_on_full_fixture_data(self, sample_key_figures):
        assert set(sample_key_figures.keys()) == self.EXPECTED_KEYS

    def test_ticker_is_string(self, sample_key_figures):
        assert isinstance(sample_key_figures["ticker"], str)

    def test_list_fields_are_lists_of_floats(self, sample_key_figures):
        list_fields = [
            "revenues", "net_incomes", "operating_incomes", "interest_expenses",
            "equities", "total_assets", "current_liabilities", "total_debts",
            "net_receivables", "ocfs", "fcfs", "earnings_yields",
        ]
        for field in list_fields:
            value = sample_key_figures[field]
            assert isinstance(value, list), f"{field} should be a list"
            for item in value:
                assert isinstance(item, float), f"items in {field} should be float"

    def test_fixture_data_produces_5_years_of_list_data(self, sample_key_figures):
        assert len(sample_key_figures["revenues"]) == 5
        assert len(sample_key_figures["ocfs"]) == 5
        assert len(sample_key_figures["fcfs"]) == 5

    def test_ticker_value_matches_input(self):
        result = _extract()
        assert result["ticker"] == "TEST"


# ── current_price ─────────────────────────────────────────────────────────────


class TestCurrentPrice:
    def test_price_extracted_from_price_data(self):
        result = _extract(price={"price": 220.50})
        assert result["current_price"] == 220.50

    def test_missing_price_key_returns_none(self):
        result = _extract(price={})
        assert result["current_price"] is None

    def test_zero_price_returns_none(self):
        # `float(0 or 0) or None` → 0.0 or None → None
        result = _extract(price={"price": 0})
        assert result["current_price"] is None


# ── interest_expenses ─────────────────────────────────────────────────────────


class TestInterestExpenses:
    def test_negative_interest_expense_stored_as_absolute_value(self):
        # FMP returns interest expense as a negative number
        result = _extract(income=[_income(interest_expense=-15.0)])
        assert result["interest_expenses"] == [15.0]

    def test_missing_interest_expense_field_produces_empty_list(self):
        # Row has no interestExpense key — must not raise KeyError
        result = _extract(income=[_income(interest_expense=None)])
        assert result["interest_expenses"] == []

    def test_multiple_rows_some_missing_interest_expense(self):
        rows = [_income(interest_expense=-10.0), _income(interest_expense=None)]
        result = _extract(income=rows)
        assert result["interest_expenses"] == [10.0]


# ── equities ──────────────────────────────────────────────────────────────────


class TestEquities:
    def test_uses_total_stockholders_equity_when_present(self):
        bs = {
            "totalStockholdersEquity": 300.0,
            "totalEquity": 999.0,  # should be ignored
            "totalAssets": 500.0, "totalDebt": 200.0,
            "totalCurrentLiabilities": 100.0, "netReceivables": 50.0,
        }
        result = _extract(balance=[bs])
        assert result["equities"] == [300.0]

    def test_falls_back_to_total_equity_when_stockholders_equity_absent(self):
        bs = {
            "totalEquity": 250.0,  # no totalStockholdersEquity key
            "totalAssets": 500.0, "totalDebt": 200.0,
            "totalCurrentLiabilities": 100.0, "netReceivables": 50.0,
        }
        result = _extract(balance=[bs])
        assert result["equities"] == [250.0]

    def test_row_excluded_when_both_equity_fields_absent(self):
        bs = {
            "totalAssets": 500.0, "totalDebt": 200.0,
            "totalCurrentLiabilities": 100.0, "netReceivables": 50.0,
        }
        result = _extract(balance=[bs])
        assert result["equities"] == []


# ── net_receivables ───────────────────────────────────────────────────────────


class TestNetReceivables:
    def test_uses_net_receivables_field(self):
        bs = _balance(net_receivables=75.0)
        result = _extract(balance=[bs])
        assert result["net_receivables"] == [75.0]

    def test_falls_back_to_accounts_receivable_when_net_receivables_absent(self):
        bs = {
            "accountsReceivable": 60.0,  # no netReceivables key
            "totalAssets": 500.0, "totalDebt": 200.0,
            "totalStockholdersEquity": 300.0, "totalEquity": 300.0,
            "totalCurrentLiabilities": 100.0,
        }
        result = _extract(balance=[bs])
        assert result["net_receivables"] == [60.0]

    def test_defaults_to_zero_when_both_fields_absent(self):
        bs = {
            "totalAssets": 500.0, "totalDebt": 200.0,
            "totalStockholdersEquity": 300.0, "totalEquity": 300.0,
            "totalCurrentLiabilities": 100.0,
        }
        result = _extract(balance=[bs])
        assert result["net_receivables"] == [0.0]

    def test_net_receivables_length_matches_number_of_balance_sheet_rows(self):
        # Unlike _pull, net_receivables always emits one entry per row (defaults to 0)
        result = _extract(balance=[_balance(), _balance(), _balance()])
        assert len(result["net_receivables"]) == 3


# ── empty statement lists ─────────────────────────────────────────────────────


class TestEmptyStatements:
    def test_empty_income_statements_produce_empty_lists(self):
        result = _extract(income=[])
        assert result["revenues"] == []
        assert result["net_incomes"] == []
        assert result["operating_incomes"] == []
        assert result["interest_expenses"] == []

    def test_empty_balance_sheets_produce_empty_lists(self):
        result = _extract(balance=[])
        assert result["equities"] == []
        assert result["total_assets"] == []
        assert result["current_liabilities"] == []
        assert result["total_debts"] == []
        assert result["net_receivables"] == []

    def test_empty_cash_flows_produce_empty_lists(self):
        result = _extract(cashflow=[])
        assert result["ocfs"] == []
        assert result["fcfs"] == []


# ── key_metrics scalar fields ─────────────────────────────────────────────────


class TestKeyMetricsScalars:
    def test_peg_ratio_taken_from_first_row(self):
        metrics = [_metrics(peg=3.1), _metrics(peg=2.5)]
        result = _extract(metrics=metrics)
        assert result["peg_ratio"] == 3.1

    def test_graham_number_taken_from_first_row(self):
        metrics = [_metrics(graham=22.5), _metrics(graham=30.0)]
        result = _extract(metrics=metrics)
        assert result["graham_number"] == 22.5

    def test_empty_key_metrics_returns_none_for_scalars(self):
        result = _extract(metrics=[])
        assert result["peg_ratio"] is None
        assert result["graham_number"] is None
        assert result["fcf_yield"] is None


# ── fcf_yield (3-year average) ────────────────────────────────────────────────


class TestFcfYield:
    def test_averages_newest_3_years_when_5_available(self):
        # Only the first 3 rows of key_metrics are used
        metrics = [
            _metrics(fcf_yield=0.04),
            _metrics(fcf_yield=0.06),
            _metrics(fcf_yield=0.02),
            _metrics(fcf_yield=0.10),  # should be excluded
            _metrics(fcf_yield=0.10),  # should be excluded
        ]
        result = _extract(metrics=metrics)
        expected = round((0.04 + 0.06 + 0.02) / 3, 6)
        assert result["fcf_yield"] == pytest.approx(expected)

    def test_averages_single_year_when_only_one_available(self):
        result = _extract(metrics=[_metrics(fcf_yield=0.05)])
        assert result["fcf_yield"] == pytest.approx(0.05)

    def test_all_negative_yields_returns_none(self):
        metrics = [_metrics(fcf_yield=-0.02), _metrics(fcf_yield=-0.01)]
        result = _extract(metrics=metrics)
        assert result["fcf_yield"] is None

    def test_average_of_mixed_yields_below_zero_returns_none(self):
        # avg of -0.04 and 0.01 = -0.015 → None
        metrics = [_metrics(fcf_yield=-0.04), _metrics(fcf_yield=0.01)]
        result = _extract(metrics=metrics)
        assert result["fcf_yield"] is None

    def test_missing_fcf_yield_field_treated_as_absent(self):
        # Row has no freeCashFlowYield key → excluded from average
        row = {"pegRatio": 2.0, "grahamNumber": 30.0, "earningsYield": 0.04}
        result = _extract(metrics=[row])
        assert result["fcf_yield"] is None


# ── earnings_yields ───────────────────────────────────────────────────────────


class TestEarningsYields:
    def test_only_positive_earnings_yields_included(self):
        metrics = [
            _metrics(earnings_yield=0.04),
            _metrics(earnings_yield=0.03),
        ]
        result = _extract(metrics=metrics)
        assert len(result["earnings_yields"]) == 2
        assert 0.04 in result["earnings_yields"]

    def test_zero_earnings_yield_excluded(self):
        metrics = [_metrics(earnings_yield=0.0), _metrics(earnings_yield=0.04)]
        result = _extract(metrics=metrics)
        assert 0.0 not in result["earnings_yields"]
        assert len(result["earnings_yields"]) == 1

    def test_negative_earnings_yield_excluded(self):
        # Negative earnings yield = company lost money that year
        metrics = [_metrics(earnings_yield=-0.02), _metrics(earnings_yield=0.04)]
        result = _extract(metrics=metrics)
        assert len(result["earnings_yields"]) == 1
        assert result["earnings_yields"][0] == pytest.approx(0.04)

    def test_missing_earnings_yield_field_excluded(self):
        row = {"pegRatio": 2.0, "grahamNumber": 30.0, "freeCashFlowYield": 0.04}
        result = _extract(metrics=[row])
        assert result["earnings_yields"] == []
