"""Layer 2 — extracts ~15-20 clean key figures from raw financial statements."""
from typing import Any


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
