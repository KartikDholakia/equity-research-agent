"""Layer 3 — tool pool: Python compute functions that return numbers, no verdicts."""
from typing import Any

_DCF_DISCOUNT_RATE   = 0.10
_DCF_TERMINAL_GROWTH = 0.03
_DCF_HORIZON         = 10


# ── Quality metrics ──────────────────────────────────────────────────────────────

def compute_roe_trend(net_incomes: list[float], equities: list[float]) -> dict[str, Any]:
    """ROE = net income / equity for each year, newest first."""
    pairs = list(zip(net_incomes, equities))
    if not pairs:
        return {"roe_values_pct": [], "avg_pct": None, "consistent_above_15": False}
    values = [round(ni / eq * 100, 2) for ni, eq in pairs if eq > 0]
    if not values:
        return {"roe_values_pct": [], "avg_pct": None, "consistent_above_15": False}
    avg = round(sum(values) / len(values), 2)
    consistent = sum(1 for v in values if v > 15) >= len(values) * 0.6
    return {"roe_values_pct": values, "avg_pct": avg, "consistent_above_15": consistent}


def compute_roce_trend(
    operating_incomes: list[float],
    total_assets: list[float],
    current_liabilities: list[float],
) -> dict[str, Any]:
    """ROCE = operating income / (total assets − current liabilities), newest first."""
    triples = list(zip(operating_incomes, total_assets, current_liabilities))
    if not triples:
        return {"roce_values_pct": [], "avg_pct": None}
    values = [
        round(oi / (ta - cl) * 100, 2)
        for oi, ta, cl in triples
        if (ta - cl) > 0
    ]
    if not values:
        return {"roce_values_pct": [], "avg_pct": None}
    avg = round(sum(values) / len(values), 2)
    return {"roce_values_pct": values, "avg_pct": avg}


def compute_fcf_consistency(fcfs: list[float]) -> dict[str, Any]:
    """Count positive free cash flow years."""
    if not fcfs:
        return {"fcf_values": [], "positive_years": 0, "total_years": 0}
    pos = sum(1 for v in fcfs if v > 0)
    return {"fcf_values": fcfs, "positive_years": pos, "total_years": len(fcfs)}


def compute_ocf_quality(ocfs: list[float], net_incomes: list[float]) -> dict[str, Any]:
    """Count consecutive recent years where OCF < net income (earnings quality)."""
    pairs = list(zip(ocfs, net_incomes))
    if not pairs:
        return {"years": 0, "consecutive_gaps": 0}
    consecutive = 0
    for ocf, ni in pairs:
        if ocf < ni:
            consecutive += 1
        else:
            break
    return {"years": len(pairs), "consecutive_gaps": consecutive}


def compute_debt_ratio(total_debts: list[float], equities: list[float]) -> dict[str, Any]:
    """Debt/Equity ratio for each year, newest first."""
    pairs = list(zip(total_debts, equities))
    if not pairs:
        return {"de_ratios": [], "latest": None}
    ratios = [round(d / e, 2) for d, e in pairs if e > 0]
    return {"de_ratios": ratios, "latest": ratios[0] if ratios else None}


def compute_interest_coverage(
    operating_incomes: list[float],
    interest_expenses: list[float],
) -> dict[str, Any]:
    """Interest coverage = operating income / interest expense, newest first."""
    if not interest_expenses:
        return {"coverage_values": [], "latest": None, "no_debt": True}
    pairs = list(zip(operating_incomes, interest_expenses))
    if not pairs:
        return {"coverage_values": [], "latest": None, "no_debt": True}
    values = [round(oi / ie, 2) for oi, ie in pairs if ie > 0]
    return {"coverage_values": values, "latest": values[0] if values else None, "no_debt": False}


# ── Valuation metrics ────────────────────────────────────────────────────────────

def compute_dcf(fcf_yield: float | None, current_price: float | None) -> dict[str, Any]:
    """3-scenario DCF. fcf_yield is freeCashFlowYield from FMP key metrics."""
    if not fcf_yield or not current_price or current_price <= 0 or fcf_yield <= 0:
        return {"bear": None, "base": None, "bull": None, "margin_of_safety_base_pct": None}
    fcf_ps = fcf_yield * current_price
    bear = _dcf_value(fcf_ps, 0.05)
    base = _dcf_value(fcf_ps, 0.10)
    bull = _dcf_value(fcf_ps, 0.15)
    mos  = round((base - current_price) / base * 100, 1) if base > 0 else None
    return {
        "bear": round(bear, 2),
        "base": round(base, 2),
        "bull": round(bull, 2),
        "margin_of_safety_base_pct": mos,
    }


def _dcf_value(fcf0: float, growth_rate: float) -> float:
    pv = 0.0
    for yr in range(1, _DCF_HORIZON + 1):
        pv += fcf0 * (1 + growth_rate) ** yr / (1 + _DCF_DISCOUNT_RATE) ** yr
    terminal_fcf = fcf0 * (1 + growth_rate) ** _DCF_HORIZON * (1 + _DCF_TERMINAL_GROWTH)
    terminal_pv  = terminal_fcf / (_DCF_DISCOUNT_RATE - _DCF_TERMINAL_GROWTH)
    pv += terminal_pv / (1 + _DCF_DISCOUNT_RATE) ** _DCF_HORIZON
    return pv


def compute_graham(graham_number: float | None, current_price: float | None) -> dict[str, Any]:
    """Graham number margin of safety vs current price."""
    if not graham_number or not current_price or current_price <= 0 or graham_number <= 0:
        return {"graham_number": None, "margin_of_safety_pct": None}
    mos = round((graham_number - current_price) / graham_number * 100, 1)
    return {"graham_number": round(graham_number, 2), "margin_of_safety_pct": mos}


def compute_peg(peg_ratio: float | None) -> dict[str, Any]:
    """Interpret PEG ratio (P/E divided by EPS growth rate)."""
    if peg_ratio is None or peg_ratio <= 0:
        return {"peg_ratio": None, "interpretation": "unavailable"}
    if peg_ratio < 1.0:
        interp = "undervalued_growth"
    elif peg_ratio < 1.5:
        interp = "fair"
    elif peg_ratio < 2.0:
        interp = "slightly_expensive"
    else:
        interp = "expensive"
    return {"peg_ratio": round(peg_ratio, 2), "interpretation": interp}


def compute_pe_history(earnings_yields: list[float]) -> dict[str, Any]:
    """Current P/E vs own 5-year average, derived from earnings yields."""
    if len(earnings_yields) < 2:
        return {"pe_values": [], "current_pe": None, "avg_5yr_pe": None, "pct_vs_avg": None}
    pe_values = [round(1 / ey, 2) for ey in earnings_yields if ey > 0]
    if not pe_values:
        return {"pe_values": [], "current_pe": None, "avg_5yr_pe": None, "pct_vs_avg": None}
    current = pe_values[0]
    avg     = round(sum(pe_values) / len(pe_values), 2)
    pct     = round((current - avg) / avg * 100, 1) if avg else None
    return {"pe_values": pe_values, "current_pe": current, "avg_5yr_pe": avg, "pct_vs_avg": pct}


def compute_revenue_cagr(revenues: list[float]) -> dict[str, Any]:
    """Revenue CAGR over available years (newest first)."""
    if len(revenues) < 2:
        return {"cagr_pct": None, "years": len(revenues)}
    oldest, newest = revenues[-1], revenues[0]
    n = len(revenues) - 1
    if oldest <= 0:
        return {"cagr_pct": None, "years": n}
    cagr = round(((newest / oldest) ** (1 / n) - 1) * 100, 2)
    return {"cagr_pct": cagr, "years": n}


# ── Bear-case metrics ────────────────────────────────────────────────────────────

def compute_cash_flow_quality(ocfs: list[float], net_incomes: list[float]) -> dict[str, Any]:
    """Auto-reject check: OCF < net income for 2+ consecutive recent years."""
    pairs = list(zip(ocfs, net_incomes))
    if not pairs:
        return {"consecutive_gaps": 0, "auto_reject": False}
    consecutive = 0
    for ocf, ni in pairs:
        if ocf < ni:
            consecutive += 1
        else:
            break
    return {"consecutive_gaps": consecutive, "auto_reject": consecutive >= 2}


def compute_receivables_growth(
    net_receivables: list[float],
    revenues: list[float],
) -> dict[str, Any]:
    """Flag years where receivables grew > 1.5× revenue growth (revenue recognition risk)."""
    n = min(len(net_receivables), len(revenues))
    if n < 3:
        return {"bad_years": 0, "ratios": []}
    ratios = []
    for i in range(n - 1):
        recv_cur, recv_prev = net_receivables[i], net_receivables[i + 1]
        rev_cur,  rev_prev  = revenues[i],         revenues[i + 1]
        if recv_prev > 0 and rev_prev > 0:
            rg = (recv_cur - recv_prev) / recv_prev
            vg = (rev_cur  - rev_prev)  / rev_prev
            ratios.append({
                "recv_growth_pct": round(rg * 100, 1),
                "rev_growth_pct":  round(vg * 100, 1),
                "flagged": vg > 0 and rg > vg * 1.5,
            })
    bad_years = sum(1 for r in ratios if r["flagged"])
    return {"bad_years": bad_years, "ratios": ratios}


def compute_debt_growth(
    total_debts: list[float],
    revenues: list[float],
) -> dict[str, Any]:
    """Auto-reject check: debt growing faster than revenue for 3+ consecutive years."""
    n = min(len(total_debts), len(revenues))
    if n < 4:
        return {"consecutive_years": 0, "auto_reject": False, "year_flags": []}
    year_flags = []
    for i in range(n - 1):
        debt_cur, debt_prev = total_debts[i], total_debts[i + 1]
        rev_cur,  rev_prev  = revenues[i],    revenues[i + 1]
        if debt_prev > 0 and rev_prev > 0:
            year_flags.append(
                (debt_cur - debt_prev) / debt_prev > (rev_cur - rev_prev) / rev_prev
            )
        else:
            year_flags.append(False)
    consecutive = 0
    for f in year_flags:
        if f:
            consecutive += 1
        else:
            break
    return {
        "consecutive_years": consecutive,
        "auto_reject": consecutive >= 3,
        "year_flags": [{"debt_grew_faster_than_revenue": f} for f in year_flags],
    }


# ── Dispatch table ───────────────────────────────────────────────────────────────

TOOL_DISPATCH: dict[str, Any] = {
    "compute_roe_trend":         compute_roe_trend,
    "compute_roce_trend":        compute_roce_trend,
    "compute_fcf_consistency":   compute_fcf_consistency,
    "compute_ocf_quality":       compute_ocf_quality,
    "compute_debt_ratio":        compute_debt_ratio,
    "compute_interest_coverage": compute_interest_coverage,
    "compute_dcf":               compute_dcf,
    "compute_graham":            compute_graham,
    "compute_peg":               compute_peg,
    "compute_pe_history":        compute_pe_history,
    "compute_revenue_cagr":      compute_revenue_cagr,
    "compute_cash_flow_quality": compute_cash_flow_quality,
    "compute_receivables_growth": compute_receivables_growth,
    "compute_debt_growth":       compute_debt_growth,
}
