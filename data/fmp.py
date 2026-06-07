"""Financial Modeling Prep API client for US stock fundamentals."""
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://financialmodelingprep.com/stable"


def _api_key() -> str:
    """Return the FMP API key, raising clearly if it is missing."""
    key = os.getenv("FMP_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "FMP_API_KEY is not set. Add it to your .env file."
        )
    return key


def _get(endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """GET a FMP endpoint and return the parsed JSON as a list of dicts.

    Raises:
        EnvironmentError: API key missing.
        requests.HTTPError: Non-2xx response.
        ValueError: FMP returned an error payload (bad ticker, expired key, etc.).
    """
    url = f"{BASE_URL}/{endpoint}"
    merged = {"apikey": _api_key(), **(params or {})}

    response = requests.get(url, params=merged, timeout=15)
    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict) and "Error Message" in data:
        raise ValueError(f"FMP API error: {data['Error Message']}")

    # FMP always returns a list for statement endpoints; guard just in case.
    return data if isinstance(data, list) else [data]


def fetch_income_statement(ticker: str, years: int = 5) -> list[dict[str, Any]]:
    """Fetch annual income statements for the last N years.

    Key fields: revenue, grossProfit, operatingIncome, netIncome,
                eps, epsdiluted, ebitda.
    """
    return _get("income-statement", {"symbol": ticker, "period": "annual", "limit": years})


def fetch_balance_sheet(ticker: str, years: int = 5) -> list[dict[str, Any]]:
    """Fetch annual balance sheet statements for the last N years.

    Key fields: totalAssets, totalDebt, totalEquity, cashAndCashEquivalents,
                totalCurrentLiabilities, longTermDebt.
    """
    return _get("balance-sheet-statement", {"symbol": ticker, "period": "annual", "limit": years})


def fetch_cash_flow(ticker: str, years: int = 5) -> list[dict[str, Any]]:
    """Fetch annual cash flow statements for the last N years.

    Key fields: operatingCashFlow, freeCashFlow, capitalExpenditure,
                dividendsPaid, netIncome.
    """
    return _get("cash-flow-statement", {"symbol": ticker, "period": "annual", "limit": years})


def fetch_key_metrics(ticker: str, years: int = 5) -> list[dict[str, Any]]:
    """Fetch annual key metrics for the last N years.

    Key fields: roe, roic, debtToEquity, interestCoverage, peRatio,
                pegRatio, evToEbitda, priceToBookRatio, freeCashFlowYield.
    """
    return _get("key-metrics", {"symbol": ticker, "period": "annual", "limit": years})


def fetch_earnings_history(ticker: str, years: int = 5) -> list[dict[str, Any]]:
    """Fetch historical earnings for the last N years.

    Key fields: date, eps, estimatedEps, revenueEstimated, revenue.
    """
    return _get("earnings", {"symbol": ticker, "limit": years})
