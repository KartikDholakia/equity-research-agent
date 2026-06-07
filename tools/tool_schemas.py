"""Anthropic tool definitions for the metrics tool pool + submit_analysis."""
from typing import Any

_FLOAT_LIST: dict[str, Any] = {"type": "array", "items": {"type": "number"}}

COMPUTATION_TOOLS: list[dict[str, Any]] = [
    {
        "name": "compute_roe_trend",
        "description": "Compute Return on Equity for each year (newest first). Returns avg and 15%+ consistency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "net_incomes": {**_FLOAT_LIST, "description": "Net income each year, newest first"},
                "equities":    {**_FLOAT_LIST, "description": "Shareholder equity each year, newest first"},
            },
            "required": ["net_incomes", "equities"],
        },
    },
    {
        "name": "compute_roce_trend",
        "description": "Compute Return on Capital Employed (operating income / capital employed) for each year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "operating_incomes":   {**_FLOAT_LIST, "description": "Operating income each year, newest first"},
                "total_assets":        {**_FLOAT_LIST, "description": "Total assets each year, newest first"},
                "current_liabilities": {**_FLOAT_LIST, "description": "Current liabilities each year, newest first"},
            },
            "required": ["operating_incomes", "total_assets", "current_liabilities"],
        },
    },
    {
        "name": "compute_fcf_consistency",
        "description": "Count positive free cash flow years. Returns fcf_values, positive_years, total_years.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fcfs": {**_FLOAT_LIST, "description": "Free cash flow each year, newest first"},
            },
            "required": ["fcfs"],
        },
    },
    {
        "name": "compute_ocf_quality",
        "description": "Count consecutive recent years where operating cash flow < net income (earnings quality check).",
        "input_schema": {
            "type": "object",
            "properties": {
                "ocfs":        {**_FLOAT_LIST, "description": "Operating cash flow each year, newest first"},
                "net_incomes": {**_FLOAT_LIST, "description": "Net income each year, newest first"},
            },
            "required": ["ocfs", "net_incomes"],
        },
    },
    {
        "name": "compute_debt_ratio",
        "description": "Compute Debt/Equity ratio for each year. Returns de_ratios list and latest value.",
        "input_schema": {
            "type": "object",
            "properties": {
                "total_debts": {**_FLOAT_LIST, "description": "Total debt each year, newest first"},
                "equities":    {**_FLOAT_LIST, "description": "Shareholder equity each year, newest first"},
            },
            "required": ["total_debts", "equities"],
        },
    },
    {
        "name": "compute_interest_coverage",
        "description": "Compute interest coverage ratio (operating income / interest expense) for each year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "operating_incomes": {**_FLOAT_LIST, "description": "Operating income each year, newest first"},
                "interest_expenses": {**_FLOAT_LIST, "description": "Interest expense (absolute value) each year, newest first"},
            },
            "required": ["operating_incomes", "interest_expenses"],
        },
    },
    {
        "name": "compute_dcf",
        "description": "3-scenario DCF valuation (bear 5%, base 10%, bull 15% growth). Returns intrinsic value per share and margin of safety.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fcf_yield":     {"type": ["number", "null"], "description": "Free cash flow yield (freeCashFlowYield from FMP)"},
                "current_price": {"type": ["number", "null"], "description": "Current stock price"},
            },
            "required": ["fcf_yield", "current_price"],
        },
    },
    {
        "name": "compute_graham",
        "description": "Graham number margin of safety. Returns graham_number and margin_of_safety_pct.",
        "input_schema": {
            "type": "object",
            "properties": {
                "graham_number": {"type": ["number", "null"], "description": "Graham number from FMP key metrics"},
                "current_price": {"type": ["number", "null"], "description": "Current stock price"},
            },
            "required": ["graham_number", "current_price"],
        },
    },
    {
        "name": "compute_peg",
        "description": "Interpret PEG ratio. Returns peg_ratio and interpretation (undervalued_growth/fair/slightly_expensive/expensive).",
        "input_schema": {
            "type": "object",
            "properties": {
                "peg_ratio": {"type": ["number", "null"], "description": "PEG ratio from FMP key metrics"},
            },
            "required": ["peg_ratio"],
        },
    },
    {
        "name": "compute_pe_history",
        "description": "Current P/E vs own 5-year average P/E, derived from earnings yields. Returns current_pe, avg_5yr_pe, pct_vs_avg.",
        "input_schema": {
            "type": "object",
            "properties": {
                "earnings_yields": {**_FLOAT_LIST, "description": "Earnings yield (EPS/price) each year, newest first"},
            },
            "required": ["earnings_yields"],
        },
    },
    {
        "name": "compute_revenue_cagr",
        "description": "Revenue compound annual growth rate over available history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "revenues": {**_FLOAT_LIST, "description": "Annual revenue, newest first"},
            },
            "required": ["revenues"],
        },
    },
    {
        "name": "compute_cash_flow_quality",
        "description": "Bear-case check: returns consecutive_gaps (years OCF < net income) and auto_reject flag (True if >= 2 consecutive).",
        "input_schema": {
            "type": "object",
            "properties": {
                "ocfs":        {**_FLOAT_LIST, "description": "Operating cash flow each year, newest first"},
                "net_incomes": {**_FLOAT_LIST, "description": "Net income each year, newest first"},
            },
            "required": ["ocfs", "net_incomes"],
        },
    },
    {
        "name": "compute_receivables_growth",
        "description": "Flag years where receivables grew > 1.5x revenue growth (revenue recognition risk). Returns bad_years count.",
        "input_schema": {
            "type": "object",
            "properties": {
                "net_receivables": {**_FLOAT_LIST, "description": "Net receivables each year, newest first"},
                "revenues":        {**_FLOAT_LIST, "description": "Revenue each year, newest first"},
            },
            "required": ["net_receivables", "revenues"],
        },
    },
    {
        "name": "compute_debt_growth",
        "description": "Bear-case check: debt growing faster than revenue. Returns consecutive_years and auto_reject (True if >= 3 consecutive).",
        "input_schema": {
            "type": "object",
            "properties": {
                "total_debts": {**_FLOAT_LIST, "description": "Total debt each year, newest first"},
                "revenues":    {**_FLOAT_LIST, "description": "Revenue each year, newest first"},
            },
            "required": ["total_debts", "revenues"],
        },
    },
]

SUBMIT_TOOL: dict[str, Any] = {
    "name": "submit_analysis",
    "description": "Submit your final analysis result. Call this once you have computed all relevant metrics and are ready to deliver your verdict.",
    "input_schema": {
        "type": "object",
        "properties": {
            "signal": {
                "type": "string",
                "enum": ["bullish", "neutral", "bearish"],
                "description": "Overall signal",
            },
            "score": {
                "type": "number",
                "description": "Conviction score 0.0 to 10.0",
            },
            "summary": {
                "type": "string",
                "description": "2-3 bullet points (each starting with '• ') referencing specific numbers. One bullet per key insight. No prose paragraphs.",
            },
            "flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Red flags found; empty list if none. Prefix auto-reject flags with 'AUTO-REJECT:'",
            },
        },
        "required": ["signal", "score", "summary", "flags"],
    },
}

ALL_TOOLS: list[Any] = COMPUTATION_TOOLS + [SUBMIT_TOOL]
