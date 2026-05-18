"""Bear case agent — screens for auto-reject red flags from SPEC.md."""
from datetime import datetime, timezone
from typing import Any

# Scoring weights (sum to 10.0)
_W_CFQ = 4.0       # Cash flow quality — OCF vs net income (hardest signal to fake)
_W_RECV = 3.0      # Receivables growth vs revenue — revenue recognition quality
_W_DEBT_GR = 3.0   # Debt growth vs revenue — balance sheet deterioration


def analyze(
    ticker: str,
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
    cash_flows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check for auto-reject red flags and return the standard agent output dict.

    Args:
        ticker: stock symbol e.g. "AAPL"
        income_statements: from fmp.fetch_income_statement() — annual, newest first
        balance_sheets: from fmp.fetch_balance_sheet()
        cash_flows: from fmp.fetch_cash_flow()
    """
    cfq = _check_cash_flow_quality(income_statements, cash_flows)
    recv = _check_receivables_growth(income_statements, balance_sheets)
    debt_gr = _check_debt_growth(income_statements, balance_sheets)

    score = round(cfq["points"] + recv["points"] + debt_gr["points"], 2)
    flags = cfq["flags"] + recv["flags"] + debt_gr["flags"]
    auto_rejected = cfq["auto_reject"] or debt_gr["auto_reject"]

    return {
        "agent": "bear_case_agent",
        "ticker": ticker,
        "signal": "bearish" if auto_rejected else _signal(score),
        "score": score,
        "summary": _summary(flags, auto_rejected),
        "details": {
            "cash_flow_quality": cfq,
            "receivables_growth": recv,
            "debt_growth": debt_gr,
            "manual_checks_required": [
                "Auditor resignation or unexplained auditor change",
                "Unusual or large related-party transactions",
                "Active regulatory investigation (SEBI, SEC, etc.)",
                "Promoter pledging > 30% (India only — check Screener.in)",
            ],
        },
        "flags": flags,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Checks ─────────────────────────────────────────────────────────────────────

def _check_cash_flow_quality(
    income_statements: list[dict[str, Any]],
    cash_flows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Auto-reject if OCF < net income for 2+ consecutive recent years."""
    paired = sorted(
        zip(income_statements, cash_flows),
        key=lambda t: t[0].get("date", ""),
        reverse=True,
    )
    years = [
        {
            "date": inc.get("date", ""),
            "net_income": inc.get("netIncome") or 0,
            "ocf": cf.get("operatingCashFlow") or 0,
            "ocf_gte_profit": (cf.get("operatingCashFlow") or 0) >= (inc.get("netIncome") or 0),
        }
        for inc, cf in paired
    ]

    if not years:
        return {"years": [], "consecutive_gaps": 0, "auto_reject": False, "points": _W_CFQ, "flags": []}

    consecutive_gaps = 0
    for yr in years:
        if not yr["ocf_gte_profit"]:
            consecutive_gaps += 1
        else:
            break

    if consecutive_gaps >= 2:
        return {
            "years": years, "consecutive_gaps": consecutive_gaps,
            "auto_reject": True, "points": 0.0,
            "flags": [f"AUTO-REJECT: Cash flow below reported profit for {consecutive_gaps} consecutive years"],
        }
    if consecutive_gaps == 1:
        return {
            "years": years, "consecutive_gaps": 1,
            "auto_reject": False, "points": _W_CFQ * 0.4,
            "flags": ["OCF below net income in most recent year — monitor closely"],
        }
    return {"years": years, "consecutive_gaps": 0, "auto_reject": False, "points": _W_CFQ, "flags": []}


def _check_receivables_growth(
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Flag if accounts receivable grow > 1.5× revenue for 2+ consecutive years."""
    paired = sorted(
        zip(income_statements, balance_sheets),
        key=lambda t: t[0].get("date", ""),
        reverse=True,
    )
    rows = list(paired)

    if len(rows) < 3:
        return {"ratios": [], "bad_years": 0, "points": _W_RECV, "flags": []}

    ratios = []
    for i in range(len(rows) - 1):
        inc_cur, bal_cur = rows[i]
        inc_prev, bal_prev = rows[i + 1]
        recv_cur = bal_cur.get("netReceivables") or bal_cur.get("accountsReceivable") or 0
        recv_prev = bal_prev.get("netReceivables") or bal_prev.get("accountsReceivable") or 0
        rev_cur = inc_cur.get("revenue") or 0
        rev_prev = inc_prev.get("revenue") or 0
        if recv_prev > 0 and rev_prev > 0:
            rg = (recv_cur - recv_prev) / recv_prev
            vg = (rev_cur - rev_prev) / rev_prev
            ratios.append({"recv_growth_pct": round(rg * 100, 1), "rev_growth_pct": round(vg * 100, 1), "flagged": vg > 0 and rg > vg * 1.5})

    if len(ratios) < 2:
        return {"ratios": ratios, "bad_years": 0, "points": _W_RECV, "flags": []}

    bad_years = sum(1 for r in ratios if r["flagged"])

    if bad_years >= 2:
        return {
            "ratios": ratios, "bad_years": bad_years,
            "points": 0.0,
            "flags": [f"Receivables growing > 1.5× revenue for {bad_years} years — revenue recognition concern"],
        }
    if bad_years == 1:
        return {
            "ratios": ratios, "bad_years": 1,
            "points": _W_RECV * 0.5,
            "flags": ["Receivables outpaced revenue growth in 1 recent year — monitor"],
        }
    return {"ratios": ratios, "bad_years": 0, "points": _W_RECV, "flags": []}


def _check_debt_growth(
    income_statements: list[dict[str, Any]],
    balance_sheets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Auto-reject if total debt grows faster than revenue for 3+ consecutive years."""
    paired = sorted(
        zip(income_statements, balance_sheets),
        key=lambda t: t[0].get("date", ""),
        reverse=True,
    )
    rows = list(paired)

    if len(rows) < 4:
        return {"year_flags": [], "consecutive_years": 0, "auto_reject": False, "points": _W_DEBT_GR, "flags": []}

    year_flags = []
    for i in range(len(rows) - 1):
        inc_cur, bal_cur = rows[i]
        inc_prev, bal_prev = rows[i + 1]
        debt_cur = bal_cur.get("totalDebt") or 0
        debt_prev = bal_prev.get("totalDebt") or 0
        rev_cur = inc_cur.get("revenue") or 0
        rev_prev = inc_prev.get("revenue") or 0
        if debt_prev > 0 and rev_prev > 0:
            year_flags.append((debt_cur - debt_prev) / debt_prev > (rev_cur - rev_prev) / rev_prev)
        else:
            year_flags.append(False)

    consecutive = 0
    for flag in year_flags:
        if flag:
            consecutive += 1
        else:
            break

    formatted = [{"debt_grew_faster_than_revenue": f} for f in year_flags]

    if consecutive >= 3:
        return {
            "year_flags": formatted, "consecutive_years": consecutive,
            "auto_reject": True, "points": 0.0,
            "flags": [f"AUTO-REJECT: Debt growing faster than revenue for {consecutive} consecutive years"],
        }
    if consecutive >= 2:
        return {
            "year_flags": formatted, "consecutive_years": consecutive,
            "auto_reject": False, "points": _W_DEBT_GR * 0.3,
            "flags": [f"Debt growing faster than revenue for {consecutive} consecutive years — warning"],
        }
    return {"year_flags": formatted, "consecutive_years": consecutive, "auto_reject": False, "points": _W_DEBT_GR, "flags": []}


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _signal(score: float) -> str:
    return "bullish" if score >= 7.0 else ("neutral" if score >= 4.0 else "bearish")


def _summary(flags: list[str], auto_rejected: bool) -> str:
    if auto_rejected:
        trigger = next((f for f in flags if "AUTO-REJECT" in f), flags[0])
        return f"AUTO-REJECT triggered. {trigger}. Do not invest without thorough investigation."
    if flags:
        return f"{len(flags)} warning(s) found. Key concern: {flags[0]}. No auto-reject criteria met."
    return "No auto-reject red flags detected in quantitative data. Manual checks still required."
