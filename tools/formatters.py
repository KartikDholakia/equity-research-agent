"""Verdict card formatter — renders the orchestrator output as a terminal string."""
from typing import Any

_SEP  = "━" * 52
_DIV  = "─" * 52
_SIGNAL_EMOJI: dict[str, str] = {"bullish": "✅", "neutral": "🟡", "bearish": "❌"}
_VERDICT_EMOJI: dict[str, str] = {"BUY": "🟢", "WATCH": "🟡", "AVOID": "🔴"}
_AGENT_LABELS: dict[str, str] = {
    "quality_agent":   "Quality",
    "value_agent":     "Value",
    "bear_case_agent": "Bear Case",
    "growth_agent":    "Growth",
    "momentum_agent":  "Momentum",
    "sentiment_agent": "Sentiment",
    "macro_agent":     "Macro",
}
_ACTIONS: dict[str, str] = {
    "BUY":   "Consider initiating a position near current levels.",
    "WATCH": "Monitor for a better entry price or improved fundamentals.",
    "AVOID": "Stay on the sidelines until red flags are resolved.",
}
_INDIA_TAX_NOTE = (
    "LTCG >₹1 lakh taxed at 12.5% (equity held >1 year). "
    "STCG taxed at 20% (held ≤1 year). STT applies on all trades."
)


def format_verdict_card(verdict: dict[str, Any]) -> str:
    """Render a final verdict dict as a human-readable terminal card."""
    ticker   = verdict.get("ticker", "")
    currency = "₹" if ticker.upper().endswith((".NS", ".BO")) else "$"
    date_str = (verdict.get("generated_at") or "")[:10]

    lines: list[str] = [
        "",
        _SEP,
        f"  {ticker}  ·  {date_str}",
        _SEP,
        "",
    ]

    lines += _section_verdict(verdict, currency)
    lines += ["", _DIV]
    lines += _section_agent_signals(verdict)
    lines += ["", _DIV]
    lines += _section_bull_reasons(verdict)
    lines += ["", _DIV]
    lines += _section_risks(verdict)
    lines += ["", _DIV]
    lines += _section_what_changes_mind(verdict)

    pf = verdict.get("portfolio_fit", "")
    if pf:
        lines += ["", _DIV, f"🗂️  PORTFOLIO FIT", "", f"  {pf}"]

    if ticker.upper().endswith((".NS", ".BO")):
        lines += ["", _DIV, "💡  INDIA TAX NOTE", "",
                  f"  {_INDIA_TAX_NOTE}"]

    lines += ["", _SEP, ""]
    return "\n".join(lines)


# ── Sections ────────────────────────────────────────────────────────────────────

def _section_verdict(verdict: dict[str, Any], currency: str) -> list[str]:
    verd   = verdict.get("verdict") or "—"
    conv   = verdict.get("conviction")
    fv     = verdict.get("fair_value")
    cp     = verdict.get("current_price")
    upside = verdict.get("upside_pct")

    vemoji   = _VERDICT_EMOJI.get(verd, "")
    conv_str = f"{conv:.1f} / 10" if conv is not None else "—"

    if fv and cp:
        fv_str = f"{currency}{fv:,.2f}  (current {currency}{cp:,.2f}  ·  {upside:+.1f}%)"
    else:
        fv_str = "Insufficient data"

    return [
        f"  {vemoji}  VERDICT     {verd}  ({conv_str})",
        f"  💰  FAIR VALUE  {fv_str}",
        f"  🎯  ACTION      {_ACTIONS.get(verd, '—')}",
    ]


def _section_agent_signals(verdict: dict[str, Any]) -> list[str]:
    signals = verdict.get("agent_signals") or []
    lines   = ["🤖  AGENT SIGNALS", ""]
    for agent in signals:
        name    = _AGENT_LABELS.get(agent.get("agent", ""), agent.get("agent", ""))
        emoji   = _SIGNAL_EMOJI.get(agent.get("signal", ""), "❓")
        score   = agent.get("score")
        score_s = f"{score:.1f}/10" if score is not None else "—"
        summary = agent.get("summary", "").strip()
        lines.append(f"  {emoji}  {name:<10}  {score_s}")
        for bullet in _bullets(summary):
            lines.append(f"             {bullet}")
        lines.append("")
    return lines


def _section_bull_reasons(verdict: dict[str, Any]) -> list[str]:
    reasons = (verdict.get("bull_reasons") or [])[:3]
    lines   = ["🐂  BULL CASE", ""]
    if not reasons:
        lines.append("  • No quantitative bull case identified")
    for r in reasons:
        for bullet in _bullets(r):
            lines.append(f"  {bullet}")
    return lines


def _section_risks(verdict: dict[str, Any]) -> list[str]:
    risks = (verdict.get("risks") or [])[:3]
    lines = ["🐻  RISKS", ""]
    if not risks:
        lines.append("  • No quantitative flags raised")
    for r in risks:
        lines.append(f"  ⚠️  {r}")
    return lines


def _section_what_changes_mind(verdict: dict[str, Any]) -> list[str]:
    wcm   = verdict.get("what_changes_mind") or {}
    lines = ["🔄  WHAT CHANGES MY MIND", ""]
    if wcm.get("bull"):
        lines.append(f"  📈  {wcm['bull']}")
    if wcm.get("bear"):
        lines.append(f"  📉  {wcm['bear']}")
    if not wcm:
        lines.append("  (not specified)")
    return lines


# ── Helpers ──────────────────────────────────────────────────────────────────────

def _bullets(text: str) -> list[str]:
    """Split a bullet-point summary into individual lines.

    Handles both pre-formatted '• ...' bullets and plain text fallback.
    """
    if not text:
        return []
    if "•" in text:
        parts = [p.strip() for p in text.split("•") if p.strip()]
        return [f"• {p}" for p in parts]
    return [f"• {text}"]
