"""Unit tests for fetch_fundamentals_yfinance in data/yfinance_client.py.

All yfinance network calls are replaced with MagicMocks — no real HTTP.
"""
from unittest.mock import MagicMock, PropertyMock, patch

import pandas as pd
import pytest

from data.yfinance_client import fetch_fundamentals_yfinance

pytestmark = pytest.mark.unit

_TICKER = "ZOMATO.NS"

# ── Minimal realistic DataFrames ──────────────────────────────────────────────


def _income_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            pd.Timestamp("2023-09-30"): [100_000, 80_000, 20_000],
            pd.Timestamp("2022-09-30"): [90_000, 75_000, 15_000],
        },
        index=["Total Revenue", "Cost Of Revenue", "Net Income"],
    )


def _balance_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            pd.Timestamp("2023-09-30"): [500_000, 200_000],
            pd.Timestamp("2022-09-30"): [450_000, 180_000],
        },
        index=["Total Assets", "Total Debt"],
    )


def _cashflow_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            pd.Timestamp("2023-09-30"): [30_000, -5_000],
            pd.Timestamp("2022-09-30"): [25_000, -4_000],
        },
        index=["Operating Cash Flow", "Capital Expenditure"],
    )


def _make_ticker(income=None, balance=None, cashflow=None, info=None, info_raises=False):
    """Build a MagicMock that mimics yf.Ticker."""
    t = MagicMock()
    t.financials = income if income is not None else _income_df()
    t.balance_sheet = balance if balance is not None else _balance_df()
    t.cashflow = cashflow if cashflow is not None else _cashflow_df()
    if info_raises:
        type(t).info = PropertyMock(side_effect=Exception("info endpoint failed"))
    else:
        t.info = info if info is not None else {"forwardPE": 28.5, "pegRatio": 1.2}
    return t


# ── Happy path ────────────────────────────────────────────────────────────────


def test_returns_four_keys():
    with patch("data.yfinance_client.yf.Ticker", return_value=_make_ticker()):
        result = fetch_fundamentals_yfinance(_TICKER)

    assert set(result.keys()) == {"income_stmt", "balance_sheet", "cashflow", "info"}


def test_dataframes_match_mock():
    income = _income_df()
    balance = _balance_df()
    cashflow = _cashflow_df()
    with patch(
        "data.yfinance_client.yf.Ticker",
        return_value=_make_ticker(income=income, balance=balance, cashflow=cashflow),
    ):
        result = fetch_fundamentals_yfinance(_TICKER)

    assert result["income_stmt"].shape == income.shape
    assert result["balance_sheet"].shape == balance.shape
    assert result["cashflow"].shape == cashflow.shape


def test_info_dict_is_passed_through():
    sample_info = {"forwardPE": 35.0, "pegRatio": 2.1, "forwardEps": 12.5}
    with patch(
        "data.yfinance_client.yf.Ticker",
        return_value=_make_ticker(info=sample_info),
    ):
        result = fetch_fundamentals_yfinance(_TICKER)

    assert result["info"]["forwardPE"] == 35.0
    assert result["info"]["pegRatio"] == 2.1


# ── Graceful degradation ──────────────────────────────────────────────────────


def test_info_failure_returns_empty_dict():
    """If yfinance raises on .info, the function must return {} not crash."""
    with patch(
        "data.yfinance_client.yf.Ticker",
        return_value=_make_ticker(info_raises=True),
    ):
        result = fetch_fundamentals_yfinance(_TICKER)

    assert result["info"] == {}


def test_info_none_coerced_to_dict():
    """If .info returns None (yfinance quirk), must be coerced to {}."""
    t = _make_ticker()
    t.info = None
    with patch("data.yfinance_client.yf.Ticker", return_value=t):
        result = fetch_fundamentals_yfinance(_TICKER)

    assert result["info"] == {}


# ── Error path ────────────────────────────────────────────────────────────────


def test_all_empty_raises_value_error():
    """All three DataFrames empty → invalid ticker → ValueError with helpful message."""
    empty = pd.DataFrame()
    with patch(
        "data.yfinance_client.yf.Ticker",
        return_value=_make_ticker(income=empty, balance=empty, cashflow=empty),
    ):
        with pytest.raises(ValueError, match="No fundamental data"):
            fetch_fundamentals_yfinance("INVALID.NS")


def test_partial_data_does_not_raise():
    """Only income_stmt present — should still succeed (not all three empty)."""
    empty = pd.DataFrame()
    with patch(
        "data.yfinance_client.yf.Ticker",
        return_value=_make_ticker(balance=empty, cashflow=empty),
    ):
        result = fetch_fundamentals_yfinance(_TICKER)

    assert not result["income_stmt"].empty
    assert result["balance_sheet"].empty
    assert result["cashflow"].empty
