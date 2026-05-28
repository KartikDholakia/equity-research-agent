"""Orchestrator — routes queries and synthesizes agent outputs into verdict cards."""
import concurrent.futures
import sys
from datetime import datetime, timezone
from typing import Any

from agents import bear_case_agent, quality_agent, value_agent
from data import fmp, yfinance_client
from tools.formatters import format_verdict_card

# Conviction weights — quality and value are equal, bear is a pass/fail modifier
_W_QUALITY = 0.40
_W_VALUE = 0.35
_W_BEAR = 0.25


def run_analysis(ticker: str, market: str = "us") -> None:
    """Full single-stock analysis: fetch data, run agents, synthesize, print."""
    print(f"\nAnalyzing {ticker} ({market.upper()}) — fetching data ...\n")
    try:
        data = _fetch_data(ticker, market)
        agent_outputs = _run_agents(ticker, data)
        verdict = _synthesize(ticker, agent_outputs, data)
        print(format_verdict_card(verdict))
    except Exception as exc:
        print(f"Analysis failed for {ticker}: {exc}")
        sys.exit(1)


# ── Routing stubs — wire up in later phases ─────────────────────────────────────

def run_screen(market: str) -> None:
    """Phase 3: run monthly screener for a market."""
    raise NotImplementedError("Screener ships in Phase 3.")


def run_review() -> None:
    """Phase 5: portfolio review across all holdings."""
    raise NotImplementedError("Portfolio review ships in Phase 5.")


def run_allocate(amount: float) -> None:
    """Phase 5: ranked candidates with suggested ₹/$ allocation."""
    raise NotImplementedError("Allocation query ships in Phase 5.")


# ── Data fetching ────────────────────────────────────────────────────────────────

def _fetch_data(ticker: str, market: str) -> dict[str, Any]:
    """Fetch all required data sources in parallel via threads."""
    fns = {
        "income_statements": lambda: fmp.fetch_income_statement(ticker),
        "balance_sheets":    lambda: fmp.fetch_balance_sheet(ticker),
        "cash_flows":        lambda: fmp.fetch_cash_flow(ticker),
        "key_metrics":       lambda: fmp.fetch_key_metrics(ticker),
        "price_data":        lambda: yfinance_client.fetch_current_price(ticker),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {key: pool.submit(fn) for key, fn in fns.items()}
        return {key: fut.result() for key, fut in futures.items()}


# ── Agent execution ──────────────────────────────────────────────────────────────

def _run_agents(ticker: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the three Phase-1 agents in parallel and return their output dicts."""
    fns = [
        lambda: quality_agent.analyze(
            ticker, data["income_statements"], data["balance_sheets"], data["cash_flows"]
        ),
        lambda: value_agent.analyze(
            ticker, data["key_metrics"], data["price_data"]
        ),
        lambda: bear_case_agent.analyze(
            ticker, data["income_statements"], data["balance_sheets"], data["cash_flows"]
        ),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        return [f.result() for f in [pool.submit(fn) for fn in fns]]


# ── Synthesis ────────────────────────────────────────────────────────────────────

def _synthesize(
    ticker: str,
    agent_outputs: list[dict[str, Any]],
    data: dict[str, Any],
) -> dict[str, Any]:
    """Combine agent scores and signals into the final verdict dict."""
    by_name = {a["agent"]: a for a in agent_outputs}
    quality = by_name.get("quality_agent", {})
    value   = by_name.get("value_agent", {})
    bear    = by_name.get("bear_case_agent", {})

    conviction = round(
        _W_QUALITY * (quality.get("score") or 0)
        + _W_VALUE  * (value.get("score")   or 0)
        + _W_BEAR   * (bear.get("score")    or 0),
        1,
    )

    auto_rejected = bear.get("signal") == "bearish" and any(
        "AUTO-REJECT" in f for f in (bear.get("flags") or [])
    )
    verdict = "AVOID" if auto_rejected else _verdict_label(conviction)

    current_price = float((data["price_data"].get("price")) or 0)
    fair_value    = (value.get("details") or {}).get("fair_value_estimate")
    upside_pct    = (
        round((fair_value - current_price) / current_price * 100, 1)
        if fair_value and current_price else None
    )

    all_flags = [f for a in agent_outputs for f in (a.get("flags") or [])]

    return {
        "ticker":             ticker,
        "verdict":            verdict,
        "conviction":         conviction,
        "fair_value":         fair_value,
        "current_price":      current_price or None,
        "upside_pct":         upside_pct,
        "bull_reasons":       _bull_reasons(quality, value, bear),
        "risks":              all_flags[:3] or ["No quantitative flags — run manual bear-case checks"],
        "what_changes_mind":  _what_changes_mind(verdict),
        "portfolio_fit":      "Portfolio context unavailable (Phase 5) — assess sector and sizing manually.",
        "agent_signals":      agent_outputs,
        "generated_at":       datetime.now(timezone.utc).isoformat(),
    }


def _verdict_label(conviction: float) -> str:
    if conviction >= 6.5:
        return "BUY"
    if conviction >= 4.5:
        return "WATCH"
    return "AVOID"


def _bull_reasons(quality: dict, value: dict, bear: dict) -> list[str]:
    reasons: list[str] = []

    avg_roe = (quality.get("details") or {}).get("roe", {}).get("avg_pct")
    if avg_roe and avg_roe >= 15:
        reasons.append(f"Strong ROE averaging {avg_roe:.1f}% — above the 15% quality threshold")

    fv = (value.get("details") or {}).get("fair_value_estimate")
    cp = (value.get("details") or {}).get("current_price")
    if fv and cp and fv > cp:
        reasons.append(
            f"Trading at ~{round((fv - cp) / cp * 100):.0f}% discount to estimated intrinsic value (${fv:,.2f})"
        )

    if bear.get("signal") != "bearish":
        reasons.append("Clean financials — no auto-reject red flags triggered in quantitative checks")

    if not reasons:
        reasons.append("Insufficient data for a quantitative bull thesis — qualitative review required")

    return reasons[:3]


def _what_changes_mind(verdict: str) -> dict[str, str]:
    if verdict == "BUY":
        return {
            "bull":  "Upgrade conviction if next 2 quarters show accelerating revenue + expanding margins",
            "bear":  "Exit if FCF turns negative for 2 consecutive quarters or D/E exceeds 2×",
        }
    if verdict == "WATCH":
        return {
            "bull":  "Buy trigger: price falls to estimated fair value or quality score improves above 7",
            "bear":  "Avoid if any auto-reject flag is triggered (check bear case agent output)",
        }
    return {
        "bull":  "Revisit once auto-reject conditions resolve and conviction rises above 6.5",
        "bear":  "Do not invest until all flagged concerns are addressed",
    }
