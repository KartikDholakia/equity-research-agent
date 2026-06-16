"""Layer 2 — extracts ~15-20 clean key figures from raw financial statements."""
from typing import Any

import pandas as pd


def extract_key_figures(
    ticker: str,
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
    cash_flows: list[dict[str, Any]],
    key_metrics: list[dict[str, Any]],
    price_data: dict[str, Any],
) -> dict[str, Any]:
    """Return a compact dict of ~15-20 numbers for LLM agent consumption.

    Rule: no raw statement dumps into the LLM — only this clean dict.
    All lists are newest-first to match FMP's default sort order.
    """
    def _pull(rows: list[dict], field: str) -> list[float]:
        return [float(r[field]) for r in rows if r.get(field) is not None]

    def _equity(bs: dict) -> float | None:
        v = bs.get("totalStockholdersEquity") or bs.get("totalEquity")
        return float(v) if v is not None else None

    return {
        "ticker":              ticker,
        "current_price":       float(price_data.get("price") or 0) or None,
        "revenues":            _pull(income_statements, "revenue"),
        "net_incomes":         _pull(income_statements, "netIncome"),
        "operating_incomes":   _pull(income_statements, "operatingIncome"),
        "interest_expenses":   [
            abs(float(r["interestExpense"]))
            for r in income_statements
            if r.get("interestExpense") is not None
        ],
        "equities":            [e for b in balance_sheets if (e := _equity(b)) is not None],
        "total_assets":        _pull(balance_sheets, "totalAssets"),
        "current_liabilities": _pull(balance_sheets, "totalCurrentLiabilities"),
        "total_debts":         _pull(balance_sheets, "totalDebt"),
        "net_receivables":     [
            float(b.get("netReceivables") or b.get("accountsReceivable") or 0)
            for b in balance_sheets
        ],
        "ocfs":                _pull(cash_flows, "operatingCashFlow"),
        "fcfs":                _pull(cash_flows, "freeCashFlow"),
        "peg_ratio":           key_metrics[0].get("pegRatio") if key_metrics else None,
        "graham_number":       key_metrics[0].get("grahamNumber") if key_metrics else None,
        "fcf_yield":           _avg_fcf_yield(key_metrics, years=3),
        "earnings_yields":     [
            float(m["earningsYield"])
            for m in key_metrics
            if (m.get("earningsYield") or 0) > 0
        ],
    }


def extract_df_key_figures(
    ticker: str,
    income_stmt: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    promoter_data: dict[str, Any],
    price_data: dict[str, Any],
    info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a compact dict of ~20 numbers for LLM agent consumption from yfinance DataFrames.

    Use this when financial data comes from yfinance (rows = metrics, cols = fiscal years).
    Use extract_key_figures() instead when data comes from FMP (list of dicts per year).

    All list fields are newest-first. Promoter/FII fields are included when available and
    are passed through from promoter_data — pass an empty dict if not applicable.
    info: the yfinance ticker.info dict (forwardPE, forwardEps, pegRatio, etc.); pass None
    or omit when not available.
    Rule: no raw DataFrames go into the LLM — only this clean dict.
    """
    _info = info or {}

    def _row(df: pd.DataFrame, *names: str) -> list[float]:
        for name in names:
            if name in df.index:
                return [float(v) for v in df.loc[name].values if not pd.isna(v)]
        return []

    revenues           = _row(income_stmt, "Total Revenue")
    net_incomes        = _row(income_stmt, "Net Income")
    operating_incomes  = _row(income_stmt, "Operating Income", "EBIT")
    ocfs               = _row(cashflow,    "Operating Cash Flow")
    fcfs               = _row(cashflow,    "Free Cash Flow")
    total_assets       = _row(balance_sheet, "Total Assets")
    current_liabilities = _row(balance_sheet, "Current Liabilities", "Total Current Liabilities")
    total_debts        = _row(balance_sheet, "Total Debt", "Long Term Debt")
    equities           = _row(balance_sheet, "Common Stock Equity", "Stockholders Equity", "Total Equity Gross Minority Interest")
    interest_expenses  = [abs(v) for v in _row(income_stmt, "Interest Expense") if v != 0]
    net_receivables    = _row(balance_sheet, "Accounts Receivable", "Net Receivables")

    market_cap = price_data.get("market_cap") or 0
    fcf_yield  = _avg_df_fcf_yield(fcfs, market_cap)

    forward_pe  = _info.get("forwardPE")
    forward_eps = _info.get("forwardEps")
    peg_ratio   = _info.get("pegRatio")

    promoter_pct   = promoter_data.get("promoter_pct")
    pledging_pct   = promoter_data.get("pledging_pct")
    fii_trend      = promoter_data.get("fii_trend")
    fii_pct        = promoter_data.get("fii_pct")

    return {
        "ticker":                   ticker,
        "current_price":            float(price_data.get("price") or 0) or None,
        "revenues":                 revenues,
        "net_incomes":              net_incomes,
        "operating_incomes":        operating_incomes,
        "interest_expenses":        interest_expenses,
        "equities":                 equities,
        "total_assets":             total_assets,
        "current_liabilities":      current_liabilities,
        "total_debts":              total_debts,
        "net_receivables":          net_receivables,
        "ocfs":                     ocfs,
        "fcfs":                     fcfs,
        "fcf_yield":                fcf_yield,
        "peg_ratio":                peg_ratio,
        "forward_pe":               forward_pe,
        "forward_eps":              forward_eps,
        "promoter_pct":             promoter_pct,
        "pledging_pct":             pledging_pct,
        "fii_trend":                fii_trend,
        "fii_pct":                  fii_pct,
        "promoter_data_available":  promoter_pct is not None,
    }


def _avg_df_fcf_yield(fcfs: list[float], market_cap: float, years: int = 3) -> float | None:
    """3-year average FCF / market_cap yield derived from yfinance DataFrames."""
    if not fcfs or not market_cap or market_cap <= 0:
        return None
    yields = [fcf / market_cap for fcf in fcfs[:years]]
    if not yields:
        return None
    avg = sum(yields) / len(yields)
    return round(avg, 6) if avg > 0 else None


def _avg_fcf_yield(key_metrics: list[dict[str, Any]], years: int = 3) -> float | None:
    """3-year average FCF yield, including negative years.

    Using a multi-year average avoids penalising companies that are temporarily
    suppressing FCF through heavy growth capex (e.g. AMZN, NVDA). Negative years
    are included because the capex was real. Returns None if the average is <= 0
    (no DCF possible) or if no data is available.
    """
    yields = [
        float(m["freeCashFlowYield"])
        for m in key_metrics[:years]
        if m.get("freeCashFlowYield") is not None
    ]
    if not yields:
        return None
    avg = sum(yields) / len(yields)
    return round(avg, 6) if avg > 0 else None
