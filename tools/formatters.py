"""Verdict card formatter — renders the orchestrator output as a terminal string."""
from typing import Any

_SEP = "━" * 42
_SIGNAL_EMOJI: dict[str, str] = {"bullish": "✅", "neutral": "🟡", "bearish": "❌"}
_AGENT_LABELS: dict[str, str] = {
    "quality_agent": "Quality Agent",
    "value_agent": "Value Agent",
    "bear_case_agent": "Bear Case Agent",
    "growth_agent": "Growth Agent",
    "momentum_agent": "Momentum Agent",
    "sentiment_agent": "Sentiment Agent",
    "macro_agent": "Macro Agent",
}
_ACTIONS: dict[str, str] = {
    "BUY": "Consider initiating a position; set a limit order near current levels.",
    "WATCH": "Monitor for a better entry price or clearer fundamental trajectory.",
    "AVOID": "Stay on the sidelines until the identified red flags are resolved.",
}


def format_verdict_card(verdict: dict[str, Any]) -> str:
    """Render a final verdict dict as a human-readable terminal card.

    Args:
        verdict: output from orchestrator.synthesize()
    """
    ticker = verdict.get("ticker", "")
    currency = "₹" if ticker.endswith((".NS", ".BO")) else "$"

    lines: list[str] = [
        _SEP,
        f"STOCK:  {ticker}",
        f"DATE:   {(verdict.get('generated_at') or '')[:10]}",
        _SEP,
    ]

    lines += _section_verdict(verdict, currency)
    lines += [""]
    lines += _section_agent_signals(verdict)
    lines += [""]
    lines += _section_bull_reasons(verdict)
    lines += [""]
    lines += _section_risks(verdict)
    lines += [""]
    lines += _section_what_changes_mind(verdict)

    pf = verdict.get("portfolio_fit", "")
    if pf:
        lines += ["", "PORTFOLIO FIT:", f"  {pf}"]

    lines.append(_SEP)
    return "\n".join(lines)


# ── Sections ────────────────────────────────────────────────────────────────────

def _section_verdict(verdict: dict[str, Any], currency: str) -> list[str]:
    verd = verdict.get("verdict") or "—"
    conv = verdict.get("conviction")
    fv = verdict.get("fair_value")
    cp = verdict.get("current_price")
    upside = verdict.get("upside_pct")

    conv_str = f"{conv:.1f} / 10" if conv is not None else "—"

    if fv and cp:
        fv_str = f"{currency}{fv:,.2f}  (current: {currency}{cp:,.2f}  →  {upside:+.1f}%)"
    else:
        fv_str = "Insufficient data to estimate"

    return [
        f"VERDICT:     {verd}",
        f"CONVICTION:  {conv_str}",
        f"FAIR VALUE:  {fv_str}",
        f"ACTION:      {_ACTIONS.get(verd, '—')}",
    ]


def _section_agent_signals(verdict: dict[str, Any]) -> list[str]:
    signals = verdict.get("agent_signals") or []
    if not signals:
        return ["AGENT SIGNALS:", "  (none)"]

    lines = ["AGENT SIGNALS:"]
    for agent in signals:
        name = _AGENT_LABELS.get(agent.get("agent", ""), agent.get("agent", "unknown"))
        emoji = _SIGNAL_EMOJI.get(agent.get("signal", ""), " ?")
        score = agent.get("score")
        score_str = f"{score:.1f}/10" if score is not None else "  —  "
        summary = agent.get("summary", "")
        lines.append(f"  {name:<16}  {emoji}  {score_str}  {summary}")
    return lines


def _section_bull_reasons(verdict: dict[str, Any]) -> list[str]:
    reasons = (verdict.get("bull_reasons") or [])[:3]
    lines = ["TOP 3 BULL REASONS:"]
    if not reasons:
        lines.append("  (none provided)")
    else:
        for i, r in enumerate(reasons, 1):
            lines.append(f"  {i}. {r}")
    return lines


def _section_risks(verdict: dict[str, Any]) -> list[str]:
    risks = (verdict.get("risks") or [])[:3]
    lines = ["TOP 3 RISKS:"]
    if not risks:
        lines.append("  (none provided)")
    else:
        for i, r in enumerate(risks, 1):
            lines.append(f"  {i}. {r}")
    return lines


def _section_what_changes_mind(verdict: dict[str, Any]) -> list[str]:
    wcm = verdict.get("what_changes_mind") or {}
    lines = ["WHAT WOULD CHANGE MY MIND:"]
    if wcm.get("bull"):
        lines.append(f"  → Strong Buy if:  {wcm['bull']}")
    if wcm.get("bear"):
        lines.append(f"  → Exit/Avoid if:  {wcm['bear']}")
    if not wcm:
        lines.append("  (not specified)")
    return lines
