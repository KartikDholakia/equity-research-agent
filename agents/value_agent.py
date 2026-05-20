"""Value agent — estimates intrinsic value via DCF, Graham formula, PEG, and P/E history."""
from datetime import datetime, timezone
from typing import Any

# Scoring weights (sum to 10.0)
_W_DCF = 3.0       # DCF valuation — present value of projected free cash flows
_W_GRAHAM = 2.5    # Graham number — conservative floor based on earnings and book value
_W_PEG = 2.0       # PEG ratio — P/E relative to earnings growth (Lynch's core metric)
_W_PE_HIST = 1.5   # P/E vs own 5yr average — cheap/expensive relative to own history

# DCF model parameters — isolate here so Phase 3 can derive growth from history instead
_DCF_DISCOUNT_RATE = 0.10    # cost of equity
_DCF_TERMINAL_GROWTH = 0.03  # perpetual growth after horizon
_DCF_HORIZON = 10            # projection years
_DCF_GROWTH_BEAR = 0.05
_DCF_GROWTH_BASE = 0.10
_DCF_GROWTH_BULL = 0.15


def analyze(
    ticker: str,
    key_metrics: list[dict[str, Any]],
    price_data: dict[str, Any],
) -> dict[str, Any]:
    """Run valuation checks and return the standard agent output dict.

    Args:
        ticker: stock symbol e.g. "AAPL"
        key_metrics: from fmp.fetch_key_metrics() — 5 years of annual metrics
        price_data: from yfinance_client.fetch_current_price()
    """
    current_price = float(price_data.get("price") or 0)

    dcf = _check_dcf(key_metrics, current_price)
    graham = _check_graham(key_metrics, current_price)
    peg = _check_peg(key_metrics)
    pe_hist = _check_pe_history(key_metrics)

    score = round(
        dcf["points"] + graham["points"] + peg["points"] + pe_hist["points"],
        2,
    )
    flags = dcf["flags"] + graham["flags"] + peg["flags"] + pe_hist["flags"]
    fair_value = _fair_value(dcf, graham)

    return {
        "agent": "value_agent",
        "ticker": ticker,
        "signal": _signal(score),
        "score": score,
        "summary": _summary(current_price, fair_value, flags),
        "details": {
            "current_price": current_price,
            "fair_value_estimate": fair_value,
            "dcf": dcf,
            "graham": graham,
            "peg": peg,
            "pe_history": pe_hist,
        },
        "flags": flags,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Checks ─────────────────────────────────────────────────────────────────────

def _check_dcf(key_metrics: list[dict[str, Any]], current_price: float) -> dict[str, Any]:
    """3-scenario DCF using FCF per share from key metrics."""
    fcf_ps = key_metrics[0].get("freeCashFlowPerShare") if key_metrics else None

    if not fcf_ps or fcf_ps <= 0 or current_price <= 0:
        return {
            "bear": None, "base": None, "bull": None,
            "margin_of_safety_base_pct": None,
            "points": 0.0,
            "flags": ["DCF unavailable — negative or missing FCF per share"],
        }

    bear = _dcf_intrinsic_value(fcf_ps, _DCF_GROWTH_BEAR)
    base = _dcf_intrinsic_value(fcf_ps, _DCF_GROWTH_BASE)
    bull = _dcf_intrinsic_value(fcf_ps, _DCF_GROWTH_BULL)
    mos = round((base - current_price) / base * 100, 1)

    pts = _W_DCF if mos >= 30 else (_W_DCF * 0.7 if mos >= 15 else (_W_DCF * 0.4 if mos >= 0 else 0.0))

    return {
        "bear": round(bear, 2),
        "base": round(base, 2),
        "bull": round(bull, 2),
        "margin_of_safety_base_pct": mos,
        "points": round(pts, 2),
        "flags": [f"Overvalued vs DCF base by {abs(mos):.0f}%"] if mos < -10 else [],
    }


def _dcf_intrinsic_value(fcf0: float, growth_rate: float) -> float:
    """10-year discounted cash flow model with terminal value."""
    pv = 0.0
    for yr in range(1, _DCF_HORIZON + 1):
        pv += fcf0 * (1 + growth_rate) ** yr / (1 + _DCF_DISCOUNT_RATE) ** yr
    terminal_fcf = fcf0 * (1 + growth_rate) ** _DCF_HORIZON * (1 + _DCF_TERMINAL_GROWTH)
    terminal_pv = terminal_fcf / (_DCF_DISCOUNT_RATE - _DCF_TERMINAL_GROWTH)
    pv += terminal_pv / (1 + _DCF_DISCOUNT_RATE) ** _DCF_HORIZON
    return pv


def _check_graham(key_metrics: list[dict[str, Any]], current_price: float) -> dict[str, Any]:
    """Graham number = sqrt(22.5 × EPS × BVPS). Only valid for positive EPS and book value."""
    if not key_metrics:
        return {"value": None, "points": 0.0, "flags": ["Graham data unavailable"]}

    eps = key_metrics[0].get("netIncomePerShare")
    bvps = key_metrics[0].get("bookValuePerShare")

    if not eps or eps <= 0 or not bvps or bvps <= 0 or current_price <= 0:
        return {
            "value": None, "eps": eps, "bvps": bvps,
            "points": 0.0,
            "flags": ["Graham formula N/A — negative or missing EPS / book value"],
        }

    graham_value = round((22.5 * eps * bvps) ** 0.5, 2)
    mos = round((graham_value - current_price) / graham_value * 100, 1)
    pts = _W_GRAHAM if mos >= 30 else (_W_GRAHAM * 0.7 if mos >= 15 else (_W_GRAHAM * 0.4 if mos >= 0 else 0.0))

    return {
        "value": graham_value,
        "eps": round(eps, 2),
        "bvps": round(bvps, 2),
        "margin_of_safety_pct": mos,
        "points": round(pts, 2),
        "flags": [f"Trading {abs(mos):.0f}% above Graham value"] if mos < -10 else [],
    }


def _check_peg(key_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """PEG < 1.0 suggests undervalued growth; > 2.0 signals expensive."""
    peg = key_metrics[0].get("pegRatio") if key_metrics else None

    if peg is None or peg <= 0:
        return {"value": None, "points": 0.0, "flags": []}

    pts = _W_PEG if peg < 1.0 else (_W_PEG * 0.6 if peg < 1.5 else (_W_PEG * 0.2 if peg < 2.0 else 0.0))

    return {
        "value": round(peg, 2),
        "points": round(pts, 2),
        "flags": [f"PEG elevated at {peg:.1f}x"] if peg >= 2.0 else [],
    }


def _check_pe_history(key_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare current P/E to own 5-year average — cheap relative to own history."""
    pe_values = [m["peRatio"] for m in key_metrics if (m.get("peRatio") or 0) > 0]

    if len(pe_values) < 2:
        return {"current": None, "avg_5yr": None, "pct_vs_avg": None, "points": 0.0, "flags": []}

    current_pe = pe_values[0]
    avg_5yr = round(sum(pe_values) / len(pe_values), 2)
    pct_vs_avg = round((current_pe - avg_5yr) / avg_5yr * 100, 1)

    # Negative = trading below own historical average (value signal)
    pts = _W_PE_HIST if pct_vs_avg <= -20 else (_W_PE_HIST * 0.6 if pct_vs_avg <= -5 else (_W_PE_HIST * 0.3 if pct_vs_avg <= 10 else 0.0))

    return {
        "current": round(current_pe, 2),
        "avg_5yr": avg_5yr,
        "pct_vs_avg": pct_vs_avg,
        "points": round(pts, 2),
        "flags": [f"P/E is {pct_vs_avg:.0f}% above own 5yr average"] if pct_vs_avg > 30 else [],
    }



# ── Helpers ─────────────────────────────────────────────────────────────────────

def _fair_value(dcf: dict, graham: dict) -> float | None:
    """Average DCF base-case and Graham value when both are available."""
    candidates = [v for v in (dcf.get("base"), graham.get("value")) if v is not None and v > 0]
    return round(sum(candidates) / len(candidates), 2) if candidates else None


def _signal(score: float) -> str:
    return "bullish" if score >= 7.0 else ("neutral" if score >= 4.0 else "bearish")


def _summary(current_price: float, fair_value: float | None, flags: list[str]) -> str:
    if fair_value and current_price > 0:
        upside = round((fair_value - current_price) / current_price * 100, 1)
        val_str = f"Fair value est. ${fair_value:.2f} vs current ${current_price:.2f} ({upside:+.1f}% upside)."
    else:
        val_str = "Fair value could not be estimated from available data."
    flag_str = f" Key concern: {flags[0]}." if flags else " No major valuation red flags."
    return f"{val_str}{flag_str}"
