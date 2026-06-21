# Financial Health Check — 12 Ratio Diagnostic

**What it does:** Calculates 12 key financial ratios across profitability, liquidity, leverage, and efficiency for any company — with trend analysis, peer benchmarking, red flag identification, and a structured output table.

**Best used in:** ChatGPT / Claude (claude.ai)

## Prompt

DIRECTION: Calculate 12 key financial ratios for [COMPANY NAME] across profitability, liquidity,
leverage, and efficiency to assess overall financial health and business quality.

PERSONA: You are a world-class equity research analyst with 20+ years specializing in rigorous
financial statement analysis. Your strength is identifying which metrics matter most and catching
red flags.

INPUT:
- Source: [Latest annual report, Screener.in, attached CSV]
- Period: [3 years: e.g. FY2023, FY2024, FY2025]
- Data format: [Consolidated, INR Crores, TTM or year-end]
- Critical instruction: If data for any ratio is missing or unclear, explicitly flag it.

MEASURE: Calculate and present 12 ratios in table format (3-year period). After calculations,
provide:

1. Quality Checks (100 words): Are all ratios calculable? Any gaps? Values reasonable? Accounting
treatments distorting comparability?

2. Interpretation Summary (300 words):
- Profitability: Healthy margins? Improving or deteriorating?
- Liquidity: Can it meet short-term obligations?
- Leverage: Sustainable? Interest coverage adequate?
- Efficiency: Productive asset use?

3. Peer Benchmark (if available): Compare to industry average. Better or worse than peers?

4. Red Flags (if any):
- Rising debt with declining profitability
- Deteriorating liquidity (current ratio declining)
- Interest coverage below 2x
- Declining efficiency ratios

5. Final Output: Formatted table with all 12 ratios, trend arrows (improving/declining), and
traffic light rating.

Success criteria: Every ratio accurate, traceable, with clear business meaning.
