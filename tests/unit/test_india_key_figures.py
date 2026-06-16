"""Tests for extract_df_key_figures — uses mock DataFrames in yfinance format."""
import pandas as pd
import pytest

from tools.key_figures import extract_df_key_figures as extract_india_key_figures


def _make_income(revenues, net_incomes, operating_incomes, interest_expenses=None):
    years = [f"FY{2024 - i}" for i in range(len(revenues))]
    data = {
        "Total Revenue":    revenues,
        "Net Income":       net_incomes,
        "Operating Income": operating_incomes,
    }
    if interest_expenses is not None:
        data["Interest Expense"] = interest_expenses
    return pd.DataFrame(data, index=years).T


def _make_balance(total_assets, current_liabilities, total_debts, equities, receivables=None):
    years = [f"FY{2024 - i}" for i in range(len(total_assets))]
    data = {
        "Total Assets":          total_assets,
        "Current Liabilities":   current_liabilities,
        "Total Debt":            total_debts,
        "Common Stock Equity":   equities,
    }
    if receivables is not None:
        data["Accounts Receivable"] = receivables
    return pd.DataFrame(data, index=years).T


def _make_cashflow(ocfs, fcfs):
    years = [f"FY{2024 - i}" for i in range(len(ocfs))]
    return pd.DataFrame(
        {"Operating Cash Flow": ocfs, "Free Cash Flow": fcfs},
        index=years,
    ).T


PRICE = {"price": 100.0, "market_cap": 1_000_000.0}
PROMOTER = {"promoter_pct": 55.0, "pledging_pct": 5.0, "fii_pct": 22.0, "fii_trend": "rising"}


# ── Basic field extraction ───────────────────────────────────────────────────────

def test_basic_fields_extracted():
    inc = _make_income([500, 450, 400], [50, 45, 40], [70, 65, 60])
    bs  = _make_balance([300, 280, 260], [100, 95, 90], [50, 45, 40], [150, 140, 130])
    cf  = _make_cashflow([60, 55, 50], [40, 38, 35])
    result = extract_india_key_figures("INFY.NS", inc, bs, cf, PROMOTER, PRICE)

    assert result["ticker"] == "INFY.NS"
    assert result["current_price"] == 100.0
    assert result["revenues"] == [500.0, 450.0, 400.0]
    assert result["net_incomes"] == [50.0, 45.0, 40.0]
    assert result["operating_incomes"] == [70.0, 65.0, 60.0]
    assert result["ocfs"] == [60.0, 55.0, 50.0]
    assert result["fcfs"] == [40.0, 38.0, 35.0]


def test_balance_sheet_fields():
    inc = _make_income([500], [50], [70])
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    result = extract_india_key_figures("ZOMATO.NS", inc, bs, cf, PROMOTER, PRICE)

    assert result["total_assets"] == [300.0]
    assert result["current_liabilities"] == [100.0]
    assert result["total_debts"] == [50.0]
    assert result["equities"] == [150.0]


# ── FCF yield ────────────────────────────────────────────────────────────────────

def test_fcf_yield_computed():
    inc = _make_income([500, 450, 400], [50, 45, 40], [70, 65, 60])
    bs  = _make_balance([300, 280, 260], [100, 95, 90], [50, 45, 40], [150, 140, 130])
    cf  = _make_cashflow([60, 55, 50], [30_000, 38_000, 35_000])
    price = {"price": 100.0, "market_cap": 1_000_000.0}
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, price)
    expected_avg = (30_000 + 38_000 + 35_000) / 3 / 1_000_000
    assert result["fcf_yield"] == pytest.approx(expected_avg, rel=1e-4)


def test_fcf_yield_none_if_no_market_cap():
    inc = _make_income([500], [50], [70])
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    price = {"price": 100.0, "market_cap": 0}
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, price)
    assert result["fcf_yield"] is None


def test_fcf_yield_none_if_negative_average():
    inc = _make_income([500, 450, 400], [50, 45, 40], [70, 65, 60])
    bs  = _make_balance([300, 280, 260], [100, 95, 90], [50, 45, 40], [150, 140, 130])
    cf  = _make_cashflow([60, 55, 50], [-100, -200, -150])
    price = {"price": 100.0, "market_cap": 1_000_000.0}
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, price)
    assert result["fcf_yield"] is None


# ── India-specific fields ────────────────────────────────────────────────────────

def test_promoter_fields_populated():
    inc = _make_income([500], [50], [70])
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    result = extract_india_key_figures("HDFCBANK.NS", inc, bs, cf, PROMOTER, PRICE)

    assert result["promoter_pct"] == 55.0
    assert result["pledging_pct"] == 5.0
    assert result["fii_pct"] == 22.0
    assert result["fii_trend"] == "rising"
    assert result["promoter_data_available"] is True


def test_promoter_data_unavailable_flag():
    inc = _make_income([500], [50], [70])
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    empty_promoter = {"promoter_pct": None, "pledging_pct": None, "fii_pct": None, "fii_trend": None}
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, empty_promoter, PRICE)

    assert result["promoter_pct"] is None
    assert result["promoter_data_available"] is False


# ── info dict (forward estimates) ────────────────────────────────────────────────

def test_forward_estimates_populated_from_info():
    inc = _make_income([500], [50], [70])
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    info = {"forwardPE": 22.5, "forwardEps": 4.8, "pegRatio": 1.1}
    result = extract_india_key_figures("INFY.NS", inc, bs, cf, PROMOTER, PRICE, info=info)

    assert result["forward_pe"] == 22.5
    assert result["forward_eps"] == 4.8
    assert result["peg_ratio"] == 1.1


def test_forward_estimates_none_when_info_omitted():
    inc = _make_income([500], [50], [70])
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, PRICE)

    assert result["forward_pe"] is None
    assert result["forward_eps"] is None
    assert result["peg_ratio"] is None


def test_forward_estimates_none_when_keys_absent_from_info():
    inc = _make_income([500], [50], [70])
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, PRICE, info={})

    assert result["forward_pe"] is None


# ── Row name fallbacks ────────────────────────────────────────────────────────────

def test_fallback_row_name_long_term_debt():
    inc = _make_income([500], [50], [70])
    bs = pd.DataFrame(
        {
            "Total Assets":        [300.0],
            "Current Liabilities": [100.0],
            "Long Term Debt":      [60.0],
            "Common Stock Equity": [150.0],
        },
        index=["FY2024"],
    ).T
    cf  = _make_cashflow([60], [40])
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, PRICE)
    assert result["total_debts"] == [60.0]


def test_missing_row_returns_empty_list():
    inc = pd.DataFrame({"Net Income": [50.0]}, index=["FY2024"]).T
    bs  = _make_balance([300], [100], [50], [150])
    cf  = _make_cashflow([60], [40])
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, PRICE)
    assert result["revenues"] == []


# ── NaN handling ─────────────────────────────────────────────────────────────────

def test_nan_values_excluded():
    import numpy as np
    inc = pd.DataFrame(
        {"Total Revenue": [500.0, float("nan"), 400.0]},
        index=["FY2024", "FY2023", "FY2022"],
    ).T
    bs  = _make_balance([300, 280, 260], [100, 95, 90], [50, 45, 40], [150, 140, 130])
    cf  = _make_cashflow([60, 55, 50], [40, 38, 35])
    result = extract_india_key_figures("TEST.NS", inc, bs, cf, PROMOTER, PRICE)
    assert float("nan") not in result["revenues"]
    assert 400.0 in result["revenues"]
