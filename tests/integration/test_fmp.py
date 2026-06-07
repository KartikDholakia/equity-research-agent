"""Integration tests for data/fmp.py — Layer 1 FMP API client.

All HTTP calls are intercepted by the `responses` library — no real network
requests are made. Each test sets FMP_API_KEY via monkeypatch so the test
environment never needs a real API key.
"""
import pytest
import requests
import responses as resp

from data.fmp import (
    fetch_balance_sheet,
    fetch_cash_flow,
    fetch_earnings_history,
    fetch_income_statement,
    fetch_key_metrics,
)

pytestmark = pytest.mark.integration

_BASE = "https://financialmodelingprep.com/stable"


# ── fetch_income_statement ────────────────────────────────────────────────────


class TestFetchIncomeStatement:
    @resp.activate
    def test_returns_list_of_dicts(self, sample_income_statements, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/income-statement", json=sample_income_statements)

        result = fetch_income_statement("AAPL")

        assert isinstance(result, list)
        assert len(result) == 5

    @resp.activate
    def test_contains_expected_keys(self, sample_income_statements, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/income-statement", json=sample_income_statements)

        result = fetch_income_statement("AAPL")

        assert "revenue" in result[0]
        assert "netIncome" in result[0]
        assert "operatingIncome" in result[0]
        assert "interestExpense" in result[0]

    @resp.activate
    def test_hits_correct_endpoint(self, sample_income_statements, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/income-statement", json=sample_income_statements)

        fetch_income_statement("AAPL")

        url = resp.calls[0].request.url
        assert url is not None
        assert url.startswith(f"{_BASE}/income-statement")


# ── fetch_balance_sheet ───────────────────────────────────────────────────────


class TestFetchBalanceSheet:
    @resp.activate
    def test_returns_list_of_dicts(self, sample_balance_sheets, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/balance-sheet-statement", json=sample_balance_sheets)

        result = fetch_balance_sheet("AAPL")

        assert isinstance(result, list)
        assert len(result) == 5

    @resp.activate
    def test_contains_expected_keys(self, sample_balance_sheets, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/balance-sheet-statement", json=sample_balance_sheets)

        result = fetch_balance_sheet("AAPL")

        assert "totalAssets" in result[0]
        assert "totalDebt" in result[0]
        assert "totalCurrentLiabilities" in result[0]


# ── fetch_cash_flow ───────────────────────────────────────────────────────────


class TestFetchCashFlow:
    @resp.activate
    def test_returns_list_of_dicts(self, sample_cash_flows, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/cash-flow-statement", json=sample_cash_flows)

        result = fetch_cash_flow("AAPL")

        assert isinstance(result, list)
        assert len(result) == 5

    @resp.activate
    def test_contains_expected_keys(self, sample_cash_flows, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/cash-flow-statement", json=sample_cash_flows)

        result = fetch_cash_flow("AAPL")

        assert "operatingCashFlow" in result[0]
        assert "freeCashFlow" in result[0]


# ── fetch_key_metrics ─────────────────────────────────────────────────────────


class TestFetchKeyMetrics:
    @resp.activate
    def test_returns_list_of_dicts(self, sample_key_metrics, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/key-metrics", json=sample_key_metrics)

        result = fetch_key_metrics("AAPL")

        assert isinstance(result, list)
        assert len(result) == 5

    @resp.activate
    def test_contains_expected_keys(self, sample_key_metrics, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/key-metrics", json=sample_key_metrics)

        result = fetch_key_metrics("AAPL")

        assert "pegRatio" in result[0]
        assert "grahamNumber" in result[0]
        assert "freeCashFlowYield" in result[0]


# ── fetch_earnings_history ────────────────────────────────────────────────────


class TestFetchEarningsHistory:
    @resp.activate
    def test_returns_list_of_dicts(self, sample_earnings, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/earnings", json=sample_earnings)

        result = fetch_earnings_history("AAPL")

        assert isinstance(result, list)
        assert len(result) == 5

    @resp.activate
    def test_contains_expected_keys(self, sample_earnings, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/earnings", json=sample_earnings)

        result = fetch_earnings_history("AAPL")

        assert "eps" in result[0]
        assert "date" in result[0]


# ── Error handling ────────────────────────────────────────────────────────────


class TestFmpErrorHandling:
    @resp.activate
    def test_fmp_error_payload_raises_value_error(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(
            resp.GET,
            f"{_BASE}/income-statement",
            json={"Error Message": "Invalid API KEY"},
            status=200,  # FMP returns 200 even for key errors
        )

        with pytest.raises(ValueError, match="FMP API error"):
            fetch_income_statement("AAPL")

    @resp.activate
    def test_http_404_raises_http_error(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "test-key")
        resp.add(resp.GET, f"{_BASE}/income-statement", status=404)

        with pytest.raises(requests.HTTPError):
            fetch_income_statement("AAPL")

    def test_missing_api_key_raises_environment_error(self, monkeypatch):
        # No responses mock needed — the EnvironmentError fires before any HTTP call
        monkeypatch.delenv("FMP_API_KEY", raising=False)

        with pytest.raises(EnvironmentError, match="FMP_API_KEY is not set"):
            fetch_income_statement("AAPL")
