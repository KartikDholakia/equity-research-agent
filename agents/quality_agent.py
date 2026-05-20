"""Quality agent — evaluates business quality from fundamental financial data."""
from datetime import datetime, timezone
from typing import Any

# Scoring weights (sum to 10.0)
_W_ROE = 2.5       # Return on Equity — measures profit generated per ₹ of shareholder capital
_W_ROCE = 1.5      # Return on Capital Employed — efficiency of total capital (debt + equity)
_W_FCF = 2.0       # Free Cash Flow consistency — cash actually left after capex (hard to fake)
_W_OCF = 1.5       # Operating Cash Flow vs Net Income — divergence signals earnings manipulation
_W_DEBT = 1.5      # Debt/Equity ratio — balance sheet risk and financial leverage
_W_INTEREST = 1.0  # Interest Coverage — ability to service debt from operating profits


def analyze(
    ticker: str,
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
    cash_flows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run quality checks and return the standard agent output dict.

    Args:
        ticker: stock symbol e.g. "AAPL"
        income_statements: from fmp.fetch_income_statement()
        balance_sheets: from fmp.fetch_balance_sheet()
        cash_flows: from fmp.fetch_cash_flow()
    """

    roe = _check_roe(income_statements, balance_sheets)
    roce = _check_roce(income_statements, balance_sheets)
    fcf = _check_fcf(cash_flows)
    ocf = _check_ocf_vs_profit(income_statements, cash_flows)
    debt = _check_debt(balance_sheets)
    interest = _check_interest_coverage(income_statements)

    score = round(
        roe["points"] + roce["points"] + fcf["points"]
        + ocf["points"] + debt["points"] + interest["points"],
        2,
    )
    flags = roe["flags"] + roce["flags"] + fcf["flags"] + ocf["flags"] + debt["flags"] + interest["flags"]

    return {
        "agent": "quality_agent",
        "ticker": ticker,
        "signal": _signal(score),
        "score": score,
        "summary": _summary(score, flags, roe, fcf),
        "details": {"roe": roe, "roce": roce, "fcf": fcf, "ocf_vs_profit": ocf, "debt": debt, "interest_coverage": interest},
        "flags": flags,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Checks ─────────────────────────────────────────────────────────────────────

def _check_roe(
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
) -> dict[str, Any]:
    """ROE = Net Income / Shareholder Equity. Target: >15% consistently."""

    values = []
    for inc, bal in zip(income_statements, balance_sheets):
        equity = bal.get("totalStockholdersEquity") or bal.get("totalEquity") or 0
        if equity > 0:
            values.append(round((inc.get("netIncome") or 0) / equity * 100, 2))

    if not values:
        return {"values_pct": [], "avg_pct": None, "consistent": False, "points": 0.0, "flags": ["ROE data unavailable"]}

    avg = round(sum(values) / len(values), 2)
    consistent = sum(1 for v in values if v > 15) >= len(values) * 0.6

    if avg >= 20 and consistent:
        pts = _W_ROE
    elif avg >= 15 and consistent:
        pts = _W_ROE * 0.8
    elif avg >= 15:
        pts = _W_ROE * 0.6
    elif avg >= 10:
        pts = _W_ROE * 0.3
    else:
        pts = 0.0

    return {
        "values_pct": values,
        "avg_pct": avg,
        "consistent": consistent,
        "points": round(pts, 2),
        "flags": [f"Low average ROE: {avg:.1f}%"] if avg < 10 else [],
    }


def _check_roce(
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
) -> dict[str, Any]:
    """ROCE = Operating Income / Capital Employed. Target: >15%."""

    values = []
    for inc, bal in zip(income_statements, balance_sheets):
        capital_employed = (bal.get("totalAssets") or 0) - (bal.get("totalCurrentLiabilities") or 0)
        if capital_employed > 0:
            values.append(round((inc.get("operatingIncome") or 0) / capital_employed * 100, 2))

    if not values:
        return {"values_pct": [], "avg_pct": None, "points": 0.0, "flags": ["ROCE data unavailable"]}

    avg = round(sum(values) / len(values), 2)
    pts = _W_ROCE if avg >= 20 else (_W_ROCE * 0.7 if avg >= 15 else (_W_ROCE * 0.3 if avg >= 10 else 0.0))

    return {
        "values_pct": values,
        "avg_pct": avg,
        "points": round(pts, 2),
        "flags": [f"Low average ROCE: {avg:.1f}%"] if avg < 10 else [],
    }


def _check_fcf(cash_flows: list[dict[str, Any]]) -> dict[str, Any]:
    """FCF should be positive in at least 3 of last 5 years."""

    values = [cf.get("freeCashFlow") for cf in cash_flows if cf.get("freeCashFlow") is not None]

    if not values:
        return {"values": [], "positive_years": None, "total_years": None, "points": 0.0, "flags": ["FCF data unavailable"]}

    pos = sum(1 for v in values if v and v > 0)
    n = len(values)
    pts = _W_FCF if pos >= n else (_W_FCF * 0.7 if pos >= n * 0.6 else (_W_FCF * 0.3 if pos >= n * 0.4 else 0.0))

    return {
        "values": values,
        "positive_years": pos,
        "total_years": n,
        "points": round(pts, 2),
        "flags": [f"FCF negative in {n - pos} of {n} years"] if pos < n * 0.6 else [],
    }


def _check_ocf_vs_profit(
    income_statements: list[dict[str, Any]],
    cash_flows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Operating cash flow should be >= net income (earnings quality check)."""

    paired = sorted(
        zip(income_statements, cash_flows),
        key=lambda t: t[0].get("date", ""),
        reverse=True,  # most recent first
    )
    years = []
    for inc, cf in paired:
        net_income = inc.get("netIncome") or 0
        ocf = cf.get("operatingCashFlow") or 0
        years.append({"net_income": net_income, "ocf": ocf, "ocf_gte_profit": ocf >= net_income})

    if not years:
        return {"years": [], "consecutive_gaps": 0, "points": 0.0, "flags": ["OCF data unavailable"]}

    # Count consecutive most-recent-first years where OCF < net income
    consecutive_gaps = 0
    for yr in years:
        if not yr["ocf_gte_profit"]:
            consecutive_gaps += 1
        else:
            break

    if consecutive_gaps >= 2:
        pts, flags = 0.0, [f"OCF below net income for {consecutive_gaps} consecutive years — earnings quality concern"]
    elif consecutive_gaps == 1:
        pts, flags = _W_OCF * 0.4, ["OCF below net income in most recent year — monitor"]
    else:
        pts, flags = _W_OCF, []

    return {"years": years, "consecutive_gaps": consecutive_gaps, "points": round(pts, 2), "flags": flags}


def _check_debt(balance_sheets: list[dict[str, Any]]) -> dict[str, Any]:
    """Debt/Equity < 1.5 for non-financial companies."""

    values = []
    for bal in balance_sheets:
        equity = bal.get("totalStockholdersEquity") or bal.get("totalEquity") or 0
        if equity > 0:
            values.append(round((bal.get("totalDebt") or 0) / equity, 2))

    if not values:
        return {"values": [], "latest": None, "points": 0.0, "flags": ["Debt/Equity data unavailable"]}

    latest = values[0]
    pts = _W_DEBT if latest < 0.5 else (_W_DEBT * 0.8 if latest < 1.0 else (_W_DEBT * 0.5 if latest < 1.5 else 0.0))

    return {
        "values": values,
        "latest": latest,
        "points": round(pts, 2),
        "flags": [f"High Debt/Equity: {latest:.2f}x"] if latest >= 1.5 else [],
    }


def _check_interest_coverage(income_statements: list[dict[str, Any]]) -> dict[str, Any]:
    """Interest coverage = EBIT / Interest Expense. Target: >3x."""

    values = []
    for inc in income_statements:
        interest = abs(inc.get("interestExpense") or 0)
        if interest > 0:
            values.append(round((inc.get("operatingIncome") or 0) / interest, 2))

    # No interest expense means no debt — full points
    if not values:
        return {"values": [], "latest": None, "points": _W_INTEREST, "flags": []}

    latest = values[0]
    pts = _W_INTEREST if latest >= 10 else (_W_INTEREST * 0.7 if latest >= 5 else (_W_INTEREST * 0.4 if latest >= 3 else 0.0))

    return {
        "values": values,
        "latest": latest,
        "points": round(pts, 2),
        "flags": [f"Weak interest coverage: {latest:.1f}x (min: 3x)"] if latest < 3 else [],
    }


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _signal(score: float) -> str:
    return "bullish" if score >= 7.0 else ("neutral" if score >= 4.0 else "bearish")


def _summary(score: float, flags: list[str], roe: dict, fcf: dict) -> str:
    avg_roe = roe.get("avg_pct")
    pos = fcf.get("positive_years")
    total = fcf.get("total_years")
    roe_str = f"Average ROE {avg_roe:.1f}%." if avg_roe is not None else "ROE data unavailable."
    fcf_str = f"FCF positive {pos}/{total} years." if pos is not None else "FCF data unavailable."
    flag_str = f" Key concern: {flags[0]}." if flags else " No major red flags."
    return f"{roe_str} {fcf_str}{flag_str}"
