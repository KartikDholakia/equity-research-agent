"""Orchestrator — routes queries and synthesizes agent outputs into verdict cards."""
import concurrent.futures
import sys
from datetime import datetime, timezone
from typing import Any

from agents import bear_case_agent, growth_agent, quality_agent, value_agent
from data import fmp, screener, yfinance_client
from tools.formatters import format_verdict_card
from tools.key_figures import extract_df_key_figures, extract_key_figures

# Conviction weights (Phase 2 — 4 agents)
_W_QUALITY = 0.35
_W_VALUE   = 0.25
_W_GROWTH  = 0.20
_W_BEAR    = 0.20


def get_verdict_data(
    ticker: str, market: str = "us"
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (verdict_dict, key_figures) without printing — for web UI use."""
    data = _fetch_data(ticker, market)
    agent_outputs = _run_agents(ticker, data)
    verdict = _synthesize(ticker, agent_outputs, data)
    return verdict, data["key_figures"]


def run_analysis(ticker: str, market: str = "us") -> None:
    """Full single-stock analysis: fetch data, run agents, synthesize, print."""
    print(f"\nAnalyzing {ticker} ({market.upper()}) — fetching data ...\n")
    try:
        verdict, _ = get_verdict_data(ticker, market)
        print(format_verdict_card(verdict))
    except Exception as exc:
        print(f"Analysis failed for {ticker}: {exc}")
        sys.exit(1)


# ── Routing stubs — wire up in later phases ─────────────────────────────────────

def run_screen(market: str) -> None:
    """Phase 4: run monthly screener for a market."""
    raise NotImplementedError("Screener ships in Phase 4.")


def run_review() -> None:
    """Phase 6: portfolio review across all holdings."""
    raise NotImplementedError("Portfolio review ships in Phase 6.")


def run_allocate(amount: float) -> None:
    """Phase 6: ranked candidates with suggested ₹/$ allocation."""
    raise NotImplementedError("Allocation query ships in Phase 6.")


# ── Data fetching ────────────────────────────────────────────────────────────────

def _is_india(ticker: str) -> bool:
    return ticker.upper().endswith(".NS") or ticker.upper().endswith(".BO")


def _fetch_data(ticker: str, market: str) -> dict[str, Any]:
    """Fetch all required data sources in parallel, then extract key figures."""
    if _is_india(ticker):
        return _fetch_data_india(ticker)
    return _fetch_data_us(ticker)


def _fetch_data_us(ticker: str) -> dict[str, Any]:
    fns = {
        "income_statements": lambda: fmp.fetch_income_statement(ticker),
        "balance_sheets":    lambda: fmp.fetch_balance_sheet(ticker),
        "cash_flows":        lambda: fmp.fetch_cash_flow(ticker),
        "key_metrics":       lambda: fmp.fetch_key_metrics(ticker),
        "price_data":        lambda: yfinance_client.fetch_current_price(ticker),
        "company_name":      lambda: yfinance_client.fetch_company_name(ticker),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {key: pool.submit(fn) for key, fn in fns.items()}
        raw: dict[str, Any] = {key: fut.result() for key, fut in futures.items()}

    raw["price_data"]["company_name"] = raw.pop("company_name")
    raw["key_figures"] = extract_key_figures(
        ticker,
        raw["income_statements"],
        raw["balance_sheets"],
        raw["cash_flows"],
        raw["key_metrics"],
        raw["price_data"],
    )
    raw["india"] = False
    return raw


def _fetch_data_india(ticker: str) -> dict[str, Any]:
    slug = ticker.upper().rsplit(".", 1)[0]
    fns = {
        "fundamentals": lambda: yfinance_client.fetch_fundamentals_yfinance(ticker),
        "price_data":   lambda: yfinance_client.fetch_current_price(ticker),
        "promoter":     lambda: screener.fetch_promoter_holding(slug),
        "fii":          lambda: screener.fetch_fii_dii_trends(slug),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {key: pool.submit(fn) for key, fn in fns.items()}
        raw: dict[str, Any] = {key: fut.result() for key, fut in futures.items()}

    fundamentals = raw["fundamentals"]
    promoter_data: dict[str, Any] = {**raw["promoter"], **raw["fii"]}
    p_err = raw["promoter"].get("error")
    f_err = raw["fii"].get("error")
    if p_err and f_err:
        promoter_data["error"] = f"promoter: {p_err}; fii: {f_err}"

    raw["key_figures"] = extract_df_key_figures(
        ticker,
        fundamentals["income_stmt"],
        fundamentals["balance_sheet"],
        fundamentals["cashflow"],
        promoter_data,
        raw["price_data"],
        fundamentals["info"],
    )
    raw["india"] = True
    return raw


# ── Agent execution ──────────────────────────────────────────────────────────────

def _run_agents(ticker: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Run all four agents in parallel and return their output dicts."""
    key_figures = data["key_figures"]
    fns = [
        lambda: quality_agent.analyze(ticker, key_figures),
        lambda: value_agent.analyze(ticker, key_figures),
        lambda: growth_agent.analyze(ticker, key_figures),
        lambda: bear_case_agent.analyze(ticker, key_figures),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
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
    growth  = by_name.get("growth_agent", {})
    bear    = by_name.get("bear_case_agent", {})

    conviction = round(
        _W_QUALITY * (quality.get("score") or 0)
        + _W_VALUE  * (value.get("score")   or 0)
        + _W_GROWTH * (growth.get("score")  or 0)
        + _W_BEAR   * (bear.get("score")    or 0),
        1,
    )

    auto_rejected = bear.get("signal") == "bearish" and any(
        "AUTO-REJECT" in f for f in (bear.get("flags") or [])
    )
    verdict = "AVOID" if auto_rejected else _verdict_label(conviction)

    current_price = float((data["price_data"].get("price")) or 0)
    fair_value    = _extract_fair_value(value)
    upside_pct    = (
        round((fair_value - current_price) / current_price * 100, 1)
        if fair_value and current_price else None
    )

    all_flags = [f for a in agent_outputs for f in (a.get("flags") or [])]

    result: dict[str, Any] = {
        "ticker":             ticker,
        "verdict":            verdict,
        "conviction":         conviction,
        "fair_value":         fair_value,
        "current_price":      current_price or None,
        "upside_pct":         upside_pct,
        "bull_reasons":       _bull_reasons(quality, value, growth, bear),
        "risks":              all_flags[:3] or ["No quantitative flags — run manual bear-case checks"],
        "what_changes_mind":  _what_changes_mind(verdict),
        "portfolio_fit":      "Portfolio context unavailable (Phase 5) — assess sector and sizing manually.",
        "agent_signals":      agent_outputs,
        "generated_at":       datetime.now(timezone.utc).isoformat(),
    }

    return result


def _extract_fair_value(value: dict[str, Any]) -> float | None:
    """Average DCF base-case and Graham number when both are available."""
    details    = value.get("details") or {}
    dcf        = details.get("compute_dcf") or {}
    graham     = details.get("compute_graham") or {}
    candidates = [
        v for v in (dcf.get("base"), graham.get("graham_number"))
        if v is not None and v > 0
    ]
    return round(sum(candidates) / len(candidates), 2) if candidates else None


def _verdict_label(conviction: float) -> str:
    if conviction >= 6.5:
        return "BUY"
    if conviction >= 4.5:
        return "WATCH"
    return "AVOID"


def _bull_reasons(
    quality: dict,
    value: dict,
    growth: dict,
    bear: dict,
) -> list[str]:
    """Extract up to 3 positive bullets from non-bearish agent summaries."""
    reasons: list[str] = []
    for agent in (quality, value, growth, bear):
        if agent.get("signal") == "bearish":
            continue
        summary = (agent.get("summary") or "").strip()
        if not summary:
            continue
        bullets = [p.strip() for p in summary.split("•") if p.strip()]
        for b in bullets:
            if len(reasons) >= 3:
                break
            lower = b.lower()
            if any(w in lower for w in ("overval", "risk", "concern", "flag", "stretched", "premium")):
                continue
            reasons.append(b)
    return reasons[:3] if reasons else ["No quantitative bull case identified — manual review required"]


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
