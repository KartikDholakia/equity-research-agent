"""FastAPI web app — wraps agents/orchestrator.py with an HTML research UI."""
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agents.orchestrator import get_verdict_data

_HERE = Path(__file__).parent

app = FastAPI(title="Equity Research")
app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")
templates = Jinja2Templates(directory=_HERE / "templates")


@app.get("/", response_class=HTMLResponse)
def get_index(request: Request) -> Any:
    """Render the ticker-input form."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/demo", response_class=HTMLResponse)
def get_demo(request: Request) -> Any:
    """Render the verdict page with hardcoded sample data for UI review."""
    verdict = {
        "ticker": "ZOMATO.NS",
        "verdict": "WATCH",
        "conviction": 5.8,
        "fair_value": 198.40,
        "current_price": 234.75,
        "upside_pct": -15.5,
        "bull_reasons": [
            "• Revenue CAGR of 68.2% over 3 years reflects genuine hyper-growth in food delivery penetration across Tier-1 and Tier-2 cities, with GOV growing faster than the market.",
            "• Zomato turned FCF-positive in FY24 for the first time, signalling an inflection in unit economics — a hallmark of platform businesses reaching operating leverage.",
            "• Blinkit integration is showing strong early metrics with dark-store count doubling YoY; quick commerce is a structurally large TAM with Zomato well-positioned as a first mover.",
        ],
        "risks": [
            "AUTO-REJECT risk: promoter holding near zero — institutional float risk if FII sentiment turns",
            "Current P/E unavailable (loss-making on reported basis); FCF yield thin at 0.4% — any growth miss reprices the stock severely",
            "Swiggy is well-funded and intensifying competition in both food delivery and quick commerce; price wars could compress margins before they fully establish",
        ],
        "what_changes_mind": {
            "bull":  "Buy trigger: price falls below ₹185 (approx. 25% discount to DCF base case) or Blinkit contribution margin turns positive for 2 consecutive quarters",
            "bear":  "Exit trigger: GOV growth decelerates below 20% YoY or D/E exceeds 0.5× due to Blinkit capex burn",
        },
        "portfolio_fit": "Portfolio context unavailable (Phase 6) — assess sector and sizing manually.",
        "agent_signals": [
            {
                "agent":   "quality_agent",
                "ticker":  "ZOMATO.NS",
                "signal":  "bullish",
                "score":   7.2,
                "summary": "• Zomato's adjusted EBITDA margin expanded from -28% to +4.5% in two years — a rapid improvement in unit economics that Munger would describe as a business finding its moat. OCF turned positive in FY24.\n• Key concern is near-zero promoter holding (Info Edge has been trimming) and high receivables growth — both demand close monitoring before initiating a meaningful position.",
                "flags":   ["Promoter holding near 0% — institutional float risk"],
                "details": {},
                "timestamp": "2026-06-24T08:31:00+00:00",
            },
            {
                "agent":   "value_agent",
                "ticker":  "ZOMATO.NS",
                "signal":  "bearish",
                "score":   2.5,
                "summary": "• At ₹234.75, Zomato trades at a significant premium to the DCF base case of ₹198.40 (-15.5% margin of safety) and the bear case of ₹142.10, offering no margin of safety by Graham's standards.\n• FCF yield of 0.4% (3yr avg) is insufficient to support current valuation; the Graham Number is not meaningful for a company with negligible book equity — this is a pure growth bet priced for perfection.",
                "flags":   [
                    "OVERVALUED: Stock at ₹234.75 trades 18.3% above DCF base case of ₹198.40",
                    "FCF yield of 0.4% is too thin for a margin-of-safety entry",
                    "Graham Number not applicable — book value near zero",
                ],
                "details": {},
                "timestamp": "2026-06-24T08:31:00+00:00",
            },
            {
                "agent":   "growth_agent",
                "ticker":  "ZOMATO.NS",
                "signal":  "bullish",
                "score":   7.8,
                "summary": "• Revenue CAGR of 68.2% over 3 years is exceptional and broad-based — food delivery GOV, Blinkit, and B2B Hyperpure all growing. Lynch would categorise this as a fast-grower with a large unaddressed market.\n• EPS CAGR is not calculable (company in transition to profitability), but management guidance for EBITDA breakeven by FY26 on all segments is credible given trajectory. Forward P/E of 112× demands execution — any slip will be punished.",
                "flags":   ["EPS CAGR unavailable — company not yet fully profitable on reported basis"],
                "details": {},
                "timestamp": "2026-06-24T08:31:00+00:00",
            },
            {
                "agent":   "bear_case_agent",
                "ticker":  "ZOMATO.NS",
                "signal":  "neutral",
                "score":   5.8,
                "summary": "• No AUTO-REJECT flags triggered. Debt is negligible, OCF is positive, and receivables growth is in line with revenue growth. The balance sheet is clean.\n• Primary concern is competitive intensity from Swiggy and the capital requirements of Blinkit's dark-store expansion — neither is an auto-reject but both are watch items that could deteriorate quickly.",
                "flags":   [
                    "Receivables growing faster than revenue in 2 of 3 years — monitor for channel stuffing",
                    "Blinkit capex trajectory could pressure FCF in FY26 if store rollout accelerates",
                ],
                "details": {},
                "timestamp": "2026-06-24T08:31:00+00:00",
            },
        ],
        "generated_at": "2026-06-24T08:31:00+00:00",
    }

    key_figures = {
        "ticker":               "ZOMATO.NS",
        "company_name":         "Zomato Limited",
        "current_price":        234.75,
        "revenues":             [32492000000, 19498000000, 11462000000, 5765000000],
        "net_incomes":          [3510000000, -9710000000, -10560000000, -8160000000],
        "operating_incomes":    [4120000000, -5820000000, -9870000000, -7420000000],
        "interest_expenses":    [420000000, 380000000, 290000000],
        "equities":             [98420000000, 95210000000, 104830000000, 112400000000],
        "total_assets":         [124600000000, 118400000000, 119200000000, 122100000000],
        "current_liabilities":  [18200000000, 16400000000, 14100000000, 12300000000],
        "total_debts":          [2100000000, 1800000000, 1400000000, 900000000],
        "net_receivables":      [3200000000, 2600000000, 1900000000, 1200000000],
        "ocfs":                 [5840000000, -2910000000, -8420000000, -6110000000],
        "fcfs":                 [1320000000, -5640000000, -11200000000, -7800000000],
        "fcf_yield":            0.004,
        "peg_ratio":            None,
        "graham_number":        None,
        "earnings_yields":      [],
        "promoter_pct":         0.0,
        "pledging_pct":         0.0,
        "fii_trend":            "falling",
        "fii_pct":              18.4,
        "forward_pe":           112.3,
        "promoter_data_available": True,
    }

    dcf = {
        "bear": 142.10,
        "base": 198.40,
        "bull": 287.60,
        "margin_of_safety_base_pct": -15.5,
    }

    return templates.TemplateResponse(
        request,
        "verdict.html",
        {
            "verdict":     verdict,
            "key_figures": key_figures,
            "dcf":         dcf,
            "currency":    "₹",
            "is_india":    True,
        },
    )


@app.get("/research", response_class=HTMLResponse)
def get_research(request: Request, ticker: str = "", market: str = "us") -> Any:
    """Handle nav search bar GET requests by delegating to the POST logic."""
    if not ticker.strip():
        return templates.TemplateResponse(request, "index.html")
    return post_research(request, ticker=ticker, market=market)


@app.post("/research", response_class=HTMLResponse)
def post_research(
    request: Request,
    ticker: str = Form(...),
    market: str = Form("us"),
) -> Any:
    """Run a full analysis and render the verdict page."""
    ticker = ticker.strip().upper()
    market = market.strip().lower()

    try:
        verdict, key_figures = get_verdict_data(ticker, market)
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"error": f"Analysis failed for {ticker}: {exc}"},
            status_code=500,
        )

    is_india = ticker.endswith((".NS", ".BO"))
    currency = "₹" if is_india else "$"

    value_signal = next(
        (a for a in verdict["agent_signals"] if a["agent"] == "value_agent"), {}
    )
    dcf: dict[str, Any] = value_signal.get("details", {}).get("compute_dcf") or {}

    return templates.TemplateResponse(
        request,
        "verdict.html",
        {
            "verdict":     verdict,
            "key_figures": key_figures,
            "dcf":         dcf,
            "currency":    currency,
            "is_india":    is_india,
        },
    )
